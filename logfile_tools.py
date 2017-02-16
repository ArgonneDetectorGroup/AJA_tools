import dateutil.parser as dp
import pandas as pd

def import_logfile(file_name):
    """Read in an AJA logfile to a pandas.DataFrame object indexed by datetime."""
    df = pd.read_csv(file_name, sep='\t', parse_dates=[[0,1]], date_parser=dp.parse, index_col=0)
    return df


def count_recipes(recipe_list, logs):
    """Return a sorted list of tuples containing (recipe, count) where count is
    the number of times that recipe has occurred accross all log files in
    logs_dict.

    Parameters
    ----------
    recipe_list : list-like
        A list containing recipe names. Use recipe_parser.build_recipe_list().

    logs_dict : dict or list
        A dictionary where the keys are unique and the values are dicts in the
        format returned by recipe_parser.get_recipe(). Alternately, a list of
        such dicts may be passed.

    Returns
    -------
    recipe_freqs : list[(string, int), ...]
        A sorted list of tuples (recipe, count) in descending order of count."""

    counts = []

    #Try and extract the values from the logs dictionary
    #If it's actually a list, this will allow it to pass through
    try:
        logs_list = list(logs.values())
    except AttributeError:
        logs_list = list(logs)

    for recipe in recipe_list:
        counter = 0
        for log in logs_list:
            counter += log['recipe'].count(recipe)
        counts.append(counter)

    recipe_freqs = list(zip(recipe_list, counts))
    recipe_freqs.sort(key=lambda x : x[1], reverse=True)

    return recipe_freqs
