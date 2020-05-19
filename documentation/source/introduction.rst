Introduction
============

PySCeSToolbox is a set of extensions to the original Python Simulator for
Cellular Systems. The goals of this software are **(1)** to provide metabolic
model analysis tools that are beyond the scope of PySCeS and **(2)** to provide
a streamlined framework for using these tools together.

Currently, PySCeSToolbox includes three main analysis tools:

#. SymCa for performing symbolic control analysis `[1] <references.html>`__.
#. RateChar for performing generalised supply demand analysis `[2,3] <references.html>`__.
#. ThermoKin for distinguishing between the thermodynamic and kinetic
   contributions towards reaction rates and enzyme elasticities  `[4,5] <references.html>`__.

In addition to these tools PySCeSToolbox provides functionality for displaying
interactive plots, tables of results, and typeset mathematical expressions and
symbols by making extensive use of the wonderful Jupyter (IPython) Notebook
platform. Therefore, in order to make the best use of its features we recommend
that users run PySCeSToolbox within the IPython Notebook environment.
Regardless of being designed for interactive work through the Notebook, the
core features are completely compatible with traditional python scripting.

We recommend that users unfamiliar with PySCeS refer to its
`documentation <http://pysces.sourceforge.net/docs/userguide.html>`_
before continuing here.


