import numpy as np
import pandas as pd


def process(series):

    no_nan = series.dropna()

    l = len(no_nan)

    if l == 0:
        return (0, np.nan, 0)

    elif l == 1:
        return (1, no_nan, 0)

    elif l == 2:
        return (l, np.average(no_nan), np.std(no_nan))

    elif 2 < l <= 4:
        return (l, np.average(no_nan), np.std(no_nan))

    elif 4 < l:
        Q1 = no_nan.quantile(0.25)
        Q3 = no_nan.quantile(0.75)
        IQR = Q3 - Q1

        removed = no_nan[(Q1 - 1.5 * IQR < no_nan) & (no_nan < Q3 + 1.5 * IQR)]

        return (len(removed), np.mean(removed), np.std(removed))

    else:
        raise Exception


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
        dft[dft['ads'] == g1].drop(
            ['type', 't', 'ads'], axis=1).reset_index().groupby('mat', sort=False).agg(process),
        dft[dft['ads'] == g2].drop(
            ['type', 't', 'ads'], axis=1).reset_index().groupby('mat', sort=False).agg(process),
        on=('mat'), suffixes=('_x', '_y'))
