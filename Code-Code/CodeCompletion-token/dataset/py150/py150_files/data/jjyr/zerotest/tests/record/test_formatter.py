from zerotest.utils.io_helper import StringIO

from zerotest.record.formatter import Formatter
from zerotest.request import Request
from zerotest.response import Response

req = Request(scheme="http", method="get", params="query_string=here", host="example.com", path="/test",
              headers={"just": "header"}, data="request")
res = Response(status=200, headers={"responsed": "header"}, body="response")
formatter = Formatter()


def test_formatter():
    writable = StringIO()
    formatter.write_record(writable, req, res)
    readable = StringIO(writable.getvalue())
    request, response = formatter.read_record(readable)
    assert req.__dict__ == request.__dict__
    assert res.__dict__ == response.__dict__
