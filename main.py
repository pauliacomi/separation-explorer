from bokeh.io import curdoc

from src.dashboard import Dashboard
from helpers import load_data

doc = curdoc()
doc.title = "Graphs"
data = load_data()
dash = Dashboard(doc, data)
doc.add_root(dash.dash_layout)

del doc
del dash
del data
