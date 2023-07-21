# -*- coding: utf-8 -*-

__author__ = """Chris Tabor (dxdstudio@gmail.com)"""

if __name__ == '__main__':
    from os import getcwd
    from os import sys
    sys.path.append(getcwd())

from MOAL.helpers.display import Section
from MOAL.helpers.trials import test_speed
from functools import wraps

DEBUG = True if __name__ == '__main__' else False

memoized = {}


def memoize(func, *args, **kwargs):
    """A decorator that memoizes the results of a decorated function."""
    funcname = func.__name__

    @wraps(func)
    def _inner(*args, **kwargs):
        key = (funcname, args)
        print(key)

        if key in memoized.keys():
            print('Getting memoized version!')
            key = (funcname, args)
            return memoized[key]
        else:
            print('Calling normal function')
            res = func(*args, **kwargs)
            memoized[key] = res
            return res
    return _inner


def memoize_lookuptable(func, *args, **kwargs):
    """A decorator that memoizes the results of a decorated function.
    Instead of checking if key is in keys, it attempts to access the
    property directly, like a typical lookup table."""
    funcname = func.__name__

    @wraps(func)
    def _inner(*args, **kwargs):
        key = (funcname, args)
        try:
            key = (funcname, args)
            return memoized[key]
        except KeyError:
            res = func(*args, **kwargs)
            memoized[key] = res
            return res
    return _inner


@test_speed
@memoize
def dolongthing(max_x, max_y):
    """Does a nested loop - running time is O(n^2)

    Args:
        max_x (int) - An integer for max outer loop
        max_y (int) - An integer for max inner loop
    Returns:
        res (int) - The resultant calculation
    """
    res = 0
    for x in range(max_x):
        for y in range(max_y):
            res += x ** y
    return res


@test_speed
@memoize_lookuptable
def dolongthing2(max_x, max_y):
    res = 0
    for x in range(max_x):
        for y in range(max_y):
            res += x ** y
    return res

if DEBUG:
    with Section('Optimization - memoization'):
        for x in range(4):
            arg = x * 100
            args = (arg, arg)
            # Non-memoized
            res = dolongthing(*args)
            # Memoized
            res2 = dolongthing(*args)
            assert res == res2

        print('Comparing memoization with lookup table vs. if check.')
        args = (500, 500)
        res1 = dolongthing(*args)
        res2 = dolongthing2(*args)
