from datetime import date
from bokeh.io import curdoc
from random import randint

from bokeh.plotting import figure
from bokeh.io import output_file, show
from bokeh.layouts import widgetbox, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn

output_file("data_table.html")

data = dict(
    dates=[date(2014, 3, i+1) for i in range(10)],
    xs=[randint(0, 100) for i in range(10)],
    ys=[randint(0, 100) for i in range(10)],
)
source = ColumnDataSource(data)

fig = figure(plot_width=500, plot_height=500)
glyphs = fig.circle('xs', 'ys', source=source, size=10)

columns = [
    TableColumn(field="dates", title="Date", formatter=DateFormatter()),
    TableColumn(field="xs", title="xs"),
    TableColumn(field="ys", title="ys"),
]
data_table = DataTable(source=source, columns=columns, width=400, height=280)

curdoc().add_root(column(fig, data_table))
