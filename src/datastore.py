from src.helpers import load_data
from src.statistics import select_data

################################
# Important global variables
################################

DATASET = None          # Entire dataset
INITIAL = None          # An example initial dataset
PROBES = None           # Probes in the initial dataset
SETTINGS = {
    'g1': 'propane',
    'g2': 'propene',
    't_abs': 303,
    't_tol': 5,
}


def load():
    """Load the global dataset and an example."""
    print('Loading and calculating initial data.')
    global DATASET, INITIAL, PROBES, SETTINGS
    # Global dataset
    DATASET = load_data()
    # List of available probes
    PROBES = sorted(list(DATASET['ads'].unique()))
    # Example dataset
    INITIAL = select_data(
        DATASET, None,
        SETTINGS['t_abs'], SETTINGS['t_tol'],
        SETTINGS['g1'], SETTINGS['g2'])
    print('Data load complete.')
