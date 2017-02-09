[![Documentation Status](https://readthedocs.org/projects/pyscestoolbox/badge/?version=latest)](http://pyscestoolbox.readthedocs.org/en/latest/?badge=latest)

# PyscesToolbox

This is a set of metabolic model analysis tools for PySCeS.

PyscesToolbox currently provides tools for:

- Generalised supply-demand analysis.
- Symbolic metabolic control analysis and control pattern analysis.
- Generating model schemas from metabolic models.
- Distinguishing between thermodynamic and kinetic contributions towards reaction rate.
- Interactive plotting

PyscesToolbox was designed to be used within the IPython notebook, but most of the core features should work in a normal Python script.

Documentation can be found at [http://pyscestoolbox.readthedocs.org](http://pyscestoolbox.readthedocs.org). While all major tools have been documented, the documentation is still a work in progress.


## IMPORTANT NOTICE

Because this project is still in its infancy, future changes might break older scripts. These types of changes will be kept to a minimum and will be documented here.

### Changes on 2017-02-09: Full cross compatibility
On 2017-02-09 Symca support via Maxima has been added to PySCeSToolbox on Windows. A configuration file located at `C:\Pysces\psctb_config.ini` can be used to specify the path to `maxima.bat`. By default, however, PySCeSToolbox should detect the path to `maxima.bat` automatically if it has been installed using the default options. This change should have no impact on any older scripts save for making them platform independent.

### Changes on 2017-02-02: Dropped IPython Notebook 3.x.x support
As of 2017-02-02 IPython Notebook 3.x.x support has been dropped in favour of Jupyter 4.x.x. This should not affect the functioning of scripts (save for those based on versions before that of 2015-11-11). PySCeSToolbox will however require the Jupyter Notebook as of this date in order to use its interactive features. Note that `ipywidgets` (an automatically installed requirement for the Jupyter notebook) needs you to run the command "`jupyter nbextension enable --py --sys-prefix widgetsnbextension`" before enabling widgets in the notebook.

### Changes on 2015-11-11: API changes
Major changes were made on 2015-11-11 that might break scripts coded before this date. These changes are related to the naming of methods and fields. For scripts older than 2015-11-11 we recommend using an older version of PySCeSToolbox (noted under **Installation**). Manual porting of scripts is also possible with details of necessary changes outlined under **Porting scripts to latest version**.


## Requirements

- Git (Windows users see [https://msysgit.github.io/](https://msysgit.github.io/))
- A Python 2.7 installation
- The full Scipy stack (see [http://scipy.org/install.html](http://scipy.org/install.html))
- PySCeS (see [http://pysces.sourceforge.net/download.html](http://pysces.sourceforge.net/download.html) or install using ``pip install pysces``)
- Networkx (see [https://networkx.github.io/](https://networkx.github.io/))
- Maxima (see [http://maxima.sourceforge.net/download.html](http://maxima.sourceforge.net/download.html))

**Notes:**

We recommend running PySCeSToolbox on Linux due to the ease of installing the Python environment, however it is compatible with Windows (see below).

Any versions of the SciPy stack components released in or after 2014 should work, the only hard requirement is a Jupyter Notebook version in the 4.x.x series (for versions later than 2017-02-02) as PyscesToolbox relies quite heavily on the features of the Jupyter Notebook and its widget system for interactive work.

Required packages should automatically download and install when using the commands specified under **Installation** below.

Maxima is only a requirement for SymCA.

**For readers of "Tracing regulatory routes in metabolism using generalised supply-demand analysis" published in BMC Systems Biology on 03/12/2015**:

To use the IPython notebook file included as "Additional file 5" in the paper, please install the **latest version** of PySCeSToolbox specified under **Installation**.

The two PySCeS MDL model files included as "Addition file 1" and "Addition file 2" are required to run the notebook. They should be renamed to "Hoefnagel_moiety_ratio.psc" and "Curien.psc", respectively. Further instructions are included within the notebook and on this page.

Firefox users should download these files using a different browser or switch to the new beta version of the BMC Systems Biology website.

**For Windows users:**

Git for Windows can be installed from the link specified under **Requirements** above. During the installation when prompted with **Adjust your PATH environment** be sure to select the option **Use Git from the Windows Command Prompt**.

We recommend the WinPython_2.7 32bit distribution ([http://winpython.sourceforge.net/](http://winpython.sourceforge.net/)). This portable scientific python distribution includes a variety of scientific packages out of the box and significantly streamlines the experience of working with Python on Windows. It can also coexist with other Python installations on a single system. Other alternatives include Anaconda, Enthought Canopy and Python(x,y).

Any existing notebooks should be placed in the ``notebooks`` subdirectory within your WinPython installation.

## Installation

PyscesToolbox can be installed from github using pip by using the following two commands in the terminal (for Linux) or in the WinPython Command Prompt (for Windows):

For the latest version:

```bash
pip install git+https://github.com/exe0cdc/ipython-d3networkx.git
pip install git+https://github.com/PySCeS/PyscesToolbox.git
```

For the pre-2015-11-11 version:

```bash
pip install git+https://github.com/exe0cdc/ipython-d3networkx.git
pip install git+https://github.com/PySCeS/PyscesToolbox.git@f63b5ab660f103105750159885608a5f48de1551
```

## Basic usage

To start a PySCeSToolbox session in a Jupyter notebook:

 1. Start up the Jupyter Notebook using the ``jupyter notebook`` command in the terminal
 2. Create a new notebook by clicking the ``New`` button on the top right of the window and selecting ``Python 2``
 3. Run the following three commands in the first cell:

```python
%matplotlib inline
import pysces
import psctb
```

Model files must be placed in `~/Pysces/psc/` if using Linux or `C:\Pysces\psc\` for Windows.

## Porting scripts to latest version

Method and variable names and the analysis objects they belong to that were changed on 2015-11-11 are documented in the tables below. To port any older script simply change the old name of any method/variable to the new name.

**RateChar**

|Old name       |New Name    |
|---------------|------------|
|save           |save_session|
|load           |load_session|
|plot_data      |scan_results|
|mca_data       |mca_results |
|plot_decompose |do_mca_scan |

**Thermokin**

|Old name       |New Name        |
|---------------|----------------|
|reactions      |reaction_results|
|mca_data       |ec_results      |
|reaction name* |J_reaction name |
|par_scan       |do_par_scan     |
*reaction name refers to the naming of a reaction as it is defined in the model file.*

**Symca**

|Old name       |New Name    |
|---------------|------------|
|CC             |cc_results  |
|CCn*           |cc_results_n|
|save           |save_session|
|load           |load_session|
|par_scan       |do_par_scan |
*CCn refers to any of the additional result dictionaries that are created when an internal metabolite is fixed and the `internal_fixed` paramenter of `do_symca` is set to `True`

**Data2D**

|Old name       |New Name    |
|---------------|------------|
|plot_data      |scan_results|
|save_data      |save_results|
