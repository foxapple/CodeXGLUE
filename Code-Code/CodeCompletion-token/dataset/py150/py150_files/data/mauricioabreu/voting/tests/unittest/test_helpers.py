import os

import pytest

from backend.helpers import parse_config


class TestHelpers:
    def test_parse_config_returns_parsed_config(self, tmpdir):
        temp = tmpdir.mkdir('temp').join('testing.ini')
        temp.write('''[test]\nkey1 = 10\nkey2 = 20''')
        config = parse_config(temp.strpath)
        assert 'key1' in dict(config.items('test'))
        assert 'key2' in dict(config.items('test'))
        os.remove(temp.strpath)

    def test_parse_config_with_inexistent_file(self):
        with pytest.raises(IOError):
            parse_config('inexistent.ini')
