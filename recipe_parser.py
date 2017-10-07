import warnings
import glob
import os
import dateutil.parser as dp

class RecipeWarning(UserWarning):
    """Warnings related to recipes."""
    pass

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

def build_logs_dict(path, jobs):
    """Build up a list of lognames sorted by last created. Each element of the list is a dict with the jobname, recipe, path, and datetime."""
    logfiles = nested_glob(path, '.dlg')

    for logfile in logfiles:
        job_name = get_job(logfile)[0]
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
                warnings.warn('Job file may be corrupt, missing final recipe step: '+ job_name, RecipeWarning)
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
