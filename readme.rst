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
Plans are in progress to make these scripts into a proper package hosted on pip.
For now, you can just clone this repository into some directory and then do something like:

.. code:: python

  import sys
  sys.path.append('/path/to/parent/directory')

  import AJA_tools.logfile_tools as lt

Reuse and citation
------------------
This code is released under the MIT license. Please cite this github repository
if you use the code in a publication or project.
