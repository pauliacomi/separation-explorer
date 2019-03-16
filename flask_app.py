from flask import Flask, render_template
from bokeh.embed import server_document

application = Flask(__name__)


@application.route("/")
def index():
    tag = server_document(url=r'/bokeh', relative_urls=True)
    return render_template('embed.html', script=tag)
