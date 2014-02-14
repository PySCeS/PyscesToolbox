try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
   'description': 'A library full of usefull functions to use with PySCeS',
    'author': 'Carl Christensen',
    'url': 'TBA.',
    'download_url': 'TBA',
    'author_email': 'exe0cdc@gmail.com',
    'version': '0.1',
    'install_requires': ['pysces','sympy'],
    'packages': ['pyscestoolbox'],
    'scripts': [],
    'name': 'PyscesToolbox'
}

setup(**config)