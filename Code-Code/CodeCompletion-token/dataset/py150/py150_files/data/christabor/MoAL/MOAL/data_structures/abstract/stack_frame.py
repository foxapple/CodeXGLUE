# -*- coding: utf-8 -*-

__author__ = """Chris Tabor (dxdstudio@gmail.com)"""

# Inspired by
# http://stackoverflow.com/questions/10057443/
#   explain-the-concept-of-a-stack-frame-in-a-nutshell

if __name__ == '__main__':
    from os import getcwd
    from os import sys
    sys.path.append(getcwd())

from MOAL.helpers.display import Section
from MOAL.data_structures.abstract.stack import Stack


class StackFrame:

    def __init__(self, func, **kwargs):
        self.func = func
        self.data = kwargs


class StackTrace(Stack):

    def __init__(self):
        super(StackTrace, self).__init__()

    def call(self, func, **kwargs):
        frame = StackFrame(func, **kwargs)
        print('Pushing new function frame onto the stack {}'.format(frame))
        self.push(frame)

    def view(self):
        items = super(StackTrace, self).view()
        for k, item in enumerate(items):
            print('{} {} {}'.format(('-' * k) + '+', item.func, item.data))


def init():

    def foo():
        print('I am the foo func!')

    def foo2():
        print('I am the foo2 func!')

    def bar():
        print('I am the bar func!')
        foo()

    def bim():
        print('I am the bim func!')
        foo2()

    tracer = StackTrace()
    for name, func in locals().iteritems():
        if name is not 'tracer':
            func()
            tracer.call(func, name=name)
    with Section('Call Stack'):
        tracer.view()


if __name__ == '__main__':
    with Section('Stack frame examples'):
        init()
