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

##Requirements

- A Python 2.7 installation
- The full Scipy stack (see [http://scipy.org/install.html](http://scipy.org/install.html))
- PySCeS (see [http://pysces.sourceforge.net/download.html](http://pysces.sourceforge.net/download.html) or install using ``pip install pysces``)
- Networkx (see [https://networkx.github.io/](https://networkx.github.io/))
- Maxima (see [http://maxima.sourceforge.net/download.html](http://maxima.sourceforge.net/download.html))

**Notes:**

Any versions of the scipy stack components released in or after 2014 should work, the only hard requirement is an IPython version in the 3.x.x series as PyscesToolbox relies quite heavily on the features of the IPython notebook and its widget system.

Required packages should automatically download and install when using the commands specified under **Installation** below.

Maxima is only a requirement for SymCA. Currently this functionality is not supported on Windows, but will be included in the near future.

**For Windows users:**

We recommend the WinPython_2.7 32bit distribution ([http://winpython.sourceforge.net/](http://winpython.sourceforge.net/)). This portable scientific python distribution includes a variety of scientific packages out of the box and significantly streamlines the experience of working with Python on Windows. Other alternatives include Anaconda, Enthought Canopy and Python(x,y).

##Installation

PyscesToolbox can be installed from github using pip with the following two commands:

```bash
pip install git+https://github.com/exe0cdc/ipython-d3networkx.git
pip install git+https://github.com/PySCeS/PyscesToolbox.git
```

##Basic usage

To start a PySCeSToolbox session in a IPython notebook start up a notebook (using the ``ipython notebook`` command) and run the following commands:

```python
import pysces
import psctb
```






