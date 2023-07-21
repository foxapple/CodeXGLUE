# encoding: utf-8

import socket

from functools import partial
from pprint import pformat

from marrow.server.http.testing import HTTPTestCase, CRLF, EOH

from marrow.util.compat import unicode


log = __import__('logging').getLogger(__name__)


from applications import *


class TestHTTP11Protocol(HTTPTestCase):
    arguments = dict(application=partial(echo, False))
    
    def test_headers(self):
        response = self.request(headers=[(b'Connection', b'close')])
        
        self.assertEquals(response.protocol, b"HTTP/1.1")
        self.assertEquals(response.code, b"200")
        self.assertEquals(response.status, b"OK")
        self.assertEquals(response[b'content-type'], b"text/plain; charset=utf8")
        # self.assertEquals(response[b'content-length'], b"468")
    
    def test_request(self):
        response = self.request(headers=[(b'Connection', b'close')])
        
        self.assertEquals(response.protocol, b"HTTP/1.1")
        self.assertEquals(response.code, b"200")
        self.assertEquals(response.status, b"OK")
        self.assertEquals(response[b'content-type'], b"text/plain; charset=utf8")
        # self.assertEquals(response[b'content-length'], b"468")
        
        request = eval(response.body)
        
        expect = {
                'CONTENT_LENGTH': None,
                'CONTENT_TYPE': None,
                'FRAGMENT': '',
                'HTTP_CONNECTION': 'close',
                'HTTP_HOST': 'localhost',
                'PARAMETERS': unicode(),
                'PATH_INFO': b'/'.decode('iso-8859-1'),
                'QUERY_STRING': unicode(),
                'REMOTE_ADDR': '127.0.0.1',
                'REQUEST_METHOD': 'GET',
                'SCRIPT_NAME': unicode(),
                'SERVER_ADDR': '127.0.0.1',
                'SERVER_PROTOCOL': 'HTTP/1.1',
                'wsgi.multiprocess': False,
                'wsgi.multithread': False,
                'wsgi.run_once': False,
                'wsgi.url_scheme': 'http',
                'wsgi.version': (2, 0),
                'REQUEST_URI': b'http://localhost/',
                'wsgi.async': False,
                'wsgi.uri_encoding': 'utf8'
            }
        
        self.assertEquals(request, expect)
    
    def test_single(self):
        self.request(headers=[(b'Connection', b'close')])
        
        def try_again():
            self.request(headers=[(b'Connection', b'close')])
        
        self.assertRaises((socket.error, IOError), try_again)
    
    def test_keepalive(self):
        one = self.request()
        two = self.request()
        
        self.assertEquals(one, two)


class TestChunkedHTTP11Protocol(HTTPTestCase):
    arguments = dict(application=partial(echo, True))
    maxDiff = None
    
    def test_chunked(self):
        response = self.request()
        
        self.assertEquals(response.protocol, b"HTTP/1.1")
        self.assertEquals(response.code, b"200")
        self.assertEquals(response.status, b"OK")
        self.assertEquals(response[b'content-type'], b"text/plain; charset=utf8")
        self.assertEquals(response[b'transfer-encoding'], b"chunked")
        
        request = eval(response.body)
        
        expect = {
                'CONTENT_LENGTH': None,
                'CONTENT_TYPE': None,
                'FRAGMENT': '',
                'HTTP_HOST': 'localhost',
                'PARAMETERS': unicode(),
                'PATH_INFO': b'/'.decode('iso-8859-1'),
                'QUERY_STRING': unicode(),
                'REMOTE_ADDR': '127.0.0.1',
                'REQUEST_METHOD': 'GET',
                'SCRIPT_NAME': unicode(),
                'SERVER_ADDR': '127.0.0.1',
                'SERVER_PROTOCOL': 'HTTP/1.1',
                'wsgi.multiprocess': False,
                'wsgi.multithread': False,
                'wsgi.run_once': False,
                'wsgi.url_scheme': 'http',
                'wsgi.version': (2, 0),
                'REQUEST_URI': b'http://localhost/',
                'wsgi.async': False,
                'wsgi.uri_encoding': 'utf8'
            }
        
        self.assertEquals(request, expect)


class TestHTTP11BodyProtocol(HTTPTestCase):
    arguments = dict(application=partial(echo, True))
    maxDiff = None
    
    def test_normal(self):
        body = b"Hello world!"
        response = self.request(b"PUT", headers=[(b'Content-Length', unicode(len(body)).encode('ascii'))], body=[body])
        
        self.assertEquals(response.protocol, b"HTTP/1.1")
        self.assertEquals(response.code, b"200")
        self.assertEquals(response.status, b"OK")
        self.assertEquals(response[b'content-type'], b"text/plain; charset=utf8")
        #self.assertEquals(response[b'transfer-encoding'], b"chunked")
        
        request = eval(response.body)
        
        expect = {
                'CONTENT_LENGTH': "12",
                'CONTENT_TYPE': None,
                'FRAGMENT': '',
                'HTTP_HOST': 'localhost',
                'PARAMETERS': unicode(),
                'PATH_INFO': b'/'.decode('iso-8859-1'),
                'QUERY_STRING': unicode(),
                'REMOTE_ADDR': '127.0.0.1',
                'REQUEST_METHOD': 'PUT',
                'SCRIPT_NAME': unicode(),
                'SERVER_ADDR': '127.0.0.1',
                'SERVER_PROTOCOL': 'HTTP/1.1',
                'wsgi.multiprocess': False,
                'wsgi.multithread': False,
                'wsgi.run_once': False,
                'wsgi.url_scheme': 'http',
                'wsgi.version': (2, 0),
                'REQUEST_URI': b'http://localhost/',
                'wsgi.async': False,
                'wsgi.uri_encoding': 'utf8',
                'wsgi.input': b"Hello world!"
            }
        
        self.assertEquals(request, expect)
    
    def test_chunked(self):
        body = b"Hello world!"
        response = self.request(b"PUT", body=[body])
        
        self.assertEquals(response.protocol, b"HTTP/1.1")
        self.assertEquals(response.code, b"200")
        self.assertEquals(response.status, b"OK")
        self.assertEquals(response[b'content-type'], b"text/plain; charset=utf8")
        self.assertEquals(response[b'transfer-encoding'], b"chunked")
        
        request = eval(response.body)
        
        expect = {
                'CONTENT_LENGTH': None,
                'CONTENT_TYPE': None,
                'FRAGMENT': '',
                'HTTP_TRANSFER_ENCODING': 'chunked',
                'HTTP_HOST': 'localhost',
                'PARAMETERS': unicode(),
                'PATH_INFO': b'/'.decode('iso-8859-1'),
                'QUERY_STRING': unicode(),
                'REMOTE_ADDR': '127.0.0.1',
                'REQUEST_METHOD': 'PUT',
                'SCRIPT_NAME': unicode(),
                'SERVER_ADDR': '127.0.0.1',
                'SERVER_PROTOCOL': 'HTTP/1.1',
                'wsgi.multiprocess': False,
                'wsgi.multithread': False,
                'wsgi.run_once': False,
                'wsgi.url_scheme': 'http',
                'wsgi.version': (2, 0),
                'REQUEST_URI': b'http://localhost/',
                'wsgi.async': False,
                'wsgi.uri_encoding': 'utf8',
                'wsgi.input': b'Hello world!'
            }
        
        self.assertEquals(request, expect)
