from datetime import date
from random import randint

from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import widgetbox, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn, Button

import numpy as np

from bokeh.io import show
from bokeh.layouts import widgetbox
from bokeh.models.widgets import CheckboxGroup
from bokeh.models import CustomJS, ColumnDataSource
from bokeh.layouts import column, row

t = np.arange(0.0, 2.0, 0.01)
s = np.sin(3*np.pi*t)
c = np.cos(3*np.pi*t)

source = ColumnDataSource(data=dict(t=t, s=s, c=c))

plot = figure(plot_width=400, plot_height=400)
a = plot.line('t', 's', source=source, line_width=3,
              line_alpha=0.6, line_color='blue')
b = plot.line('t', 'c', source=source, line_width=3,
              line_alpha=0.6, line_color='red')

checkbox = CheckboxGroup(labels=["Cosinus", "Sinus"], active=[0, 1])

checkbox.callback = CustomJS(args=dict(line0=a, line1=b), code="""
    //console.log(cb_obj.active);
    line0.visible = false;
    line1.visible = false;
    for (i in cb_obj.active) {
        //console.log(cb_obj.active[i]);
        if (cb_obj.active[i] == 0) {
            line0.visible = true;
        } else if (cb_obj.active[i] == 1) {
            line1.visible = true;
        }
        <script>
            function change_on_hover(name, idx, value) {
                var ds = Bokeh.documents[0].get_model_by_name('my-data-source');
                ds.data[name][idx] = value;
                ds.change.emit();
            }
        </script>
    }
""")

layout = row(plot, widgetbox(checkbox))


curdoc().add_root(layout)
