import json

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

j2_env = Environment(
    loader=FileSystemLoader(str(Path.cwd() / 'templates')))
# str() wrapper to path needed because of 3.7 bug
# see: https://bugs.python.org/issue33617

iso_packed = "./data/iso-packed"


def load_tooltip():
    """Load the graph tooltip."""
    return j2_env.get_template('tooltip.html')


def load_details():
    """Load the detail snippet."""
    return j2_env.get_template('iso-details.html')


def load_details_js():
    """Load the detail snippet."""
    path = Path.cwd() / 'templates' / 'js' / 'populate-details.js'
    with open(path, 'r') as file:
        return file.read()


def load_isotherm(filename):
    """Load a particular isotherm."""

    import shelve

    iso_packed = "./data/iso-packed"

    try:
        with shelve.open(iso_packed) as db:
            iso = db[filename]
    except Exception as e:
        print(e)

    return {
        'labels': [filename],
        'x': [iso['x']],
        'y': [iso['y']],
        'doi': [iso['doi']],
        'temp': [iso['temp']],
    }


def load_data():
    """Load explorer data."""
    import pandas as pd
    return pd.read_hdf(Path.cwd() / 'data' / 'kpi.h5', 'table')
