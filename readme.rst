AJA Tools (alpha realease)
==========================
Some tools to help with loading and parsing AJA sputter tool logfiles.

Example
-------
Probably the thing you will want the most is just to plot a logfile:

.. code:: python

  import AJA_tools.logfile_tools as lt
  fig = lt.plot_log('/path/to/logfile.dlg', 'metals')
  fig.save_fig('/path/to/figure.png', bbox_to_inches='tight')

Pretty easy, right?! At the moment there is only support for the ANL metals sputter tool.


Installation
------------
After pulling in the code from github, open a terminal and run the following:

.. code:: bash

  pip install -e /path/to/AJA_tools

That ensures that when you pull down the latest changes, or switch to a
different branch you'll always be using the code in the repo directly.

Reuse and citation
------------------
This code is released under the MIT license. Please cite this github repository
if you use the code in a publication or project.
