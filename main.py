import json
import os

from bokeh.io import curdoc

from jinja2 import Environment, FileSystemLoader

from src.dashboard import Dashboard

j2_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


def load_data():
    """Load explorer data."""
    path = os.path.join(os.path.dirname(__file__), 'data', 'data.json')
    with open(path) as file:
        data = json.load(file)
    return data


doc = curdoc()
doc.title = "Graphs"
data = load_data()
dash = Dashboard(doc, data,
                 t_tooltip=j2_env.get_template('tooltip.html'),
                 t_matdet=j2_env.get_template('mat_details.html'),
                 t_isodet=j2_env.get_template('mat_isotherms.html')
                 )
doc.add_root(dash.dash_layout)

del doc
del dash
del data
