from __future__ import absolute_import
from __future__ import unicode_literals

import io
import logging
import os
import os.path
import re
import shutil

import mock
import pkg_resources
import pytest

from pre_commit import five
from pre_commit.clientlib.validate_config import CONFIG_JSON_SCHEMA
from pre_commit.clientlib.validate_config import validate_config_extra
from pre_commit.jsonschema_extensions import apply_defaults
from pre_commit.languages import helpers
from pre_commit.languages import node
from pre_commit.languages import python
from pre_commit.languages import ruby
from pre_commit.repository import Repository
from pre_commit.util import cmd_output
from pre_commit.util import cwd
from testing.fixtures import config_with_local_hooks
from testing.fixtures import git_dir
from testing.fixtures import make_config_from_repo
from testing.fixtures import make_repo
from testing.fixtures import modify_manifest
from testing.util import skipif_slowtests_false
from testing.util import xfailif_no_pcre_support
from testing.util import xfailif_windows_no_node
from testing.util import xfailif_windows_no_ruby


def _test_hook_repo(
        tempdir_factory,
        store,
        repo_path,
        hook_id,
        args,
        expected,
        expected_return_code=0,
        config_kwargs=None
):
    path = make_repo(tempdir_factory, repo_path)
    config = make_config_from_repo(path, **(config_kwargs or {}))
    repo = Repository.create(config, store)
    hook_dict = [
        hook for repo_hook_id, hook in repo.hooks if repo_hook_id == hook_id
    ][0]
    ret = repo.run_hook(hook_dict, args)
    assert ret[0] == expected_return_code
    assert ret[1].replace(b'\r\n', b'\n') == expected


@pytest.mark.integration
def test_python_hook(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'python_hooks_repo',
        'foo', [os.devnull],
        b"['" + five.to_bytes(os.devnull) + b"']\nHello World\n"
    )


@pytest.mark.integration
def test_python_hook_args_with_spaces(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'python_hooks_repo',
        'foo',
        [],
        b"['i have spaces', 'and\"\\'quotes', '$and !this']\n"
        b'Hello World\n',
        config_kwargs={
            'hooks': [{
                'id': 'foo',
                'args': ['i have spaces', 'and"\'quotes', '$and !this'],
            }]
        },
    )


@pytest.mark.integration
def test_switch_language_versions_doesnt_clobber(tempdir_factory, store):
    # We're using the python3 repo because it prints the python version
    path = make_repo(tempdir_factory, 'python3_hooks_repo')

    def run_on_version(version, expected_output):
        config = make_config_from_repo(
            path, hooks=[{'id': 'python3-hook', 'language_version': version}],
        )
        repo = Repository.create(config, store)
        hook_dict, = [
            hook
            for repo_hook_id, hook in repo.hooks
            if repo_hook_id == 'python3-hook'
        ]
        ret = repo.run_hook(hook_dict, [])
        assert ret[0] == 0
        assert ret[1].replace(b'\r\n', b'\n') == expected_output

    run_on_version('python3.4', b'3.4\n[]\nHello World\n')
    run_on_version('python3.3', b'3.3\n[]\nHello World\n')


@pytest.mark.integration
def test_versioned_python_hook(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'python3_hooks_repo',
        'python3-hook',
        [os.devnull],
        b"3.3\n['" + five.to_bytes(os.devnull) + b"']\nHello World\n",
    )


@skipif_slowtests_false
@xfailif_windows_no_node
@pytest.mark.integration
def test_run_a_node_hook(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'node_hooks_repo',
        'foo', ['/dev/null'], b'Hello World\n',
    )


@skipif_slowtests_false
@xfailif_windows_no_node
@pytest.mark.integration
def test_run_versioned_node_hook(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'node_0_11_8_hooks_repo',
        'node-11-8-hook', ['/dev/null'], b'v0.11.8\nHello World\n',
    )


@skipif_slowtests_false
@xfailif_windows_no_ruby
@pytest.mark.integration
def test_run_a_ruby_hook(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'ruby_hooks_repo',
        'ruby_hook', ['/dev/null'], b'Hello world from a ruby hook\n',
    )


@skipif_slowtests_false
@xfailif_windows_no_ruby
@pytest.mark.integration
def test_run_versioned_ruby_hook(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'ruby_1_9_3_hooks_repo',
        'ruby_hook',
        ['/dev/null'],
        b'1.9.3\n551\nHello world from a ruby hook\n',
    )


@pytest.mark.integration
def test_system_hook_with_spaces(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'system_hook_with_spaces_repo',
        'system-hook-with-spaces', ['/dev/null'], b'Hello World\n',
    )


@pytest.mark.integration
def test_run_a_script_hook(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'script_hooks_repo',
        'bash_hook', ['bar'], b'bar\nHello World\n',
    )


@pytest.mark.integration
def test_run_hook_with_spaced_args(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'arg_per_line_hooks_repo',
        'arg-per-line',
        ['foo bar', 'baz'],
        b'arg: hello\narg: world\narg: foo bar\narg: baz\n',
    )


@pytest.mark.integration
def test_run_hook_with_curly_braced_arguments(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'arg_per_line_hooks_repo',
        'arg-per-line',
        [],
        b"arg: hi {1}\narg: I'm {a} problem\n",
        config_kwargs={
            'hooks': [{
                'id': 'arg-per-line',
                'args': ['hi {1}', "I'm {a} problem"],
            }]
        },
    )


@xfailif_no_pcre_support
@pytest.mark.integration
def test_pcre_hook_no_match(tempdir_factory, store):
    path = git_dir(tempdir_factory)
    with cwd(path):
        with io.open('herp', 'w') as herp:
            herp.write('foo')

        with io.open('derp', 'w') as derp:
            derp.write('bar')

        _test_hook_repo(
            tempdir_factory, store, 'pcre_hooks_repo',
            'regex-with-quotes', ['herp', 'derp'], b'',
        )

        _test_hook_repo(
            tempdir_factory, store, 'pcre_hooks_repo',
            'other-regex', ['herp', 'derp'], b'',
        )


@xfailif_no_pcre_support
@pytest.mark.integration
def test_pcre_hook_matching(tempdir_factory, store):
    path = git_dir(tempdir_factory)
    with cwd(path):
        with io.open('herp', 'w') as herp:
            herp.write("\nherpfoo'bard\n")

        with io.open('derp', 'w') as derp:
            derp.write('[INFO] information yo\n')

        _test_hook_repo(
            tempdir_factory, store, 'pcre_hooks_repo',
            'regex-with-quotes', ['herp', 'derp'], b"herp:2:herpfoo'bard\n",
            expected_return_code=1,
        )

        _test_hook_repo(
            tempdir_factory, store, 'pcre_hooks_repo',
            'other-regex', ['herp', 'derp'], b'derp:1:[INFO] information yo\n',
            expected_return_code=1,
        )


@xfailif_no_pcre_support
@pytest.mark.integration
def test_pcre_hook_case_insensitive_option(tempdir_factory, store):
    path = git_dir(tempdir_factory)
    with cwd(path):
        with io.open('herp', 'w') as herp:
            herp.write('FoOoOoObar\n')

        _test_hook_repo(
            tempdir_factory, store, 'pcre_hooks_repo',
            'regex-with-grep-args', ['herp'], b'herp:1:FoOoOoObar\n',
            expected_return_code=1,
        )


@xfailif_no_pcre_support
@pytest.mark.integration
def test_pcre_many_files(tempdir_factory, store):
    # This is intended to simulate lots of passing files and one failing file
    # to make sure it still fails.  This is not the case when naively using
    # a system hook with `grep -H -n '...'` and expected_return_code=1.
    path = git_dir(tempdir_factory)
    with cwd(path):
        with io.open('herp', 'w') as herp:
            herp.write('[INFO] info\n')

        _test_hook_repo(
            tempdir_factory, store, 'pcre_hooks_repo',
            'other-regex',
            ['/dev/null'] * 15000 + ['herp'],
            b'herp:1:[INFO] info\n',
            expected_return_code=1,
        )


def _norm_pwd(path):
    # Under windows bash's temp and windows temp is different.
    # This normalizes to the bash /tmp
    return cmd_output(
        'bash', '-c', "cd '{0}' && pwd".format(path),
        encoding=None,
    )[1].strip()


@pytest.mark.integration
def test_cwd_of_hook(tempdir_factory, store):
    # Note: this doubles as a test for `system` hooks
    path = git_dir(tempdir_factory)
    with cwd(path):
        _test_hook_repo(
            tempdir_factory, store, 'prints_cwd_repo',
            'prints_cwd', ['-L'], _norm_pwd(path) + b'\n',
        )


@pytest.mark.integration
def test_lots_of_files(tempdir_factory, store):
    _test_hook_repo(
        tempdir_factory, store, 'script_hooks_repo',
        'bash_hook', ['/dev/null'] * 15000, mock.ANY,
    )


@pytest.fixture
def mock_repo_config():
    config = {
        'repo': 'git@github.com:pre-commit/pre-commit-hooks',
        'sha': '5e713f8878b7d100c0e059f8cc34be4fc2e8f897',
        'hooks': [{
            'id': 'pyflakes',
            'files': '\\.py$',
        }],
    }
    config_wrapped = apply_defaults([config], CONFIG_JSON_SCHEMA)
    validate_config_extra(config_wrapped)
    return config_wrapped[0]


def test_repo_url(mock_repo_config):
    repo = Repository(mock_repo_config, None)
    assert repo.repo_url == 'git@github.com:pre-commit/pre-commit-hooks'


def test_sha(mock_repo_config):
    repo = Repository(mock_repo_config, None)
    assert repo.sha == '5e713f8878b7d100c0e059f8cc34be4fc2e8f897'


@pytest.mark.integration
def test_languages(tempdir_factory, store):
    path = make_repo(tempdir_factory, 'python_hooks_repo')
    config = make_config_from_repo(path)
    repo = Repository.create(config, store)
    assert repo.languages == set([('python', 'default')])


@pytest.mark.integration
def test_additional_dependencies(tempdir_factory, store):
    path = make_repo(tempdir_factory, 'python_hooks_repo')
    config = make_config_from_repo(path)
    config['hooks'][0]['additional_dependencies'] = ['pep8']
    repo = Repository.create(config, store)
    assert repo.additional_dependencies['python']['default'] == set(('pep8',))


@pytest.mark.integration
def test_additional_python_dependencies_installed(tempdir_factory, store):
    path = make_repo(tempdir_factory, 'python_hooks_repo')
    config = make_config_from_repo(path)
    config['hooks'][0]['additional_dependencies'] = ['mccabe']
    repo = Repository.create(config, store)
    repo.require_installed()
    with python.in_env(repo.cmd_runner, 'default'):
        output = cmd_output('pip', 'freeze', '-l')[1]
        assert 'mccabe' in output


@pytest.mark.integration
def test_additional_dependencies_roll_forward(tempdir_factory, store):
    path = make_repo(tempdir_factory, 'python_hooks_repo')
    config = make_config_from_repo(path)
    # Run the repo once without additional_dependencies
    repo = Repository.create(config, store)
    repo.require_installed()
    # Now run it with additional_dependencies
    config['hooks'][0]['additional_dependencies'] = ['mccabe']
    repo = Repository.create(config, store)
    repo.require_installed()
    # We should see our additional dependency installed
    with python.in_env(repo.cmd_runner, 'default'):
        output = cmd_output('pip', 'freeze', '-l')[1]
        assert 'mccabe' in output


@skipif_slowtests_false
@xfailif_windows_no_ruby
@pytest.mark.integration
def test_additional_ruby_dependencies_installed(
        tempdir_factory, store,
):  # pragma: no cover (non-windows)
    path = make_repo(tempdir_factory, 'ruby_hooks_repo')
    config = make_config_from_repo(path)
    config['hooks'][0]['additional_dependencies'] = ['thread_safe']
    repo = Repository.create(config, store)
    repo.require_installed()
    with ruby.in_env(repo.cmd_runner, 'default'):
        output = cmd_output('gem', 'list', '--local')[1]
        assert 'thread_safe' in output


@skipif_slowtests_false
@xfailif_windows_no_node
@pytest.mark.integration
def test_additional_node_dependencies_installed(
        tempdir_factory, store,
):  # pragma: no cover (non-windows)
    path = make_repo(tempdir_factory, 'node_hooks_repo')
    config = make_config_from_repo(path)
    # Careful to choose a small package that's not depped by npm
    config['hooks'][0]['additional_dependencies'] = ['lodash']
    repo = Repository.create(config, store)
    repo.require_installed()
    with node.in_env(repo.cmd_runner, 'default'):
        cmd_output('npm', 'config', 'set', 'global', 'true')
        output = cmd_output('npm', 'ls')[1]
        assert 'lodash' in output


def test_reinstall(tempdir_factory, store, log_info_mock):
    path = make_repo(tempdir_factory, 'python_hooks_repo')
    config = make_config_from_repo(path)
    repo = Repository.create(config, store)
    repo.require_installed()
    # We print some logging during clone (1) + install (3)
    assert log_info_mock.call_count == 4
    log_info_mock.reset_mock()
    # Reinstall with same repo should not trigger another install
    repo.require_installed()
    assert log_info_mock.call_count == 0
    # Reinstall on another run should not trigger another install
    repo = Repository.create(config, store)
    repo.require_installed()
    assert log_info_mock.call_count == 0


def test_control_c_control_c_on_install(tempdir_factory, store):
    """Regression test for #186."""
    path = make_repo(tempdir_factory, 'python_hooks_repo')
    config = make_config_from_repo(path)
    repo = Repository.create(config, store)
    hook = repo.hooks[0][1]

    class MyKeyboardInterrupt(KeyboardInterrupt):
        pass

    # To simulate a killed install, we'll make PythonEnv.run raise ^C
    # and then to simulate a second ^C during cleanup, we'll make shutil.rmtree
    # raise as well.
    with pytest.raises(MyKeyboardInterrupt):
        with mock.patch.object(
            helpers, 'run_setup_cmd', side_effect=MyKeyboardInterrupt,
        ):
            with mock.patch.object(
                shutil, 'rmtree', side_effect=MyKeyboardInterrupt,
            ):
                repo.run_hook(hook, [])

    # Should have made an environment, however this environment is broken!
    assert os.path.exists(repo.cmd_runner.path('py_env-default'))

    # However, it should be perfectly runnable (reinstall after botched
    # install)
    retv, stdout, stderr = repo.run_hook(hook, [])
    assert retv == 0


@pytest.mark.integration
def test_really_long_file_paths(tempdir_factory, store):
    base_path = tempdir_factory.get()
    really_long_path = os.path.join(base_path, 'really_long' * 10)
    cmd_output('git', 'init', really_long_path)

    path = make_repo(tempdir_factory, 'python_hooks_repo')
    config = make_config_from_repo(path)

    with cwd(really_long_path):
        repo = Repository.create(config, store)
        repo.require_installed()


@pytest.mark.integration
def test_config_overrides_repo_specifics(tempdir_factory, store):
    path = make_repo(tempdir_factory, 'script_hooks_repo')
    config = make_config_from_repo(path)

    repo = Repository.create(config, store)
    assert repo.hooks[0][1]['files'] == ''
    # Set the file regex to something else
    config['hooks'][0]['files'] = '\\.sh$'
    repo = Repository.create(config, store)
    assert repo.hooks[0][1]['files'] == '\\.sh$'


def _create_repo_with_tags(tempdir_factory, src, tag):
    path = make_repo(tempdir_factory, src)
    with cwd(path):
        cmd_output('git', 'tag', tag)
    return path


@pytest.mark.integration
def test_tags_on_repositories(in_tmpdir, tempdir_factory, store):
    tag = 'v1.1'
    git_dir_1 = _create_repo_with_tags(tempdir_factory, 'prints_cwd_repo', tag)
    git_dir_2 = _create_repo_with_tags(
        tempdir_factory, 'script_hooks_repo', tag,
    )

    repo_1 = Repository.create(
        make_config_from_repo(git_dir_1, sha=tag), store,
    )
    ret = repo_1.run_hook(repo_1.hooks[0][1], ['-L'])
    assert ret[0] == 0
    assert ret[1].strip() == _norm_pwd(in_tmpdir)

    repo_2 = Repository.create(
        make_config_from_repo(git_dir_2, sha=tag), store,
    )
    ret = repo_2.run_hook(repo_2.hooks[0][1], ['bar'])
    assert ret[0] == 0
    assert ret[1] == b'bar\nHello World\n'


def test_local_repository():
    config = config_with_local_hooks()
    local_repo = Repository.create(config, 'dummy')
    with pytest.raises(NotImplementedError):
        local_repo.sha
    with pytest.raises(NotImplementedError):
        local_repo.manifest
    assert len(local_repo.hooks) == 1


@pytest.yield_fixture
def fake_log_handler():
    handler = mock.Mock(level=logging.INFO)
    logger = logging.getLogger('pre_commit')
    logger.addHandler(handler)
    yield handler
    logger.removeHandler(handler)


def test_hook_id_not_present(tempdir_factory, store, fake_log_handler):
    path = make_repo(tempdir_factory, 'script_hooks_repo')
    config = make_config_from_repo(path)
    config['hooks'][0]['id'] = 'i-dont-exist'
    repo = Repository.create(config, store)
    with pytest.raises(SystemExit):
        repo.install()
    assert fake_log_handler.handle.call_args[0][0].msg == (
        '`i-dont-exist` is not present in repository {0}.  '
        'Typo? Perhaps it is introduced in a newer version?  '
        'Often `pre-commit autoupdate` fixes this.'.format(path)
    )


def test_too_new_version(tempdir_factory, store, fake_log_handler):
    path = make_repo(tempdir_factory, 'script_hooks_repo')
    with modify_manifest(path) as manifest:
        manifest[0]['minimum_pre_commit_version'] = '999.0.0'
    config = make_config_from_repo(path)
    repo = Repository.create(config, store)
    with pytest.raises(SystemExit):
        repo.install()
    msg = fake_log_handler.handle.call_args[0][0].msg
    assert re.match(
        r'^The hook `bash_hook` requires pre-commit version 999\.0\.0 but '
        r'version \d+\.\d+\.\d+ is installed.  '
        r'Perhaps run `pip install --upgrade pre-commit`\.$',
        msg,
    )


@pytest.mark.parametrize(
    'version',
    ('0.1.0', pkg_resources.get_distribution('pre-commit').version),
)
def test_versions_ok(tempdir_factory, store, version):
    path = make_repo(tempdir_factory, 'script_hooks_repo')
    with modify_manifest(path) as manifest:
        manifest[0]['minimum_pre_commit_version'] = version
    config = make_config_from_repo(path)
    # Should succeed
    Repository.create(config, store).install()
