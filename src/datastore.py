from src.helpers import load_data
from src.statistics import select_data

################################
# Important global variables
################################

DATASET = None          # Entire dataset
INITIAL = None          # An example initial dataset


def load():
    """Loads the global dataset and an example."""
    global DATASET, INITIAL
    # Global dataset
    DATASET = load_data()
    # Example dataset
    INITIAL = select_data(
        DATASET, None, 303, 10, 'propane', 'propene')
