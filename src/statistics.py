import numpy as np
import pandas as pd
from contextlib import contextmanager


@contextmanager
def _group_selection_context(groupby):
    """
    Set / reset the _group_selection_context.
    """
    groupby._set_group_selection()
    yield groupby
    groupby._reset_group_selection()


def stats(series):

    no_nan = series.dropna()
    size = len(no_nan)

    if size == 0:
        med = np.nan
        std = 0
    elif size == 1:
        med = float(no_nan)
        std = 0
    elif size == 2:
        med = np.average(no_nan)
        std = 0
    elif 2 < size <= 4:
        med = np.average(no_nan)
        std = np.std(no_nan)
    elif 4 < size:
        # Computing IQR
        Q3, Q1 = np.nanpercentile(
            sorted(no_nan), [75, 25], interpolation='linear')
        IQR = Q3 - Q1
        med = np.mean((Q1 - 1.5 * IQR < no_nan) | (no_nan > Q3 + 1.5 * IQR))
        std = np.std(no_nan)

    return pd.Series((size, med, std), index=(["size", "med", "err"]),
                     name=series.name)


def process(data):
    with _group_selection_context(data):
        return data.apply(
            lambda x: pd.concat(
                [stats(s) for _, s in x.items()],
                axis=1, sort=False)
        ).unstack()


def select_data(data, i_type, t_abs, t_tol, g1, g2):
    """Generate two-ads dataframe when selected."""
    # Select on data type
    if i_type:
        dft = data[data['type'] == i_type]
    else:
        dft = data

    # select on temperature
    dft = dft[dft['t'].between(t_abs - t_tol, t_abs + t_tol)]

    # generate required data
    return pd.merge(
        process(dft[dft['ads'] == g1].drop(
            columns=['type', 't', 'ads']).groupby('mat', sort=False)),
        process(dft[dft['ads'] == g2].drop(
            columns=['type', 't', 'ads']).groupby('mat', sort=False)),
        on=('mat'), suffixes=('_x', '_y'))
