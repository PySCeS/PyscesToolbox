from setuptools import setup, find_packages
from os import path
try:
  from jupyterpip import cmdclass
except:
  import pip
  import importlib
  pip.main(['install', 'jupyter-pip'])
  cmdclass = importlib.import_module('jupyterpip').cmdclass

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

packages = find_packages()

setup(
    name='PyscesToolbox',
    version='0.8.8',
    packages=packages,
    url='https://github.com/PySCeS/PyscesToolbox',
    download_url='http://github.com/PySCeS/PyscesToolbox/archive/0.8.8.tar.gz',
    license='BSD-3-Clause',
    author='Carl Christensen',
    author_email='carldc@sun.ac.za',
    description='A set of metabolic model analysis tools for PySCeS.',
    long_description=long_description,
    install_requires=['IPython>=4.0.0',
                      'numpy',
                      'sympy',
                      'pysces',
                      'matplotlib',
                      'numpydoc',
                      'jupyter-pip',
                      'networkx',
                      'jupyter',
                      'pandas'
                      ],
    package_data={'d3networkx_psctb': ['widget.js'],},
    keywords=['metabolism','metabolic control analysis','modelling'],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Intended Audience :: Science/Research',
                 'Topic :: Scientific/Engineering :: Bio-Informatics',
                 'License :: OSI Approved :: BSD License',
                 'Programming Language :: Python :: 2.7'],
    cmdclass=cmdclass('d3networkx_psctb'),
)