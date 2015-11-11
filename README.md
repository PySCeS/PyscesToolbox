#PyscesToolbox

This is a set of metabolic model analysis tools for PySCeS.

PyscesToolbox currently provides tools for:

- Generalised supply-demand analysis.
- Symbolic metabolic control analysis and control pattern analysis.
- Generating model schemas from metabolic models.
- Distinguishing between thermodynamic and kinetic contributions towards reaction rate.
- Interactive plotting

PyscesToolbox was designed to be used within the IPython notebook, but most of the core features should work in a normal Python script.

This project is a work in progress and most features still require proper documentation.

##IMPORTANT NOTICE 

Because this project is still in its infancy, future changes might break older scripts. These types of changes will be kept to a minimum and will be documented here.

Major changes were made on 11/11/2015 that might break scripts coded before this date. These changes are related to the naming of methods and fields. For scripts older than 11/11/2015 we recommend using an older version of PySCeSToolbox (noted under **Installation**). Manual porting of scripts is also possible with details of necessary changes outlined under **Porting scripts to latest version**. 



##Requirements

- Git (Windows users see [https://msysgit.github.io/](https://msysgit.github.io/))
- A Python 2.7 installation
- The full Scipy stack (see [http://scipy.org/install.html](http://scipy.org/install.html))
- PySCeS (see [http://pysces.sourceforge.net/download.html](http://pysces.sourceforge.net/download.html) or install using ``pip install pysces``)
- Networkx (see [https://networkx.github.io/](https://networkx.github.io/))
- Maxima (see [http://maxima.sourceforge.net/download.html](http://maxima.sourceforge.net/download.html))

**Notes:**

We recommend running PySCeSToolbox on Linux due to the ease of installing the Python environment, however it is compatible with Windows (see below). 

Any versions of the scipy stack components released in or after 2014 should work, the only hard requirement is an IPython version in the 3.x.x series as PyscesToolbox relies quite heavily on the features of the IPython notebook and its widget system.

Required packages should automatically download and install when using the commands specified under **Installation** below.

Maxima is only a requirement for SymCA. Currently this functionality is not supported on Windows, but will be included in the near future.

**For Windows users:**

Git for Windows can be installed from the link specified under **Requirements** above. During the installation when prompted with **Adjust your PATH environment** be sure to select the option **Use Git from the Windows Command Prompt**. 

We recommend the WinPython_2.7 32bit distribution ([http://winpython.sourceforge.net/](http://winpython.sourceforge.net/)). This portable scientific python distribution includes a variety of scientific packages out of the box and significantly streamlines the experience of working with Python on Windows. It can also coexist with other Python installations on a single system. Other alternatives include Anaconda, Enthought Canopy and Python(x,y).

Any existing notebooks should be placed in the ``notebooks`` subdirectory within your WinPython installation. 

##Installation

PyscesToolbox can be installed from github using pip by using the following two commands in the terminal (for Linux) or in the WinPython Command Prompt (for Windows):

For the pre-11/11/2015 version:

```bash
pip install git+https://github.com/exe0cdc/ipython-d3networkx.git
pip install git+https://github.com/PySCeS/PyscesToolbox.git@f63b5ab660f103105750159885608a5f48de1551
```


For the latest version:

```bash
pip install git+https://github.com/exe0cdc/ipython-d3networkx.git
pip install git+https://github.com/PySCeS/PyscesToolbox.git
```

##Basic usage

To start a PySCeSToolbox session in a IPython notebook:

 1. Start up the IPython Notebook using the ``ipython notebook`` command in the terminal on Linux or by opening "IPython Notebook.exe" on Windows 
 2. Create a new notebook by clicking the ``New`` button on the top right of the window and selecting ``Python 2``
 3. Run the following three commands in the first cell:

```python
%matplotlib inline
import pysces
import psctb
```

##Porting scripts to latest version

Method and variable names and the analysis objects they belong to that were changed on 11/11/2015 are documented in the tables below. To port any older script simply change the old name of any method/variable to the new name.

**RateChar**

|Old name       |New Name    |
|---------------|------------|
|save           |save_session|
|load           |load_session|
|plot_data      |scan_results|
|mca_data       |mca_results |
|plot_decompose |mca_results |

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



