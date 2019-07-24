import os
import json

from jinja2 import Environment, FileSystemLoader

j2_env = Environment(
    loader=FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')))


def load_isotherm(filename):
    """Load a particular isotherm."""
    path = os.path.join(os.path.dirname(__file__), 'data', 'isotherms',
                        '{0}.json'.format(filename))

    try:
        with open(path) as file:
            iso = json.load(file)
    except Exception:
        return None

    name = iso['filename']
    pressure = [a['loading'] for a in iso['isotherm_data']]
    loading = [a['pressure'] for a in iso['isotherm_data']]
    doi = iso['DOI']
    temp = iso['temperature']

    return name, pressure, loading, doi, temp


def load_isotherm_internal(filename):
    """Load a particular isotherm."""
    path = os.path.join(os.path.dirname(__file__), 'data', 'isotherms-aw',
                        '{0}.json'.format(filename))

    try:
        with open(path) as file:
            iso = json.load(file)
    except Exception:
        return None

    name = iso['material'] + ' ' + iso['material_batch']
    pressure = [a['loading'] for a in iso['isotherm_data']]
    loading = [a['pressure'] for a in iso['isotherm_data']]
    doi = iso['material']
    temp = iso['temperature']

    return name, pressure, loading, doi, temp


def load_data():
    """Load explorer data."""
    import json
    import pandas as pd

    with open(os.path.join(
            os.path.dirname(__file__), 'data', 'data.json')) as file:
        data = json.load(file)

    data_new = {
        a: {(ok, ik): val for (ok, idct) in b.items()
            for ik, val in idct.items()}
        for (a, b) in data.items()
    }

    return pd.DataFrame.from_dict(data_new, orient='index')


def load_data_internal():
    """Load explorer data."""
    import json
    import pandas as pd

    with open(os.path.join(
            os.path.dirname(__file__), 'data', 'data-aw.json')) as file:
        data = json.load(file)

    data_new = {
        a: {(ok, ik): val for (ok, idct) in b.items()
            for ik, val in idct.items()}
        for (a, b) in data.items()
    }

    return pd.DataFrame.from_dict(data_new, orient='index')
