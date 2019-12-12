from bokeh.io import curdoc

from src.datamodel import DataModel
from src.dash_sep import SeparationDash

doc = curdoc()

model = DataModel(doc)

sep_dash = SeparationDash(model)

model.callback_link_sep(sep_dash)

doc.add_root(sep_dash.dsel_widgets)
doc.add_root(sep_dash.process)
doc.add_root(sep_dash.kpi_plots)
doc.add_root(sep_dash.detail_plots)
