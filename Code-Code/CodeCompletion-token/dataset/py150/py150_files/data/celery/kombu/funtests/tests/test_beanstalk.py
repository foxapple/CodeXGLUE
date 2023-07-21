from __future__ import absolute_import, unicode_literals

from funtests import transport

from kombu.tests.case import skip


@skip.unless_module('beanstalkc')
class test_beanstalk(transport.TransportCase):
    transport = 'beanstalk'
    prefix = 'beanstalk'
    event_loop_max = 10
    message_size_limit = 47662

    def after_connect(self, connection):
        connection.channel().client
