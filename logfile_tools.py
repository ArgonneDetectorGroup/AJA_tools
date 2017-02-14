import pandas as pd

def import_logfile(file_name):
    """Read in an AJA logfile to a pandas.DataFrame object indexed by datetime."""
    df = pd.read_csv(file_name, sep='\t', parse_dates=[[0,1]], infer_datetime_format=True, index_col=0)
    return df
