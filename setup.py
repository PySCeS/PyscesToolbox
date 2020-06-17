from setuptools import setup, find_packages
from os import path

try:
    from jupyterpip import cmdclass
except:
    import sys
    import subprocess
    import importlib
    subprocess.call([sys.executable, '-m', 'pip', 'install', 'jupyter-pip'])
    cmdclass = importlib.import_module('jupyterpip').cmdclass

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

with open(path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()
  
with open(path.join(here, 'psctb', 'version.py')) as f:
    exec(f.read())

dlurl = 'http://github.com/PySCeS/PyscesToolbox/archive/' + __version__ + '.tar.gz'

packages = find_packages()

setup(
    name='PyscesToolbox',
    version=__version__,
    packages=packages,
    url='https://github.com/PySCeS/PyscesToolbox',
    download_url=dlurl,
    license='BSD-3-Clause',
    author='Carl Christensen and Johann Rohwer',
    author_email='exe0cdc@gmail.com, j.m.rohwer@gmail.com',
    description='A set of metabolic model analysis tools for PySCeS.',
    long_description=long_description,
    install_requires=requirements,
    package_data={'d3networkx_psctb': ['widget.js'],
                  'psctb': ['docs/*']},
    keywords=['metabolism','metabolic control analysis','modelling'],
    classifiers=['Development Status :: 5 - Production/Stable',
                             'Intended Audience :: Science/Research',
                             'Topic :: Scientific/Engineering :: Bio-Informatics',
                             'License :: OSI Approved :: BSD License',
                             'Programming Language :: Python :: 3'],
    cmdclass=cmdclass('d3networkx_psctb'),
)
