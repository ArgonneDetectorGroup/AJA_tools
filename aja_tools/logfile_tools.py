import dateutil.parser as dp
import warnings
import os

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd


def nested_glob(path, extension):
    """This just searches all subdirectories of path for anything with the right extension"""
    files = [os.path.join(dirpath, f)
             for dirpath, dirnames, files in os.walk(path)
             for f in files if f.endswith(extension)]

    return files

def build_jobs_dict(path):
    """Build a dictionary of "job_name" : [recipe list] from a directory full of job
    files."""

    jobfiles = nested_glob(path, '.ajp')

    jobs = {}
    for jobfile in jobfiles:
        job_name = os.path.basename(jobfile).strip('.ajp')
        try:
            recipe = parse_jobfile(jobfile)
            jobs[job_name] = recipe
        except:
            warnings.warn("Unable to parse " + jobfile)

    return jobs

def build_logs_list(path, jobs = None):
    """Build up a list of lognames sorted by last created. Each element of the list is a dict with the jobname, recipe, path, and datetime."""
    logfiles = nested_glob(path, '.dlg')

    if jobs is None:
        try:
            warnings.warn("Attempting to locate jobs in path")
            jobs = build_jobs_dict(path)
        except:
            jobs = {}

    logs = []
    for logfile in logfiles:
        job_name = get_job(logfile)
        job_exists = job_name in jobs.keys()
        with open(logfile, 'r') as f:
            headers = f.readline()
            firstline = f.readline()

        date, time = firstline.split('\t')[0:2]

        try:
            datetime = dp.parse(date+' '+time)
            if job_exists:
                recipe = jobs[job_name]
            else:
                recipe = None
            logs.append({'job':job_name, 'datetime':datetime, 'path':logfile, 'recipe':recipe})
        except:
            warnings.warn("Could not parse: "+logfile)

    logs.sort(key=lambda x : x['datetime'], reverse=True)

    return logs

def get_job(logfile_path, jobs_dict={}, job_folder_path=None):
    """Extract the name of the job from the logfile path.

    Parameters
    ----------
    logfile_path : string
        Path to the logfile, usually has extension '.dlg'

    Returns
    -------
    job_name : string
        The job name"""

    #Extract the job name from the logfile_path
    job_name = '_'.join(os.path.basename(logfile_path).strip('.dlg').split('_')[0:-2])

    return job_name

def parse_jobfile(file_path, return_raw_recipe = False):
    """Read in an AJA job file and return a list of AJA recipe steps.

    Parameters
    ----------
    file_path : string
        Path to the job file (extension '.ajp')

    return_raw_recipe : bool
        Whether to return the raw output as parsed before cleaning it. Useful for debugging. Default is False.

    Returns
    -------
    parsed_recipe : list
        A list of recipe steps from the job file prepended by 'Start' at index 0.
    """


    if file_path.split('.')[-1] == 'ajp':
        #Extract job_name from job file path
        job_name = file_path.strip('.ajp').split('/')[-1]
    else:
        raise NameError("Unknown filetype: "+file_path.split('.')[-1])

    #Open the job file up and read it in
    with open(file_path, 'r') as f:
        raw_job = f.read()

    #Initalize a few more empty lists
    raw_recipe = []
    parsed_recipe = []

    #Parse through the recipe file and extract the information
    #Recipe files have an 8 character initial string followed by recipe steps.
    #Each recipe step is the name of a recipe file followed by a 4 char terminator.
    #The initializer and terminators all start with '\x00'
    init_len = 8
    term_len = 4
    term_char = '\x00'
    start_ix = 0
    while start_ix > -1:
        if start_ix == 0:
            raw_recipe.append((0, raw_job[0:init_len]))
            start_ix = init_len
        else:
            next_ix = raw_job.find(term_char, start_ix+1)
            if next_ix > -1:
                recipe = raw_job[start_ix:next_ix]
                delim = raw_job[next_ix:next_ix+term_len]

                raw_recipe.append((start_ix, recipe))
                raw_recipe.append((next_ix, delim))
                start_ix = next_ix + term_len
            elif start_ix < len(raw_job)-1:
                recipe = raw_job[start_ix:]
                raw_recipe.append((start_ix, recipe))
                start_ix = -1
            else:
                warnings.warn('Job file may be corrupt, missing final recipe step: '+ job_name)
                start_ix = -1

    #Make one more pass through to handle duplicates that

    #Strip out the extra data from AJA and just get the recipe names
    parsed_recipe = [rstep[1] for rstep in raw_recipe if rstep[1][0] != '\x00']

    if len(parsed_recipe) == 0:
        warnings.warn('Job file may be corrupt, no recipe steps found!')

    #The first layer of any logfile is one line with layer0. Add in a step so log layer index
    #matches recipe list index.
    parsed_recipe.insert(0, 'Start')

    if return_raw_recipe:
        retval = raw_recipe
    else:
        retval = parsed_recipe

    return retval

def import_logfile(file_name):
    """Read in an AJA logfile to a pandas.DataFrame object indexed by datetime."""

    df = pd.read_csv(file_name, sep='\t', parse_dates=[[0,1]], date_parser=dp.parse, index_col=0)
    return df

def plot_log(logfile, logtype, **kwargs):
    """Make a plot of a single logfile in a somewhat readable way."""

    if logtype == 'metals':
        target_sources = {'RF#1':'Substrate bias', 'RF#2':'Au', 'DC#1':'Ti old', 'DC#5A':'empty', 'DC#5B':'AlMn 950', 'DC#5C':'Ti new', 'DC#5D':'AlMn 850'}
        gas_sources = {'Gas#1 Flow':'Ar', 'Gas#2 Flow':'N', 'Gas#3 Flow':'O'}
    elif logtype == 'dielectrics':
        target_sources = {'RF#1':'Substrate bias', 'RF#2':'SiOx gun 3', 'RF#4A':'SiOx gun 2', 'RF#4B':'Si', 'RF#4C':'Ti', 'DC#5A':'Palladium', }
        gas_sources = {'Gas#1 Flow':'Ar', 'Gas#2 Flow':'O', 'Gas#3 Flow':'N'}
    else:
        logtype = None
        target_sources = None
        gas_sources = None

    #Allow for custom figure sizing
    figsize = kwargs.pop('figsize', None)

    #Or for a custom figure size x-multiplier
    figsize_xmult = kwargs.pop('figsize_xmult', 1.0)

    #Whether or not to show the layer subdivisions
    show_layers = kwargs.pop('show_layers', False)

    #Load in the data
    dat = import_logfile(logfile)

    #Convert boolean to boolean
    dat = dat.replace(to_replace='Closed', value=0)
    dat = dat.replace(to_replace='Open', value=1)
    dat = dat.replace(to_replace='OFF', value=0)
    dat = dat.replace(to_replace='ON', value=1)

    #Strip out any columns that are completely zero
    dat = dat.loc[:,(dat != 0).any(axis=0)]

    #Return list of remaining columns
    columns = dat.columns

    #Figure out how many guns were on at some point and build up the plot
    sources_present = []
    gas_sources = {}
    if (target_sources is not None):
        for source in target_sources.keys():
            for col in columns:
                if source in col:
                    sources_present.append(source)
                    break
    else:
        for col in columns:
            if any(source in col for source in ['RF#', 'DC#']):
                sources_present.append(col.split(' ')[0])
            if 'Gas#' in col:
                gas_sources[col] = col
        sources_present = list(set(sources_present))
        target_sources = {}
        for source in sources_present:
            target_sources[source] = source

    #For each source there are Shutter, Plasma, and target parameters axes
    #Them there is the gas axis, and temp, pressure, and rotation
    height_ratios = [1,1,4]*len(sources_present)+[2]+[1]*3

    #Figure out how many/which wafers loaded for autosizing
    if 'Wafer # Loaded' in dat.columns:
        wafers = dat['Wafer # Loaded'].unique()
    else:
        wafers = [1]

    #Set up the figure
    if figsize is None:
        figsize = (figsize_xmult*6*len(wafers), len(sources_present)*4+3.33)

    fig, axes = plt.subplots(nrows = len(height_ratios), ncols = 1,
                             figsize=figsize, sharex=True,
                             gridspec_kw = {'height_ratios':height_ratios, 'hspace':0})

    #Set up some basic axis properties so it doesn't look too bad
    for ax in axes:
        ax.margins(0.05)
        ax.tick_params(direction='in', axis='both', top='on', right='on', color=plt.cm.gray(0.9))
        ax.grid(True, color = plt.cm.gray(0.9), linestyle='--')
        for pos, sp in ax.spines.items():
            sp.set_edgecolor(plt.cm.gray(0.5))

    #Optionally plot vertical lines for each layer change
    if show_layers:
        if 'Layer #' in dat.columns:
            layer_id = 'Layer #'
        elif 'layer #' in dat.columns:
            layer_id = 'layer #'
            
        v_by_layer = dat.groupby(layer_id)
        for (layer, v_layer) in v_by_layer:
            for ax in axes:
                ax.axvline(v_layer.index[0], color='k', linestyle='--', linewidth=0.2)

    #Loop through each column and plot it in the right place
    for col in columns:
        for ix, source in enumerate(sources_present):
            color = plt.cm.Vega10(ix)
            if source in col:
                if 'Shutter' in col:
                    axes[ix*3].plot(dat[col], color=color, label=target_sources[source]+' Shutter')
                elif 'Plasma' in col:
                    axes[ix*3+1].plot(dat[col], color=color, label=target_sources[source]+' Plasma')
                else:
                    if ' V ' in col:
                        label = ' V'
                        linestyle='--'
                    elif ' mA ' in col:
                        label = ' mA'
                        linestyle='-.'
                    elif ' W ' in col:
                        label= ' W'
                        linestyle='-'
                    elif ' DC Bias' in col:
                        label= ' DC Bias'
                        linestyle = '--'
                    axes[ix*3+2].plot(dat[col], color=color, linestyle=linestyle, label=target_sources[source]+label)
                break

        if 'Gas' in col:
            axes[-4].semilogy(dat[col], color=plt.cm.Vega10(list(sorted(gas_sources.keys())).index(col)+7), label=gas_sources[col])
        elif col == 'C.M. Press.':
            axes[-3].plot(dat[col], color='k', alpha=0.7, label=col)
        elif col == 'Sub. Temp.':
            axes[-2].plot(dat[col], color='k', alpha=0.7, label=col)
        elif col == 'Sub. Rot.':
            axes[-1].plot(dat[col], color='k', alpha=0.7, label=col)

    for ax in axes:
        if len(ax.get_lines()) > 0:
            ax.legend(loc='center left', prop={'size':20}, frameon=False)

    fig.tight_layout()
    return fig
