# -*- coding: utf-8 -
#
# This file is part of flower. See the NOTICE for more information.

from flower.core import channel, getcurrent, get_scheduler
from flower.core.uv import uv_server

class NoMoreListener(Exception):
    pass

class Listener(object):

    def __init__(self):
        self.task = getcurrent()
        self.uv = uv_server()
        self.sched = get_scheduler()
        self.c = channel()


    @property
    def loop(self):
        return self.uv.loop


class IConn(object):
    """ connection interface """

    def read(self):
        """ return data """

    def write(self, data):
        """ send data to the remote connection """

    def writelines(self, seq):
        """ send data using a list or an iterator to the remote
        connection """

    def local_addr(self):
        """ return the local address """

    def remote_addr(self):
        """ return the remote address """

    @property
    def status(self):
        """ return current status """
        if self.client.closed:
            return "closed"
        elif self.client.readable and self.client.writable:
            return "open"
        elif self.client.readable and not self.client.writable:
            return "readonly"
        elif not self.client.readable and self.client.writable:
            return "writeonly"
        else:
            return "closed"


class IListen(object):

    def accept(self):
        """ accept a connection. Return a Conn instance. It always
        block the current task """

    def close(self):
        """ stop listening """

    def addr(self):
        " return the bound address """

class IDial(object):

    """ base interface for Dial class """
