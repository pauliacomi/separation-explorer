from bokeh.io import curdoc

from src.dashboard import Dashboard

doc = curdoc()
doc.title = "Separation explorer"
doc.add_root(Dashboard(doc).dash_layout)

del doc
