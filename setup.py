from __future__ import print_function

import setuptools

packages = setuptools.find_packages()

config = {
    'description': 'A library full of useful functions to use with PySCeS',
    'author': 'Carl Christensen',
    'url': 'TBA.',
    'download_url': 'TBA',
    'author_email': 'exe0cdc@gmail.com',
    'version': '0.1',
    'install_requires': ['sympy', 'numpy', 'pysces',],
    'packages': packages,
    'include_package_data': True,
    'scripts': [],
    'name': 'PyscesToolbox',
}
setuptools.setup(**config)
