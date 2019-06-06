import numpy as np

from bokeh.plotting import figure
from bokeh.layouts import widgetbox, gridplot, layout
from bokeh.models import Slider, RangeSlider, Div, Paragraph, Select
from bokeh.models import Circle
from bokeh.models import ColorBar, HoverTool, TapTool, OpenURL, Range1d
from bokeh.models import ColumnDataSource
from bokeh.models import LogTicker
from bokeh.transform import log_cmap
from bokeh.palettes import viridis as gen_palette

from itertools import cycle

from helpers import load_isotherm, load_data, j2_env
from functools import partial
from threading import Thread
from tornado import gen


class Dashboard():

    def __init__(self, doc):

        # Save templates
        self.t_tooltip = j2_env.get_template('tooltip.html')
        self.t_matdet = j2_env.get_template('mat_details.html')
        self.t_isodet = j2_env.get_template('mat_isotherms.html')

        # Save reference
        self._df = load_data()
        self.doc = doc

        # Gas definitions
        gases = list(self._df.columns.levels[0])
        self.g1 = "nitrogen"
        self.g2 = "carbon dioxide"

        # Pressure definitions
        self.lp = 0   # 0.5 bar
        self.p1 = 0   # 0.5 bar
        self.p2 = 9   # 5.0 bar

        # Bokeh specific data generation
        self.data = ColumnDataSource(data=self.gen_data())
        self.errors = ColumnDataSource(data=self.gen_error())

        # Data callback
        self.data.selected.on_change('indices', self.selection_callback)

        # Gas selections
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

        # Top graphs
        self.p_henry, rend1 = self.top_graph(
            "K", "Initial Henry's constant",
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

        self.top_graph_labels()

        # Pressure slider
        p_slider = Slider(title="Pressure", value=0.5,
                          start=0.5, end=20, step=0.5,
                          callback_policy='throttle',
                          callback_throttle=500,
                          )
        p_slider.on_change('value_throttled', self.pressure_callback)

        # Working capacity slider
        wc_slider = RangeSlider(title="Working capacity",
                                value=(0.5, 5),
                                start=0.5, end=20, step=0.5,
                                callback_policy='throttle',
                                callback_throttle=500,)
        wc_slider.on_change('value_throttled', self.wc_callback)

        # Material details
        self.details = Div(
            text=self.gen_details(),
            style={'width': '100%'})

        # Isotherms
        self.s_g1iso = ColumnDataSource(data=self.gen_isos())
        self.s_g2iso = ColumnDataSource(data=self.gen_isos())
        self.p_g1iso = self.bottom_graph(self.s_g1iso, self.g1)
        self.p_g2iso = self.bottom_graph(self.s_g2iso, self.g2)
        self.c_cyc = cycle(gen_palette(20))

        self.dash_layout = layout([
            [g1_sel, g2_sel],
            [gridplot([
                [self.details, self.p_henry],
                [self.p_loading, self.p_wc]],
                sizing_mode='scale_width')],
            [p_slider, wc_slider],
            [Paragraph(text="""
                Once a material has been selected, the graphs below
                show the isotherms from the ISODB database that have been
                used for calculations. Click on them to be directed
                to the NIST page for the corresponding publication which
                contains detailed information about the isotherm source.
            """)],
            [gridplot(
                [[self.p_g1iso, self.p_g2iso]],
                sizing_mode='scale_width')],
        ], sizing_mode='scale_width')

    def top_graph(self, ind, title, **kwargs):

        # Generate figure dict
        plot_side_size = 400
        fig_dict = dict(tools="pan,wheel_zoom,tap,reset",
                        active_scroll="wheel_zoom",
                        plot_width=plot_side_size,
                        plot_height=plot_side_size,
                        title=title)
        fig_dict.update(kwargs)

        # Create a colour mapper
        mapper = log_cmap(
            field_name='n_{0}'.format(ind), palette="Viridis256",
            low_color='grey', high_color='yellow',
            low=3, high=100)

        # create a new plot and add a renderer
        graph = figure(**fig_dict)

        graph.add_tools(HoverTool(
            names=["data_{0}".format(ind)],
            tooltips=self.t_tooltip.render(p=ind))
        )

        # Data
        rend = graph.circle(
            "x_{0}".format(ind), "y_{0}".format(ind),
            source=self.data, size=10,
            line_color=mapper, color=mapper,
            name="data_{0}".format(ind)
        )

        # Errors
        graph.segment(
            '{0}_x0'.format(ind), '{0}_y0'.format(ind),
            '{0}_x1'.format(ind), '{0}_y1'.format(ind),
            source=self.errors,
            color="black", line_width=2,
            line_cap='square', line_dash='dotted')

        # Colorbar
        graph.add_layout(ColorBar(
            color_mapper=mapper['transform'],
            ticker=LogTicker(desired_num_ticks=10),
            width=8, location=(0, 0)),
            'right'
        )

        return graph, rend

    def bottom_graph(self, source, gas):

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

        url = "https://adsorption.nist.gov/isodb/index.php?DOI=@doi#biblio"
        graph.add_tools(TapTool(renderers=[rend],
                                callback=OpenURL(url=url)))
        graph.add_tools(HoverTool(show_arrow=False,
                                  line_policy='nearest',
                                  tooltips='@labels'))

        graph.xaxis.axis_label = 'Pressure (bar)'
        graph.yaxis.axis_label = 'Uptake (mmol/g)'

        return graph

    def top_graph_labels(self):
        self.p_loading.xaxis.axis_label = '{0} (mmol/g)'.format(self.g1)
        self.p_loading.yaxis.axis_label = '{0} (mmol/g)'.format(self.g2)
        self.p_henry.xaxis.axis_label = '{0} (dimensionless)'.format(
            self.g1)
        self.p_henry.yaxis.axis_label = '{0} (dimensionless)'.format(
            self.g2)
        self.p_wc.xaxis.axis_label = '{0} (mmol/g)'.format(self.g1)
        self.p_wc.yaxis.axis_label = '{0} (mmol/g)'.format(self.g2)

    # #########################################################################
    # Selection update

    def new_gas_callback(self):

        # # Reset any selected materials
        if self.data.selected.indices:
            self.data.selected.update(indices=[])

        # # Gen data
        self.data.data = self.gen_data()

        # # Update labels
        self.top_graph_labels()
        self.p_g1iso.title.text = 'Isotherms {0}'.format(self.g1)
        self.p_g2iso.title.text = 'Isotherms {0}'.format(self.g2)

        # # Update bottom
        self.s_g1iso.data = self.gen_isos()
        self.s_g2iso.data = self.gen_isos()

    # #########################################################################
    # Set up pressure slider and callback

    def pressure_callback(self, attr, old, new):
        self.lp = int(new * 2) - 1
        self.data.patch(self.patch_data_l())
        sel = self.data.selected.indices
        if sel:
            self.errors.patch(self.patch_error_l(sel[0]))
            self.details.text = self.gen_details(sel[0])

    # #########################################################################
    # Set up working capacity slider and callback

    def wc_callback(self, attr, old, new):
        self.p1, self.p2 = int(new[0] * 2) - 1, int(new[1] * 2) - 1
        self.data.patch(self.patch_data_w())
        sel = self.data.selected.indices
        if sel:
            self.errors.data = self.gen_error(sel[0])
            self.details.text = self.gen_details(sel[0])

    # #########################################################################
    # Data generator

    def gen_data(self):

        def get_loading(x):
            if not x:
                return np.nan
            elif len(x) <= self.lp:
                return np.nan
            return x[self.lp]

        def get_wc(x):
            if not x:
                return np.nan
            elif len(x) <= self.p1 or len(x) <= self.p2:
                return np.nan
            return x[self.p2] - x[self.p1]

        def get_nwc(x):
            if not x:
                return np.nan
            elif len(x) <= self.p1 or len(x) <= self.p2:
                return np.nan
            return x[self.p1] + x[self.p2]

        return {
            'labels': self._df.index,

            # henry data
            'x_K': self._df[self.g1, 'mKh'].values,
            'y_K': self._df[self.g2, 'mKh'].values,
            'n_xK': self._df[self.g1, 'lKh'].values,
            'n_yK': self._df[self.g2, 'lKh'].values,
            'n_K': self._df[self.g1, 'lKh'].values + self._df[self.g2, 'lKh'].values,

            # loading data
            'x_L': self._df[self.g1, 'mL'].apply(get_loading).values,
            'y_L': self._df[self.g2, 'mL'].apply(get_loading).values,
            'n_xL': self._df[self.g1, 'lL'].apply(get_loading).values,
            'n_yL': self._df[self.g2, 'lL'].apply(get_loading).values,
            'n_L': self._df[self.g1, 'lL'].apply(get_loading).values +
            self._df[self.g2, 'lL'].apply(get_loading).values,

            # Working capacity data
            'x_W': self._df[self.g1, 'mL'].apply(get_wc).values,
            'y_W': self._df[self.g2, 'mL'].apply(get_wc).values,
            'n_xW': self._df[self.g1, 'lL'].apply(get_nwc).values,
            'n_yW': self._df[self.g2, 'lL'].apply(get_nwc).values,
            'n_W': self._df[self.g1, 'lL'].apply(get_nwc).values +\
            self._df[self.g2, 'lL'].apply(get_nwc).values,
        }

    def patch_data_l(self):

        def get_loading(x):
            if not x:
                return np.nan
            elif len(x) <= self.lp:
                return np.nan
            return x[self.lp]

        return {
            'x_L': [(slice(None), self._df[self.g1, 'mL'].apply(get_loading).values)],
            'y_L': [(slice(None), self._df[self.g2, 'mL'].apply(get_loading).values)],
            'n_xL': [(slice(None), self._df[self.g1, 'lL'].apply(get_loading).values)],
            'n_yL': [(slice(None), self._df[self.g2, 'lL'].apply(get_loading).values)],
            'n_L': [(slice(None), self._df[self.g1, 'lL'].apply(get_loading).values +
                     self._df[self.g2, 'lL'].apply(get_loading).values)]
        }

    def patch_data_w(self):

        def get_wc(x):
            if not x:
                return np.nan
            elif len(x) <= self.p1 or len(x) <= self.p2:
                return np.nan
            return x[self.p2] - x[self.p1]

        def get_nwc(x):
            if not x:
                return np.nan
            elif len(x) <= self.p1 or len(x) <= self.p2:
                return np.nan
            return x[self.p1] + x[self.p2]

        return {
            'x_W': [(slice(None), self._df[self.g1, 'mL'].apply(get_wc).values)],
            'y_W': [(slice(None), self._df[self.g2, 'mL'].apply(get_wc).values)],
            'n_xW': [(slice(None), self._df[self.g1, 'lL'].apply(get_nwc).values)],
            'n_yW': [(slice(None), self._df[self.g2, 'lL'].apply(get_nwc).values)],
            'n_W': [(slice(None), self._df[self.g1, 'lL'].apply(get_nwc).values +
                     self._df[self.g2, 'lL'].apply(get_nwc).values)]
        }

    # #########################################################################
    # Error generator

    def gen_error(self, index=None):

        if index is None:
            return {
                'K_x0': [], 'K_y0': [], 'K_x1': [], 'K_y1': [],
                'L_x0': [], 'L_y0': [], 'L_x1': [], 'L_y1': [],
                'W_x0': [], 'W_y0': [], 'W_x1': [], 'W_y1': [],
            }

        else:
            def get_err(x, y):
                if not x:
                    return np.nan
                elif len(x) <= y:
                    return np.nan
                return x[y]

            mat = self.data.data['labels'][index]
            K_x = self.data.data['x_K'][index]
            K_y = self.data.data['y_K'][index]
            L_x = self.data.data['x_L'][index]
            L_y = self.data.data['y_L'][index]
            W_x = self.data.data['x_W'][index]
            W_y = self.data.data['y_W'][index]
            K_ex = self._df.loc[mat, (self.g1, 'eKh')]
            K_ey = self._df.loc[mat, (self.g2, 'eKh')]
            if np.isnan(L_x) or np.isnan(L_y):
                L_x, L_y = 0, 0
                L_ex, L_ey = 0, 0
            else:
                L_ex = get_err(self._df.loc[mat, (self.g1, 'eL')], self.lp)
                L_ey = get_err(self._df.loc[mat, (self.g2, 'eL')], self.lp)
            if np.isnan(W_x) or np.isnan(W_y):
                W_x, W_y = 0, 0
                W_ex, W_ey = 0, 0
            else:
                W_ex = get_err(self._df.loc[mat, (self.g1, 'eL')], self.p1) + \
                    get_err(self._df.loc[mat, (self.g1, 'eL')], self.p2)
                W_ey = get_err(self._df.loc[mat, (self.g2, 'eL')], self.p1) + \
                    get_err(self._df.loc[mat, (self.g2, 'eL')], self.p2)

            return {
                'labels': [mat, mat],

                # henry data
                'K_x0': [K_x - K_ex, K_x],
                'K_y0': [K_y, K_y - K_ey],
                'K_x1': [K_x + K_ex, K_x],
                'K_y1': [K_y, K_y + K_ey],
                # loading data
                'L_x0': [L_x - L_ex, L_x],
                'L_y0': [L_y, L_y - L_ey],
                'L_x1': [L_x + L_ex, L_x],
                'L_y1': [L_y, L_y + L_ey],
                # working capacity data
                'W_x0': [W_x - W_ex, W_x],
                'W_y0': [W_y, W_y - W_ey],
                'W_x1': [W_x + W_ex, W_x],
                'W_y1': [W_y, W_y + W_ey],
            }

    def patch_error_l(self, index=None):
        if index is None:
            return {
                # loading data
                'L_x0': [(slice(None), [])],
                'L_y0': [(slice(None), [])],
                'L_x1': [(slice(None), [])],
                'L_y1': [(slice(None), [])],
            }
        else:
            def get_err(x, y):
                if not x:
                    return np.nan
                elif len(x) <= y:
                    return np.nan
                return x[y]
            L_x = self.data.data['x_L'][index]
            L_y = self.data.data['y_L'][index]
            if np.isnan(L_x) or np.isnan(L_y):
                L_x, L_y = 0, 0
                L_ex, L_ey = 0, 0
            else:
                mat = self.data.data['labels'][index]
                L_ex = get_err(self._df.loc[mat, (self.g1, 'eL')], self.lp)
                L_ey = get_err(self._df.loc[mat, (self.g2, 'eL')], self.lp)
            return {
                # loading data
                'L_x0': [(slice(None), [L_x - L_ex, L_x])],
                'L_y0': [(slice(None), [L_y, L_y - L_ey])],
                'L_x1': [(slice(None), [L_x + L_ex, L_x])],
                'L_y1': [(slice(None), [L_y, L_y + L_ey])],
            }

    def patch_error_wc(self, index=None):
        if index is None:
            return {
                # loading data
                'W_x0': [(slice(None), [])],
                'W_y0': [(slice(None), [])],
                'W_x1': [(slice(None), [])],
                'W_y1': [(slice(None), [])],
            }
        else:
            def get_err(x, y):
                if not x:
                    return np.nan
                elif len(x) <= y:
                    return np.nan
                return x[y]
            W_x = self.data.data['x_W'][index]
            W_y = self.data.data['y_W'][index]
            if np.isnan(W_x) or np.isnan(W_y):
                W_x, W_y = 0, 0
                W_ex, W_ey = 0, 0
            else:
                mat = self.data.data['labels'][index]
                W_ex = get_err(self._df.loc[mat, (self.g1, 'eL')], self.p1) + \
                    get_err(self._df.loc[mat, (self.g1, 'eL')], self.p2)
                W_ey = get_err(self._df.loc[mat, (self.g2, 'eL')], self.p1) + \
                    get_err(self._df.loc[mat, (self.g2, 'eL')], self.p2)
            return {
                # loading data
                'W_x0': [(slice(None), [W_x - W_ex, W_x])],
                'W_y0': [(slice(None), [W_y, W_y - W_ey])],
                'W_x1': [(slice(None), [W_x + W_ex, W_x])],
                'W_y1': [(slice(None), [W_y, W_y + W_ey])],
            }

    # #########################################################################
    # Text generator

    def gen_details(self, index=None):
        if index is None:
            return self.t_matdet.render()
        else:
            mat = self.data.data['labels'][index]
            data = {
                'material': mat,
                'gas1': self.g1,
                'gas2': self.g2,
                'gas1_niso': len(self._df.loc[mat, (self.g1, 'iso')]),
                'gas2_niso': len(self._df.loc[mat, (self.g2, 'iso')]),
                'gas1_load': self.data.data['x_L'][index],
                'gas2_load': self.data.data['y_L'][index],
                'gas1_eload': self.errors.data['L_x1'][0] - self.errors.data['L_x1'][1],
                'gas2_eload': self.errors.data['L_y1'][1] - self.errors.data['L_y1'][0],
                'gas1_hk': self.data.data['x_K'][index],
                'gas2_hk': self.data.data['y_K'][index],
                'gas1_ehk': self.errors.data['K_x1'][0] - self.errors.data['K_x1'][1],
                'gas2_ehk': self.errors.data['L_y1'][1] - self.errors.data['L_y1'][0],
            }
            return self.t_matdet.render(**data)

    # #########################################################################
    # Iso generator

    def gen_isos(self):
        return {
            'labels': [],
            'doi': [],
            'x': [],
            'y': [],
            'color': [],
        }

    # #########################################################################
    # Callback for selection

    def selection_callback(self, attr, old, new):

        # Check if the user has selected a point
        if len(new) > 1:

            # we only get the first point
            self.data.selected.update(indices=[new[0]])

        elif len(new) == 0:

            # Remove error points:
            self.errors.data = self.gen_error()

            # Remove material details
            self.details.text = self.gen_details()

            # Reset bottom graphs
            self.s_g1iso.data = self.gen_isos()
            self.s_g2iso.data = self.gen_isos()
            self.s_g1iso.selected.update(indices=[])
            self.s_g2iso.selected.update(indices=[])
            self.p_g1iso.x_range.end = 1
            self.p_g1iso.y_range.end = 1
            self.p_g2iso.x_range.end = 1
            self.p_g2iso.y_range.end = 1

            # done here
            return

        # Display error points:
        self.errors.data = self.gen_error(new[0])

        # Generate material details
        self.details.text = self.gen_details(new[0])

        # Reset bottom graphs
        self.s_g1iso.data = self.gen_isos()
        self.s_g2iso.data = self.gen_isos()
        self.s_g1iso.selected.update(indices=[])
        self.s_g2iso.selected.update(indices=[])
        self.p_g1iso.x_range.end = 1
        self.p_g1iso.y_range.end = 1
        self.p_g2iso.x_range.end = 1
        self.p_g2iso.y_range.end = 1

        # Generate bottom graphs
        Thread(target=self.populate_isos, args=[new[0], 'g1']).start()
        Thread(target=self.populate_isos, args=[new[0], 'g2']).start()

    # #########################################################################
    # Isotherm interactions

    def populate_isos(self, index=None, which=None):

        if index is None:
            return

        else:
            mat = self.data.data['labels'][index]

            if which == 'g1':

                for iso in self._df.loc[mat, (self.g1, 'iso')]:

                    parsed = load_isotherm(iso)

                    # update the document from callback
                    if parsed:
                        self.doc.add_next_tick_callback(
                            partial(self.iso_update_g1, iso=parsed))

            elif which == 'g2':

                for iso in self._df.loc[mat, (self.g2, 'iso')]:
                    parsed = load_isotherm(iso)

                    # update the document from callback
                    if parsed:
                        self.doc.add_next_tick_callback(
                            partial(self.iso_update_g2, iso=parsed))
            else:
                raise Exception

    @gen.coroutine
    def iso_update_g1(self, iso):
        self.s_g1iso.stream({
            'labels': [iso[0]],
            'x': [iso[2]],
            'y': [iso[1]],
            'doi': [iso[3]],
            'color': [next(self.c_cyc)],
        })
        if float(iso[2][-1]) > self.p_g1iso.x_range.end:
            self.p_g1iso.x_range.end = float(iso[2][-1])
        if float(iso[1][-1]) > self.p_g1iso.y_range.end:
            self.p_g1iso.y_range.end = float(iso[1][-1])

    @gen.coroutine
    def iso_update_g2(self, iso):
        self.s_g2iso.stream({
            'labels': [iso[0]],
            'x': [iso[2]],
            'y': [iso[1]],
            'doi': [iso[3]],
            'color': [next(self.c_cyc)],
        })
        if float(iso[2][-1]) > self.p_g2iso.x_range.end:
            self.p_g2iso.x_range.end = float(iso[2][-1])
        if float(iso[1][-1]) > self.p_g2iso.y_range.end:
            self.p_g2iso.y_range.end = float(iso[1][-1])
