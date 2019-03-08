from bokeh.plotting import figure
from bokeh.transform import linear_cmap
from bokeh.layouts import row, column, gridplot, layout
from bokeh.models import Circle, ColorBar
from bokeh.models import ColumnDataSource, RadioButtonGroup, Slider, Div
from bokeh.io import curdoc
from bokeh.layouts import widgetbox
from bokeh.palettes import Spectral10 as palette

from helpers import load_data, load_nist_isotherm
data_dict = load_data()


def intersect(a, b):
    return [val for val in a if val in b]


gases = ['carbon dioxide', 'nitrogen', 'methane', 'ethane', 'ethene']
gas = [gases[0], gases[1]]
pnt = 0


def gen_data(g1, g2, p):

    common = intersect([a for a in data_dict[g1]],
                       [a for a in data_dict[g2]])

    return dict(
        labels=common,
        x0=[data_dict[g1][mat]['mL'][p] for mat in common],
        y0=[data_dict[g2][mat]['mL'][p] for mat in common],
        x1=[data_dict[g1][mat]['mKh'] for mat in common],
        y1=[data_dict[g2][mat]['mKh'] for mat in common],
        z0=[data_dict[g1][mat]['lL'][p] + data_dict[g2][mat]['lL'][p]
            for mat in common],
        z1=[data_dict[g1][mat]['lKh'] + data_dict[g2][mat]['lKh']
            for mat in common],
    )


source = ColumnDataSource(data=gen_data(gas[0], gas[1], pnt))

# #########################################################################
# Error generator and points


def gen_error(index, p=0):

    if index is None:
        return dict(
            x00=[], y00=[], x01=[], y01=[],
            x10=[], y10=[], x11=[], y11=[])

    else:
        mat = source.data['labels'][index]
        x0 = source.data['x0'][index]
        y0 = source.data['y0'][index]
        xe00 = data_dict[gas[0]][mat]['eL'][p]
        xe01 = data_dict[gas[1]][mat]['eL'][p]
        x1 = source.data['x1'][index]
        y1 = source.data['y1'][index]
        xe10 = data_dict[gas[0]][mat]['eKh']
        xe11 = data_dict[gas[1]][mat]['eKh']

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


errors = ColumnDataSource(data=gen_error(None))

# #########################################################################
# Plot

TOOLS = "pan,wheel_zoom,tap,reset"

TOOLTIP1 = """
<div>
    <div>
        <span style="font-size: 17px; font-weight: bold;">@labels</span>
    </div>
    <div>
        <span style="font-size: 10px;">Location:</span>
        <span style="font-size: 10px; color: #696;">(@x0, @y0)</span>
    </div>
    <div>
        <span style="font-size: 10px;">Isotherms:</span>
        <span style="font-size: 10px; color: #696;">@z0</span>
    </div>
</div>
"""

TOOLTIP2 = """
<div>
    <div>
        <span style="font-size: 17px; font-weight: bold;">@labels</span>
    </div>
    <div>
        <span style="font-size: 10px;">Location:</span>
        <span style="font-size: 10px; color: #696;">(@x1, @y1)</span>
    </div>
    <div>
        <span style="font-size: 10px;">Isotherms:</span>
        <span style="font-size: 10px; color: #696;">@z1</span>
    </div>
</div>
"""

mapper0 = linear_cmap(
    field_name='z0', palette=palette,
    low_color='grey', high_color='red',
    low=3, high=90)
mapper1 = linear_cmap(
    field_name='z1', palette=palette,
    low_color='grey', high_color='red',
    low=3, high=90)

l_width = 500

# create a new plot and add a renderer
p_loading = figure(tools=TOOLS, tooltips=TOOLTIP1,
                   active_scroll="wheel_zoom",
                   x_range=(0, 12), y_range=(0, 12),
                   plot_width=l_width, plot_height=500,
                   title='Amount adsorbed')
rendl = p_loading.circle('x0', 'y0', source=source, size=10,
                         line_color=mapper0, color=mapper0)
errs = p_loading.segment('x00', 'y00', 'x01', 'y01', source=errors,
                         color="black", line_width=2)

# create another new plot and add a renderer
p_henry = figure(tools=TOOLS, tooltips=TOOLTIP2,
                 active_scroll="wheel_zoom",
                 x_range=(1e-2, 1e5), y_range=(1e-2, 1e5),
                 plot_width=500, plot_height=500,
                 y_axis_type="log", x_axis_type="log",
                 title='Initial Henry constant')
rendr = p_henry.circle('x1', 'y1', source=source, size=10,
                       line_color=mapper1, color=mapper1)
errs = p_henry.segment('x10', 'y10', 'x11', 'y11', source=errors,
                       color="black", line_width=2)

p_loading.xaxis.axis_label = '%s (mmol/g)' % gas[0]
p_loading.yaxis.axis_label = '%s (mmol/g)' % gas[1]
p_henry.xaxis.axis_label = '%s (dimensionless)' % gas[0]
p_henry.yaxis.axis_label = '%s (dimensionless)' % gas[1]

color_bar0 = ColorBar(
    color_mapper=mapper0['transform'], width=8,  location=(0, 0))
color_bar1 = ColorBar(
    color_mapper=mapper1['transform'], width=8,  location=(0, 0))
p_loading.add_layout(color_bar0, 'right')
p_henry.add_layout(color_bar1, 'right')

# #########################################################################
# Add click display between the two

sel = Circle(fill_alpha=1, size=15, fill_color="black", line_color=None)

rendl.selection_glyph = sel
rendr.selection_glyph = sel
rendl.hover_glyph = sel
rendr.hover_glyph = sel


# #########################################################################
# Radio selections

s_type = RadioButtonGroup(
    labels=["CO2 / N2", "CO2 / CH4", "C3H6 / C2H4"], active=0)


def s_type_callback(index):

    # Reset selected
    source.selected.update(indices=[])

    if index == 0:
        gas[0] = gases[0]
        gas[1] = gases[1]
        source.data = gen_data(gas[0], gas[1], pnt)
    elif index == 1:
        gas[0] = gases[0]
        gas[1] = gases[2]
        source.data = gen_data(gas[0], gas[1], pnt)
    elif index == 2:
        gas[0] = gases[3]
        gas[1] = gases[4]
        source.data = gen_data(gas[0], gas[1], pnt)
    else:
        raise Exception

    # Update labels
    p_loading.xaxis.axis_label = '%s (mmol/g)' % gas[0]
    p_loading.yaxis.axis_label = '%s (mmol/g)' % gas[1]
    p_henry.xaxis.axis_label = '%s (dimensionless)' % gas[0]
    p_henry.yaxis.axis_label = '%s (dimensionless)' % gas[1]


s_type.on_click(s_type_callback)


# #########################################################################
# Isotherm graph

# create a new plot and add a renderer
p_g1iso = figure(tools=TOOLS, active_scroll="wheel_zoom",
                 plot_width=l_width, plot_height=500,
                 title='Amount adsorbed')


def gen_isos(index):

    if index is None:
        return dict()

    else:
        mat = source.data['labels'][index]
        isos = data_dict[gas[0]][mat]['isos']

        for iso in isos:

            parsed = load_nist_isotherm(iso)
            p_g1iso.line(x=parsed.pressure(), y=parsed.loading())


# #########################################################################

# Set up widgets
slider = Slider(title="pressure", value=1, start=1, end=3, step=1,)


def pressure_update(attrname, old, new):
    source.data = gen_data(gas[0], gas[1], slider.value - 1)
    sel = source.selected.indices
    if sel:
        errors.data = gen_error(sel[0], slider.value - 1)


slider.on_change('value', pressure_update)


# #########################################################################
# Div Display details

def gen_details(index=None):
    if index is None:
        return ""
    else:
        text = """
        <div>
            <h2>Material</h2>
        </div>
        <div>
            <span>Trying something</span>
            <span style="font-size: 20px; font-weight: bold;>And something else</span>
        </div>
        """
        return text


details = Div(text=gen_details(), width=800, height=500)

# #########################################################################
# Callback for selection


def callback(attr, old, new):
    if len(new) == 1:
        errors.data = gen_error(new[0], pnt)
        details.text = gen_details(new[0])
        gen_isos(new[0])
        details.style = dict()
        # details.style = ""
    else:
        errors.data = gen_error(None, pnt)
        details.style = dict(display="none")
        # details.text = gen_details(None)


source.selected.on_change('indices', callback)


# #########################################################################
# Final layout

instructions = Div(
    text="""
    <h1>Material explorer for separations</h1>
    Select the separation dataset by clicking on the buttons below.
    Hover over a point to display a tool-tip with material information,
    click it to focus on a particular material.
    The loading graph shows the amount adsorbed at the pressure
    set by the slider below it.
    """,
    width=800, height=100
)

l = layout([
    [instructions],
    [s_type],
    gridplot([[p_loading, p_henry]]),
    [widgetbox(slider)],
    [details, p_g1iso]
])


curdoc().title = "Graphs"
curdoc().add_root(l)
