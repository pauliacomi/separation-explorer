import json
from os.path import dirname, join

import requests

import pygaps


def intersect(a, b):
    return [val for val in a if val in b]


def load_data():
    """Load explorer data."""
    path = join(dirname(__file__), 'data', 'data.json')
    with open(path) as file:
        data = json.load(file)
    return data


def load_isotherm(id):
    """Load a particular isotherm."""
    path = join(dirname(__file__), 'data', 'isotherms', 'id.json')
    with open(path) as file:
        isotherm = pygaps.isotherm_from_json(file.read())
    return isotherm


def load_nist_isotherm(filename):
    """Load an isotherm from NIST ISODB."""

    url = r"https://adsorption.nist.gov/isodb/api/isotherm/{0}".format(
        filename)
    r = requests.get(url)

    # TODO: Need to fail gracefully

    return pygaps.isotherm_from_json(r.text, fmt="NIST")
