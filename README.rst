|Documentation Status|

PySCeSToolbox
=============

This is a set of metabolic model analysis tools for PySCeS.

PySCeSToolbox currently provides tools for:

-  Generalised supply-demand analysis.
-  Symbolic metabolic control analysis and control pattern analysis.
-  Generating model schemas from metabolic models.
-  Distinguishing between thermodynamic and kinetic contributions
   towards reaction rate.
-  Interactive plotting

PySCeSToolbox was designed to be used within the Jupyter notebook, but
most of the core features should work in a normal Python script.

Documentation can be found at http://pyscestoolbox.readthedocs.org.
While all major tools have been documented, the documentation is still a
work in progress.

Contents of README
------------------

-  `Requirements <#requirements>`__
-  `Installation <#installation>`__
-  `Basic usage <#basic-usage>`__
-  `Important notices <#important-notices>`__
-  `Porting scripts to latest
   version <#porting-scripts-to-latest-version>`__

Requirements
------------

An abbreviated list of requirements is given below. Python dependencies
will be installed automatically when installing PySCeSToolbox via pip.
For detailed operating system specific instructions on installing the
requirements see the documentation at
`http://pyscestoolbox.readthedocs.io/ <http://pyscestoolbox.readthedocs.io>`__,

-  A Python 2.7 installation
-  The full SciPy stack (see http://scipy.org/install.html)
-  PySCeS (see http://pysces.sourceforge.net/download.html or install
   using ``pip install pysces``)
-  Maxima (see http://maxima.sourceforge.net/download.html)
-  Jupyter Notebook (version in the 4.x.x series)

**Notes:**

Required packages should automatically download and install when using
the commands specified under `Installation <#installation>`__ below.

Maxima is only a requirement for SymCA.

Installation
------------

The latest release of PySCeSToolbox can be installed from PyPi by
running the following commands in the terminal (or Windows equivalent):

.. code:: bash

    pip install pyscestoolbox

To enable widgets you may need to run the following commands:

.. code:: bash

    jupyter nbextension enable --py --sys-prefix widgetsnbextension
    jupyter nbextension install --py --user d3networkx_psctb
    jupyter nbextension enable --py --user d3networkx_psctb


The latest development version can be installed from GitHub with:

.. code:: bash

    pip install git+https://github.com/PySCeS/PySCeSToolbox.git

For the pre-2015-11-11 version:

.. code:: bash

    pip install git+https://github.com/exe0cdc/ipython-d3networkx.git
    pip install git+https://github.com/PySCeS/PySCeSToolbox.git@f63b5ab660f103105750159885608a5f48de1551

Basic usage
-----------

To start a PySCeSToolbox session in a Jupyter notebook:

1. Start up the Jupyter Notebook using the ``jupyter notebook`` command
   in the terminal
2. Create a new notebook by clicking the ``New`` button on the top right
   of the window and selecting ``Python 2``
3. Run the following three commands in the first cell:

.. code:: python

    %matplotlib inline
    import pysces
    import psctb

Model files must be placed in ``~/Pysces/psc/`` if using Linux or
``C:\Pysces\psc\`` for Windows.

Important notices
-----------------

For readers of "Tracing regulatory routes in metabolism using generalised supply-demand analysis" published in BMC Systems Biology on 03/12/2015:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use the IPython notebook file included as "Additional file 5" in the
paper, please install the **latest version** of PySCeSToolbox specified
under `Installation <#installation>`__.

The two PySCeS MDL model files included as "Addition file 1" and
"Addition file 2" are required to run the notebook. They should be
renamed to "Hoefnagel\_moiety\_ratio.psc" and "Curien.psc",
respectively. Further instructions are included within the notebook and
on this page.

Firefox users should download these files using a different browser or
switch to the new beta version of the BMC Systems Biology website.

Changes:
~~~~~~~~

Because this project is still in its infancy, future changes might break
older scripts. These types of changes will be kept to a minimum and will
be documented here.

Changes on 2017-02-09: Full cross compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On 2017-02-09 Symca support via Maxima has been added to PySCeSToolbox
on Windows. A configuration file located at
``C:\Pysces\psctb_config.ini`` can be used to specify the path to
``maxima.bat``. By default, however, PySCeSToolbox should detect the
path to ``maxima.bat`` automatically if it has been installed using the
default options. This change should have no impact on any older scripts
save for making them platform independent.

Changes on 2017-02-02: Dropped IPython Notebook 3.x.x support
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As of 2017-02-02 IPython Notebook 3.x.x support has been dropped in
favour of Jupyter 4.x.x. This should not affect the functioning of
scripts (save for those based on versions before that of 2015-11-11).
PySCeSToolbox will however require the Jupyter Notebook as of this date
in order to use its interactive features. Note that ``ipywidgets`` (an
automatically installed requirement for the Jupyter notebook) needs you
to run the command
"``jupyter nbextension enable --py --sys-prefix widgetsnbextension``"
before enabling widgets in the notebook.

Changes on 2015-11-11: API changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Major changes were made on 2015-11-11 that might break scripts coded
before this date. These changes are related to the naming of methods and
fields. For scripts older than 2015-11-11 we recommend using an older
version of PySCeSToolbox (noted under `Installation <#installation>`__).
Manual porting of scripts is also possible with details of necessary
changes outlined under `Porting scripts to latest
version <#porting-scripts-to-latest-version>`__.

Porting scripts to latest version
---------------------------------

Method and variable names and the analysis objects they belong to that
were changed on 2015-11-11 are documented in the tables below. To port
any older script simply change the old name of any method/variable to
the new name.

**RateChar**

+-------------------+-----------------+
| Old name          | New Name        |
+===================+=================+
| save              | save\_session   |
+-------------------+-----------------+
| load              | load\_session   |
+-------------------+-----------------+
| plot\_data        | scan\_results   |
+-------------------+-----------------+
| mca\_data         | mca\_results    |
+-------------------+-----------------+
| plot\_decompose   | do\_mca\_scan   |
+-------------------+-----------------+

**Thermokin**

+-------------------+---------------------+
| Old name          | New Name            |
+===================+=====================+
| reactions         | reaction\_results   |
+-------------------+---------------------+
| mca\_data         | ec\_results         |
+-------------------+---------------------+
| reaction name\*   | J\_reaction name    |
+-------------------+---------------------+
| par\_scan         | do\_par\_scan       |
+-------------------+---------------------+

\*reaction name refers to the naming of a reaction as it is defined in
the model file.

**Symca**

+-------------+------------------+
| Old name    | New Name         |
+=============+==================+
| CC          | cc\_results      |
+-------------+------------------+
| CCn\*       | cc\_results\_n   |
+-------------+------------------+
| save        | save\_session    |
+-------------+------------------+
| load        | load\_session    |
+-------------+------------------+
| par\_scan   | do\_par\_scan    |
+-------------+------------------+

\*CCn refers to any of the additional result dictionaries that are
created when an internal metabolite is fixed and the ``internal_fixed``
paramenter of ``do_symca`` is set to ``True``

**Data2D**

+--------------+-----------------+
| Old name     | New Name        |
+==============+=================+
| plot\_data   | scan\_results   |
+--------------+-----------------+
| save\_data   | save\_results   |
+--------------+-----------------+

.. |Documentation Status| image:: https://readthedocs.org/projects/pyscestoolbox/badge/?version=latest
   :target: http://pyscestoolbox.readthedocs.org/en/latest/?badge=latest
