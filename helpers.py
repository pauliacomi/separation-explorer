import json
from os.path import dirname, join

import requests

import pygaps

INSTRUCTIONS = """
    <h1>Material explorer for separations</h1>

    Select the separation dataset by clicking on the buttons below.
    Hover over a point to display a tool-tip with material information,
    click it to focus on a particular material. The loading graph shows 
    the amount adsorbed at the pressure set by the slider below it.
"""

TOOLTIP = """
    <div>
        <div>
            <span style="font-size: 17px; font-weight: bold;">@labels</span>
        </div>
        <div>
            <span style="font-size: 10px;">Coord (x, y):</span>
            <span style="font-size: 10px; color: #696;">(@x{0}, @y{0})</span>
        </div>
        <div>
            <span style="font-size: 10px;">Isotherms:</span>
            <span style="font-size: 10px; color: #696;">@z{0}</span>
        </div>
    </div>
"""

TOOLS = "pan,wheel_zoom,tap,reset"


def intersect(a, b):
    return [val for val in a if val in b]


def load_data():
    """Load explorer data."""
    path = join(dirname(__file__), 'data', 'data.json')
    with open(path) as file:
        data = json.load(file)
    return data


def load_local_isotherm(filename):
    """Load a particular isotherm."""
    path = join(dirname(__file__), 'data', 'isotherms',
                '{0}.json'.format(filename))
    with open(path) as file:
        isotherm = pygaps.isotherm_from_json(file.read())
    return isotherm


def load_nist_isotherm(filename):
    """Load an isotherm from NIST ISODB."""

    url = r"https://adsorption.nist.gov/isodb/api/isotherm/{0}".format(
        filename)

    try:
        r = requests.get(url, timeout=0.5)

    except requests.exceptions.Timeout:
        print('Connection timeout')
        return None

    except requests.exceptions.ConnectionError:
        print('Connection error')
        return None

    return pygaps.isotherm_from_json(r.text, fmt="NIST")
