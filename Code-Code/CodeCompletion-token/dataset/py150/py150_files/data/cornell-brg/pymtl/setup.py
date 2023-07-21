#=========================================================================
# setup.py
#=========================================================================
# setup.py inspired by the PyPA sample project:
# https://github.com/pypa/sampleproject/blob/master/setup.py

from setuptools import setup, find_packages
from codecs     import open   # To use a consistent encoding
from os         import path
from subprocess import check_output

#-------------------------------------------------------------------------
# get_version
#-------------------------------------------------------------------------
# We use the output of git describe to create a version number. Note that
# this will fail without a release tag because git describe will fail.
# Eventually when we actually have tarball releases we will need to
# also support using a separate RELEASE-VERSION file, but for now we
# always install using pip git+https from GitHub so this shoud work fine.

def get_version():
  cmd = "git describe --dirty"
  try:
    result = check_output( cmd.split(),  ).strip()
  except:
    result = "?"
  return result

#-------------------------------------------------------------------------
# get_long_descrption
#-------------------------------------------------------------------------

def get_long_description():
  here = path.abspath(path.dirname(__file__))
  with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

#-------------------------------------------------------------------------
# setup
#-------------------------------------------------------------------------

setup(

  name             = 'pymtl',
  version          = get_version(),
  description      = 'Python-based hardware modeling framework',
  long_description = get_long_description(),
  url              = 'https://github.com/cornell-brg/pymtl',
  author           = 'Batten Research Group',
  author_email     = 'brg-pymtl@csl.cornell.edu',

  # BSD 3-Clause License:
  # - http://choosealicense.com/licenses/bsd-3-clause
  # - http://opensource.org/licenses/BSD-3-Clause

  license='BSD',

  # See https://pypi.python.org/pypi?%3Aaction=list_classifiers

  classifiers=[
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 2.7',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX :: Linux',
  ],

  packages = find_packages(
    exclude=['scripts']
  ),

  package_data={
    'pymtl': [
      'tools/translation/verilator_wrapper.templ.c',
      'tools/translation/verilator_wrapper.templ.py',
      'tools/translation/cpp_wrapper.templ.py',
    ],
  },

  install_requires = [
    'pytest',
    'pytest-xdist',
    'cffi',
    'greenlet',
    'pyparsing'
  ],

)

