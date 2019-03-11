from datetime import date
from random import randint

from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import widgetbox, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn, Button


def data():
    return dict(
        dates=[date(2014, 3, i+1) for i in range(10)],
        xs=[randint(0, 100) for i in range(10)],
        ys=[randint(0, 100) for i in range(10)],
    )


source = ColumnDataSource(data())

fig = figure(plot_width=500, plot_height=500)
glyphs = fig.circle('xs', 'ys', source=source, size=10)

columns = [
    TableColumn(field="dates", title="Date"),
    TableColumn(field="xs", title="xs"),
    TableColumn(field="ys", title="ys"),
]
data_table = DataTable(source=source, columns=columns, width=400, height=280)


def recreate_data():
    source.data = data()


bt = Button(label="Click")
bt.on_click(recreate_data)

curdoc().add_root(column(fig, data_table, widgetbox(bt)))
