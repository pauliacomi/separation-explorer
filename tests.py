from bokeh.io import curdoc

from bokeh.plotting import figure
from bokeh.layouts import layout, gridplot, column, row, widgetbox
from bokeh.models.widgets import (
    Button, RadioButtonGroup, Spinner,
    Slider, RangeSlider, Select, Div
)

# l = layout([
#     [
#         Button(label="Show me how this works!"),
#         RadioButtonGroup(labels=["All Data", "Experimental", "Simulated"])
#     ],
#     [
#         Select(title="Adsorbate 1", options=['a', 'b'], value='a'),
#         Select(title="Adsorbate 2", options=['a', 'b'], value='b'),
#         Spinner(value=303, title='Temperature:'),
#         Spinner(value=10, title='Tolerance:'),
#     ],
# ], sizing_mode='scale_width')

l = layout([
    [
        RadioButtonGroup(
            labels=["All Data", "Experimental", "Simulated"])
    ],
    [
        Select(title="Adsorbate 1", options=['a', 'b'], value='a'),
        Select(title="Adsorbate 2", options=['a', 'b'], value='b'),
        Spinner(value=303, title='Temperature:'),
        Spinner(value=10, title='Tolerance:'),
    ],
], sizing_mode='scale_width')

curdoc().add_root(l)
curdoc().add_root(l)
