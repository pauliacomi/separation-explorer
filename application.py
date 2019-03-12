from bokeh.embed import server_session
from bokeh.client import pull_session
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"

# @app.route('/', methods=['GET'])
# def bkapp_page():

#     with pull_session(url="http://localhost:5006/material-explorer") as session:

#         # generate a script to load the customized session
#         script = server_session(session_id=session.id,
#                                 url='http://localhost:5006/material-explorer')

#         # use the script in the rendered page
#         return render_template("embed.html", script=script, template="Flask")


if __name__ == '__main__':
    app.run(port=8080)
