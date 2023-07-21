# -*- coding: utf-8 -*-

import logging
import re

from polaris_health import Error, ProtocolError, MonitorFailed
from polaris_health.protocols.tcp import TCPSocket
from . import BaseMonitor


__all__ = [ 'TCP' ]

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())

# maximum allowed length of match_re parameter
MAX_MATCH_RE_LEN = 128

# maximum allowed length of send_string parameter
MAX_SEND_STRING_LEN = 256


class TCP(BaseMonitor):

    """TCP monitor base"""

    def __init__(self, port, send_string=None, match_re=None,
                 interval=10, timeout=5, retries=2):
        """
        args:
            port: int, port number
            send_string: string, a string to send to the socket,
                before reading a response
            match_re: string, a regular expression to search for in a response

            Other args as per BaseMonitor() spec
        """
        super(TCP, self).__init__(interval=interval, timeout=timeout,
                                      retries=retries)

        # name to show in generic state export
        self.name = 'tcp'

        ### port ###
        self.port = port
        if not isinstance(port, int) or port < 1 or port > 65535:
            log_msg = ('port "{}" must be an integer between 1 and 65535'.
                       format(port))
            LOG.error(log_msg)
            raise Error(log_msg)

        ### match_re ###
        self.match_re = match_re
        self._match_re_compiled = None
        if self.match_re is not None:
            if not isinstance(match_re, str) \
                    or len(match_re) > MAX_MATCH_RE_LEN:
                log_msg = ('match_re "{}" must be a string, {} chars max'.
                           format(match_re, MAX_MATCH_RE_LEN))
                LOG.error(log_msg)
                raise Error(log_msg)
            
            # compile regexp obj to use for matching
            try:
                self._match_re_compiled = re.compile(self.match_re, flags=re.I)
            except Exception as e:
                log_msg = ('failed to compile a regular '
                           'expression from "{}", {}'
                           .format(self.match_re, e))
                LOG.error(log_msg)
                raise Error(log_msg)

        ### send_string ###
        self.send_string = send_string
        self._send_bytes = None
        if send_string is not None:
            if not isinstance(send_string, str) \
                    or len(send_string) > MAX_SEND_STRING_LEN:
                log_msg = ('send_string "{}" must be a string, {} chars max'.
                       format(send_string, MAX_SEND_STRING_LEN))
                LOG.error(log_msg)
                raise Error(log_msg)

            # convert to bytes for sending over network
            self._send_bytes = self.send_string.encode()

    def run(self, dst_ip):
        """
        Connect a tcp socket 
        If we have a string to send, send it to the socket
        If have a regexp to match, read response and match the regexp

        args:
            dst_ip: string, IP address to connect to

        returns:
            None

        raises:
            MonitorFailed() on a socket operation timeout/error or if failed
            match the regexp.
        """
        tcp_sock = TCPSocket(ip=dst_ip, port=self.port, timeout=self.timeout)

        # connect socket, send string if required
        try:
            tcp_sock.connect()
            if self.send_string is not None:
                tcp_sock.sendall(self._send_bytes)
        except ProtocolError as e:
            raise MonitorFailed(e)

        # if we have nothing to match, close the socket and return
        if self.match_re is None:
            tcp_sock.close()
            return

        # we have a regexp to match
        # continuously read from the socket and perform matching until either
        # a match is found, a timeout occurred or remote end 
        # closed the conection
        response_string = ''
        while True:
            try:
                recv_bytes = tcp_sock.recv()
            except ProtocolError as e:
                log_msg = ('failed to match the regexp within the timeout, '
                           'got {error}, '
                           'response(up to 512 chars): {response_string}'
                           .format(error=e,
                                   response_string=response_string[:512]))
                raise MonitorFailed(log_msg)

            # remote side closed connection, no need to call sock.close()
            if recv_bytes == b'':
                raise MonitorFailed('remote closed the connection, '
                                    'failed to match the regexp in the '
                                    'response(up to 512 chars): {}'
                                    .format(response_string[:512]))
        
            # received data
            else:
                response_string += recv_bytes.decode(errors='ignore')
                if self._match_re_compiled.search(response_string):
                    tcp_sock.close()
                    return

