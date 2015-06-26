from __future__ import print_function

import setuptools

try:
    from jupyterpip import cmdclass
except:
    import pip, importlib

    pip.main(['install', 'jupyter-pip'])
    cmdclass = importlib.import_module('jupyterpip').cmdclass

packages = setuptools.find_packages()

config = {
    'description': 'A library full of useful functions to use with PySCeS',
    'author': 'Carl Christensen',
    'url': 'TBA.',
    'download_url': 'TBA',
    'author_email': 'exe0cdc@gmail.com',
    'version': '0.1',
    'install_requires': ['sympy', 'numpy', 'pysces', 'jupyter-pip', 'pip'],
    'packages': packages,
    'include_package_data': True,
    'scripts': [],
    'name': 'PyscesToolbox',
    'cmdclass': cmdclass('d3networkx_psctb'),
}
setuptools.setup(**config)
