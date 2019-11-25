import numpy as np

from bokeh.plotting import figure
from bokeh.layouts import widgetbox, gridplot, layout, row
from bokeh.models import Slider, Button, RadioButtonGroup, RangeSlider, Div, Paragraph, Select
from bokeh.models import Circle
from bokeh.models import ColorBar, HoverTool, TapTool, OpenURL, LabelSet
from bokeh.models import ColumnDataSource
from bokeh.models import DataTable, TableColumn, NumberFormatter
from bokeh.models import LogTicker
from bokeh.models.callbacks import CustomJS
from bokeh.transform import log_cmap
from bokeh.palettes import viridis as gen_palette

from itertools import cycle

from helpers import j2_env
from helpers import load_data as load_data
from helpers import load_isotherm as load_isotherm
from functools import partial
from threading import Thread
from tornado import gen


class Dashboard():
    """
    Initialize all the Bokeh dashboard.

    Pass a reference to the Bokeh document for threading access.
    """

    def __init__(self, doc):

        # Save templates
        self.t_tooltip = j2_env.get_template('tooltip.html')

        # Save reference
        self.doc = doc

        # Dataset
        self._df = load_data()      # Entire dataset
        self._dfs = None            # Selected gas dataset

        # Gas definitions
        gases = list(self._df.columns.levels[0])
        self.g1 = "nitrogen"
        self.g2 = "carbon dioxide"

        # Generate selected gas dataframe
        self.gen_sel_gas()

        # Pressure definitions
        self.lp = 1    # 0.5 bar
        self.p1 = 1    # 0.5 bar
        self.p2 = 10   # 5.0 bar

        # Bokeh-specific data source generation
        self.data = ColumnDataSource(data=self.gen_data())
        self.errors = ColumnDataSource(data=self.gen_error())

        # Data selection callback
        self.data.selected.on_change('indices', self.selection_callback)

        # Gas drop-down selections
        g1_sel = Select(title="Gas 1", options=gases, value=self.g1)
        g2_sel = Select(title="Gas 2", options=gases, value=self.g2)

        def g1_sel_callback(attr, old, new):
            self.g1 = new
            self.new_gas_callback()

        def g2_sel_callback(attr, old, new):
            self.g2 = new
            self.new_gas_callback()

        g1_sel.on_change("value", g1_sel_callback)
        g2_sel.on_change("value", g2_sel_callback)

        # Top graph generation
        self.p_henry, rend1 = self.top_graph(
            "K", "Initial Henry constant",
            x_range=(1e-3, 1e7), y_range=(1e-3, 1e7),
            y_axis_type="log", x_axis_type="log")
        self.p_loading, rend2 = self.top_graph(
            "L", "Uptake at selected pressure")
        self.p_wc, rend3 = self.top_graph(
            "W", "Working capacity in selected range")

        # Give graphs the same hover and select effect
        sel = Circle(fill_alpha=1, fill_color="red", line_color='black')
        for rend in [rend1, rend2, rend3]:
            rend.selection_glyph = sel
            rend.hover_glyph = sel

        # Generate the axis labels
        self.top_graph_labels()

        # Pressure slider
        p_slider = Slider(title="Pressure (bar)", value=0.5,
                          start=0, end=20, step=0.5,
                          callback_policy='throttle',
                          callback_throttle=500,
                          )
        p_slider.on_change('value_throttled', self.uptake_callback)

        # Working capacity slider
        wc_slider = RangeSlider(title="Working capacity (bar)",
                                value=(0.5, 5),
                                start=0, end=20, step=0.5,
                                callback_policy='throttle',
                                callback_throttle=500,
                                )
        wc_slider.on_change('value_throttled', self.wc_callback)

        # Material datatable
        self.details = DataTable(
            columns=[
                TableColumn(field="labels", title="Material", width=300),
                TableColumn(field="sel", title="KH2/KH1", width=25,
                            formatter=NumberFormatter(format='‘0.0a’')),
                TableColumn(field="psa_W", title="PSA-API", width=30,
                            formatter=NumberFormatter(format='‘0.0a’')),
            ],
            source=self.data,
            index_position=None,
            selectable='checkbox',
            scroll_to_selection=True,
            width=400,
            fit_columns=True,
        )

        # Isotherm display datasources
        self.s_g1iso = ColumnDataSource(data=self.gen_iso_dict())
        self.s_g2iso = ColumnDataSource(data=self.gen_iso_dict())
        # Isotherm display graphs
        self.p_g1iso = self.bottom_graph(self.s_g1iso, self.g1)
        self.p_g2iso = self.bottom_graph(self.s_g2iso, self.g2)
        # Isotherm display palette
        self.c_cyc = cycle(gen_palette(20))

        tour_button = Button(
            label="Show me how this works!", button_type="success")
        tour_button.js_on_click(CustomJS(code="startIntro()"))
        data_type = RadioButtonGroup(
            labels=["All Data", "Experimental", "Simulated"], active=0)
        # Layout
        self.dash_layout = layout([
            [tour_button, data_type],
            [g1_sel, g2_sel],
            [gridplot([
                [self.details, self.p_henry],
                [self.p_loading, self.p_wc]], sizing_mode='scale_width')],
            [p_slider, wc_slider],
            [self.p_g1iso, self.p_g2iso],
        ], sizing_mode='scale_width')

        # Custom css classes for interactors
        data_type.css_classes = ['dtypes']
        self.details.css_classes = ['t-details']
        self.p_henry.css_classes = ['g-henry']
        self.p_loading.css_classes = ['g-load']
        self.p_wc.css_classes = ['g-wcap']

        self.dash_layout.children[1].css_classes = ['g-selectors']
        self.dash_layout.children[2].css_classes = ['kpi']
        self.dash_layout.children[3].css_classes = ['p-selectors']
        self.dash_layout.children[4].css_classes = ['isotherms']

    # #########################################################################
    # Graph generators

    def top_graph(self, ind, title, **kwargs):
        """Generate the top graphs (KH, uptake, WC)."""

        # Generate figure dict
        plot_side_size = 400
        fig_dict = dict(tools="pan,wheel_zoom,tap,reset,save",
                        active_scroll="wheel_zoom",
                        plot_width=plot_side_size,
                        plot_height=plot_side_size,
                        title=title)
        fig_dict.update(kwargs)

        # Create a colour mapper for number of isotherms
        mapper = log_cmap(
            field_name='{0}_n'.format(ind), palette="Viridis256",
            low_color='grey', high_color='yellow',
            low=3, high=100)

        # Create a new plot
        graph = figure(**fig_dict)

        # Add the hover tooltip
        graph.add_tools(HoverTool(
            names=["{0}_data".format(ind)],
            tooltips=self.t_tooltip.render(p=ind))
        )

        # Plot the data
        rend = graph.circle(
            "{0}_x".format(ind), "{0}_y".format(ind),
            source=self.data, size=10,
            line_color=mapper, color=mapper,
            name="{0}_data".format(ind)
        )

        # Plot the error margins
        graph.segment(
            '{0}_x0'.format(ind), '{0}_y0'.format(ind),
            '{0}_x1'.format(ind), '{0}_y1'.format(ind),
            source=self.errors,
            color="black", line_width=2,
            line_cap='square', line_dash='dotted')

        # Plot labels next to selected materials
        graph.add_layout(LabelSet(
            x='{0}_x'.format(ind), y='{0}_y'.format(ind),
            source=self.errors,
            text='labels', level='glyph',
            x_offset=5, y_offset=5,
            render_mode='canvas',
            text_font_size='8pt',
        ))

        # Add the colorbar to the side
        graph.add_layout(ColorBar(
            color_mapper=mapper['transform'],
            ticker=LogTicker(desired_num_ticks=10),
            width=8, location=(0, 0)),
            'right'
        )

        return graph, rend

    def top_graph_labels(self):
        """Generate the top graph labels from selected gases."""
        self.p_loading.xaxis.axis_label = '{0} (mmol/g)'.format(self.g1)
        self.p_loading.yaxis.axis_label = '{0} (mmol/g)'.format(self.g2)
        self.p_henry.xaxis.axis_label = '{0} (mmol/bar)'.format(
            self.g1)
        self.p_henry.yaxis.axis_label = '{0} (mmol/bar)'.format(
            self.g2)
        self.p_wc.xaxis.axis_label = '{0} (mmol/g)'.format(self.g1)
        self.p_wc.yaxis.axis_label = '{0} (mmol/g)'.format(self.g2)

    def bottom_graph(self, source, gas):
        """Generate the bottom graphs (isotherm display)."""

        graph = figure(tools="pan,wheel_zoom,tap,reset",
                       active_scroll="wheel_zoom",
                       plot_width=400, plot_height=250,
                       x_range=(-0.1, 1), y_range=(-0.1, 1),
                       title='Isotherms {0}'.format(gas))
        rend = graph.multi_line('x', 'y', source=source,
                                alpha=0.6, line_width=3,
                                hover_line_alpha=1.0,
                                hover_line_color="black",
                                line_color='color')

        # Make clicking a graph oben the NIST database
        url = "https://adsorption.nist.gov/isodb/index.php?DOI=@doi#biblio"
        graph.add_tools(TapTool(renderers=[rend],
                                callback=OpenURL(url=url)))
        graph.add_tools(HoverTool(show_arrow=False,
                                  line_policy='nearest',
                                  tooltips=[
                                      ('Label', '@labels'),
                                      ('T (K)', '@temp'),
                                  ]))

        graph.xaxis.axis_label = 'Pressure (bar)'
        graph.yaxis.axis_label = 'Uptake (mmol/g)'

        return graph

    # #########################################################################
    # Selection update

    def gen_sel_gas(self):
        """Generate two-gas dataframe when selected."""
        sel = self._df[[self.g1, self.g2]]
        sel = sel[sel[(self.g1, 'iso')].apply(lambda x: len(x) > 0)]
        sel = sel[sel[(self.g2, 'iso')].apply(lambda x: len(x) > 0)]
        self._dfs = sel

    def new_gas_callback(self):
        """What to do when a new gas is selected."""

        # Generate specific dataframe
        self.gen_sel_gas()

        # Reset any selected materials
        if self.data.selected.indices:
            self.data.selected.update(indices=[])

        # Gen data
        self.data.data = self.gen_data()

        # Update labels
        self.top_graph_labels()

        # Update bottom
        self.s_g1iso.data = self.gen_iso_dict()
        self.s_g2iso.data = self.gen_iso_dict()
        self.p_g1iso.title.text = 'Isotherms {0}'.format(self.g1)
        self.p_g2iso.title.text = 'Isotherms {0}'.format(self.g2)

    # #########################################################################
    # Set up pressure slider and callback

    def uptake_callback(self, attr, old, new):
        """Callback on each pressure selected for uptake."""
        self.lp = int(new * 2)
        # regenerate graph data
        self.data.patch(self.patch_data_l())
        if self.data.selected.indices:
            self.errors.patch(self.patch_error_l(self.data.selected.indices))

    # #########################################################################
    # Set up working capacity slider and callback

    def wc_callback(self, attr, old, new):
        """Callback on pressure range for working capacity."""
        self.p1, self.p2 = int(new[0] * 2), int(new[1] * 2)
        # regenerate graph data
        self.data.patch(self.patch_data_w())
        if self.data.selected.indices:
            self.errors.patch(self.patch_error_wc(self.data.selected.indices))

    # #########################################################################
    # Some useful functions

    def get_loading(self, x):
        if not x:
            return np.nan
        elif len(x) <= self.lp:
            return np.nan
        return x[self.lp]

    def get_wc(self, x):
        if not x:
            return np.nan
        elif len(x) <= self.p1 or len(x) <= self.p2:
            return np.nan
        return x[self.p2] - x[self.p1]

    def get_nwc(self, x):
        if not x:
            return np.nan
        elif len(x) <= self.p1 or len(x) <= self.p2:
            return np.nan
        return max([x[self.p1], x[self.p2]])

    def get_err(self, x, y):
        if not x:
            return np.nan
        elif len(x) <= y:
            return np.nan
        return x[y]

    # #########################################################################
    # Data generator

    def gen_data(self):
        """Select or generate all KPI data for a pair of gases."""

        K_x = self._dfs[self.g1, 'mKh'].values
        K_y = self._dfs[self.g2, 'mKh'].values
        K_nx = self._dfs[self.g1, 'lKh'].values
        K_ny = self._dfs[self.g2, 'lKh'].values
        K_n = K_nx + K_ny

        L_x = self._dfs[self.g1, 'mL'].apply(self.get_loading).values
        L_y = self._dfs[self.g2, 'mL'].apply(self.get_loading).values
        L_nx = self._dfs[self.g1, 'lL'].apply(self.get_loading).values
        L_ny = self._dfs[self.g2, 'lL'].apply(self.get_loading).values
        L_n = L_nx + L_ny

        W_x = self._dfs[self.g1, 'mL'].apply(self.get_wc).values
        W_y = self._dfs[self.g2, 'mL'].apply(self.get_wc).values
        W_nx = self._dfs[self.g1, 'lL'].apply(self.get_nwc).values
        W_ny = self._dfs[self.g2, 'lL'].apply(self.get_nwc).values
        W_n = W_nx + W_ny

        sel = K_y / K_x
        psa_W = (W_y / W_x) * sel

        ret_dict = {
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

        return ret_dict

    def patch_data_l(self):
        """Patch KPI data when uptake changes."""

        L_x = self._dfs[self.g1, 'mL'].apply(self.get_loading).values
        L_y = self._dfs[self.g2, 'mL'].apply(self.get_loading).values
        L_nx = self._dfs[self.g1, 'lL'].apply(self.get_loading).values
        L_ny = self._dfs[self.g2, 'lL'].apply(self.get_loading).values
        L_n = L_nx + L_ny

        ret_dict = {
            # Loading data
            'L_x': [(slice(None), L_x)], 'L_y': [(slice(None), L_y)],
            'L_nx': [(slice(None), L_nx)], 'L_ny': [(slice(None), L_ny)],
            'L_n': [(slice(None), L_n)]
        }

        return ret_dict

    def patch_data_w(self):
        """Patch KPI data when working capacity changes."""

        W_x = self._dfs[self.g1, 'mL'].apply(self.get_wc).values
        W_y = self._dfs[self.g2, 'mL'].apply(self.get_wc).values
        W_nx = self._dfs[self.g1, 'lL'].apply(self.get_nwc).values
        W_ny = self._dfs[self.g2, 'lL'].apply(self.get_nwc).values
        W_n = W_nx + W_ny

        psa_W = (W_y / W_x) * self.data.data['sel']

        ret_dict = {
            # parameters
            'psa_W': [(slice(None), psa_W)],

            # Working capacity data
            'W_x': [(slice(None), W_x)], 'W_y': [(slice(None), W_y)],
            'W_nx': [(slice(None), W_nx)], 'W_ny': [(slice(None), W_ny)],
            'W_n': [(slice(None), W_n)]
        }

        return ret_dict

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
                    K_ex = self._dfs.loc[mat, (self.g1, 'eKh')]
                    K_ey = self._dfs.loc[mat, (self.g2, 'eKh')]

                if np.isnan(L_x) or np.isnan(L_y):
                    L_x, L_y = 0, 0
                    L_ex, L_ey = 0, 0
                else:
                    L_ex = self.get_err(
                        self._dfs.loc[mat, (self.g1, 'eL')], self.lp)
                    L_ey = self.get_err(
                        self._dfs.loc[mat, (self.g2, 'eL')], self.lp)

                if np.isnan(W_x) or np.isnan(W_y):
                    W_x, W_y = 0, 0
                    W_ex, W_ey = 0, 0
                else:
                    W_ex = self.get_err(self._dfs.loc[mat, (self.g1, 'eL')], self.p1) + \
                        self.get_err(
                            self._dfs.loc[mat, (self.g1, 'eL')], self.p2)
                    W_ey = self.get_err(self._dfs.loc[mat, (self.g2, 'eL')], self.p1) + \
                        self.get_err(
                            self._dfs.loc[mat, (self.g2, 'eL')], self.p2)

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
                'K_x0': K_X1,
                'K_y0': K_Y1,
                'K_x1': K_X2,
                'K_y1': K_Y2,
                # loading data
                'L_x0': L_X1,
                'L_y0': L_Y1,
                'L_x1': L_X2,
                'L_y1': L_Y2,
                # working capacity data
                'W_x0': W_X1,
                'W_y0': W_Y1,
                'W_x1': W_X2,
                'W_y1': W_Y2,
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
                if np.isnan(L_x) or np.isnan(L_y):
                    L_x, L_y = 0, 0
                    L_ex, L_ey = 0, 0
                else:
                    mat = self.data.data['labels'][index]
                    L_ex = self.get_err(
                        self._dfs.loc[mat, (self.g1, 'eL')], self.lp)
                    L_ey = self.get_err(
                        self._dfs.loc[mat, (self.g2, 'eL')], self.lp)

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
                    W_ex = self.get_err(self._dfs.loc[mat, (self.g1, 'eL')], self.p1) + \
                        self.get_err(
                            self._dfs.loc[mat, (self.g1, 'eL')], self.p2)
                    W_ey = self.get_err(self._dfs.loc[mat, (self.g2, 'eL')], self.p1) + \
                        self.get_err(
                            self._dfs.loc[mat, (self.g2, 'eL')], self.p2)

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
            self.s_g1iso.data = self.gen_iso_dict()
            self.s_g2iso.data = self.gen_iso_dict()
            self.s_g1iso.selected.update(indices=[])
            self.s_g2iso.selected.update(indices=[])
            self.p_g1iso.x_range.end = 1
            self.p_g1iso.y_range.end = 1
            self.p_g2iso.x_range.end = 1
            self.p_g2iso.y_range.end = 1

            # done here
            return

        # If the user has selected more than one point
        # Display error points:
        self.errors.data = self.gen_error(new)

        # Reset bottom graphs
        self.s_g1iso.data = self.gen_iso_dict()
        self.s_g2iso.data = self.gen_iso_dict()
        self.s_g1iso.selected.update(indices=[])
        self.s_g2iso.selected.update(indices=[])
        self.p_g1iso.x_range.end = 1
        self.p_g1iso.y_range.end = 1
        self.p_g2iso.x_range.end = 1
        self.p_g2iso.y_range.end = 1

        # If we have only one point then we display isotherms
        if len(new) == 1:
            # Generate bottom graphs
            Thread(target=self.populate_isos, args=[new[0], 'g1']).start()
            Thread(target=self.populate_isos, args=[new[0], 'g2']).start()

    # #########################################################################
    # Isotherm interactions

    def populate_isos(self, index, gas):
        """Threaded code to add isotherms to bottom graphs."""

        mat = self.data.data['labels'][index]

        if gas == 'g1':

            loading = self._dfs.loc[mat, (self.g1, 'mL')]
            pressure = [p * 0.5 for p in range(len(loading) + 1)]

            self.doc.add_next_tick_callback(
                partial(
                    self.iso_update_g1,
                    iso=['median', loading, pressure, '', ''], color='k'))

            for iso in self._dfs.loc[mat, (self.g1, 'iso')]:

                parsed = load_isotherm(iso)

                # update the document from callback
                if parsed:
                    self.doc.add_next_tick_callback(
                        partial(self.iso_update_g1, iso=parsed))

        elif gas == 'g2':

            loading = self._dfs.loc[mat, (self.g2, 'mL')]
            pressure = [p * 0.5 for p in range(len(loading) + 1)]

            self.doc.add_next_tick_callback(
                partial(
                    self.iso_update_g2,
                    iso=['median', loading, pressure, '', ''], color='k'))

            for iso in self._dfs.loc[mat, (self.g2, 'iso')]:
                parsed = load_isotherm(iso)

                # update the document from callback
                if parsed:
                    self.doc.add_next_tick_callback(
                        partial(self.iso_update_g2, iso=parsed))

    @gen.coroutine
    def iso_update_g1(self, iso, color=None):
        if not color:
            color = next(self.c_cyc)
        self.s_g1iso.stream({
            'labels': [iso[0]],
            'x': [iso[2]],
            'y': [iso[1]],
            'doi': [iso[3]],
            'temp': [iso[4]],
            'color': [color],
        })
        if float(iso[2][-1]) > self.p_g1iso.x_range.end:
            self.p_g1iso.x_range.end = float(iso[2][-1])
        if float(iso[1][-1]) > self.p_g1iso.y_range.end:
            self.p_g1iso.y_range.end = float(iso[1][-1])

    @gen.coroutine
    def iso_update_g2(self, iso, color=None):
        if not color:
            color = next(self.c_cyc)
        self.s_g2iso.stream({
            'labels': [iso[0]],
            'x': [iso[2]],
            'y': [iso[1]],
            'doi': [iso[3]],
            'temp': [iso[4]],
            'color': [color],
        })
        if float(iso[2][-1]) > self.p_g2iso.x_range.end:
            self.p_g2iso.x_range.end = float(iso[2][-1])
        if float(iso[1][-1]) > self.p_g2iso.y_range.end:
            self.p_g2iso.y_range.end = float(iso[1][-1])
