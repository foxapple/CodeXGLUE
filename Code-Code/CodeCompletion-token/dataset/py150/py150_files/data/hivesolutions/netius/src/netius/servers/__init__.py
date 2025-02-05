#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Netius System
# Copyright (c) 2008-2016 Hive Solutions Lda.
#
# This file is part of Hive Netius System.
#
# Hive Netius System is free software: you can redistribute it and/or modify
# it under the terms of the Apache License as published by the Apache
# Foundation, either version 2.0 of the License, or (at your option) any
# later version.
#
# Hive Netius System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# Apache License for more details.
#
# You should have received a copy of the Apache License along with
# Hive Netius System. If not, see <http://www.apache.org/licenses/>.

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2016 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "Apache License, Version 2.0"
""" The license for the module """

from . import dhcp
from . import echo
from . import ftp
from . import http
from . import mjpg
from . import pop
from . import proxy
from . import smtp
from . import socks
from . import torrent
from . import ws
from . import wsgi

from .dhcp import DHCPRequest, DHCPServer
from .echo import EchoServer
from .ftp import FTPConnection, FTPServer
from .http import PLAIN_ENCODING, CHUNKED_ENCODING, GZIP_ENCODING, HTTPConnection,\
    HTTPServer
from .mjpg import MJPGServer
from .pop import POPConnection, POPServer
from .proxy import ProxyConnection, ProxyServer
from .smtp import TERMINATION_SIZE, SMTPConnection, SMTPServer
from .socks import SOCKSConnection, SOCKSServer
from .torrent import Pieces, TorrentTask, TorrentServer
from .ws import WSConnection, WSServer
from .wsgi import WSGIServer
