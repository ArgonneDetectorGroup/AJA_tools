import glob

def get_recipe(job_file_path, recipe_folder_path):
    """Read in an AJA job file and return a list of AJA recipe steps.

    Parameters
    ----------
    job_file_path : string
        Path to the job file. Usually has extension '.ajp'

    recipe_folder_path : string
        Path to the folder containing all the extant AJA recipe step files.

    Returns
    -------
    output_dict : dict
        Output dictionary containing the following keys:

            * 'recipe' : List of recipe steps called by job
            * 'raw_recipe' : List of tuples containing (index, recipe step).
              This includes all the binary separators between recipe steps.
            * 'raw_job' : The raw output of the AJA job file."""

    #Do a little checking to make sure path was entered right
    if recipe_folder_path[-1] != '/':
        recipe_folder_path += '/'

    #Grab a list of recipe files from the recipe folder
    recipe_files = glob.glob(recipe_folder_path + '*')

    #Initialize empty list of recipes
    recipes =[]

    #Step through the list and grab the names of each file, but not the extension
    for recipe_file in recipe_files:
        if '.rcp' in recipe_file:
            recipes.append(recipe_file.split('.rcp')[0].split('/')[-1])

    #Open the job file up and read it in
    with open(job_file_path, 'r') as f:
        raw_job = f.read()

    #Initalize a few more empty lists
    raw_recipe = []
    parsed_recipe = []

    #Step through all the recipes and check if they are called in the raw job contents
    #Output is a list of tuples (index where recipe appears, recipe)
    for r in recipes:
        if r in raw_job:
            start_ix = 0
            while raw_job.find(r, start_ix) > -1:
                match_ix = raw_job.find(r, start_ix)
                start_ix = match_ix+1

                #This little block just checks to make sure the longest
                #matching recipe is the one that gets used
                if (len(raw_recipe) > 0):
                    if (match_ix) == raw_recipe[-1][0]:
                        raw_recipe[-1] = (match_ix, r)
                    else:
                        raw_recipe.append((match_ix, r))
                else:
                    raw_recipe.append((match_ix, r))

    #Sort the list by the index so all the recipes are now listed in order
    raw_recipe.sort(key=lambda x: x[0])

    #Make a copy of the list of recipes, this is what we care about
    raw_recipe_no_junk = raw_recipe[:]

    #Step through the list again, gather up anything that wasn't
    #recognized as a recipe, and insert it in the proper place
    start_ix = 0
    for rix, r in raw_recipe:
        if start_ix < rix:
            raw_recipe.append((start_ix, raw_job[start_ix:rix]))
            start_ix = rix+len(r)
        else:
            start_ix += 1

    raw_recipe.sort(key=lambda x: x[0])

    #Strip out the index numbers and return just the final list
    parsed_recipe = list(zip(*raw_recipe_no_junk)[1])



    output_dict = {'recipe' : parsed_recipe,
                   'raw_recipe' : raw_recipe,
                   'raw_job' : raw_job}

    return output_dict
