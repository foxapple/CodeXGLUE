"""
Modules for making HTTP requests using the built in Python http.client module
"""

import codecs
import json
import os
import socket
import subprocess
import tempfile
import threading
import time
import zlib

from .message import Response
from .util import normalize_line_endings
from .util import scan_bytes_for_encoding
from .util import scan_string_for_encoding
import sublime

try:
    from http.client import HTTPConnection
    try:
        from http.client import HTTPSConnection
    except ImportError:
        # Linux with no SSL support.
        pass
except ImportError:
    # Python 2
    from httplib import HTTPConnection
    try:
        from httplib import HTTPSConnection
    except ImportError:
        # Linux with no SSL support.
        pass


def decode(bytes_sequence, encodings):
    """Return the first successfully decoded string"""
    for encoding in encodings:
        try:
            decoded = bytes_sequence.decode(encoding)
            return decoded
        except UnicodeDecodeError:
            # Try the next in the list.
            pass
    raise DecodeError


class HttpRequestThread(threading.Thread):
    def __init__(self, request, settings, encoding="UTF8", eol="\n"):
        threading.Thread.__init__(self)
        self.request = request
        self.response = None
        self.message = None
        self.success = False
        self.elapsed = None
        self._encoding = encoding
        self._encodings = settings.get("default_response_encodings", [])
        self._eol = eol
        self._output_request = settings.get("output_request", True)
        self._output_response = settings.get("output_response", True)
        self._timeout = settings.get("timeout", None)

    def _decode_body(self, body_bytes):

        # Decode the body. The hard part here is finding the right encoding.
        # To do this, create a list of possible matches.
        encodings = []

        # Check the content-type header, if present.
        content_type = self.response.get_header("content-type")
        if content_type:
            encoding = scan_string_for_encoding(content_type)
            if encoding:
                encodings.append(encoding)

        # Scan the body
        encoding = scan_bytes_for_encoding(body_bytes)
        if encoding:
            encodings.append(encoding)

        # Add any default encodings not already discovered.
        for encoding in self._encodings:
            if encoding not in encodings:
                encodings.append(encoding)

        # Decoding using the encodings discovered.
        try:
            body = decode(body_bytes, encodings)
        except DecodeError:
            body = "{Unable to decode body}"

        return body

    def _read_body(self, body_bytes):
        # Decode the body from a list of bytes
        # This must be called AFTER the response headers are populated.
        if not body_bytes:
            return None
        body_bytes = self._unzip_body(body_bytes)
        body = self._decode_body(body_bytes)
        body = normalize_line_endings(body, self._eol)
        return body

    def _unzip_body(self, body_bytes):
        content_encoding = self.response.get_header("content-encoding")
        if content_encoding:
            content_encoding = content_encoding.lower()
            if "gzip" in content_encoding or "deflate" in content_encoding:
                body_bytes = zlib.decompress(body_bytes, 15 + 32)
        return body_bytes

    def _validate_request(self):

        # Fail if the hostname is not set.
        if not self.request.host:
            self.message = "Unable to make request. Please provide a hostname."
            self.success = False
            return False

        if self.request.protocol not in ("http", "https"):
            self.message = "Unsupported protocol " + self.request.protocol + \
                           ". Use http of https"
            self.success = False
            return False

        return True


class HttpClientRequestThread(HttpRequestThread):
    def run(self):
        """Method to run when the thread is started."""

        if not self._validate_request():
            return

        # Determine the class to use for the connection.
        if self.request.protocol == "https":
            try:
                connection_class = HTTPSConnection
            except NameError:
                message = "Your Python interpreter does not have SSL. " \
                          "If you have cURL installed, set the http_client " \
                          "setting to \"curl\"."
                sublime.error_message(message)
                self.message = "Unable to make HTTPS requests."
                self.success = False
                return

        else:
            connection_class = HTTPConnection

        # Create the connection.
        conn = connection_class(self.request.host,
                                port=self.request.port,
                                timeout=self._timeout)

        try:

            # Body: encode and add Content-length header
            body_bytes = None
            if self.request.body:
                body_bytes = self.request.body.encode(self._encoding)
                if not self.request.get_header("Content-length"):
                    self.request.headers.append(("Content-length", len(body_bytes)))

            # Insert a host header, if needed.
            if not self.request.get_header("host"):
               self.request.headers.append(("Host", self.request.host))

            # Method and Path
            conn.putrequest(self.request.method, self.request.full_path, True, True)

            # Headers
            for key, value in self.request.headers:
                conn.putheader(key, value)
            conn.endheaders()

            # Body
            if body_bytes:
                conn.send(body_bytes)

        except socket.gaierror:
            self.message = "Unable to make request. " \
                           "Make sure the hostname is valid."
            self.success = False
            conn.close()
            return

        except ConnectionRefusedError:
            self.message = "Connection refused."
            self.success = False
            conn.close()
            return

        # Read the response.
        #noinspection PyBroadException
        try:
            time_start = time.time()
            resp = conn.getresponse()
        except socket.timeout:
            self.message = "Request timed out."
            self.success = False
            conn.close()
            return
        except:
            self.message = "Unexpected error making request."
            self.success = False
            conn.close()
            return

        # Read the response
        self._read_response(resp)
        time_end = time.time()
        self.elapsed = time_end - time_start
        conn.close()
        self.success = True

    def _read_response(self, resp):

        # Read the HTTPResponse and populate the response member.
        self.response = Response()

        # HTTP/1.1 is the default
        if resp.version == 10:
            self.response.protocol = "HTTP/1.0"

        # Status
        self.response.status = resp.status
        self.response.reason = resp.reason

        # Headers
        self.response.headers = resp.getheaders()

        # Body
        self.response.body = self._read_body(resp.read())


class CurlRequestThread(HttpRequestThread):
    def __init__(self, request, settings, **kwargs):
        HttpRequestThread.__init__(self, request, settings, **kwargs)
        self._curl_command = settings.get("curl_command", "curl")
        self._curl_options = settings.get("curl_options", [])
        self._request_body_file = None

    def run(self):

        if not self._validate_request():
            return

        # Build the list of arguments to run cURL.
        curl = subprocess.Popen(self._get_args(), stdout=subprocess.PIPE)
        time_start = time.time()
        output = curl.communicate()[0]
        time_end = time.time()
        self.elapsed = time_end - time_start
        returncode = curl.returncode

        # Delete the temporary file for message body.
        if self._request_body_file:
            os.remove(self._request_body_file)

        if returncode != 0:
            self._read_curl_error(returncode)
            self.success = False
            return

        self._read_response(output)

    def _get_args(self):

        # Build the list of arguments to run cURL.

        # Append a JSON dict of metadata to the end.
        extra = "\n\n"
        extra += "{"
        extra += "\"size_header\": %{size_header},"
        extra += "\"size_download\": %{size_download}"
        extra += "}"

        args = [self._curl_command, "--include", "--write-out", extra]

        if self._timeout:
            args += ["--max-time", str(self._timeout)]
            args += ["--connect-timeout", str(self._timeout)]

        # Method
        if self.request.method == "HEAD":
            args.append("--head")
        elif self.request.method == "GET":
            pass
        else:
            args.append("--request")
            args.append(self.request.method)

        # Headers
        for header in self.request.header_lines:
            args += ['--header', header]

        # Body
        if self.request.method in ("POST", "PUT", "PATCH") and \
                self.request.body:

            # Open a temporary file to write the request body to.
            # (Note: Using codecs to support Python 2.6)
            tmpfile = tempfile.NamedTemporaryFile("w", delete=False)
            filename = tmpfile.name
            tmpfile.close()
            tmpfile = codecs.open(filename, "w", encoding="UTF8")
            tmpfile.write(self.request.body)
            tmpfile.close()

            args.append("--data-binary")
            args.append("@" + filename)

            # Store the temporary file's filename for later deletion.
            self._request_body_file = filename

        args += self._curl_options

        # URI
        args.append(self.request.uri)
        return args

    def _read_response(self, curl_output):

        # Build a new response.
        self.response = Response()

        # Read the metadata appended to the end of the request.
        meta = curl_output[curl_output.rfind(b"\n\n"):]
        meta = meta.decode("ascii")
        meta = json.loads(meta)
        size_header = meta["size_header"]
        size_download = meta["size_download"]

        # Extract the headers and body
        headers = curl_output[0:size_header]
        body = curl_output[size_header:size_header + size_download]

        # Parse the headers as ASCII
        headers = headers.decode("ascii")
        headers = headers.split("\r\n")

        # Consume blank lines and CONTINUE status lines from headers
        for i in range(len(headers)):
            header = headers[i].upper()
            if header and "100 CONTINUE" not in header:
                headers = headers[i:]
                break

        # Read the first line as the status line.
        status_line = headers[0]
        try:
            (protocol, status, reason) = status_line.split(" ", 2)
        except ValueError:
            print(curl_output)
            self.message = "Unable to read response. " \
                           "Response may have times out."
            self.success = False
            return

        self.response.protocol = protocol
        self.response.status = int(status)
        self.response.reason = reason

        # Add each header
        for header in headers[1:]:
            if ":" in header:
                (key, value) = header.split(":", 1)
                self.response.headers.append((key.strip(), value.strip()))

        # Read the body
        self.response.body = self._read_body(body)
        self.success = True

    def _read_curl_error(self, code):
        # Set the message based on the cURL error code.
        # CURLE_UNSUPPORTED_PROTOCOL
        if code == 1:
            self.message = "Unsupported protocol " + self.request.protocol + \
                           "Use http of https"
        # CURLE_COULDNT_RESOLVE_HOST
        elif code == 6:
            self.message = "Unable to resolve host."
        # CURLE_COULDNT_RESOLVE_HOST
        elif code == 7:
            self.message = "Unable to connect."
        # CURLE_COULDNT_RESOLVE_HOST
        elif code == 28:
            self.message = "Operation timed out."
        else:
            self.message = "cURL exited with error code " + str(code)


class DecodeError(Exception):
    pass
