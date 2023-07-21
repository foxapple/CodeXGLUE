from zerotest.request import Request


req = Request(scheme="http", method="GET", params={"hello": "test"}, host="example.com", path="/test",
              headers={"Auth": "FOR_TEST"}, data="ok")


def test_url():
    assert req.url == 'http://example.com/test'


def test_endpoint():
    assert req.endpoint == 'http://example.com'


def test_endpoint_setter():
    endpoint = req.endpoint
    req.endpoint = "https://another-example.com"
    assert req.endpoint == "https://another-example.com"
    assert req.host == "another-example.com"
    assert req.scheme == "https"
    req.endpoint = endpoint


def test__str__():
    assert str(req) == """[GET]http://example.com/test
{'Auth': 'FOR_TEST'}
ok"""
