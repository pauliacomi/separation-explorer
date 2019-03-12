from datetime import date
from random import randint

from bokeh.io import curdoc
from bokeh.plotting import figure, Row
from bokeh.layouts import widgetbox, column
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models.widgets import DataTable, TableColumn, Button

import numpy as np

p = figure()

a = {
    'labels': ['10.1016j.micromeso.2013.06.023.Isotherm9'],
    'x': [[0.00731707, 0.0121951, 0.0219512, 0.0341463, 0.0707317, 0.097561, 0.134146, 0.165854, 0.202439, 0.236585, 0.270732, 0.3, 0.334146, 0.368293, 0.395122, 0.463415, 0.534146, 0.6, 0.665854, 0.731707, 0.8, 0.865854, 0.931707, 1.00976, 1.06585]],
    'y': [[0.313564, 0.57009, 0.769752, 0.912492, 1.34071, 1.65474, 1.88353, 2.02673, 2.14156, 2.31331, 2.42808, 2.54274, 2.60053, 2.74379, 2.8014, 2.97397, 3.0896, 3.20513, 3.34914, 3.43618, 3.55176, 3.66728, 3.72582, 3.81315, 3.92844]]
}


source = ColumnDataSource(data=a)

p.multi_line('x', 'y', source=source,
             alpha=0.6, line_width=4,
             hover_line_alpha=1.0)

p.add_tools(HoverTool(show_arrow=False,
                      line_policy='nearest'))
layout = Row(p)


curdoc().add_root(layout)
