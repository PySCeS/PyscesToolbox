
Installation
============

PySCeSToolbox is compatible with Mac OS X, Linux, and Windows. Operating
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

- A Python 2.7 installation
- The full SciPy Stack (see http://scipy.org/install.html).
- PySCeS (see http://pysces.sourceforge.net)
- Maxima (see http://maxima.sourceforge.net)
- Jupyter Notebook (version in the 4.x.x series)


Windows
-------

Windows requires the manual installation of **Python 2.7**,
**PySCeS** and **Maxima**. Installation was tested on Windows 8 and
10.

Python
~~~~~~

For Windows users (especially those unfamiliar with Python) we recommend using
the Anaconda Python distribution
(https://www.continuum.io/downloads#windows). This is a low fuss solution
that will install Python on you system *together with many of the packages
necessary for running PySCeSToolbox*. Download the appropriate **Python 2.7**
package from the download page (most probably the 64bit edition) and follow the
instructions of the installation wizard.

PySCeS
~~~~~~
After installing Anaconda, download and install the latest PySCeS binary
package from \break http://pysces.sourceforge.net/download.html. PySCeS can also
be built from source (for more details see the instructions given at the
provided URL).

Maxima
~~~~~~

Maxima is necessary for generating control coefficient expressions using SymCA.
The latest version of Maxima can be downloaded and installed from the Windows
download page at http://maxima.sourceforge.net/download.html.

Windows might also require the path to ``maxima.bat`` to be defined in the
``psctb_config.ini`` file (found at ``C:\Pysces\psctb_config.ini`` by default).
The default path included in ``psctb_config.ini`` is set as ``C:\Program
Files?\Maxima?\bin\maxima.bat``, where the question marks are wildcards
(since the specific path will depend on the version of Maxima). If Maxima has
been installed to a user specified directory, the correct path to the
``maxima.bat`` file must be specified here.

PySCeSToolbox
~~~~~~~~~~~~~

Now you are ready to install PySCeSToolbox. In the
Anaconda Command Prompt (Start --> Anaconda Command Prompt), simply
type in and execute the command:

.. code:: bash

    pip install pyscestoolbox

As previously mentioned, this will automatically download both PySCeSToolbox
and any outstanding requirements.

Enabling widgets
~~~~~~~~~~~~~~~~

If you are running the Jupyter notebook for the first time, or if you have not
yet enabled the notebook widgets you may need to run the following command:

.. code:: bash

    jupyter nbextension enable --py --sys-prefix widgetsnbextension

We also recommend running the following two commands to enable the
`ModelGraph <basic_usage.html#graphic-representation-of-metabolic-networks>`__
functionality of PySCeSToolbox. Rerunning this command may be necessary when
updating/reinstalling PySCeSToolbox.

.. code:: bash

    jupyter nbextension install --py --user d3networkx_psctb
    jupyter nbextension enable --py --user d3networkx_psctb


Mac OS X (MacOS)
----------------


Mac OS X requires the manual installation of **PySCeS** and **Maxima**. While
OS X comes pre-installed with **Python 2.7** we still recommend installing a
Python distribution such as Anaconda as it will take care of many of the SciPy
stack requirements. Installation was tested on MacOS Sierra.

Python
~~~~~~
One of the most simple ways to get Python on your system is to install the
Anaconda Python distribution (https://www.continuum.io/downloads#macos).
Download either of the Python 2.7 installers from the download page and
follow the provided instructions.

PySCeS
~~~~~~

Currently the only options for installing PySCeS on OS X are to either build it
from source (see http://pysces.sourceforge.net/download.html) or to
install it with pip via the command:

.. code:: bash

    pip install pysces

Both cases requires the **xcode** command line tools and the **gfortran compiler**
to be present on the system. The xcode command line tools can be
installed by running:

.. code:: bash

    sudo xcode-select --install

in the terminal and following the instructions given in the resulting
popup (the full xcode package is *not required*. Gfortran dmg's for your
particular version of OS X (or MacOS) can downloaded and installed from
http://gcc.gnu.org/wiki/GFortranBinaries.

Once the appropriate compilers are present the actual PySCeS install may be
skipped as PySCeS will be installed automatically when PySCeSToolbox is
installed.

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
    export PYTHONPATH=${M_PREFIX/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/:$PYTHONPATH
    export MANPATH=${M_PREFIX/share/man:$MANPATH
    export PATH=${M_PREFIX/bin:$PATH
    alias maxima=rmaxima


PySCeSToolbox
~~~~~~~~~~~~~

Now you are ready to install PySCeSToolbox. In the Terminal (or iTerm) simply
type in and execute the command:

.. code:: bash

    pip install pyscestoolbox

As previously mentioned, this will automatically download both
PySCeSToolbox and any outstanding requirements.

.. note:: You may encounter an error during the installation of PySCeSToolbox
          relating to the removal of temporary files on OS X or MacOS. This does
          not impact on the functioning of PySCeSToolbox at all, and we mean
          to address this bug in the future.

Enabling widgets
~~~~~~~~~~~~~~~~

If you are running the Jupyter notebook for the first time, or if you have not
yet enabled the notebook widgets you may need to run the following command:

.. code:: bash

    jupyter nbextension enable --py --sys-prefix widgetsnbextension

We also recommend running the following two commands to enable the
`ModelGraph <basic_usage.html#graphic-representation-of-metabolic-networks>`__
functionality of PySCeSToolbox. Rerunning this command may be necessary when
updating/reinstalling PySCeSToolbox.

.. code:: bash

    jupyter nbextension install --py --user d3networkx_psctb
    jupyter nbextension enable --py --user d3networkx_psctb

Linux
-----

Linux requires the manual installation **Maxima** and **PySCeS**.
Most Linux systems come pre-installed with **Python 2.7**, however a
Python distribution such as Anaconda may be used instead. Installation
was tested on Ubuntu 16.04.

Python
~~~~~~

We assume that your system comes with Python 2.7 and with pip (necessary for
installing Python packages that are not available in your OS's repositories).
Pip may be installed from your OS's repositories or by following the
instructions found at https://pip.pypa.io/en/stable/installing/.

PySCeS
~~~~~~

Currently the only options for installing PySCeS on Linux are to build it from
source (see http://pysces.sourceforge.net/download.html) or to install it
with the command:

.. code:: bash

    pip install pysces

Both cases require the gcc, g++, and gfortran compilers to be present on the
system. These compilers are most probably available from your OS's
repositories.

Once the appropriate compilers are present the actual PySCeS install may be
skipped as PySCeS will be installed automatically when PySCeSToolbox is
installed.

Maxima
~~~~~~

Maxima is necessary for generating control coefficient expressions using SymCA.
Maxima can be installed from your repositories, if available, otherwise the
latest packages can be downloaded from the Linux link at
http://maxima.sourceforge.net/download.html.

PySCeSToolbox
~~~~~~~~~~~~~

Now you are ready to install PySCeSToolbox. In the terminal simply
type in and execute the command:

.. code:: bash

    pip install pyscestoolbox


Enabling widgets
~~~~~~~~~~~~~~~~

If you are running the Jupyter notebook for the first time, or if you have not
yet enabled the notebook widgets you may need to run the following command:

.. code:: bash

    jupyter nbextension enable --py --sys-prefix widgetsnbextension

We also recommend running the following two commands to enable the
`ModelGraph <basic_usage.html#graphic-representation-of-metabolic-networks>`__
functionality of PySCeSToolbox. Rerunning this command may be necessary when
updating/reinstalling PySCeSToolbox.

.. code:: bash

    jupyter nbextension install --py --user d3networkx_psctb
    jupyter nbextension enable --py --user d3networkx_psctb