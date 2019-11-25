import json

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

j2_env = Environment(
    loader=FileSystemLoader(str(Path.cwd() / 'templates')))
# str() wrapper to path needed because of 3.7 bug
# see: https://bugs.python.org/issue33617


def load_isotherm(filename):
    """Load a particular isotherm."""
    path = Path.cwd() / 'data' / 'isotherms' / '{0}.json'.format(filename)

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


def load_data():
    """Load explorer data."""
    import json
    import pandas as pd

    with open(Path.cwd() / 'data' / 'kpi.json') as file:
        data = json.load(file)

    data_new = {
        a: {(ok, ik): val for (ok, idct) in b.items()
            for ik, val in idct.items()}
        for (a, b) in data.items()
    }

    return pd.DataFrame.from_dict(data_new, orient='index')
