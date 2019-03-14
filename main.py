from dashboard import Dashboard
from bokeh.io import curdoc

doc = curdoc()
dash = Dashboard(doc)
dash.show_dash()
