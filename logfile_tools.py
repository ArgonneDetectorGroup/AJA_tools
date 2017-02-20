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


def filter_logs(logs_dict, target_recipe, read_data = True, read_layers = True, force_overwrite = False):
    """Filter a dict of logfiles to only include those containing target_recipe.

    Parameters
    ----------
    logs_dict : dict
        Dictionary of logfiles where filename is key and value is dictionary
        with format identical to that returend by recipe_parser.get_recipe().

    target_recipe : string
        The name of the recipe to filter by.

    Keyword Arguments
    -----------------
    read_data : bool
        Whether or not to load the data from the logfile and add it to
        filtered_dict with key 'data'. Default is True.

    read_layers : bool
        Whether or not to parse the recipe list to find the indices of occurence
        of target_recipe in the job. Indices are returned as a tuple and stored
        in the layers dict (key 'layers') with key target_recipe. Default is
        True.

    force_overwrite : bool
        By default, filter_logs checks if data and layers have already been
        loaded to avoid doubling the effort. setting force_overwrite to True
        will reload the data.

    """

    #Initialize empty dict
    filtered_logs = {}

    for logfile in logs_dict.keys():
        if target_recipe in logs_dict[logfile]['recipe']:

            #get_recipe will return None if there is no extant job file
            if logs_dict[logfile]['recipe'] is not None:
                filtered_logs[logfile] = logs_dict[logfile]

                if read_data:
                    if ('data' not in filtered_logs[logfile].keys()) or (force_overwrite == True):
                        filtered_logs[logfile]['data'] = import_logfile(logfile)

                if read_layers:
                    if 'layers' not in filtered_logs[logfile].keys():
                        filtered_logs[logfile]['layers'] = {}

                    if (target_recipe not in filtered_logs[logfile]['layers'].keys()) or (force_overwrite == True):
                        layers = []
                        for rix, recipe in enumerate(filtered_logs[logfile]['recipe']):
                            if recipe == target_recipe:
                                layers.append(rix+1)

                        #Convert to tuple, as this list should be immutable
                        filtered_logs[logfile]['layers'][target_recipe] = tuple(layers)

    return filtered_logs
