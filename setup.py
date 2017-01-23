from setuptools import setup, find_packages

packages = find_packages()

setup(
    name='PyscesToolbox',
    version='0.8.2',
    packages=packages,
    url='https://github.com/PySCeS/PyscesToolbox',
    license='',
    author='Carl Christensen',
    author_email='carldc@sun.ac.za',
    description='A set of metabolic model analysis tools for PySCeS.',
    install_requires=['numpydoc'],
)
