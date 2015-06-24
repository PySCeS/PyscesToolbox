#PyscesToolbox


This is a set of metabolic model analysis tools using PySCeS as a basis.

PyscesToolbox currently provides tools for:

- Generalised supply-demand analysis.
- Symbolic metabolic control analysis and control pattern analysis.
- Generating model schemas from metabolic models.
- Distinguishing
 between thermodynamic and kinetic contributions towards reaction rate.
- Interactive plotting

PyscesToolbox was designed to be used within the IPython notebook, but most of the core features should work in a normal Python script.

This project is a work in progress and most features still require proper documentation.

##Requirements

- A Python 2.7 installation
- The full Scipy stack (see [http://scipy.org/install.html](http://scipy.org/install.html))
- PySCeS (see [http://pysces.sourceforge.net/download.html](http://pysces.sourceforge.net/download.html) or install using ``pip install pysces``)
- A Linux system

Notes:

Any versions of the scipy stack components released in or after 2014 should work, the only hard requirement is an IPython version in the 3.x.x series as PyscesToolbox relies quite heavily on the features of the IPython notebook and its widget system.

A  Linux system might not be required, but the software has thus far only been tested on Linux (Ubuntu 14.04)

##Installation

PyscesToolbox can be installed from github using pip with the following command:

'''
pip install git+git://github.com/PySCeS/pysces.git
'''



