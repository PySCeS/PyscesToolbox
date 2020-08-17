Installation
============

PySCeSToolbox is compatible with macOS, Linux, and Windows, and can be 
installed either with ``conda`` in an Anaconda environment, 
or with ``pip`` in an existing Python environment. We have made special effort 
to provide as detailed instructions as possible, assuming a clean installation 
of each operating system prior to installation of PySCeSToolbox, and relatively 
limited knowledge of Python. If further assistance is required, please contact 
the developers.

Below follow abbreviated requirements, installation instructions for 
``conda`` and ``pip``, as well as operating 
system-specific instructions for setting up Maxima. 

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



Installation on Anaconda
------------------------

For most users (especially those unfamiliar with Python) we recommend using
the Anaconda Python distribution
(https://www.anaconda.com/products/individual#Downloads).
This is a low fuss solution available for all three
operating systems that will install Python on you system *together with many of
the packages necessary for running PySCeSToolbox*. Download the appropriate
**Python 3.7** package from the download page (most probably the 64bit
edition) and follow the instructions of the installation wizard.

Virtual environments
~~~~~~~~~~~~~~~~~~~~

Virtual environments are a great way to keep package dependencies separate from
your system files. It is highly recommended to install PyscesToolbox into a separate
environment, which first must be created (here we create an environment
called ``pysces``). It is recommended to use a Python version >=3.6 (here we use
Python 3.7). After creation, activate the environment:

.. code:: bash

    (base) $ conda create -n pysces python=3.7
    (base) $ conda activate pysces

Then install PyscesToolbox:

.. code:: bash

    (pysces) $ conda install -c pysces -c sbmlteam pyscestoolbox

Be sure to specify the *pysces* and *sbmlteam* channels in the command line 
as above, otherwise some of the packages won't be found. The required Python 
dependencies will be installed automatically. For Maxima,
refer to the operating system-specific instructions below.

.. _enabling_widgets:

Enabling widgets
~~~~~~~~~~~~~~~~

If you are running the Jupyter notebook for the first time, or if you have not
yet enabled the notebook widgets you may need to run the following command:

.. code:: bash

    (pysces) $ jupyter nbextension enable --py --sys-prefix widgetsnbextension

We also recommend running the following two commands to enable the
`ModelGraph <basic_usage.html#graphic-representation-of-metabolic-networks>`_
functionality of PySCeSToolbox. Rerunning these commands may be necessary when
updating/reinstalling PySCeSToolbox.

.. code:: bash

    (pysces) $ jupyter nbextension install --py --user d3networkx_psctb
    (pysces) $ jupyter nbextension enable --py --user d3networkx_psctb


Alternative: direct ``pip``-based install
-----------------------------------------

First be sure to have Python 3 and ``pip`` installed.
`Pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_ is a useful Python
package management system.

On Debian and Ubuntu-like Linux systems these can be installed with the following
terminal commands:

.. code:: bash

    $ sudo apt install python3
    $ sudo apt install python3-pip
    
Other Linux distributions will also have Python 3 and ``pip`` available in 
their repositories.

On Windows, download Python from https://www.python.org/downloads/windows;
be sure to install ``pip`` as well when prompted by the installer, and add the
Python directories to the system PATH. You can verify that the Python paths are
set up correctly by checking the ``pip`` version in a Windows Command Prompt:

.. code:: bash

    > pip -V

On macOS you can install Python directly from
https://www.python.org/downloads/mac-osx, or by installing
`Homebrew <https://docs.brew.sh/Installation>`_ and then installing Python 3
with Homebrew. Both come with ``pip`` available.

.. note::

    While most Linux distributions come pre-installed with a version of Python
    3, the options for Windows and macOS detailed above are more advanced and
    for experienced users, who prefer fine-grained control. If you are
    starting out, we strongly recommend using Anaconda!

Virtual environments
~~~~~~~~~~~~~~~~~~~~

Again it is highly recommended to install PyscesToolbox
into a separate virtual environment.
There are several options for setting up your working
environment. We will use `virtualenvwrapper
<https://virtualenvwrapper.readthedocs.io/en/latest/index.html>`_,
which works
out of the box on Linux and macOS. On Windows, virtualenvwrapper can be used
under an `MSYS <http://www.mingw.org/wiki/MSYS>`_ environment in a native
Windows Python installation. Alternatively, you can use `virtualenvwrapper-win
<https://pypi.org/project/virtualenvwrapper-win/>`_. This will take care of
managing your virtual environments by maintaining a separate Python
*site-directory* for you.

Install virtualenvwrapper using ``pip``. On Linux and MacOS:

.. code:: bash

    $ sudo -H pip install virtualenv
    $ sudo -H pip install virtualenvwrapper

On Windows in a Python command prompt:

.. code:: bash

    > pip install virtualenv
    > pip install virtualenvwrapper-win

Make a new virtual environment for working with PyscesToolbox (e.g. ``pysces``), and
specify that it use Python 3 (we used Python 3.7):

.. code:: bash

    $ mkvirtualenv -p /path/to/your/python3.7 pysces

The new virtual environment will be activated automatically, and this will be
indicated in the shell prompt, e.g.:

.. code:: bash

    (pysces) $

If you are not yet familiar with virtual environments we recommend you survey
the basic commands (https://virtualenvwrapper.readthedocs.io/en/latest/) before
continuing.

The PyscesToolbox code and its dependencies can now be installed directly from PyPI
into your virtual environment using ``pip``.

.. code:: bash

    (pysces) $ pip install pyscestoolbox

As for the ``conda``-based install, the required Python dependencies will be
installed automatically. For Maxima,
refer to the operating system-specific instructions below.

Enabling widgets
~~~~~~~~~~~~~~~~

Refer to the :ref:`Anaconda-based install <enabling_widgets>`.

Maxima
-------

Maxima is necessary for generating control coefficient expressions using SymCA.
Below we provide operating-specific instructions for setting up Maxima.

Windows
~~~~~~~

The latest version of Maxima can be downloaded and installed from the Windows
download page at http://maxima.sourceforge.net/download.html.

Windows might also require the path to ``maxima.bat`` to be defined in the
``psctb_config.ini`` file, found at ``%USERPROFILE%\Pysces\psctb_config.ini``
by default, or in ``C:\Pysces`` for older PySCeS versions.

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

macOS (Mac OS X)
~~~~~~~~~~~~~~~~

The latest version of Maxima can be downloaded and installed from the MacOS
download page at http://maxima.sourceforge.net/download.html. We
recommend the VTK version of Maxima.

After downloading and installing the Maxima dmg, the following lines must be
added to your ``.bash_profile`` or ``.zshrc`` file (depending on which shell 
you use):

.. code:: bash

    export M_PREFIX=/Applications/Maxima.app/Contents/Resources/opt
    export PYTHONPATH=${M_PREFIX}/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/:$PYTHONPATH
    export MANPATH=${M_PREFIX}/share/man:$MANPATH
    export PATH=${M_PREFIX}/bin:$PATH
    alias maxima=rmaxima

Linux
~~~~~

Maxima can be installed from your repositories, if available, otherwise the
latest packages can be downloaded from the Linux link at
http://maxima.sourceforge.net/download.html.

