import dateutil.parser as dp
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

    Returns
    -------
    filtered_logs : dict
        Dict identical to logs_dict, but filtered to only include those logs
        containing references to target_recipe. Additionally, if read_layers ==
        True, then an extra key 'layers' is added containing a list of layer
        indices which match target_recipe. If read_data == True an extra key
        'data' is added containing a pandas.DataFrame object holding all the raw
        logfile data."""

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

def get_means(logs_dict, target_recipe, **kwargs):
    """Calculate the mean, standard deviation, and length of all instances of
    target_recipe found in the logfiles in logs_dict.

    Parameters
    ----------
    logs_dict : dict
        Dict where key is path to logfile and value is dict of type returned by
        get_recipe.

    target_recipe : string
        Name of the recipe to get data for.

    Keyword Arguments
    -----------------
    keys_to_ignore : list
        List of column headings (keys) in logfile data to ignore. Can't take an
        average of a column full of text descriptors. Default list is:
        `['Layer #', 'Wafer # Loaded', 'Sub. Rot.', 'Radak', 'Dep. Program#']`.

    matches_to_ignore : list
        List of partial column headings to ignore. For instance, whether or not
        the plasma is on is not a value that averages, so we exclude all columns
        containing 'Plasma'. Default is `['Shutter', 'Plasma', 'SP']`.

    sources_to_ignore : list
        List of sources to exclude. Useful for skipping sources that were turned
        off. This list can contain partial matches. For instance, passing
        sources_to_ignore = ['#5'] will ignore all column headings containing
        '#5'.

    outlier_sigma : float
        If ignore outliers is turned on, this is the threshold for excluding
        points; any datapoint with a standard deviation greater than
        outlier_sigma will be cut. Default is 5.

    strip_outliers : bool
        Whether or not to exclude outliers from data. Mean and standard
        deviation will be calculated twice. Once to exclude outliers, and once
        for the final value. Default is False.

    min_length : float
        Any recipe lasting less than min_length minutes will be excluded from the
        final results. This is useful for excluding purposefully aborted jobs.
        Default is 0.

    avg_interval : [start, end]
        A tuple or list conatining the starting and ending index of the
        sub-array to average over. This is useful as some recipes start
        presputtering another target before they finish, and you may not want to
        include that step function in the average. Note that `start` and `end`
        are in points, not time. A point covers roughly 5 seconds.

    Returns
    -------
    output_dict : dict
        Dict containing the following key-value pairs:
            * 'means' : dict containing the means of each recipe ordered by
              date, indexed by logfile column name.
            * 'stdevs' : dict containing the standard deviation of each recipe
              ordered by date, indexed by logfile column name.
            * 'lengths' : list containing the lengths of each recipe, ordered
              by date.
            * 'times' : list containing the dates when the recipes were run.
            * 'keys' : list containing the keys (column headings) for which
              means were calculated.
            * 'recipe' : string containing target_recipe."""
    #Get all available keys
    keys_all = list(logs_dict.values())[0]['data'].keys()

    #Use the keys parser to return keys we care about

    #We never need to plot these keys
    keys_to_ignore = kwargs.pop('keys_to_ignore', ['Layer #', 'Wafer # Loaded', 'Sub. Rot.', 'Radak', 'Dep. Program#'])

    #Shutter and Plasma are boolean flags for each source, which can
    #also be ignored. Not sure what SP1 and SP2 are.
    matches_to_ignore = kwargs.pop('matches_to_ignore', ['Shutter', 'Plasma', 'SP'])

    #Can also ignore sources that weren't turned on
    sources_to_ignore = kwargs.pop('sources_to_ignore', [])

    matches_to_ignore += sources_to_ignore

    keys_filtered = keys_parser(keys_all, ignore_keys = keys_to_ignore, match_ignore = matches_to_ignore)

    #If desired can ignore outliers
    outlier_sigma = kwargs.pop('outlier_sigma', 5)
    strip_outliers = kwargs.pop('strip_outliers', False)

    #Minimum time length
    min_length = kwargs.pop('min_length', 0)

    #Interval over which to calculate
    avg_interval = kwargs.pop('avg_interval', [])

    if len(avg_interval) == 0:
        avg_start = 0
        avg_end = -1
    else:
        avg_start = avg_interval[0]
        avg_end = avg_interval[1]

    #Empty dicts for stuffing reduced data
    means = {}
    stdevs = {}

    #Times are the same between all column keys
    times = []

    #Length of each times vector
    lengths = []

    #Step through the keys and reduce data in each one
    for kix, key in enumerate(keys_filtered):
        means[key] = []
        stdevs[key] = []

        #Step through all the logfiles and locate all instances of the recipe in question
        for logfile, data_dict in logs_dict.items():
            #The logfile DataFrame
            df = data_dict['data']

            #The layernumbers corresponding to the recipe
            lnums = data_dict['layers'][target_recipe]

            #Some jobs call the same recipe multiple times, so grab them all
            for lnum in lnums:
                if lnum in set(df['Layer #'].values):

                    #The column of data to plot
                    col_df = df[df['Layer #'] == lnum][key]

                    #Time in minutes
                    td = 1e-9/60*np.array(col_df.index-col_df.index[0], float)

                    if td[-1] > min_length:

                        #Can strip outliers if they are really bad
                        if strip_outliers:
                            col_df = col_df[np.abs(col_df-col_df.mean())<=(outlier_sigma*col_df.std())]
                            td = 1e-9/60*np.array(col_df.index-col_df.index[0], float)

                        #Since all the lengths and times are the same between keys, only need to do this for the first one
                        if kix == 0:
                            lengths.append(td[-1])
                            times.append(col_df.index[-1])

                        #Get mean and stdev of reach recipe run within some window
                        means[key].append(col_df[avg_start:avg_end].mean())
                        stdevs[key].append(col_df[avg_start:avg_end].std())
                else:
                    #Sometimes a job is cancelled before the planned recipe was executed
                    warnings.warn(logfile+" aborted early! May not be any data to plot.", UserWarning)

    output_dict = { 'means':means,
                    'stdevs':stdevs,
                    'lengths' : lengths,
                    'times':times,
                    'keys' : keys_filtered,
                    'recipe': target_recipe}

    return output_dict


def keys_parser(keys, ignore_keys = [], match_ignore = []):
    """Parse a list of keys and remove ones that don't fit.

    Parameters
    ----------
    keys : list
        List of strings.

    ignore_keys : list
        List of strings. These keys will be removed if there is an exact match.

    match_ignore : list
        List of strings. Any key that contains as a substring one of the strings
        in match_ignore will be removed.

    Returns
    -------
    filtered_keys : list
        List of strings."""

    for key in keys:
        if any(match in key for match in match_ignore):
            ignore_keys.append(key)

    filtered_keys = list(set(keys)-set(ignore_keys))
    filtered_keys.sort()

    return filtered_keys

def plot_means(means_dict, **kwargs):
    """Plot all the data returned by get_means.

    Parameters
    ----------
    means_dict : dict
        A dict of the format returned by get_means.

    Keyword Arguments
    -----------------
    return_fig : bool
        Whether or not function returns a matplotlib.figure object. Default is
        False.

    overlay_fig : matplotlib.figure
        Can pass a figure returned by plot_means and it will overplot a second
        recipe's data. This only works if all the relevant column headings
        between recipes are the same.

    num_rows : int
        How many rows of subplots the resulting figure shoudl have. Default is 3.

    grid_kwargs : dict
        A dict of keyword arguments that will be passed through to matplotlib's
        grid function. Default is {}.

    err_kwargs : varied
        Any extra keyword arguments that are passed will be bundled into
        err_kwargs and passed through to matplotlib.pyplot.errorbar().

    Returns
    -------
    fig : matplotlib.figure
        If return_fig == True, then returns the figure object. Otherwise there
        is no return value."""

    keys_to_plot = means_dict['keys']

    return_fig = kwargs.pop('return_fig', False)

    overlay_fig = kwargs.pop('overlay_fig', None)

    num_rows = kwargs.pop('num_rows', 3)
    num_cols = np.ceil((len(keys_to_plot)+1)/num_rows)

    grid_kwargs = kwargs.pop('grid_kwargs', {})

    #Whatever is left is passed to plt.errorbar
    err_kwargs = kwargs
    if 'fmt' not in err_kwargs.keys():
        err_kwargs['fmt'] = 'o'

    #Set up subplots grid
    if overlay_fig is None:
        fig = plt.figure(figsize=(4*num_cols, 4*num_rows))

        #Empty list for holding axes
        axs = []
    else:
        fig = overlay_fig
        axs = fig.get_axes()

    #First axis
    if overlay_fig is None:
        axs.append(fig.add_subplot(num_rows, num_cols, 1))

    splot = axs[0].scatter(means_dict['times'], means_dict['lengths'])
    axs[0].set_title('Job length')
    axs[0].set_xlabel('Date')
    axs[0].set_ylabel('Job length (min)')
    axs[0].grid()

    #Step through the keys and plot the data in each one
    for aix, key in enumerate(keys_to_plot):
        if overlay_fig is None:
            ax = fig.add_subplot(num_rows, num_cols, aix+2)
            axs.append(ax)
        else:
            ax = axs[aix+1]

        ax.errorbar(means_dict['times'], means_dict['means'][key], yerr=means_dict['stdevs'][key], **err_kwargs)

        ax.grid(**grid_kwargs)

        ax.set_title(key)
        ax.set_xlabel('Date')
        ax.set_ylabel(key)

    #Have to call the draw method in order for the x-ticks to get calculated.
    fig.canvas.draw()

    #Rotate the date labels by 45 deg so they don't crowd each other.
    if overlay_fig is None:
        for ax in axs:
            ax.set_xticklabels(labels=ax.get_xmajorticklabels(), rotation=45)

        fig.legend(handles=[splot], labels=[means_dict['recipe']], scatterpoints=1)
    else:
        new_labels = fig.legend.get_labels() + [means_dict['recipe']]

        legend_handles = fig.legend.get_handles() + [splot]

        fig.legend(handles=legend_handles, labels=new_labels)

    #This adjusts subplot spacing so there's no overlap
    fig.tight_layout()

    #Adjust the whole thing down and add a main title
    st = fig.suptitle('Reduced recipe data', fontsize="x-large")
    st.set_y(0.95)
    fig.subplots_adjust(top=0.90)

    if return_fig:
        return fig

def overplot_all(logs_dict, target_recipe, **kwargs):
    """Plot all instances of target_recipe vs. time on top of each other.

    Parameters
    ----------
    logs_dict : dict
        Dict of format returned by calling filter_logs with read_data set to True.

    Keyword Arguments
    -----------------
    keys_to_ignore : list
        List of column headings (keys) in logfile data to ignore. Can't take an
        average of a column full of text descriptors. Default list is:
        `['Layer #', 'Wafer # Loaded', 'Sub. Rot.', 'Radak', 'Dep. Program#']`.

    matches_to_ignore : list
        List of partial column headings to ignore. For instance, whether or not
        the plasma is on is not a value that averages, so we exclude all columns
        containing 'Plasma'. Default is `['Shutter', 'Plasma', 'SP']`.

    sources_to_ignore : list
        List of sources to exclude. Useful for skipping sources that were turned
        off. This list can contain partial matches. For instance, passing
        sources_to_ignore = ['#5'] will ignore all column headings containing
        '#5'.

    outlier_sigma : float
        If ignore outliers is turned on, this is the threshold for excluding
        points; any datapoint with a standard deviation greater than
        outlier_sigma will be cut. Default is 5.

    strip_outliers : bool
        Whether or not to exclude outliers from data. Mean and standard
        deviation will be calculated twice. Once to exclude outliers, and once
        for the final value. Default is False.

    min_recipe_time : float
        Any recipe lasting less than min_recipe_time minutes will be excluded
        from the final results. This is useful for excluding purposefully
        aborted jobs. Default is 0.

    num_rows : int
        The number of rows in the subplot grid.

    overplot_vlines : list
        A list of indices where vertical lines should be plotted. This is
        useful for visualizing the avg_interval passed to get_means.

    vline_kwargs : dict
        A dict of keyword arguments passed to matplotlib.Axis.axvline() to
        enable customization of appearance. Default is {color : 0.4,
        linestyle : '--'}.

    return_fig : bool
        Whether or not to return the figure object. Default is False.

    plt_kwargs : varied
        Any remaining keyword arguments will be bundled and passed on to
        matplotlib.Axis.plot().

    Returns
    -------
    fig : matplotlib.Figure
        If return_fig == True, then fig is returned. Otherwise nothing is
        returned."""

    #Get all available keys
    all_keys = list(logs_dict.values())[0]['data'].keys()

    #Use the keys parser to return keys we care about

    #We never need to plot these keys
    keys_to_ignore = kwargs.pop('keys_to_ignore', ['Layer #', 'Wafer # Loaded', 'Sub. Rot.', 'Radak', 'Dep. Program#'])

    #Shutter and Plasma are boolean flags for each source, which can
    #also be ignored. Not sure what SP1 and SP2 are.
    matches_to_ignore = kwargs.pop('matches_to_ignore', ['Shutter', 'Plasma', 'SP'])

    #Can also ignore sources that weren't turned on
    sources_to_ignore = kwargs.pop('sources_to_ignore', [])

    matches_to_ignore += sources_to_ignore

    keys_to_plot = keys_parser(all_keys, ignore_keys = keys_to_ignore, match_ignore = matches_to_ignore)

    #How many rows of plots to have
    num_rows = kwargs.pop('num_rows',3)

    #If desired can ignore outliers
    outlier_sigma = kwargs.pop('outlier_sigma', 5)
    strip_outliers = kwargs.pop('strip_outliers', False)

    #What is the minimum length recipe to plot (minutes)?
    #This is to weed out known bad runs that were aborted manually
    min_recipe_time = kwargs.pop('min_recipe_time', 0)

    #Overplot vlines if desired
    overplot_vlines = kwargs.pop('overplot_vlines', [])

    #Whether or not to return the figure object
    return_fig = kwargs.pop('return_fig', False)

    #Can optionally plot some nice vertical lines to denote a range
    vline_kwargs = kwargs.pop('vline_kwargs', {})

    #Set up the default vline plotting kwargs
    if 'color' not in vline_kwargs.keys():
        vline_kwargs['color'] = '0.4'

    if 'linestyle' not in vline_kwargs.keys():
        vline_kwargs['linestyle'] = '--'

    #Whatever kwargs are left over are assumed to be plotting kwargs
    plt_kwargs = kwargs

    #Set some plotting defaults

    #transparency of individual traces
    if 'alpha' not in plt_kwargs.keys():
        plt_kwargs['alpha'] = 0.5

    fig = plt.figure(figsize=(4*np.ceil(len(keys_to_plot)/num_rows),4*num_rows))

    #Step through the keys and plot the data in each one
    for aix, key in enumerate(keys_to_plot):
        ax = fig.add_subplot(num_rows,np.ceil(len(keys_to_plot)/num_rows),aix+1)
        ax.set_title(key)
        ax.set_xlabel('Time (m)')
        ax.set_ylabel(key)

        #Step through all the logfiles and locate all instances of the recipe in question
        for logfile, data_dict in logs_dict.items():
            #The logfile DataFrame
            df = data_dict['data']

            #The layernumbers corresponding to the recipe
            lnums = data_dict['layers'][target_recipe]

            #Some jobs call the same recipe multiple times, so grab them all
            for lnum in lnums:
                if lnum in set(df['Layer #'].values):

                    #The column of data to plot
                    col_df = df[df['Layer #'] == lnum][key]

                    if len(col_df) > 0:

                        #Time in minutes
                        td = 1e-9/60*np.array(col_df.index-col_df.index[0], float)

                        if td[-1] > min_recipe_time:

                            #Can strip outliers if they are really bad
                            if strip_outliers:
                                col_df = col_df[np.abs(col_df-col_df.mean())<=(outlier_sigma*col_df.std())]
                                td = 1e-9/60*np.array(col_df.index-col_df.index[0], float)

                            if td[-1] > min_recipe_time:
                                ax.plot(td, col_df, **plt_kwargs)

                                for vline in overplot_vlines:
                                    if vline < len(td-1):
                                        ax.axvline(td[vline], **vline_kwargs)

                else:
                    #Sometimes a job is cancelled before the planned recipe was executed
                    warnings.warn(logfile+" aborted early! May not be any data to plot.", UserWarning)


    fig.tight_layout()


    #Adjust the whole thing down and add a main title
    st = fig.suptitle(target_recipe, fontsize="x-large")
    st.set_y(0.95)
    fig.subplots_adjust(top=0.90)

    #Most people probably just want to output a figure
    if return_fig:
        return fig
