import pandas as pd

def clean_indices(df):
    """Cleans the leading and trailing spaces in the index and columns names

    Parameters
    ----------
    df: pd.DataFrame
    DataFrame to clean

    Returns
    -------
    df: pd.DataFrame
    Cleaned dataframe

    """
    if type(df.index[0]) == str:
        df.index = df.index.str.strip()
    if type(df.columns[0]) == str:
        df.columns = df.columns.str.strip()

    return df
