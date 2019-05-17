from bokeh.io import curdoc

from src.dashboard_old import Dashboard

doc = curdoc()
dash = Dashboard(doc)
doc.title = "Graphs"
doc.add_root(dash.dash_layout)


def cleanup_session(session_context):
    """Attempt to cleanup session when leaving"""
    pass


del dash

doc.on_session_destroyed(cleanup_session)
