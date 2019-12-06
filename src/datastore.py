from src.helpers import load_data
from src.statistics import select_data

################################
# Important global variables
################################

DATASET = None          # Entire dataset
INITIAL = None          # An example initial dataset
PROBES = None          # An example initial dataset


def load():
    """Load the global dataset and an example."""
    print('Loading and calculating initial data.')
    global DATASET, INITIAL, PROBES
    # Global dataset
    DATASET = load_data()
    # List of available probes
    PROBES = sorted(list(DATASET['ads'].unique()))
    # Example dataset
    INITIAL = select_data(
        DATASET, None, 303, 10, 'propane', 'propene')
    print('Data load complete.')
