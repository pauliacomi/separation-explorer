from os.path import dirname, join

from bokeh.io import curdoc

from src.dashboard import Dashboard


def load_data():
    """Load explorer data."""
    path = join(dirname(__file__), 'data', 'data.json')
    with open(path) as file:
        data = json.load(file)
    return data


doc = curdoc()
doc.title = "Graphs"
data = load_data()
dash = Dashboard(doc, data)
doc.add_root(dash.dash_layout)

del doc
del dash
del data
