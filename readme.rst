AJA Tools (alpha realease)
==========================
Some tools to help with loading and parsing AJA sputter tool logfiles.

Description of files
--------------------
  * recipe_parser.py : Contains code for figuring out what processes were called
    during a specific job, and aligning logfiles with the right job.
  * logfile_tools.py : Tools for loading, plotting, and filtering out data from
    logfiles based on specific recipes.
  * Example1.ipynb : Jupyter notebook with a short tutorial for using some of
    the functions contained in recipe_parser.py.
  * Example2.ipynb : Jupyter notebook with a short tutorial for using the
    plotting code in logfile_tools.py to do a timeline analysis of a specific
    recipe step.

Installation
------------
Plans are in progress to make these scripts into a proper package hosted on pip.
For now, you can just do something like::

  import sys
  sys.path.append('/path/to/parent/directory')

  import AJA_tools.recipe_parser as rp
  import AJA_tools.logfile_tools as lt

Reuse and citation
------------------
This code is released under the MIT license. Please cite this github repository
if you use the code in a publication or project.
