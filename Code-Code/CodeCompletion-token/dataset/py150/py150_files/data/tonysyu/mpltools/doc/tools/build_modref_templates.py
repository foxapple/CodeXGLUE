#!/usr/bin/env python
"""Script to auto-generate our API docs.
"""
from __future__ import print_function
# stdlib imports
import os, sys

# local imports
from apigen import ApiDocWriter

# version comparison
from distutils.version import LooseVersion as V

#*****************************************************************************

def abort(error):
    print('*WARNING* API documentation not generated: %s'%error)
    exit()


def assert_source_and_install_match(package):
    """
    Check that the source version is equal to the installed
    version. If the versions mismatch the API documentation sources
    are not (re)generated. This avoids automatic generation of documentation
    for older or newer versions if such versions are installed on the system.
    """
    module = sys.modules[package]

    installed_version = V(module.version.version)

    setup_lines = open('../setup.py').readlines()
    for l in setup_lines:
        if l.startswith('VERSION'):
            source_version = V(l.split("'")[1])
            break

    if source_version != installed_version:
        abort("Installed version does not match source version")


if __name__ == '__main__':
    package = 'mpltools'

    # Check that the 'image' package is available. If not, the API
    # documentation is not (re)generated and existing API documentation
    # sources will be used.

    try:
        __import__(package)
    except ImportError as e:
        abort("Cannot import mpltools")

    #assert_source_and_install_match(package)

    outdir = 'source/api'
    docwriter = ApiDocWriter(package)
    docwriter.package_skip_patterns += [r'\.fixes$',
                                        r'\.externals$',
                                        ]
    docwriter.write_api_docs(outdir)
    docwriter.write_index(outdir, 'api', relative_to='source/api')
    print('%d files written' % len(docwriter.written_modules))
