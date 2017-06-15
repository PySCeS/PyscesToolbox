from setuptools import setup, find_packages
try:
  from jupyterpip import cmdclass
except:
  import pip
  import importlib
  pip.main(['install', 'jupyter-pip'])
  cmdclass = importlib.import_module('jupyterpip').cmdclass

packages = find_packages()

setup(
    name='PyscesToolbox',
    version='0.8.4.2',
    packages=packages,
    url='https://github.com/PySCeS/PyscesToolbox',
    license='',
    author='Carl Christensen',
    author_email='carldc@sun.ac.za',
    description='A set of metabolic model analysis tools for PySCeS.',
    install_requires=['IPython>=4.0.0',
                      'numpy',
                      'sympy',
                      'pysces',
                      'matplotlib',
                      'numpydoc',
                      'jupyter-pip',
                      'networkx',
                      'jupyter',
                      'ipywidgets'],
    include_pakage_data=True,
    package_data={'': ['default_config.ini']},
    cmdclass=cmdclass('d3networkx_psctb'),
)