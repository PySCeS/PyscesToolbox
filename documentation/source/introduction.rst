Introduction
============

PySCeSToolbox is a set of extensions to the original Python Simulator for
Cellular Systems (PySCeS) `[1] <references.html>`_. The goals of this software 
are **(1)** to provide metabolic
model analysis tools that are beyond the scope of PySCeS and **(2)** to provide
a streamlined framework for using these tools together. The reader is referred 
to the *Bioinformatics* paper `[2] <references.html>`_ for further details.

Currently, PySCeSToolbox includes three main analysis tools:

#. SymCa for performing symbolic control analysis `[3,4] <references.html>`_.
#. RateChar for performing generalised supply demand analysis 
   `[5,6] <references.html>`_.
#. ThermoKin for distinguishing between the thermodynamic and kinetic
   contributions towards reaction rates and enzyme elasticities  
   `[7,8] <references.html>`_.

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


