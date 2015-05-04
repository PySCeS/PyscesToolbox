from __future__ import print_function

# try:
from setuptools import setup, find_packages
# except ImportError:
#    from distutils.core import setup



try:
    from ipythonpip import cmdclass
except:
    import pip, importlib
    pip.main(['install', 'ipython-pip']); cmdclass = importlib.import_module('ipythonpip').cmdclass

packages = find_packages()

config = {
    'description': 'A library full of useful functions to use with PySCeS',
    'author': 'Carl Christensen',
    'url': 'TBA.',
    'download_url': 'TBA',
    'author_email': 'exe0cdc@gmail.com',
    'version': '0.1',
    'install_requires': ['sympy', 'numpy', 'pysces', 'ipython-pip'],
    'packages': packages,
    'include_package_data': True,
    'scripts': [],
    'name': 'PyscesToolbox',
    'cmdclass':cmdclass('d3networkx_psctb'),
}
setup(**config)
