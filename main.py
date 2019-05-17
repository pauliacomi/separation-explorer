from bokeh.plotting import figure
from bokeh.layouts import widgetbox, gridplot, layout
from bokeh.models import Slider, Div, RadioButtonGroup
from bokeh.io import curdoc


def gen_graph():

    plot_side_size = 500
    fig_dict = dict(active_scroll="wheel_zoom",
                    plot_width=plot_side_size,
                    plot_height=plot_side_size)
    # create a new plot and add a renderer
    graph = figure(**fig_dict)

    # Data
    rend = graph.circle(x=[0, 2, 3], y=[3, 6, 4], size=10)

    return graph, rend


def gen_layout():

    # Radio selections
    s_type = RadioButtonGroup(
        labels=["CO2 / N2", "CO2 / CH4", "C2H6 / C2H4"], active=0)

    p_loading, rend0 = gen_graph()
    p_henry, rend1 = gen_graph()

    # Pressure slider
    slider = Slider(title="Pressure", value=0.5,
                    start=0.5, end=20, step=0.5)

    # Material details
    details = Div(text="Middle text", width=500)

    p_g0iso, rend0 = gen_graph()
    p_g1iso, rend1 = gen_graph()

    # Isotherm details
    details_iso = Div(text="Bottom text", height=400)

    return layout([
        [widgetbox(s_type)],
        [gridplot([[p_henry, p_loading]])],
        [widgetbox(children=[slider])],
        [details],
        [gridplot([[p_g0iso, p_g1iso]])],
        [details_iso],
    ], sizing_mode='scale_width')


doc = curdoc()
doc.title = "Graphs"
doc.add_root(gen_layout())


def cleanup_session(session_context):
    """Attempt to cleanup session when leaving"""
    pass


doc.on_session_destroyed(cleanup_session)
