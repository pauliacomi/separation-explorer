from bokeh.io import curdoc
from bokeh.models.widgets import Panel, Tabs

from src.datamodel import DataModel
from src.dash_sep import SeparationDash
from src.dash_stor import StorageDash

doc = curdoc()

model = DataModel(doc)

sep_dash = SeparationDash(model)
stor_dash = StorageDash(model)

model.callback_link_sep(sep_dash)

s_tab = Panel(child=sep_dash.layout, title="Separation Explorer")
u_tab = Panel(child=stor_dash.layout, title="Storage Explorer")
tabs = Tabs(tabs=[s_tab, u_tab])

doc.add_root(tabs)
