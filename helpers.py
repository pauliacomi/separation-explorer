import json
from os.path import dirname, join

import pygaps


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
