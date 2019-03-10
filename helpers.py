import json
from os.path import dirname, join
from pathlib import Path

import requests

import pygaps

TOOLS = "pan,wheel_zoom,tap,reset"

TOOLTIP = Path(dirname(__file__), 'templates', 'tooltip.html').read_text()
DETAILS = Path(dirname(__file__), 'templates', 'mat_details.html').read_text()


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
