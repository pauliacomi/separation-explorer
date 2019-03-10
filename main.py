from bokeh.plotting import figure
from bokeh.transform import linear_cmap
from bokeh.layouts import row, column, gridplot, layout
from bokeh.models import Circle, ColorBar
from bokeh.models import ColumnDataSource, RadioButtonGroup, Slider, Div
from bokeh.io import curdoc
from bokeh.layouts import widgetbox
from bokeh.palettes import Spectral10 as palette

from functools import partial
from threading import Thread

from tornado import gen

from helpers import TOOLS, TOOLTIP, DETAILS
from helpers import load_data, load_nist_isotherm, intersect


class Dashboard():

    def __init__(self):

        self.data_dict = load_data()

        # Parameters
        self.gases = ['carbon dioxide', 'nitrogen',
                      'methane', 'ethane', 'ethene']
        self.g0 = self.gases[0]
        self.g1 = self.gases[1]
        self.pressure = 0

        # Bokeh specific data generation
        self.doc = curdoc()  # Save curdoc().
        self.data = ColumnDataSource(data=self.gen_data())
        self.errors = ColumnDataSource(data=self.gen_error(None))

        # Data callback
        self.data.selected.on_change('indices', self.selection_callback)

        # Radio selections
        self.s_type = RadioButtonGroup(
            labels=["CO2 / N2", "CO2 / CH4", "C3H6 / C2H4"], active=0)
        self.s_type.on_click(self.s_type_callback)

        # Top graphs
        self.p_loading = None
        self.p_henry = None
        self.top_graphs()

        # Pressure slider
        self.slider = Slider(title="Pressure", value=1, start=1, end=3, step=1)
        self.slider.on_change('value', self.pressure_callback)

        # Details text
        self.details = Div(text=self.gen_details(), width=400, height=400)

        # Isotherms
        self.p_g1iso = None
        self.p_g2iso = None
        self.bottom_graphs()

        # Layout
        self.material_detail = row(
            [self.details, gridplot([[self.p_g1iso, self.p_g2iso]])])

        self.dash_layout = layout([
            [self.s_type],
            gridplot([[self.p_loading, self.p_henry]]),
            [widgetbox(self.slider)],
        ])
        self.doc.title = "Graphs"

    def show_dash(self):
        self.doc.add_root(self.dash_layout)

    def top_graphs(self):

        mapper0 = self.mapper(0)
        mapper1 = self.mapper(1)

        l_width = 500

        # create a new plot and add a renderer
        self.p_loading = figure(tools=TOOLS, tooltips=TOOLTIP.format(0),
                                active_scroll="wheel_zoom",
                                x_range=(0, 12), y_range=(0, 12),
                                plot_width=l_width, plot_height=500,
                                title='Amount adsorbed')

        # create another new plot and add a renderer
        self.p_henry = figure(tools=TOOLS, tooltips=TOOLTIP.format(1),
                              active_scroll="wheel_zoom",
                              x_range=(1e-2, 1e5), y_range=(1e-2, 1e5),
                              plot_width=500, plot_height=500,
                              y_axis_type="log", x_axis_type="log",
                              title='Initial Henry constant')

        # Data
        rendl = self.p_loading.circle('x0', 'y0', source=self.data, size=10,
                                      line_color=mapper0, color=mapper0)
        rendr = self.p_henry.circle('x1', 'y1', source=self.data, size=10,
                                    line_color=mapper1, color=mapper1)

        # Errors
        errs = self.p_loading.segment('x00', 'y00', 'x01', 'y01', source=self.errors,
                                      color="black", line_width=2)
        errs = self.p_henry.segment('x10', 'y10', 'x11', 'y11', source=self.errors,
                                    color="black", line_width=2)

        # Colorbars
        color_bar0 = ColorBar(
            color_mapper=mapper0['transform'], width=8,  location=(0, 0))
        color_bar1 = ColorBar(
            color_mapper=mapper1['transform'], width=8,  location=(0, 0))
        self.p_loading.add_layout(color_bar0, 'right')
        self.p_henry.add_layout(color_bar1, 'right')

        # Add a linked selection and hover effect
        sel = Circle(fill_alpha=1, fill_color="black", line_color='red')
        rendl.selection_glyph = sel
        rendr.selection_glyph = sel
        rendl.hover_glyph = sel
        rendr.hover_glyph = sel

        # Generate labels:
        self.top_graph_label()

    def top_graph_label(self):
        self.p_loading.xaxis.axis_label = '{0} (mmol/g)'.format(self.g0)
        self.p_loading.yaxis.axis_label = '{0} (mmol/g)'.format(self.g1)
        self.p_henry.xaxis.axis_label = '{0} (dimensionless)'.format(
            self.g0)
        self.p_henry.yaxis.axis_label = '{0} (dimensionless)'.format(
            self.g1)

    def mapper(self, z):
        return linear_cmap(
            field_name='z{0}'.format(z), palette=palette,
            low_color='grey', high_color='red',
            low=3, high=90)

    def bottom_graphs(self):
        self.p_g1iso = figure(tools=TOOLS, active_scroll="wheel_zoom",
                              plot_width=400, plot_height=400,
                              title='Isotherms 1')
        self.p_g2iso = figure(tools=TOOLS, active_scroll="wheel_zoom",
                              plot_width=400, plot_height=400,
                              title='Isotherms 2')

    # #########################################################################
    # Data generator

    def gen_data(self):

        common = intersect([a for a in self.data_dict[self.g0]],
                           [a for a in self.data_dict[self.g1]])

        dd = self.data_dict
        g0 = self.g0
        g1 = self.g1
        p = self.pressure

        return dict(
            labels=common,
            x0=[dd[g0][mat]['mL'][p] for mat in common],
            y0=[dd[g1][mat]['mL'][p] for mat in common],
            x1=[dd[g0][mat]['mKh'] for mat in common],
            y1=[dd[g1][mat]['mKh'] for mat in common],
            z0=[dd[g0][mat]['lL'][p] + dd[g1][mat]['lL'][p] for mat in common],
            z1=[dd[g0][mat]['lKh'] + dd[g1][mat]['lKh'] for mat in common],
        )

    # #########################################################################
    # Error generator

    def gen_error(self, index):

        if index is None:
            return dict(
                x00=[], y00=[], x01=[], y01=[],
                x10=[], y10=[], x11=[], y11=[])

        else:
            p = self.pressure

            mat = self.data.data['labels'][index]
            x0 = self.data.data['x0'][index]
            y0 = self.data.data['y0'][index]
            xe00 = self.data_dict[self.g0][mat]['eL'][p]
            xe01 = self.data_dict[self.g1][mat]['eL'][p]
            x1 = self.data.data['x1'][index]
            y1 = self.data.data['y1'][index]
            xe10 = self.data_dict[self.g0][mat]['eKh']
            xe11 = self.data_dict[self.g1][mat]['eKh']

            e_dict = dict(
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
    # Text

    def gen_details(self, index=None):
        if index is None:
            return ""
        else:
            mat = self.data.data['labels'][index]

            data = {
                'material': mat,
                'gas0': self.g0,
                'gas1': self.g1,
                'gas0_load': self.data.data['x0'][index],
                'gas1_load': self.data.data['y0'][index],
                'gas0_hk': self.data_dict[self.g0][mat]['mKh'],
                'gas1_hk': self.data_dict[self.g1][mat]['mKh'],
                'gas0_iso': len(self.data_dict[self.g0][mat]['isos']),
                'gas1_iso': len(self.data_dict[self.g1][mat]['isos']),
            }
            return DETAILS.format(**data)

    # #########################################################################
    # Isotherms

    def gen_isos(self, index, which=None):

        if index is None:
            self.doc.add_next_tick_callback(self.bottom_graphs)

        else:
            mat = self.data.data['labels'][index]

            if which == 'right':
                isos = self.data_dict[self.g0][mat]['isos']
                fig = self.p_g1iso
            elif which == 'left':
                isos = self.data_dict[self.g1][mat]['isos']
                fig = self.p_g2iso
            else:
                raise Exception

            for iso in isos:
                parsed = load_nist_isotherm(iso)

                # update the document from callback
                if parsed:
                    self.doc.add_next_tick_callback(
                        partial(self.iso_update, f=fig,
                                x=parsed.pressure(), y=parsed.loading()))

    # #########################################################################
    # Update
    @gen.coroutine
    def iso_update(self, f, x, y):
        f.line(x=x, y=y)

    # #########################################################################
    # Selection update

    def s_type_callback(self, index):

        # Reset any selected materials
        self.data.selected.update(indices=[])

        if index == 0:
            self.g0 = self.gases[0]
            self.g1 = self.gases[1]
            self.data.data = self.gen_data()
        elif index == 1:
            self.g0 = self.gases[0]
            self.g1 = self.gases[2]
            self.data.data = self.gen_data()
        elif index == 2:
            self.g0 = self.gases[3]
            self.g1 = self.gases[4]
            self.data.data = self.gen_data()
        else:
            raise Exception

        # Update labels
        self.top_graph_label()

    # #########################################################################
    # Set up pressure slider and callback

    def pressure_callback(self, attrname, old, new):
        self.pressure = self.slider.value - 1
        self.data.data = self.gen_data()
        sel = self.data.selected.indices
        if sel:
            self.details.text = self.gen_details(sel[0])
            self.errors.data = self.gen_error(sel[0])

    # #########################################################################
    # Callback for selection

    def selection_callback(self, attr, old, new):

        if len(new) == 1:
            # The user has selected a point

            # Display error points:
            self.errors.data = self.gen_error(new[0])

            # Display layout
            self.dash_layout.children.append(self.material_detail)

            # Generate material details
            self.details.text = self.gen_details(new[0])

            # Generate plots
            Thread(target=self.gen_isos, args=[new[0], 'left']).start()
            Thread(target=self.gen_isos, args=[new[0], 'right']).start()

        else:
            Thread(target=self.gen_isos, args=[None]).start()
            # dash_layout.children.remove(material_detail)
            self.errors.data = self.gen_error(None)


dash = Dashboard()
dash.show_dash()
