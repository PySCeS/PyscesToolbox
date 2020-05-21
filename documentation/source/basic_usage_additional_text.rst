
Starting a PySCeSToolbox session
--------------------------------

To start a PySCeSToolbox session in a Jupyter notebook:

1. Open a terminal in the environment where you installed PyscesToolbox (i.e. 
   Anaconda environment or other Python environment)
2. Start up the Jupyter Notebook using the ``jupyter notebook`` command
   in the terminal
3. Create a new notebook by clicking the ``New`` button on the top right
   of the window and selecting ``Python 3``
4. Run the following three commands in the first cell:

.. code:: python

    import pysces
    import psctb
    %matplotlib inline

Downloading interactive Jupyter notebooks
-----------------------------------------

To facilitate learning of this software, a set of interactive Jupyter notebooks 
are provided that mirror the pages for Basic Usage (this page), 
`RateChar <RateChar.html>`_, `Symca <Symca.html>`_  and 
`Thermokin <Thermokin.html>`_ found in 
this documentation. They can be downloaded from 
`Included Files <included_files.html>`_. The
`models and associated files <included_files.html#models>`_ should be saved in 
the ``~/Pysces/psc`` folder, while the 
`example notebooks <included_files.html#example-notebooks>`_ can go anywhere.
