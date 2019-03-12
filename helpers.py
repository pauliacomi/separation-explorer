import pygaps
import requests
import json
from os.path import dirname, join

from jinja2 import Environment, FileSystemLoader

j2_env = Environment(
    loader=FileSystemLoader(join(dirname(__file__), 'templates')))


TOOLS = "pan,wheel_zoom,tap,reset"

TOOLTIP = j2_env.get_template('tooltip.html')
DETAILS = j2_env.get_template('mat_details.html')
ISOTHERMS = j2_env.get_template('mat_isotherms.html')
HOVER = j2_env.get_template('js/hover.js')


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

    return load_local_isotherm(filename)

    url = r"https://adsorption.nist.gov/isodb/api/isotherm/{0}.json".format(
        filename)

    try:
        r = requests.get(url, timeout=0.5)

    except requests.exceptions.Timeout:
        print('Connection timeout')
        return load_local_isotherm(filename)

    except requests.exceptions.ConnectionError:
        print('Connection error')
        return load_local_isotherm(filename)

    return pygaps.isotherm_from_json(r.text, fmt="NIST")
