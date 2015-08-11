#!/bin/env python
from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):

    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(['source/python'] + self.pytest_args)
        sys.exit(errno)


setup(
    name='ben10',
    version='0.2.0',

    author='Alexandre Andrade',
    author_email='ama@esss.com.br',

    url='https://github.com/ESSS/ben10',

    description = 'Basic ESSS Namespace',
    long_description = '''BEN10 name is a collection of python utilities from ESSS (www.esss.com.br) development team.

This is a draft effort to publish a Open Source library with our base code, developed during the last 10 year using Python.
''',

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',  # Python Framework!

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    include_package_data=True,

    package_dir = {'' : 'source/python'},
    packages=find_packages('source/python'),

    install_requires=[
        'cogapp',
        'colorama',
        'cov-core',
        'coverage',
        'faulthandler',
        'ftputil',
        'funcsigs',
        'mock',
        'path.py',
        'py',
        'pyftpdlib',
        'pytest',
        'pytest-cache',
        'pytest-cov',
        'pytest-localserver',
        'pytest-timeout',
        'pytest-xdist',
        'rarfile',
        'ruamel.ordereddict',
        'six',
        'wheel',
    ],
    cmdclass={'test': PyTest},
)
