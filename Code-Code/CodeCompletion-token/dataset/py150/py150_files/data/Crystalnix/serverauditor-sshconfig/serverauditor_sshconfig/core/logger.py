# coding: utf-8

"""
Copyright (c) 2013 Crystalnix.
License BSD, see LICENSE for more details.
"""

from __future__ import print_function

import pprint
import sys
import time


class PrettyLogger(object):

    COLOR_END = '\033[0m'
    COLOR_BOLD = '\033[1m'
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'blue': '\033[94m',
        'yellow': '\033[93m',
        'magenta': '\033[95m',
        'end': COLOR_END
    }

    def log(self, message, sleep=0.5, color='end', color_bold=False, is_pprint=False, *args, **kwargs):
        fl = kwargs.get('file', sys.stdout)
        print(self.COLORS.get(color, self.COLOR_END), end='', file=fl)
        if color_bold:
            print(self.COLOR_BOLD, end='', file=fl)
        if is_pprint:
            pprint.pprint(message, *args, **kwargs)
        else:
            print(message, end='', *args, **kwargs)
        print(self.COLOR_END, file=fl)
        if sleep:
            time.sleep(sleep)
        return
