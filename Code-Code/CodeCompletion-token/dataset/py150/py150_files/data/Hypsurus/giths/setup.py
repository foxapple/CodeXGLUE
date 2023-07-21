#!/usr/bin/env python2
# 
# setup.py - setup script
#
#  This file is part of giths 
#
# Copyright (c) 2016 Hypsurus <hypsurus@mail.ru>.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


from setuptools import setup, find_packages

version = '0.1'

setup(
    name='giths',
    version=version,
    description='Search code through github without API',
    author='Hypsurus',
    author_email='hypsurus@mail.ru',
    license='MIT',
    keywords=['github', 'command line', 'cli'],
    url='https://github.com/Hypsurus/giths',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'giths=giths.giths:main'
        ],
    }
)
