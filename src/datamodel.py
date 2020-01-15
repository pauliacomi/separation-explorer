import numpy as np

from bokeh.models import ColumnDataSource
from bokeh.models.callbacks import CustomJS

from src.datastore import DATASET, INITIAL, PROBES, SETTINGS
from src.helpers import load_isotherm as load_isotherm
from src.statistics import select_data, get_isohash, find_nearest
from functools import partial
from threading import Thread
from tornado import gen


################################
# DataModel class
################################

class DataModel():
    """
    Processing of data for a Dashboard.
    """

    def __init__(self, doc):

        # Save reference
        self.doc = doc

        # Dataset
        self._df = DATASET                          # Entire dataset
        self._dfs = INITIAL                         # Pre-processed KPI dataset
        self.ads_list = PROBES                      # All probes in the dashboard
        self.p_range = np.arange(0.5, 20.5, 0.5)

        # Adsorbate definitions
        self.g1 = SETTINGS['g1']
        self.g2 = SETTINGS['g2']

        # Temperature definitions
        self.t_abs = SETTINGS['t_abs']
        self.t_tol = SETTINGS['t_tol']

        # Isotherm type definitions
        self.iso_type = None

        # Pressure definitions
        self.lp = '1'    # 0.5 bar
        self.p1 = '1'    # 0.5 bar
        self.p2 = '10'   # 5.0 bar

        # Bokeh-specific data source generation
        self.data = ColumnDataSource(
            data=self.gen_data(self.lp, self.p1, self.p2))
        self.errors = ColumnDataSource(data=self.gen_error())
        self.g1_iso_sel = ColumnDataSource(data=self.gen_iso_dict())
        self.g2_iso_sel = ColumnDataSource(data=self.gen_iso_dict())

        # Data selection callback
        self.data.selected.on_change('indices', self.selection_callback)
        self.data.js_on_change('data', CustomJS(code="toggleLoading()"))

    def callback_link_sep(self, sep_dash):
        """Link the separation dashboard to the model."""

        # Store reference
        self.sep_dash = sep_dash

        # Data type selections
        def dtype_callback(attr, old, new):
            if new == 0:
                self.iso_type = None
            elif new == 1:
                self.iso_type = 'exp'
            elif new == 2:
                self.iso_type = 'sim'

        self.sep_dash.data_type.on_change('active', dtype_callback)

        # Adsorbate drop-down selections
        def g1_sel_callback(attr, old, new):
            self.g1 = new

        def g2_sel_callback(attr, old, new):
            self.g2 = new

        self.sep_dash.g1_sel.on_change("value", g1_sel_callback)
        self.sep_dash.g2_sel.on_change("value", g2_sel_callback)

        # Temperature selection callback
        def t_abs_callback(attr, old, new):
            self.t_abs = new

        def t_tol_callback(attr, old, new):
            self.t_tol = new

        self.sep_dash.t_absolute.on_change("value", t_abs_callback)
        self.sep_dash.t_tolerance.on_change("value", t_tol_callback)

        # Update callback
        self.sep_dash.process.on_click(self.update_data)

        # Pressure slider
        self.sep_dash.p_slider.on_change(
            'value_throttled', self.uptake_callback)

        # Working capacity slider
        self.sep_dash.wc_slider.on_change('value_throttled', self.wc_callback)

        # Slider limits
        if len(self.data.data['labels']) > 0:
            limit = find_nearest(self.p_range, np.nanmin([
                np.nanmax(self.data.data['L_x']),
                np.nanmax(self.data.data['L_y'])
            ]))
            self.sep_dash.p_slider.end = limit
            self.sep_dash.wc_slider.end = limit

    # #########################################################################
    # Selection update

    def update_data(self):
        """What to do when new data is needed."""

        # Request calculation in separate thread
        Thread(target=self.calculate_data).start()

        # Reset any selected materials
        if self.data.selected.indices:
            self.data.selected.update(indices=[])

        # Update labels
        self.sep_dash.top_graph_labels()

        # Update detail plots
        self.g1_iso_sel.data = self.gen_iso_dict()
        self.g2_iso_sel.data = self.gen_iso_dict()
        self.sep_dash.p_g1iso.title.text = 'Isotherms {0}'.format(self.g1)
        self.sep_dash.p_g2iso.title.text = 'Isotherms {0}'.format(self.g2)

    def calculate_data(self):
        self._dfs = select_data(
            self._df, self.iso_type,
            self.t_abs, self.t_tol,
            self.g1, self.g2
        )
        self.doc.add_next_tick_callback(self.push_data)

    @gen.coroutine
    def push_data(self):
        """Assign data"""
        self.data.data = self.gen_data(self.lp, self.p1, self.p2)

        # Recalculate slider limits
        if len(self.data.data['labels']) > 0:
            limit = find_nearest(self.p_range, np.nanmin([
                np.nanmax(self.data.data['L_x']),
                np.nanmax(self.data.data['L_y'])
            ]))
            self.sep_dash.p_slider.end = limit
            self.sep_dash.wc_slider.end = limit

    # #########################################################################
    # Set up pressure slider and callback

    def uptake_callback(self, attr, old, new):
        """Callback on each pressure selected for uptake."""
        self.lp = str(int(2*new))
        # regenerate graph data
        self.data.patch(self.patch_data_l(self.lp))
        if self.data.selected.indices:
            self.errors.patch(self.patch_error_l(self.data.selected.indices))

    # #########################################################################
    # Set up working capacity slider and callback

    def wc_callback(self, attr, old, new):
        """Callback on pressure range for working capacity."""
        self.p1, self.p2 = str(int(2*new[0])), str(int(2*new[1]))
        # regenerate graph data
        self.data.patch(self.patch_data_w(self.p1, self.p2))
        if self.data.selected.indices:
            self.errors.patch(self.patch_error_wc(self.data.selected.indices))

    # #########################################################################
    # Data generator

    def gen_data(self, lp, p1, p2):
        """Select or generate all KPI data for a pair of ads_list."""

        if self._dfs is None:
            return {
                'labels': [], 'sel': [], 'psa_W': [],
                'K_x': [], 'K_y': [], 'K_nx': [], 'K_ny': [], 'K_n': [],
                'L_x': [], 'L_y': [], 'L_nx': [], 'L_ny': [], 'L_n': [],
                'W_x': [], 'W_y': [], 'W_nx': [], 'W_ny': [], 'W_n': [],
            }

        # Henry coefficient
        K_x = self._dfs[('kH_x', 'med')]
        K_y = self._dfs[('kH_y', 'med')]
        K_nx = self._dfs[('kH_x', 'size')]
        K_ny = self._dfs[('kH_y', 'size')]
        K_n = K_nx + K_ny

        # Loading
        L_x, L_y, L_nx, L_ny, L_n = 0, 0, 0, 0, 0
        if self.lp != '0':

            L_x = self._dfs[(f'{lp}_x', 'med')]
            L_y = self._dfs[(f'{lp}_y', 'med')]
            L_nx = self._dfs[(f'{lp}_x', 'size')]
            L_ny = self._dfs[(f'{lp}_y', 'size')]
            L_n = L_nx + L_ny

        # Working capacity
        if self.p1 == '0':
            W_xp1 = W_yp1 = 0
        else:
            W_xp1 = self._dfs[(f'{p1}_x', 'med')]
            W_yp1 = self._dfs[(f'{p1}_y', 'med')]

        if self.p2 == '0':
            W_xp2 = W_yp2 = 0
        else:
            W_xp2 = self._dfs[(f'{p2}_x', 'med')]
            W_yp2 = self._dfs[(f'{p2}_y', 'med')]

        W_x = W_xp2 - W_xp1
        W_y = W_yp2 - W_yp1

        W_nx = np.maximum(
            self._dfs[(f'{p1}_x', 'size')] if p1 != '0' else 0,
            self._dfs[(f'{p2}_x', 'size')] if p2 != '0' else 0
        )
        W_ny = np.maximum(
            self._dfs[(f'{p1}_y', 'size')] if p1 != '0' else 0,
            self._dfs[(f'{p2}_y', 'size')] if p2 != '0' else 0
        )
        W_n = W_nx + W_ny

        sel = np.exp(K_y - K_x)
        psa_W = (W_y / W_x) * sel

        return {
            'labels': self._dfs.index,

            # parameters
            'sel': sel,
            'psa_W': psa_W,

            # Henry data
            'K_x': K_x, 'K_y': K_y,
            'K_nx': K_nx, 'K_ny': K_ny, 'K_n': K_n,

            # Loading data
            'L_x': L_x, 'L_y': L_y,
            'L_nx': L_nx, 'L_ny': L_ny, 'L_n': L_n,

            # Working capacity data
            'W_x': W_x, 'W_y': W_y,
            'W_nx': W_nx, 'W_ny': W_ny, 'W_n': W_n,
        }

    def patch_data_l(self, p):
        """Patch KPI data when uptake changes."""

        if self._dfs is None:
            return {}

        if p == '0':
            L_x = L_y = L_nx = L_ny = L_n = [0 for a in self._dfs.index]
        else:
            L_x = self._dfs.loc[:, (f'{p}_x', 'med')]
            L_y = self._dfs.loc[:, (f'{p}_y', 'med')]
            L_nx = self._dfs.loc[:, (f'{p}_x', 'size')]
            L_ny = self._dfs.loc[:, (f'{p}_y', 'size')]
            L_n = L_nx + L_ny

        return {
            # Loading data
            'L_x': [(slice(None), L_x)], 'L_y': [(slice(None), L_y)],
            'L_nx': [(slice(None), L_nx)], 'L_ny': [(slice(None), L_ny)],
            'L_n': [(slice(None), L_n)]
        }

    def patch_data_w(self, p1, p2):
        """Patch KPI data when working capacity changes."""

        if self._dfs is None:
            return {}

        if self.p1 == '0':
            W_xp1 = W_yp1 = 0
        else:
            W_xp1 = self._dfs[(f'{p1}_x', 'med')]
            W_yp1 = self._dfs[(f'{p1}_y', 'med')]

        if self.p2 == '0':
            W_xp2 = W_yp2 = 0
        else:
            W_xp2 = self._dfs[(f'{self.p2}_x', 'med')]
            W_yp2 = self._dfs[(f'{self.p2}_y', 'med')]

        W_x = W_xp2 - W_xp1
        W_y = W_yp2 - W_yp1

        W_nx = np.maximum(
            self._dfs[(f'{p1}_x', 'size')] if p1 != '0' else 0,
            self._dfs[(f'{p2}_x', 'size')] if p2 != '0' else 0
        )
        W_ny = np.maximum(
            self._dfs[(f'{p1}_y', 'size')] if p1 != '0' else 0,
            self._dfs[(f'{p2}_y', 'size')] if p2 != '0' else 0
        )
        W_n = W_nx + W_ny
        psa_W = (W_y / W_x) * self.data.data['sel']

        return {
            # parameters
            'psa_W': [(slice(None), psa_W)],

            # Working capacity data
            'W_x': [(slice(None), W_x)], 'W_y': [(slice(None), W_y)],
            'W_nx': [(slice(None), W_nx)], 'W_ny': [(slice(None), W_ny)],
            'W_n': [(slice(None), W_n)]
        }

    # #########################################################################
    # Error generator

    def gen_error(self, indices=None):
        """Select or generate all error data for selected points."""

        if indices is None:
            return {
                'labels': [],
                'K_x': [], 'K_y': [],
                'L_x': [], 'L_y': [],
                'W_x': [], 'W_y': [],
                'K_x0': [], 'K_y0': [], 'K_x1': [], 'K_y1': [],
                'L_x0': [], 'L_y0': [], 'L_x1': [], 'L_y1': [],
                'W_x0': [], 'W_y0': [], 'W_x1': [], 'W_y1': [],
            }

        else:

            mats = []
            K_X, K_Y, L_X, L_Y, W_X, W_Y = [], [], [], [], [], []
            K_X1, K_Y1, K_X2, K_Y2 = [], [], [], []
            L_X1, L_Y1, L_X2, L_Y2 = [], [], [], []
            W_X1, W_Y1, W_X2, W_Y2 = [], [], [], []

            for index in indices:

                mat = self.data.data['labels'][index]
                K_x = self.data.data['K_x'][index]
                K_y = self.data.data['K_y'][index]
                L_x = self.data.data['L_x'][index]
                L_y = self.data.data['L_y'][index]
                W_x = self.data.data['W_x'][index]
                W_y = self.data.data['W_y'][index]

                # NaN values have to be avoided
                if np.isnan(K_x) or np.isnan(K_y):
                    K_x, K_y = 0, 0
                    K_ex, K_ey = 0, 0
                else:
                    K_ex = self._dfs.loc[mat, ('kH_x', 'err')]
                    K_ey = self._dfs.loc[mat, ('kH_y', 'err')]

                if np.isnan(L_x) or np.isnan(L_y) or self.lp == '0':
                    L_x, L_y = 0, 0
                    L_ex, L_ey = 0, 0
                else:
                    L_ex = self._dfs.loc[mat,
                                         (f'{self.lp}_x', 'err')]
                    L_ey = self._dfs.loc[mat,
                                         (f'{self.lp}_y', 'err')]

                if np.isnan(W_x) or np.isnan(W_y):
                    W_x, W_y = 0, 0
                    W_ex, W_ey = 0, 0
                else:
                    W_ex = self._dfs.loc[mat, (f'{self.p1}_x', 'err')] if self.p1 != 0 else 0 + \
                        self._dfs.loc[mat, ('{}_x'.format(
                            self.p2), 'err')] if self.p2 != 0 else 0
                    W_ey = self._dfs.loc[mat, (f'{self.p1}_y', 'err')] if self.p1 != 0 else 0 + \
                        self._dfs.loc[mat, ('{}_y'.format(
                            self.p2), 'err')] if self.p2 != 0 else 0

                mats.extend([mat, mat])
                K_X.extend([K_x, K_x])
                K_Y.extend([K_y, K_y])
                L_X.extend([L_x, L_x])
                L_Y.extend([L_y, L_y])
                W_X.extend([W_x, W_x])
                W_Y.extend([W_y, W_y])
                # henry data
                K_X1.extend([K_x - K_ex, K_x])
                K_Y1.extend([K_y, K_y - K_ey])
                K_X2.extend([K_x + K_ex, K_x])
                K_Y2.extend([K_y, K_y + K_ey])
                # loading data
                L_X1.extend([L_x - L_ex, L_x])
                L_Y1.extend([L_y, L_y - L_ey])
                L_X2.extend([L_x + L_ex, L_x])
                L_Y2.extend([L_y, L_y + L_ey])
                # working capacity data
                W_X1.extend([W_x - W_ex, W_x])
                W_Y1.extend([W_y, W_y - W_ey])
                W_X2.extend([W_x + W_ex, W_x])
                W_Y2.extend([W_y, W_y + W_ey])

            return {
                # labels
                'labels': mats,
                'K_x': K_X, 'K_y': K_Y,
                'L_x': L_X, 'L_y': L_Y,
                'W_x': W_X, 'W_y': W_Y,
                # henry data
                'K_x0': K_X1, 'K_y0': K_Y1, 'K_x1': K_X2, 'K_y1': K_Y2,
                # loading data
                'L_x0': L_X1, 'L_y0': L_Y1, 'L_x1': L_X2, 'L_y1': L_Y2,
                # working capacity data
                'W_x0': W_X1, 'W_y0': W_Y1, 'W_x1': W_X2, 'W_y1': W_Y2,
            }

    def patch_error_l(self, indices=None):
        """Patch error data when uptake changes."""
        if indices is None:
            return {
                # loading data
                'L_x': [(slice(None), [])],
                'L_y': [(slice(None), [])],
                'L_x0': [(slice(None), [])],
                'L_y0': [(slice(None), [])],
                'L_x1': [(slice(None), [])],
                'L_y1': [(slice(None), [])],
            }
        else:
            L_X, L_Y = [], []
            L_X1, L_Y1, L_X2, L_Y2 = [], [], [], []

            for index in indices:

                L_x = self.data.data['L_x'][index]
                L_y = self.data.data['L_y'][index]
                if np.isnan(L_x) or np.isnan(L_y) or self.lp == '0':
                    L_x, L_y = 0, 0
                    L_ex, L_ey = 0, 0
                else:
                    mat = self.data.data['labels'][index]
                    L_ex = self._dfs.loc[mat,
                                         (f'{self.lp}_x', 'err')]
                    L_ey = self._dfs.loc[mat,
                                         (f'{self.lp}_y', 'err')]

                L_X.extend([L_x, L_x])
                L_Y.extend([L_y, L_y])
                L_X1.extend([L_x - L_ex, L_x])
                L_Y1.extend([L_y, L_y - L_ey])
                L_X2.extend([L_x + L_ex, L_x])
                L_Y2.extend([L_y, L_y + L_ey])

            return {
                # loading data
                'L_x': [(slice(None), L_X)],
                'L_y': [(slice(None), L_Y)],
                'L_x0': [(slice(None), L_X1)],
                'L_y0': [(slice(None), L_Y1)],
                'L_x1': [(slice(None), L_X2)],
                'L_y1': [(slice(None), L_Y2)],
            }

    def patch_error_wc(self, indices=None):
        """Patch error data when working capacity changes."""
        if indices is None:
            return {
                # loading data
                'W_x': [(slice(None), [])],
                'W_y': [(slice(None), [])],
                'W_x0': [(slice(None), [])],
                'W_y0': [(slice(None), [])],
                'W_x1': [(slice(None), [])],
                'W_y1': [(slice(None), [])],
            }
        else:
            W_X, W_Y = [], []
            W_X1, W_Y1, W_X2, W_Y2 = [], [], [], []

            for index in indices:

                W_x = self.data.data['W_x'][index]
                W_y = self.data.data['W_y'][index]
                if np.isnan(W_x) or np.isnan(W_y):
                    W_x, W_y = 0, 0
                    W_ex, W_ey = 0, 0
                else:
                    mat = self.data.data['labels'][index]
                    W_ex = self._dfs.loc[mat, (f'{self.p1}_x', 'err')] if self.p1 != 0 else 0 + \
                        self._dfs.loc[mat, ('{}_x'.format(
                            self.p2), 'err')] if self.p2 != 0 else 0
                    W_ey = self._dfs.loc[mat, (f'{self.p1}_y', 'err')] if self.p1 != 0 else 0 + \
                        self._dfs.loc[mat, ('{}_y'.format(
                            self.p2), 'err')] if self.p2 != 0 else 0

                W_X.extend([W_x, W_x])
                W_Y.extend([W_y, W_y])
                W_X1.extend([W_x - W_ex, W_x])
                W_Y1.extend([W_y, W_y - W_ey])
                W_X2.extend([W_x + W_ex, W_x])
                W_Y2.extend([W_y, W_y + W_ey])

            return {
                # loading data
                'W_x': [(slice(None), W_X)],
                'W_y': [(slice(None), W_Y)],
                'W_x0': [(slice(None), W_X1)],
                'W_y0': [(slice(None), W_Y1)],
                'W_x1': [(slice(None), W_X2)],
                'W_y1': [(slice(None), W_Y2)],
            }

    # #########################################################################
    # Iso generator

    def gen_iso_dict(self):
        """Empty dictionary for isotherm display."""
        return {
            'labels': [],
            'doi': [],
            'x': [],
            'y': [],
            'temp': [],
            'color': [],
        }

    # #########################################################################
    # Callback for selection

    def selection_callback(self, attr, old, new):
        """Display selected points on graph and the isotherms."""

        # If the user has not selected anything
        if len(new) == 0:
            # Remove error points:
            self.errors.data = self.gen_error()

            # Reset bottom graphs
            self.g1_iso_sel.data = self.gen_iso_dict()
            self.g2_iso_sel.data = self.gen_iso_dict()
            self.g1_iso_sel.selected.update(indices=[])
            self.g2_iso_sel.selected.update(indices=[])
            self.sep_dash.p_g1iso.x_range.end = 0.01
            self.sep_dash.p_g1iso.y_range.end = 0.01
            self.sep_dash.p_g2iso.x_range.end = 0.01
            self.sep_dash.p_g2iso.y_range.end = 0.01

            # done here
            return

        # If the user has selected more than one point
        # Display error points:
        self.errors.data = self.gen_error(new)

        # Reset bottom graphs
        self.g1_iso_sel.data = self.gen_iso_dict()
        self.g2_iso_sel.data = self.gen_iso_dict()
        self.g1_iso_sel.selected.update(indices=[])
        self.g2_iso_sel.selected.update(indices=[])
        self.sep_dash.p_g1iso.x_range.end = 0.01
        self.sep_dash.p_g1iso.y_range.end = 0.01
        self.sep_dash.p_g2iso.x_range.end = 0.01
        self.sep_dash.p_g2iso.y_range.end = 0.01

        # If we have only one point then we display isotherms
        if len(new) == 1:
            # Generate bottom graphs
            self.sel_mat = self.data.data['labels'][new[0]]
            self.g1_hashes = get_isohash(
                self._df, self.iso_type, self.t_abs, self.t_tol, self.g1, self.sel_mat)
            self.g2_hashes = get_isohash(
                self._df, self.iso_type, self.t_abs, self.t_tol, self.g2, self.sel_mat)
            Thread(target=self.populate_isos, args=['g1']).start()
            Thread(target=self.populate_isos, args=['g2']).start()

    # #########################################################################
    # Isotherm interactions

    def populate_isos(self, ads):
        """Threaded code to add isotherms to bottom graphs."""

        if ads == 'g1':
            # "average" isotherm
            loading = self._dfs.loc[self.sel_mat,
                                    (slice(None), 'med')].values[1:41]
            self.doc.add_next_tick_callback(
                partial(
                    self.iso_update_g1,
                    iso={'labels': ['median'],
                         'x': [self.p_range[~np.isnan(loading)]],
                         'y': [loading[~np.isnan(loading)]],
                         'temp': [self.t_abs], 'doi': ['']}, color='k'))

            # rest of the isotherms
            for iso in get_isohash(
                    self._df, self.iso_type, self.t_abs, self.t_tol,
                    self.g1, self.sel_mat):
                parsed = load_isotherm(iso)
                if parsed:
                    self.doc.add_next_tick_callback(
                        partial(self.iso_update_g1, iso=parsed))

        elif ads == 'g2':
            # "average" isotherm
            loading = self._dfs.loc[self.sel_mat,
                                    (slice(None), 'med')].values[42:]
            self.doc.add_next_tick_callback(
                partial(
                    self.iso_update_g2,
                    iso={'labels': ['median'],
                         'x': [self.p_range[~np.isnan(loading)]],
                         'y': [loading[~np.isnan(loading)]],
                         'temp': [self.t_abs], 'doi': ['']},
                    color='k', resize=False))

            # rest of the isotherms
            for iso in get_isohash(
                    self._df, self.iso_type, self.t_abs, self.t_tol,
                    self.g2, self.sel_mat):
                parsed = load_isotherm(iso)
                if parsed:
                    self.doc.add_next_tick_callback(
                        partial(self.iso_update_g2, iso=parsed))

    @gen.coroutine
    def iso_update_g1(self, iso, color=None):
        iso['color'] = [next(self.sep_dash.c_cyc) if color is None else color]
        self.g1_iso_sel.stream(iso)
        if float(iso['x'][0][-1]) > self.sep_dash.p_g1iso.x_range.end:
            self.sep_dash.p_g1iso.x_range.end = 1.1 * float(iso['x'][0][-1])
        if float(iso['y'][0][-1]) > self.sep_dash.p_g1iso.y_range.end:
            self.sep_dash.p_g1iso.y_range.end = 1.1 * float(iso['y'][0][-1])

    @gen.coroutine
    def iso_update_g2(self, iso, color=None, resize=True):
        iso['color'] = [next(self.sep_dash.c_cyc) if color is None else color]
        self.g2_iso_sel.stream(iso)
        if float(iso['x'][0][-1]) > self.sep_dash.p_g2iso.x_range.end:
            self.sep_dash.p_g2iso.x_range.end = 1.1 * float(iso['x'][0][-1])
        if float(iso['y'][0][-1]) > self.sep_dash.p_g2iso.y_range.end:
            self.sep_dash.p_g2iso.y_range.end = 1.1 * float(iso['y'][0][-1])
