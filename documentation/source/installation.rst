Installation
============

PySCeSToolbox is compatible with macOS, Linux, and Windows. Operating
system-specific instructions are discussed in the sections below. We have made
special
effort to provide as detailed instructions as possible, assuming a
clean installation of each operating system prior to installation of
PySCeSToolbox, and relatively limited knowledge of Python. If further
assistance is required, please contact the developers.

Abbreviated requirements
------------------------

PySCeSToolbox has a number of requirements that must be met before
installation can take place. Fortunately most requirements, save for a few
exceptions (as discussed in the operating system-specific sections), will be
taken care of automatically during installation. An abbreviated list of
requirements follows:

- A Python 3.x installation (Python 3.6 or higher is recommended)
- The full SciPy Stack (see http://scipy.org/install.html).
- PySCeS (see http://pysces.sourceforge.net)
- Maxima (see http://maxima.sourceforge.net)
- Jupyter Notebook (jupyter-core version in the 4.x.x series)


Windows
-------

Windows requires the manual installation of **Python 3.x**,
**PySCeS** and **Maxima**. Installation was tested on Windows 10.

Python
~~~~~~

For Windows users (especially those unfamiliar with Python) we recommend using 
the Anaconda Python distribution 
(https://www.anaconda.com/products/individual#Downloads). This is a low fuss 
solution that will install Python on you system *together with many of the 
packages necessary for running PySCeSToolbox*. Download the appropriate **Python 
3.7** package from the download page (most probably the 64bit edition) and 
follow the instructions of the installation wizard.

If you prefer more fine-grained control it is also possible to install Python 
from Python.org (https://www.python.org/downloads/windows/); be sure to install 
``pip`` as well when prompted by the installer, and add the Python directories 
to the system PATH.

PySCeS
~~~~~~

If you installed Anaconda, PySCeS can be installed by opening a command prompt 
in an Anaconda environment (Python 3.6 or 3.7) and executing the command:

.. code:: bash

    conda install -c sbmlteam -c pysces pysces

If you installed Python from Python.org directly, open a Windows Command 
Prompt, verify that the Python paths are set up correctly by checking the 
``pip`` version and install PySCeS by executing:

.. code:: bash

    pip -V
    pip install pysces
    
Currently Python versions 3.6-3.8 are supported with a pip install.

Maxima
~~~~~~

Maxima is necessary for generating control coefficient expressions using SymCA.
The latest version of Maxima can be downloaded and installed from the Windows
download page at http://maxima.sourceforge.net/download.html.

Windows might also require the path to ``maxima.bat`` to be defined in the
``psctb_config.ini`` file, found at ``C:\Pysces\psctb_config.ini``
by default.

.. note:: As of PySCeS version 0.9.8 the default location of configuration and 
    model files moved from ``C:\Pysces`` to ``%USERPROFILE%\Pysces``, i.e. 
    typically ``C:\Users\<username>\Pysces``, to bring the Windows installation 
    more in line with the macOS and Linux installations. Refer to the 
    `PySCeS 0.9.8 release notes 
    <https://github.com/PySCeS/pysces/releases/tag/0.9.8>`_ 
    for more information.
    
The default path included in ``psctb_config.ini`` is set as 
``C:\maxima?\bin\maxima.bat``, where the question marks are 
wildcards (since the specific path will depend on the version of Maxima). If 
Maxima has been installed to a user specified directory, the correct path to the
``maxima.bat`` file must be specified here.

PySCeSToolbox
~~~~~~~~~~~~~

Now you are ready to install PySCeSToolbox. If you are using Anaconda, open 
up the Anaconda Command Prompt (Start --> Anaconda Command Prompt), else 
open up the Windows Command Prompt if you installed PySCeS with ``pip``. In the 
command prompt, type in and execute the command:

.. code:: bash

    pip install pyscestoolbox

This will automatically download both PySCeSToolbox
and any outstanding requirements.

Enabling widgets
~~~~~~~~~~~~~~~~

If you are running the Jupyter notebook for the first time, or if you have not
yet enabled the notebook widgets you may need to run the following command:

.. code:: bash

    jupyter nbextension enable --py --sys-prefix widgetsnbextension

We also recommend running the following two commands to enable the
`ModelGraph <basic_usage.html#graphic-representation-of-metabolic-networks>`_
functionality of PySCeSToolbox. Rerunning this command may be necessary when
updating/reinstalling PySCeSToolbox.

.. code:: bash

    jupyter nbextension install --py --user d3networkx_psctb
    jupyter nbextension enable --py --user d3networkx_psctb


macOS (Mac OS X)
----------------


macOS requires the manual installation of **PySCeS** and **Maxima**. While OS X 
comes pre-installed with Python 2.7, **Python 3.x** is needed and we recommend 
installing a Python distribution such as Anaconda as it will take care of many 
of the SciPy stack requirements. Installation was tested on macOS High Sierra.

Python
~~~~~~
One of the easiest ways to get Python on your system is to install the
Anaconda Python distribution 
(https://www.anaconda.com/products/individual#Downloads).
Download either of the Python 3.7 installers for macOS from the download page 
and follow the provided instructions.

If you prefer more fine-grained control, there are other options such as 
installing directly from Python.org 
(https://www.python.org/downloads/mac-osx/), or installing
`Homebrew <https://docs.brew.sh/Installation>`_ and then installing Python 3.7 
with Homebrew. **These are advanced options for experienced users, and if you 
are starting out, we recommend Anaconda!**


PySCeS
~~~~~~

Binary packages are available for Anaconda, and binary wheels are available for 
direct installation with ``pip``. Depending on your Python installation (see 
above), the process is similar to the Windows install.

For Anaconda:

.. code:: bash

    conda install -c sbmlteam -c pysces pysces

For a ``pip`` based install (Python versions 3.6-3.8 are supported):
    
.. code:: bash

    pip install pysces

Maxima
~~~~~~

Maxima is necessary for generating control coefficient expressions using SymCA.
The latest version of Maxima can be downloaded and installed from the MacOS
download page at http://maxima.sourceforge.net/download.html. We
recommend the VTK version of Maxima.

After downloading and installing the Maxima dmg, the following lines must be
added to your ``.bash_profile`` file:

.. code:: bash

    export M_PREFIX=/Applications/Maxima.app/Contents/Resources/opt
    export PYTHONPATH=${M_PREFIX}/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/:$PYTHONPATH
    export MANPATH=${M_PREFIX}/share/man:$MANPATH
    export PATH=${M_PREFIX}/bin:$PATH
    alias maxima=rmaxima


PySCeSToolbox
~~~~~~~~~~~~~

Now you are ready to install PySCeSToolbox. If you are using Anaconda, open 
up a terminal in the Anaconda environment where PySCeS is installed. For 
``pip`` based installations, just open up a Terminal. Execute the command:

.. code:: bash

    pip install pyscestoolbox

This will automatically download both PySCeSToolbox and any outstanding 
requirements.

.. note:: You may encounter an error during the installation of PySCeSToolbox
          relating to the removal of temporary files on OS X or macOS. This does
          not impact on the functioning of PySCeSToolbox at all, and we mean
          to address this bug in the future.

Enabling widgets
~~~~~~~~~~~~~~~~

If you are running the Jupyter notebook for the first time, or if you have not
yet enabled the notebook widgets you may need to run the following command:

.. code:: bash

    jupyter nbextension enable --py --sys-prefix widgetsnbextension

We also recommend running the following two commands to enable the
`ModelGraph <basic_usage.html#graphic-representation-of-metabolic-networks>`_
functionality of PySCeSToolbox. Rerunning this command may be necessary when
updating/reinstalling PySCeSToolbox.

.. code:: bash

    jupyter nbextension install --py --user d3networkx_psctb
    jupyter nbextension enable --py --user d3networkx_psctb

Linux
-----

Linux requires the manual installation **Maxima** and **PySCeS**.
Most Linux systems come pre-installed with a version of **Python 3.x** or it 
is available from the distribution repositories. However, a
Python distribution such as Anaconda may be used instead. Installation
was tested on Ubuntu 18.04.

Python
~~~~~~

We assume that your system comes with Python 3.x (versions 3.6-3.8 are 
recommended) and with ``pip`` (necessary for
installing Python packages that are not available in your OS's repositories).
In case ``pip`` is not yet installed, it may be installed from your OS's 
repositories or by following the instructions found at 
https://pip.pypa.io/en/stable/installing/.

If you prefer Anaconda, Linux installers are available 
`here <https://www.anaconda.com/products/individual#Downloads>`_.

PySCeS
~~~~~~

Binary packages are available for Anaconda, and binary wheels are available for 
direct installation with ``pip``. Depending on your Python installation (see 
above), the process is similar to the Windows and macOS installs.

For Anaconda:

.. code:: bash

    conda install -c sbmlteam -c pysces pysces

For a ``pip`` based install (Python versions 3.6-3.8 are supported):
    
.. code:: bash

    pip install pysces

Maxima
~~~~~~

Maxima is necessary for generating control coefficient expressions using SymCA.
Maxima can be installed from your repositories, if available, otherwise the
latest packages can be downloaded from the Linux link at
http://maxima.sourceforge.net/download.html.

PySCeSToolbox
~~~~~~~~~~~~~

Now you are ready to install PySCeSToolbox. Open a terminal in the
environment where you installed PySCeS (i.e. Anaconda environment or the native 
Python environment of your OS), and simply type in and execute the command:

.. code:: bash

    pip install pyscestoolbox


Enabling widgets
~~~~~~~~~~~~~~~~

If you are running the Jupyter notebook for the first time, or if you have not
yet enabled the notebook widgets you may need to run the following command:

.. code:: bash

    jupyter nbextension enable --py --sys-prefix widgetsnbextension

We also recommend running the following two commands to enable the
`ModelGraph <basic_usage.html#graphic-representation-of-metabolic-networks>`_
functionality of PySCeSToolbox. Rerunning this command may be necessary when
updating/reinstalling PySCeSToolbox.

.. code:: bash

    jupyter nbextension install --py --user d3networkx_psctb
    jupyter nbextension enable --py --user d3networkx_psctb
