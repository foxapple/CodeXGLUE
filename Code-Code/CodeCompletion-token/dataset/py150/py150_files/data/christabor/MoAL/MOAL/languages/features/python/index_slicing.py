# -*- coding: utf-8 -*-

__author__ = """Chris Tabor (dxdstudio@gmail.com)"""

if __name__ == '__main__':
    from os import getcwd
    from os import sys
    sys.path.append(getcwd())

from MOAL.helpers.display import Section
from MOAL.helpers.display import prnt
from random import shuffle
import re

DEBUG = True if __name__ == '__main__' else False


if DEBUG:
    with Section('Python - index slicing'):
        default = range(40)
        shuffle(default)
        prnt('Slice from beginning', default[:20])
        prnt('Slice to end', default[10:])
        prnt('Slice to end -x dynamic', default[:-2])
        prnt('Slice based on `len` result', default[0:len(default) / 2])
        prnt('Slice based on `index` result', default[0:default.index(4)])

        prnt('Slice both ends based on `index` result',
             default[default.index(3):default.index(20)])

        _def = default[::-1]
        prnt('Slice using slice reverse "sugar"', _def[1:10])

        testing = 'Hello world'
        index = re.search(r'world', testing)
        prnt('Slice word based on regex', testing[0:index.start()])
        prnt('Slice substring with reverse', testing[-3::-1])
        for n in range(1, len(testing)):
            print('Slice with reverse n: {} - {}'.format(n, testing[::-n]))
        test = range(12)
        prnt('Slice with odds/evens', test)
        for n in range(1, 10):
            print('Slice with sequence n - {}, {}'.format(n, test[-n::-n]))
