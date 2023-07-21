from zerotest.cli import CLI


class AttributeDict(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs


def test_verify_parse_result():
    cli = CLI()
    cli._parse_result = AttributeDict(url='invalid.url')
    assert not cli.verify_parse_result()
    cli._parse_result = AttributeDict(url='http://valid.url')
    assert cli.verify_parse_result()
    cli._parse_result = AttributeDict(endpoint='invalid.url')
    assert not cli.verify_parse_result()
    cli._parse_result = AttributeDict(endpoint='http://valid.url')
    assert cli.verify_parse_result()
