import json

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

j2_env = Environment(
    loader=FileSystemLoader(str(Path.cwd() / 'templates')))
# str() wrapper to path needed because of 3.7 bug
# see: https://bugs.python.org/issue33617

isodb_base = "https://adsorption.nist.gov/isodb/api/"


def load_tooltip():
    """Load the graph tooltip."""
    return j2_env.get_template('tooltip.html')


def load_spinner():
    """Load the graph tooltip."""
    return j2_env.get_template('spinner.html')


def load_isotherm(filename):
    """Load a particular isotherm."""
    # path = Path.cwd() / 'data' / 'isotherms' / '{0}.json'.format(filename)

    # try:
    #     with open(path) as file:
    #         iso = json.load(file)
    # except Exception:
    #     return None

    import requests
    isodb_session = requests.Session()

    try:
        iso = isodb_session.get(
            isodb_base + "isotherm/" + filename + '.json', timeout=5).json()
    except Exception as e:
        print(e)

    return {
        'labels': iso['filename'],
        'x': [a['pressure'] for a in iso['isotherm_data']],
        'y': [a['species_data'][0]['adsorption']
              for a in iso['isotherm_data']],
        'doi': iso['DOI'],
        'temp': iso['temperature'],
    }


def load_data():
    """Load explorer data."""
    import pandas as pd
    return pd.read_hdf(Path.cwd() / 'data' / 'kpi.h5', 'table')
