import json
import os
from click.testing import CliRunner
from unittest.mock import MagicMock
import yaml
import zign.api
from pierone.cli import cli


def test_version(monkeypatch):
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['--version'], catch_exceptions=False)
        assert 'Pier One CLI' in result.output


def test_login(monkeypatch, tmpdir):
    response = MagicMock()

    runner = CliRunner()

    monkeypatch.setattr('stups_cli.config.load_config', lambda x: {})
    monkeypatch.setattr('pierone.api.get_named_token', MagicMock(return_value={'access_token': 'tok123'}))
    monkeypatch.setattr('os.path.expanduser', lambda x: x.replace('~', str(tmpdir)))
    monkeypatch.setattr('requests.get', lambda x, timeout: response)

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['login'], catch_exceptions=False, input='pieroneurl\n')
        with open(os.path.join(str(tmpdir), '.docker/config.json')) as fd:
            data = json.load(fd)
        assert data['auths']['https://pieroneurl']['auth'] == 'b2F1dGgyOnRvazEyMw=='
        assert 'Storing Docker client configuration' in result.output
        assert result.output.rstrip().endswith('OK')


def test_login_given_url_option(monkeypatch, tmpdir):
    response = MagicMock()

    runner = CliRunner()

    config = {}
    def store(data, section):
        config.update(**data)

    monkeypatch.setattr('stups_cli.config.load_config', lambda x: {})
    monkeypatch.setattr('stups_cli.config.store_config', store)
    monkeypatch.setattr('pierone.api.get_named_token', MagicMock(return_value={'access_token': 'tok123'}))
    monkeypatch.setattr('os.path.expanduser', lambda x: x.replace('~', str(tmpdir)))
    monkeypatch.setattr('requests.get', lambda x, timeout: response)

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['login'], catch_exceptions=False, input='pieroneurl\n')
        assert config == {'url': 'https://pieroneurl'}
        result = runner.invoke(cli, ['login', '--url', 'someotherregistry'], catch_exceptions=False)
        with open(os.path.join(str(tmpdir), '.docker/config.json')) as fd:
            data = json.load(fd)
        assert data['auths']['https://pieroneurl']['auth'] == 'b2F1dGgyOnRvazEyMw=='
        assert data['auths']['https://someotherregistry']['auth'] == 'b2F1dGgyOnRvazEyMw=='
        assert config == {'url': 'https://pieroneurl'}


def test_scm_source(monkeypatch, tmpdir):
    response = MagicMock()
    response.json.return_value = {'url': 'git:somerepo', 'revision': 'myrev123'}

    runner = CliRunner()
    monkeypatch.setattr('stups_cli.config.load_config', lambda x: {'url':'foobar'})
    monkeypatch.setattr('zign.api.get_token', MagicMock(return_value='tok123'))
    monkeypatch.setattr('pierone.cli.get_tags', MagicMock(return_value={}))
    monkeypatch.setattr('os.path.expanduser', lambda x: x.replace('~', str(tmpdir)))
    monkeypatch.setattr('pierone.api.session.get', MagicMock(return_value=response))
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['scm-source', 'myteam', 'myart', '1.0'], catch_exceptions=False)
        assert 'myrev123' in result.output
        assert 'git:somerepo' in result.output

def test_image(monkeypatch, tmpdir):
    response = MagicMock()
    response.json.return_value = [{'name': '1.0', 'team': 'stups', 'artifact': 'kio'}]

    runner = CliRunner()
    monkeypatch.setattr('stups_cli.config.load_config', lambda x: {'url':'foobar'})
    monkeypatch.setattr('zign.api.get_token', MagicMock(return_value='tok123'))
    monkeypatch.setattr('os.path.expanduser', lambda x: x.replace('~', str(tmpdir)))
    monkeypatch.setattr('pierone.api.session.get', MagicMock(return_value=response))
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['image', 'abcd'], catch_exceptions=False)
        assert 'kio' in result.output
        assert 'stups' in result.output
        assert '1.0' in result.output


def test_tags(monkeypatch, tmpdir):
    response = MagicMock()
    response.json.return_value = [{'name': '1.0', 'created_by': 'myuser', 'created': '2015-08-20T08:14:59.432Z'}]

    runner = CliRunner()
    monkeypatch.setattr('stups_cli.config.load_config', lambda x: {'url':'foobar'})
    monkeypatch.setattr('zign.api.get_token', MagicMock(return_value='tok123'))
    monkeypatch.setattr('os.path.expanduser', lambda x: x.replace('~', str(tmpdir)))
    monkeypatch.setattr('pierone.api.session.get', MagicMock(return_value=response))
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['tags', 'myteam', 'myart'], catch_exceptions=False)
        assert '1.0' in result.output


def test_latest(monkeypatch, tmpdir):
    response = MagicMock()
    response.json.return_value = [
            {'name': '1.0', 'created_by': 'myuser', 'created': '2015-08-20T08:14:59.432Z'},
            # 1.1 was pushed BEFORE 1.0, i.e. latest tag is actually "1.0"!
            {'name': '1.1', 'created_by': 'myuser', 'created': '2015-08-20T08:11:59.432Z'}]

    runner = CliRunner()
    monkeypatch.setattr('stups_cli.config.load_config', lambda x: {'url': 'https://pierone.example.org'})
    monkeypatch.setattr('zign.api.get_token', MagicMock(return_value='tok123'))
    monkeypatch.setattr('pierone.api.get_existing_token', MagicMock(return_value={'access_token': 'tok123'}))
    monkeypatch.setattr('pierone.api.session.get', MagicMock(return_value=response))
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['latest', 'myteam', 'myart'], catch_exceptions=False)
        assert '1.0' == result.output.rstrip()


def test_latest_not_found(monkeypatch, tmpdir):
    response = MagicMock()
    response.raise_for_status.side_effect = Exception('FAIL')
    runner = CliRunner()
    monkeypatch.setattr('stups_cli.config.load_config', lambda x: {'url': 'https://pierone.example.org'})
    monkeypatch.setattr('zign.api.get_token', MagicMock(return_value='tok123'))
    monkeypatch.setattr('pierone.api.get_existing_token', MagicMock(return_value={'access_token': 'tok123'}))
    monkeypatch.setattr('pierone.api.session.get', MagicMock(return_value=response))
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['latest', 'myteam', 'myart'], catch_exceptions=False)
        assert 'None' == result.output.rstrip()


def test_url_without_scheme(monkeypatch, tmpdir):
    response = MagicMock()
    response.json.return_value = [{'name': '1.0', 'created_by': 'myuser', 'created': '2015-08-20T08:14:59.432Z'}]

    def get(url, **kwargs):
        assert url == 'https://example.org/teams/myteam/artifacts'
        return response

    runner = CliRunner()
    monkeypatch.setattr('zign.api.get_token', MagicMock(return_value='tok123'))
    monkeypatch.setattr('os.path.expanduser', lambda x: x.replace('~', str(tmpdir)))
    monkeypatch.setattr('pierone.api.session.get', get)
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['artifacts', 'myteam', '--url', 'example.org'], catch_exceptions=False)
        assert '1.0' in result.output
