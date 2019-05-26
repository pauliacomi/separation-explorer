## labels not being generated
## hover tools not working when gas is changed
##

from bokeh.plotting import figure
from bokeh.layouts import widgetbox, gridplot, layout
from bokeh.models import Slider, RangeSlider, Div, Select
from bokeh.models import Circle, ColorBar, HoverTool
from bokeh.models import ColumnDataSource
from bokeh.transform import linear_cmap
from bokeh.palettes import Spectral10 as palette

from helpers import GASES, TOOLS, TOOLTIP, DETAILS


def gen_cmap(z):
    """Create a linear cmap with a particular name."""
    return linear_cmap(
        field_name='z{0}'.format(z), palette=palette,
        low_color='grey', high_color='red',
        low=3, high=90)


def graph_link(rends):
    """Add a linked selection and hover effect."""
    sel = Circle(fill_alpha=1, fill_color="black", line_color='black')
    for rend in rends:
        rend.selection_glyph = sel
        rend.hover_glyph = sel


class Dashboard():

    def __init__(self, doc, data):

        # Save references for thread access
        self._data_dict = data
        self._doc = doc

        # Gas definitions
        self.g1 = GASES[0]
        self.g2 = GASES[1]

        # Pressure definitions
        self.lp = 0
        self.p1 = 0
        self.p2 = 1

        # Bokeh specific data generation
        self.data = ColumnDataSource(data=self.gen_data())
        self.errors = ColumnDataSource(data=self.gen_error())

        # Data callback
        self.data.selected.on_change('indices', self.selection_callback)

        # Gas selections
        g1_sel = Select(title="Gas 1", options=GASES, value=self.g1)
        g2_sel = Select(title="Gas 2", options=GASES, value=self.g2)

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
            1, "Initial Henry's constant",
            x_range=(1e-3, 1e7), y_range=(1e-3, 1e7),
            y_axis_type="log", x_axis_type="log")
        self.p_loading, rend2 = self.top_graph(
            0, "Uptake at selected pressure")
        self.p_wc, rend3 = self.top_graph(
            2, "Working capacity in selected range")
        graph_link([rend1, rend2, rend3])
        self.top_graph_labels()

        # Pressure slider
        p_slider = Slider(title="Pressure", value=0.5,
                          start=0.5, end=20, step=0.5)
        p_slider.on_change('value', self.pressure_callback)

        # Working capacity slider
        wc_slider = RangeSlider(title="Working capacity", value=(1, 5),
                                start=0.5, end=20, step=0.5)
        wc_slider.on_change('value', self.wc_callback)

        # Material details
        self.details = Div(text=self.gen_details())

        # Isotherm details
        self.details_iso = Div(text="Bottom text", height=400)

        self.dash_layout = layout([
            [g1_sel, g2_sel],
            [gridplot([
                [self.details, self.p_henry],
                [self.p_loading, self.p_wc]])],
            [widgetbox(children=[p_slider, wc_slider])],
            # [gridplot([[self.p_g0iso, self.p_g1iso]])],
            [self.details_iso],
        ], sizing_mode='scale_width')

    def top_graph(self, ind, title, **kwargs):

        # Generate figure dict
        plot_side_size = 400
        fig_dict = dict(tools=TOOLS,
                        active_scroll="wheel_zoom",
                        plot_width=plot_side_size,
                        plot_height=plot_side_size,
                        title=title)
        fig_dict.update(kwargs)

        # Create a colour mapper
        mapper = gen_cmap(ind)

        # create a new plot and add a renderer
        graph = figure(**fig_dict)

        graph.add_tools(HoverTool(
            names=["data{0}".format(ind)],
            tooltips=TOOLTIP.render(p=ind, gas0=self.g1, gas1=self.g2))
        )

        # Data
        rend = graph.circle(
            "x{0}".format(ind), "y{0}".format(ind),
            source=self.data, size=10,
            line_color=mapper, color=mapper,
            name="data{0}".format(ind)
        )

        # Errors
        errs = graph.segment('x{0}0'.format(ind), 'y{0}0'.format(ind),
                             'x{0}1'.format(ind), 'y{0}1'.format(ind),
                             source=self.errors, color="black", line_width=2)

        # Colorbar
        graph.add_layout(ColorBar(
            color_mapper=mapper['transform'],
            width=8, location=(0, 0)),
            'right'
        )

        return graph, rend

    def top_graph_labels(self):
        self.p_loading.xaxis.axis_label = '{0} (mmol/g)'.format(self.g1)
        self.p_loading.yaxis.axis_label = '{0} (mmol/g)'.format(self.g2)
        self.p_henry.xaxis.axis_label = '{0} (dimensionless)'.format(
            self.g1)
        self.p_henry.yaxis.axis_label = '{0} (dimensionless)'.format(
            self.g2)

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

        # # Update bottom
        # self.purge_isos()

    # #########################################################################
    # Set up pressure slider and callback

    def pressure_callback(self, attr, old, new):
        self.lp = int(new * 2) - 1
        self.data.data = self.gen_data()
        sel = self.data.selected.indices
        if sel:
            self.errors.data = self.gen_error(sel[0])
            self.details.text = self.gen_details(sel[0])
            # self.details_iso.text = self.gen_iso_text(sel[0])

    # #########################################################################
    # Set up working capacity slider and callback

    def wc_callback(self, attr, old, new):
        self.p1, self.p2 = int(new[0] * 2) - 1, int(new[1] * 2) - 1
        self.data.data = self.gen_data()
        sel = self.data.selected.indices
        if sel:
            self.errors.data = self.gen_error(sel[0])
            self.details.text = self.gen_details(sel[0])
        # self.details_iso.text = self.gen_iso_text(sel[0])

    # #########################################################################
    # Data generator

    def gen_data(self):

        dd = self._data_dict
        g1 = self.g1
        g2 = self.g2
        p = self.lp
        p1 = self.p1
        p2 = self.p2

        common = [mat for mat in dd if
                  dd[mat].get(g1, False) and
                  dd[mat].get(g2, False)]

        z0x = [dd[mat][g1]['lL'][p] for mat in common]
        z0y = [dd[mat][g2]['lL'][p] for mat in common]
        z1x = [dd[mat][g1]['lKh'] for mat in common]
        z1y = [dd[mat][g2]['lKh'] for mat in common]

        return dict(
            labels=common,
            
            x0=[dd[mat][g1]['mL'][p] for mat in common],
            y0=[dd[mat][g2]['mL'][p] for mat in common],

            x1=[dd[mat][g1]['mKh'] for mat in common],
            y1=[dd[mat][g2]['mKh'] for mat in common],

            x2=[dd[mat][g1]['mL'][p2] - dd[mat][g1]['mL'][p1] for mat in common],
            y2=[dd[mat][g2]['mL'][p2] - dd[mat][g2]['mL'][p1] for mat in common],
            
            z0x=z0x,
            z0y=z0y,
            z1x=z1x,
            z1y=z1y,
            z2x=z0x,
            z2y=z0y,
            z0=[z0x[a] + z0y[a] for a in range(len(z0x))],
            z1=[z1x[a] + z1y[a] for a in range(len(z1x))],
            z2=[z0x[a] + z0y[a] for a in range(len(z0x))],
        )

    # #########################################################################
    # Error generator

    def gen_error(self, index=None):

        if index is None:
            return dict(
                x00=[], y00=[], x01=[], y01=[],
                x10=[], y10=[], x11=[], y11=[],
                x20=[], y20=[], x21=[], y21=[],
                )

        else:
            p = self.lp

            mat = self.data.data['labels'][index]
            x0 = self.data.data['x0'][index]
            y0 = self.data.data['y0'][index]
            xe00 = self._data_dict[mat][self.g1]['eL'][p]
            xe01 = self._data_dict[mat][self.g2]['eL'][p]
            x1 = self.data.data['x1'][index]
            y1 = self.data.data['y1'][index]
            xe10 = self._data_dict[mat][self.g1]['eKh']
            xe11 = self._data_dict[mat][self.g2]['eKh']

            if x0 == 'NaN':
                x0 = 0
            if y0 == 'NaN':
                y0 = 0
            if x1 == 'NaN':
                x1 = 0
            if y1 == 'NaN':
                y1 = 0

            e_dict = dict(
                labels=[mat, mat],
                x00=[x0 - xe00, x0],
                y00=[y0, y0-xe01],
                x01=[x0 + xe00, x0],
                y01=[y0, y0+xe01],
                x10=[x1 - xe10, x1],
                y10=[y1, y1-xe11],
                x11=[x1 + xe10, x1],
                y11=[y1, y1+xe11],
            )
            return e_dict

    # #########################################################################
    # Text generator

    def gen_details(self, index=None):
        if index is None:
            return DETAILS.render()
        else:
            mat = self.data.data['labels'][index]
            p = self.lp

            data = {
                'material': mat,
                'gas0': self.g1,
                'gas1': self.g2,
                'gas0_niso': len(self._data_dict[mat][self.g1]['iso']),
                'gas1_niso': len(self._data_dict[mat][self.g2]['iso']),
                'gas0_load': self.data.data['x0'][index],
                'gas1_load': self.data.data['y0'][index],
                'gas0_eload': self._data_dict[mat][self.g1]['eL'][p],
                'gas1_eload': self._data_dict[mat][self.g2]['eL'][p],
                'gas0_hk': self._data_dict[mat][self.g1]['mKh'],
                'gas1_hk': self._data_dict[mat][self.g2]['mKh'],
                'gas0_ehk': self._data_dict[mat][self.g1]['eKh'],
                'gas1_ehk': self._data_dict[mat][self.g2]['eKh'],
            }
            return DETAILS.render(**data)

    # #########################################################################
    # Callback for selection

    def selection_callback(self, attr, old, new):

        if len(new) == 1:
            # The user has selected a point

            # # Display error points:
            self.errors.data = self.gen_error(new[0])

            # Generate material details
            self.details.text = self.gen_details(new[0])

        else:
            # Remove error points:
            self.errors.data = self.gen_error()