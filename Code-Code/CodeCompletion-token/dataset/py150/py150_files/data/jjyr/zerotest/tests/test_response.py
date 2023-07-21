from zerotest.response import Response


def test_response__str__():
    response = Response(200, {"just test": "hope pass"}, "happy test!")
    assert str(response) == """200
{'just test': 'hope pass'}
happy test!"""
