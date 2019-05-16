from bokeh.plotting import figure
from bokeh.layouts import widgetbox, gridplot, layout
from bokeh.models import Slider, Div, RadioButtonGroup


class Dashboard():

    def __init__(self, doc):

        # Radio selections
        self.s_type = RadioButtonGroup(
            labels=["CO2 / N2", "CO2 / CH4", "C2H6 / C2H4"], active=0)

        self.p_loading, self.rend0 = self.gen_graph()
        self.p_henry, self.rend1 = self.gen_graph()

        # Pressure slider
        self.slider = Slider(title="Pressure", value=0.5,
                             start=0.5, end=20, step=0.5)

        # Material details
        self.details = Div(text="Middle text", width=500)

        self.p_g0iso, self.rend0 = self.gen_graph()
        self.p_g1iso, self.rend1 = self.gen_graph()

        # Isotherm details
        self.details_iso = Div(text="Bottom text", height=400)

        self.dash_layout = layout([
            [widgetbox(self.s_type)],
            [gridplot([[self.p_henry, self.p_loading]])],
            [widgetbox(children=[self.slider])],
            [self.details],
            [gridplot([[self.p_g0iso, self.p_g1iso]])],
            [self.details_iso],
        ], sizing_mode='scale_width')

        doc.title = "Graphs"
        doc.add_root(self.dash_layout)

    def gen_graph(self):

        plot_side_size = 500
        fig_dict = dict(active_scroll="wheel_zoom",
                        plot_width=plot_side_size,
                        plot_height=plot_side_size)
        # create a new plot and add a renderer
        graph = figure(**fig_dict)

        # Data
        rend = graph.circle(x=[0, 2, 3], y=[3, 6, 4], size=10)

        return graph, rend
