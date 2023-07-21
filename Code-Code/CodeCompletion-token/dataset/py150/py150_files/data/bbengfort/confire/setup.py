#!/usr/bin/env python
# setup
# Setup script for confire
#
# Author:   Benjamin Bengfort <benjamin@bengfort.com>
# Created:  Sun Jul 20 11:06:56 2014 -0400
#
# Copyright (C) 2014-2015 Benjamin Bengfort
# For license information, see LICENSE.txt
#
# ID: setup.py [] benjamin@bengfort.com $

"""
Setup script for confire
"""

##########################################################################
## Imports
##########################################################################

try:
    from setuptools import setup
    from setuptools import find_packages
except ImportError:
    raise ImportError("Could not import \"setuptools\"."
                      "Please install the setuptools package.")

##########################################################################
## Package Information
##########################################################################

version  = __import__('confire').__version__

## Discover the packages
packages = find_packages(where=".", exclude=("tests", "bin", "docs", "fixtures", "register",))

## Load the requirements
requires = []
with open('requirements.txt', 'r') as reqfile:
    for line in reqfile:
        requires.append(line.strip())

## Define the classifiers
classifiers = (
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities',
)

## Define the keywords
keywords = ('configuration', 'yaml', 'config', 'confire')

## Define the description
long_description = "Confire is a simple but powerful configuration scheme that builds on the configuration parsers of Scapy, elasticsearch, Django and others. The basic scheme is to have a configuration search path that looks for YAML files in standard locations. The search path is hierarchical (meaning that system configurations are overloaded by user configurations, etc). These YAML files are then added to a default, class-based configuration management scheme that allows for easy development.\n\nDocumentation is available here: http://confire.readthedocs.org/en/latest/"

## Define the configuration
config = {
    "name": "confire",
    "version": version,
    "description": "A simple app configuration scheme using YAML and class based defaults.",
    "long_description": long_description,
    "license": "MIT",
    "author": "Benjamin Bengfort",
    "author_email": "benjamin@bengfort.com",
    "url": "https://github.com/bbengfort/confire",
    "download_url": 'https://github.com/bbengfort/confire/tarball/v%s' % version,
    "packages": packages,
    "install_requires": requires,
    "classifiers": classifiers,
    "keywords": keywords,
    "zip_safe": True,
    "scripts": [],
}

##########################################################################
## Run setup script
##########################################################################

if __name__ == '__main__':
    setup(**config)
