# -*- coding: utf-8 -*-
import copy
import os
from contextlib import contextmanager
from contextlib import nested

import mock
import pushmanager.core.git
import shutil
import tempfile
import testify as T
from pushmanager.core import db
from pushmanager.core.git import GitCommand
from pushmanager.core.git import GitException
from pushmanager.core.git import GitQueue
from pushmanager.core.git import GitTaskAction
from pushmanager.core.settings import Settings
from pushmanager.testing import testdb
from pushmanager.testing.mocksettings import MockedSettings


pushmanager_url = 'www.example.com'


class CoreGitTest(T.TestCase):

    @T.class_setup
    def setup_db(self):
        self.temp_git_dirs = []
        self.db_file = testdb.make_test_db()
        MockedSettings['db_uri'] = testdb.get_temp_db_uri(self.db_file)
        MockedSettings['irc'] = {
            "nickname": "pushhamster+test",
            "channel": "pushmanagertest"
        }
        with mock.patch.dict(db.Settings, MockedSettings):
            db.init_db()

    @T.setup
    def setup_fake_request_and_settings(self):
        self.fake_request = {
            'id': 1,
            'title': 'Test Push Request Title',
            'user': 'testuser',
            'tags': 'super-safe,logs',
            'revision': "0"*40,
            'reviewid': 9001,
            'state': 'requested',
            'repo': 'testuser',
            'branch': 'super_safe_fix',
            'comments': 'No comment',
            'description': 'I approve this fix!',
        }
        self.fake_settings = {
            'scheme': 'git',
            'auth': '',
            'port': '',
            'servername': 'example',
            'main_repository': 'main_repository',
            'dev_repositories_dir': 'dev_directory'
        }

    @T.class_teardown
    def cleanup_db(self):
        db.finalize_db()
        os.unlink(self.db_file)
        for temp_dir in self.temp_git_dirs:
            shutil.rmtree(temp_dir)

    @contextmanager
    def mocked_update_request(self, req, duplicate_req=None):
        with nested(
            mock.patch("%s.pushmanager.core.git.time" % __name__),
            mock.patch("%s.pushmanager.core.git.MailQueue" % __name__),
            mock.patch("%s.pushmanager.core.git.webhook_req" % __name__),
            mock.patch(
                "%s.pushmanager.core.git.GitQueue._get_branch_sha_from_repo" % __name__,
                return_value=req['revision']
            ),
            mock.patch(
                "%s.pushmanager.core.git.GitQueue._get_request" % __name__,
                return_value=req
            ),
            mock.patch(
                "%s.pushmanager.core.git.GitQueue._get_request_with_sha" % __name__,
                return_value=duplicate_req
            ),
        ):
            pushmanager.core.git.GitQueue.verify_branch(req['id'], 'http://example.com')
            yield

    def test_get_repository_uri_basic(self):
        MockedSettings["git"] = self.fake_settings
        with mock.patch.dict(Settings, MockedSettings):
            T.assert_equal(
                pushmanager.core.git.GitQueue._get_repository_uri("main_repository"),
                "git://example/main_repository"
            )
            T.assert_equal(
                pushmanager.core.git.GitQueue._get_repository_uri("second_repository"),
                "git://example/dev_directory/second_repository"
            )

    def test_get_repository_uri_with_auth(self):
        MockedSettings["git"] = self.fake_settings
        MockedSettings["git"]["auth"] = "myuser:mypass"
        with mock.patch.dict(Settings, MockedSettings):
            T.assert_equal(
                pushmanager.core.git.GitQueue._get_repository_uri("main_repository"),
                "git://myuser:mypass@example/main_repository"
            )
            T.assert_equal(
                pushmanager.core.git.GitQueue._get_repository_uri("second_repository"),
                "git://myuser:mypass@example/dev_directory/second_repository"
            )

    def test_get_repository_uri_with_port(self):
        MockedSettings["git"] = self.fake_settings
        MockedSettings["git"]["port"] = "0"
        with mock.patch.dict(Settings, MockedSettings):
            T.assert_equal(
                pushmanager.core.git.GitQueue._get_repository_uri("main_repository"),
                "git://example:0/main_repository"
            )
            T.assert_equal(
                pushmanager.core.git.GitQueue._get_repository_uri("second_repository"),
                "git://example:0/dev_directory/second_repository"
            )

    def test_process_queue_successful(self):
        """Update the request with its sha"""
        with nested(
            mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_failure" % __name__),
            mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_successful" % __name__),
            self.mocked_update_request(self.fake_request)
        ):
            # Successful call to update_request should trigger verify_branch_successful
            T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_failure.call_count, 0)
            T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_successful.call_count, 1)

        result = [None]

        def on_db_return(success, db_results):
            assert success, "Database error"
            result[0] = db_results.first()

        request_info_query = db.push_requests.select().where(
            db.push_requests.c.id == self.fake_request['id']
        )
        db.execute_cb(request_info_query, on_db_return)

        T.assert_equal(result[0][5], self.fake_request['revision'])

    def test_process_queue_req_with_str_id(self):
        """Update the request with its sha"""
        with nested(
            mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_failure" % __name__),
            mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_successful" % __name__),
            mock.patch("%s.pushmanager.core.git.time" % __name__),
            mock.patch("%s.pushmanager.core.git.MailQueue" % __name__),
            mock.patch("%s.pushmanager.core.git.webhook_req" % __name__),
            mock.patch(
                "%s.pushmanager.core.git.GitQueue._get_branch_sha_from_repo" % __name__,
                return_value=self.fake_request['revision']
            ),
            mock.patch(
                "%s.pushmanager.core.git.GitQueue._get_request" % __name__,
                return_value=self.fake_request
            ),
            mock.patch(
                "%s.pushmanager.core.git.GitQueue._get_request_with_sha" % __name__,
                return_value=self.fake_request
            ),
        ):
            pushmanager.core.git.GitQueue.verify_branch(str(self.fake_request['id']), 'http://example.com')
            T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_failure.call_count, 0)
            T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_successful.call_count, 1)

    def test_process_queue_duplicate(self):
        duplicate_req = copy.deepcopy(self.fake_request)
        duplicate_req['id'] = 11
        with nested(
            mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_failure" % __name__),
            mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_successful" % __name__),
            # This will fail, stop logging errors
            mock.patch("%s.pushmanager.core.git.logging.error" % __name__),
            mock.patch(
                "%s.pushmanager.core.git.GitQueue._get_request_with_sha" % __name__,
                return_value={'id': 10, 'state': 'requested'}
            ),
            self.mocked_update_request(self.fake_request, duplicate_req)
        ):
            # GitQueue._get_request_with_sha returning a value means
            # we have a duplicated request. This should trigger a
            # failure
            T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_failure.call_count, 1)
            T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_successful.call_count, 0)

            # Match the error message for duplicate revision. error_msg
            # should be the last item of the first call object's *args list
            # (from mock library).
            T.assert_in(
                "another request with the same revision sha",
                pushmanager.core.git.GitQueue.verify_branch_failure.call_args_list[0][0][1]
            )

    def test_update_duplicate_request_discarded(self):
        duplicate_req = copy.deepcopy(self.fake_request)
        duplicate_req['state'] = "discarded"
        with nested(
            mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_failure" % __name__),
            mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_successful" % __name__),
            self.mocked_update_request(self.fake_request, duplicate_req)
        ):
            T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_failure.call_count, 0)
            T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_successful.call_count, 1)

    def test_verify_branch(self):
        with mock.patch('pushmanager.core.git.GitCommand') as GC:
            GC.return_value = GC
            GC.run.return_value = (0, "hashashash", "")
            pushmanager.core.git.GitQueue.verify_branch(1, 'http://example.com')
            calls = [
                 mock.call('ls-remote', '-h', u'git://git.example.com/devs/bmetin', u'bmetin_fix_stuff'),
                 mock.call.run()
            ]
            GC.assert_has_calls(calls)

    def test_verify_branch_successful(self):
        with nested(
            mock.patch("%s.pushmanager.core.git.MailQueue.enqueue_user_email" % __name__),
            mock.patch("%s.pushmanager.core.git.webhook_req" % __name__)
        ):
            pushmanager.core.git.GitQueue.verify_branch_successful(self.fake_request, 'http://example.com')
            T.assert_equal(pushmanager.core.git.MailQueue.enqueue_user_email.call_count, 1)
            T.assert_equal(pushmanager.core.git.webhook_req.call_count, 3)

    def test_verify_branch_failure(self):
        with nested(
            mock.patch("%s.pushmanager.core.git.MailQueue.enqueue_user_email" % __name__),
            mock.patch("%s.pushmanager.core.git.webhook_req" % __name__),
            mock.patch("%s.pushmanager.core.git.logging.error" % __name__),
        ):
            pushmanager.core.git.GitQueue.verify_branch_failure(self.fake_request, "fake failure", 'http://example.com')
            T.assert_equal(pushmanager.core.git.MailQueue.enqueue_user_email.call_count, 1)

    def test_verify_branch_excluded_from_git_verification(self):
        for tag in pushmanager.core.git.GitQueue.EXCLUDE_FROM_GIT_VERIFICATION:
            req = copy.deepcopy(self.fake_request)
            req['branch'] = None
            req['tags'] = tag

            with nested(
                mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_failure" % __name__),
                mock.patch("%s.pushmanager.core.git.GitQueue.verify_branch_successful" % __name__),
                self.mocked_update_request(req)
            ):
                T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_failure.call_count, 0)
                T.assert_equal(pushmanager.core.git.GitQueue.verify_branch_successful.call_count, 0)

    def test_branch_context_manager_success(self):
        with mock.patch('pushmanager.core.git.GitCommand') as GC:
            GC.return_value = GC
            GC.run.return_value = (0, "hashashash", "")
            with pushmanager.core.git.git_branch_context_manager(
                    "name_of_test_branch",
                    "path_to_master_repo"):
                    pass
            calls = [
                mock.call('checkout', 'origin/master', '-b', 'name_of_test_branch', cwd='path_to_master_repo'),
                mock.call.run(),
                mock.call('checkout', 'master', cwd='path_to_master_repo'),
                mock.call.run(),
                mock.call('branch', '-D', 'name_of_test_branch', cwd='path_to_master_repo'),
                mock.call.run()
            ]
            GC.assert_has_calls(calls)

    def test_branch_context_manager_failure(self):
        with mock.patch('pushmanager.core.git.GitCommand') as GC:
            GC.return_value = GC
            GC.run.return_value = (0, "hashashash", "")
            with pushmanager.core.git.git_branch_context_manager(
                    "name_of_test_branch",
                    "path_to_master_repo"):
                    pass
            calls = [
                mock.call('checkout', 'origin/master', '-b', 'name_of_test_branch', cwd='path_to_master_repo'),
                mock.call.run(),
                mock.call('checkout', 'master', cwd='path_to_master_repo'),
                mock.call.run(),
                mock.call('branch', '-D', 'name_of_test_branch', cwd='path_to_master_repo'),
                mock.call.run()
            ]
            GC.assert_has_calls(calls)

    def test_merge_context_manager_success(self):
        with mock.patch('pushmanager.core.git.GitCommand') as GC:
            GC.return_value = GC
            GC.run.return_value = (0, "hashashash", "")
            with pushmanager.core.git.git_merge_context_manager(
                    "name_of_test_branch",
                    "path_to_master_repo"):
                    pass
            calls = [
                mock.call('rev-parse', 'name_of_test_branch', cwd='path_to_master_repo'),
                mock.call.run(),
                mock.call('reset', '--hard', 'hashashash', cwd='path_to_master_repo'),
                mock.call.run()
            ]
            GC.assert_has_calls(calls)

    def test_merge_context_manager_failure(self):
        with mock.patch('pushmanager.core.git.GitCommand') as GC:
            GC.return_value = GC
            GC.run.return_value = (0, "hashashash", "")
            try:
                with pushmanager.core.git.git_merge_context_manager(
                        "name_of_test_branch",
                        "path_to_master_repo"):
                        raise pushmanager.core.git.GitException("We tried to merge and it broke!")
            except Exception:
                pass

            calls = [
                mock.call('rev-parse', 'name_of_test_branch', cwd='path_to_master_repo'),
                mock.call.run(),
                mock.call('reset', '--hard', 'hashashash', cwd='path_to_master_repo'),
                mock.call.run()
            ]
            GC.assert_has_calls(calls)

    def test_git_reset_to_ref(self):
        with mock.patch('pushmanager.core.git.GitCommand') as GC:
            pushmanager.core.git.git_reset_to_ref('some_ref', 'git_dir')
            calls = [
                mock.call('reset', '--hard', 'some_ref', cwd='git_dir').run()
            ]
            GC.assert_has_calls(calls)

    def test_create_or_update_local_repo_master(self):
        expected_cwd = '/place/to/store/on-disk/git/repos/main-repository.0'
        with mock.patch('pushmanager.core.git.GitCommand') as GC:
            pushmanager.core.git.GitQueue.create_or_update_local_repo(
                0,
                Settings['git']['main_repository'],
                'test_branch',
                fetch=True,
            )
            calls = [
                mock.call('clone', 'git://git.example.com/main-repository', expected_cwd),
                mock.call().run(),
                mock.call('remote', 'add', 'origin', 'git://git.example.com/main-repository', cwd=expected_cwd),
                mock.call().run(),
                mock.call(
                    'fetch',
                    '--prune',
                    'origin',
                    '+refs/heads/test_branch:refs/remotes/origin/test_branch',
                    cwd=expected_cwd
                ),
                mock.call().run(),
                mock.call('reset', '--hard', 'HEAD', cwd=expected_cwd),
                mock.call().run(),
                mock.call('clean', '-fdfx', cwd=expected_cwd),
                mock.call().run(),
                mock.call('checkout', 'origin/test_branch', cwd=expected_cwd),
                mock.call().run(),
                mock.call('submodule', '--quiet', 'sync', cwd=expected_cwd),
                mock.call().run(),
                mock.call('submodule', '--quiet', 'update', '--init', cwd=expected_cwd),
                mock.call().run()
            ]
            GC.assert_has_calls(calls)

    def test_create_or_update_local_repo_dev(self):
        expected_cwd = '/place/to/store/on-disk/git/repos/main-repository.0'
        with mock.patch('pushmanager.core.git.GitCommand') as GC:
            pushmanager.core.git.GitQueue.create_or_update_local_repo(0, 'some_dev_name', 'test_branch', fetch=True)
            calls = [
                mock.call(
                    'clone',
                    'git://git.example.com/main-repository',
                    '/place/to/store/on-disk/git/repos/main-repository.0'
                ),
                mock.call().run(),
                mock.call(
                    'remote',
                    'add',
                    'some_dev_name',
                    'git://git.example.com/devs/some_dev_name',
                    cwd=expected_cwd
                ),
                mock.call().run(),
                mock.call(
                    'fetch',
                    '--prune',
                    'some_dev_name',
                    '+refs/heads/test_branch:refs/remotes/some_dev_name/test_branch',
                    cwd=expected_cwd
                ),
                mock.call().run(),
                mock.call('reset', '--hard', 'HEAD', cwd=expected_cwd),
                mock.call().run(),
                mock.call('clean', '-fdfx', cwd=expected_cwd),
                mock.call().run(),
                mock.call('checkout', 'some_dev_name/test_branch', cwd=expected_cwd),
                mock.call().run(),
                mock.call('submodule', '--quiet', 'sync', cwd=expected_cwd),
                mock.call().run(),
                mock.call('submodule', '--quiet', 'update', '--init', cwd=expected_cwd),
                mock.call().run(),
            ]
            GC.assert_has_calls(calls)

    def test_create_or_update_local_repo_master_integration(self):
        test_settings = copy.deepcopy(Settings)
        test_settings['git']['local_repo_path'] = tempfile.mkdtemp(prefix="pushmanager")
        self.temp_git_dirs.append(test_settings['git']['local_repo_path'])
        test_settings['git']['servername'] = "github.com"
        test_settings['git']['scheme'] = "https"
        test_settings['git']['main_repository'] = "Yelp/pushmanager/"
        with mock.patch.dict(Settings, test_settings, clear=True):
                pushmanager.core.git.GitQueue.create_or_update_local_repo(0, 'origin', 'master')

    def test_create_or_update_local_repo_with_reference(self):
        test_settings = copy.deepcopy(Settings)
        test_settings['git']['use_local_mirror'] = True
        test_settings['git']['local_mirror'] = '/'
        expected_cwd = '/place/to/store/on-disk/git/repos/main-repository.0'
        with mock.patch.dict(Settings, test_settings, clear=True):
            with mock.patch('pushmanager.core.git.GitCommand') as GC:
                pushmanager.core.git.GitQueue.create_or_update_local_repo(0, 'some_dev_name', 'test_branch', fetch=True)
                calls = [
                    mock.call('clone', 'git://git.example.com/main-repository', '--reference', '/', expected_cwd),
                    mock.call().run(),
                    mock.call(
                        'remote',
                        'add',
                        'some_dev_name',
                        'git://git.example.com/devs/some_dev_name',
                        cwd=expected_cwd
                    ),
                    mock.call().run(),
                    mock.call(
                        'fetch',
                        '--prune',
                        'some_dev_name',
                        '+refs/heads/test_branch:refs/remotes/some_dev_name/test_branch',
                        cwd=expected_cwd
                    ),
                    mock.call().run(),
                    mock.call('reset', '--hard', 'HEAD', cwd=expected_cwd),
                    mock.call().run(),
                    mock.call('clean', '-fdfx', cwd=expected_cwd),
                    mock.call().run(),
                    mock.call('checkout', 'some_dev_name/test_branch', cwd=expected_cwd),
                    mock.call().run(),
                    mock.call('submodule', '--quiet', 'sync', cwd=expected_cwd),
                    mock.call().run(),
                    mock.call('submodule', '--quiet', 'update', '--init', cwd=expected_cwd),
                    mock.call().run()
                ]
                GC.assert_has_calls(calls)

    def test_clear_pickme_conflict_details(self):
        GQ = pushmanager.core.git.GitQueue()
        sample_req = {
            'tags': 'asdasd,conflict-master,git-ok,conflict-pickme',
            'conflicts': 'This conflicts with everything!',
        }
        clean_req = {
            'tags': 'asdasd,git-ok',
            'conflicts': '',
        }
        with mock.patch('pushmanager.core.git.GitQueue._update_request') as update_req:
            GQ._clear_pickme_conflict_details(sample_req)
            update_req.assert_called_with(sample_req, clean_req)

    def test_pickme_conflict_pickme_integration_state_pickme(self):
        conflict, updated_request = self._pickme_conflict_pickme_integration('pickme')
        T.assert_equal(conflict, True)
        T.assert_equal('conflict-pickme' in updated_request[0][1]['tags'], True)
        T.assert_equal('Welsh' in updated_request[0][1]['conflicts'], True)

    def test_pickme_conflict_pickme_integration_state_added(self):
        conflict, updated_request = self._pickme_conflict_pickme_integration('added')
        T.assert_equal(conflict, True)
        T.assert_equal('conflict-pickme' in updated_request[0][1]['tags'], True)
        T.assert_equal('Welsh' in updated_request[0][1]['conflicts'], True)

    def test_pickme_conflict_pickme_integration_depickmed(self):
        conflict, _ = self._pickme_conflict_pickme_integration('accepted')
        T.assert_equal(conflict, False)

    def test_no_requeue_added_pickmes(self):
        added_request = copy.deepcopy(self.fake_request)
        added_request['state'] = 'added'
        added_request['tags'] = 'no-conflicts'
        pickme_request = copy.deepcopy(self.fake_request)
        pickme_request['state'] = 'pickme'
        pickme_request['tags'] = 'no-conflicts'
        with nested(
            mock.patch('pushmanager.core.git.GitQueue.create_or_update_local_repo'),
            mock.patch('pushmanager.core.git.GitQueue.git_merge_pickme'),
            mock.patch('pushmanager.core.git.git_branch_context_manager'),
            mock.patch('pushmanager.core.git.git_merge_context_manager'),
            mock.patch('pushmanager.core.git.GitQueue._get_request_ids_in_push'),
            mock.patch('pushmanager.core.git.GitQueue._get_request'),
            mock.patch('pushmanager.core.git.GitQueue.enqueue_request'),
            mock.patch('pushmanager.core.git.GitQueue._get_branch_sha_from_repo'),
            mock.patch('pushmanager.core.git.GitQueue._sha_exists_in_master'),
        ) as (update_repo, merge_pickme, branch_mgr, merge_mgr, ids_in_push,
              get_req, enqueue_req, get_sha, sha_in_master):

            def throw_gitexn(*args):
                raise GitException(
                    "GitException!",
                    gitret=1,
                    giterr="some_stderr_string",
                    gitout="some_stdout_string",
                )
            merge_mgr.side_effect = throw_gitexn
            ids_in_push.return_value = [2]
            get_req.return_value = pickme_request
            get_sha.return_code = 'some_sha'
            sha_in_master.return_value = False

            conflicts, _ = GitQueue._test_pickme_conflict_pickme(
                0,
                added_request,
                'some_test_branch',
                '/local/repo/path',
                pushmanager_url,
                True
            )
            assert conflicts is False
            enqueue_req.assert_has_calls([
                mock.call(GitTaskAction.TEST_PICKME_CONFLICT, 2, pushmanager_url=pushmanager_url, requeue=False)
            ])

    def _pickme_conflict_pickme_integration(self, request_state):
        test_settings = copy.deepcopy(Settings)
        repo_path = tempfile.mkdtemp(prefix="pushmanager")
        self.temp_git_dirs.append(repo_path)
        test_settings['git']['local_repo_path'] = repo_path

        # Create a repo with two conflicting branches
        GitCommand('init', test_settings['git']['local_repo_path'], cwd=repo_path).run()
        # Prevent Git complaints about names
        GitCommand('config', 'user.email', 'test@pushmanager', cwd=repo_path).run()
        GitCommand('config', 'user.name', 'pushmanager tester', cwd=repo_path).run()
        with open(os.path.join(repo_path, "code.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Hello World!")\nPrint("Goodbye!")\n')
        GitCommand('add', repo_path, cwd=repo_path).run()
        GitCommand('commit', '-a', '-m', 'Master Commit', cwd=repo_path).run()

        GitCommand('checkout', '-b', 'change_german', cwd=repo_path).run()
        with open(os.path.join(repo_path, "code.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Hallo Welt!")\nPrint("Goodbye!")\n')
        GitCommand('commit', '-a', '-m', 'verpflichten', cwd=repo_path).run()
        GitCommand('checkout', 'master', cwd=repo_path).run()
        german_req = {
            'id': 1,
            'state': request_state,
            'user': 'test',
            'tags': 'git-ok,no-conflicts',
            'title': 'German',
            'repo': '.',
            'branch': 'change_german'
        }

        GitCommand('checkout', '-b', 'change_welsh', cwd=repo_path).run()
        with open(os.path.join(repo_path, "code.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Helo Byd!")\nPrint("Goodbye!")\n')
        GitCommand('commit', '-a', '-m', 'ymrwymo', cwd=repo_path).run()
        GitCommand('checkout', 'master', cwd=repo_path).run()
        welsh_req = {
            'id': 2,
            'state': request_state,
            'user': 'test',
            'user': 'test',
            'tags': 'git-ok,no-conflicts',
            'title': 'Welsh',
            'repo': '.',
            'branch': 'change_welsh'
        }

        # Create a test branch for merging
        GitCommand('checkout', '-b', 'test_pcp', cwd=repo_path).run()

        # Merge on the first pickme
        with mock.patch('pushmanager.core.git.GitQueue.create_or_update_local_repo') as update_repo:
            pushmanager.core.git.GitQueue.git_merge_pickme(0, german_req, repo_path)
            update_repo.assert_called_with(0, '.', 'change_german', checkout=False)

        with nested(
                mock.patch('pushmanager.core.git.GitQueue._get_push_for_request'),
                mock.patch('pushmanager.core.git.GitQueue._get_request_ids_in_push'),
                mock.patch('pushmanager.core.git.GitQueue._get_request'),
                mock.patch('pushmanager.core.git.GitQueue._get_branch_sha_from_repo'),
                mock.patch('pushmanager.core.git.GitQueue._sha_exists_in_master'),
                mock.patch('pushmanager.core.git.GitQueue.create_or_update_local_repo'),
                mock.patch('pushmanager.core.git.GitQueue._update_request'),
                mock.patch.dict(Settings, test_settings, clear=True)
        ) as (p_for_r, r_in_p, get_req, get_sha, sha_exists, _, update_req, _):
            p_for_r.return_value = {'push': 1}
            r_in_p.return_value = [1, 2]
            get_req.return_value = welsh_req
            get_sha.return_value = "0"*40
            sha_exists.return_value = False
            update_req.return_value = german_req
            conflict, _ = pushmanager.core.git.GitQueue._test_pickme_conflict_pickme(
                0,
                german_req,
                "test_pcp",
                repo_path,
                pushmanager_url,
                False
            )
            return (conflict, update_req.call_args)

    def test_pickme_conflict_master_integration(self):
        test_settings = copy.deepcopy(Settings)
        repo_path = tempfile.mkdtemp(prefix="pushmanager")
        self.temp_git_dirs.append(repo_path)
        test_settings['git']['local_repo_path'] = repo_path

        # Create a repo
        GitCommand('init', test_settings['git']['local_repo_path'], cwd=repo_path).run()
        # Prevent Git complaints about names
        GitCommand('config', 'user.email', 'test@pushmanager', cwd=repo_path).run()
        GitCommand('config', 'user.name', 'pushmanager tester', cwd=repo_path).run()
        with open(os.path.join(repo_path, "code.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Hello World!")\nPrint("Goodbye!")\n')
        GitCommand('add', repo_path, cwd=repo_path).run()
        GitCommand('commit', '-a', '-m', 'Master Commit', cwd=repo_path).run()

        # Branch master, commit a change
        GitCommand('checkout', '-b', 'change_german', cwd=repo_path).run()
        with open(os.path.join(repo_path, "code.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Hallo Welt!")\nPrint("Goodbye!")\n')
        GitCommand('commit', '-a', '-m', 'verpflichten', cwd=repo_path).run()
        german_req = {'id': 1, 'tags': 'git-ok', 'title': 'German', 'repo': '.', 'branch': 'change_german'}

        # Back on master, make a conflicting change
        GitCommand('checkout', 'master', cwd=repo_path).run()
        with open(os.path.join(repo_path, "code.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Helo Byd!")\nPrint("Goodbye!")\n')
        GitCommand('commit', '-a', '-m', 'ymrwymo', cwd=repo_path).run()

        class NoRemoteBranchContextManager(object):
            # The real branch context manager uses remote names as part
            # of the branch spec, for testing we don't have remotes.
            def __init__(self, branch, path):
                self.branch = branch
                self.path = path

            def __enter__(self):
                GitCommand('checkout', '-b', self.branch, cwd=self.path).run()

            def __exit__(self, *args):
                pass

        with nested(
                mock.patch('pushmanager.core.git.GitQueue._update_request'),
                mock.patch(
                    'pushmanager.core.git.git_branch_context_manager',
                    NoRemoteBranchContextManager
                ),
                mock.patch('pushmanager.core.git.GitQueue.create_or_update_local_repo'),
                mock.patch.dict(Settings, test_settings, clear=True)
        ) as (update_req, _, _, _):
            conflict, _ = pushmanager.core.git.GitQueue._test_pickme_conflict_master(
                0,
                german_req,
                "test_pcm",
                repo_path,
                pushmanager_url,
                False
            )
            T.assert_equal(conflict, True)
            updated_request = update_req.call_args
            T.assert_equal('conflict-master' in updated_request[0][1]['tags'], True)
            T.assert_equal('master' in updated_request[0][1]['conflicts'], True)

    def test_requeue_pickmes_with_conflicts(self):
        with nested(
            mock.patch.object(GitQueue, '_get_request_ids_in_push'),
            mock.patch.object(GitQueue, '_get_request'),
            mock.patch.object(GitQueue, 'enqueue_request')
        ) as (ids_in_push, get_req, enqueue_req):

            reqs = [
                {'id': 1, 'tags': 'git-ok,conflict-pickme'},
                {'id': 2, 'tags': 'git-ok,conflict-master'},
                {'id': 3, 'tags': 'git-ok,feature'}
            ]

            ids_in_push.return_value = [0, 1, 2]
            get_req.return_value = reqs[0]

            def update_get_req(i):
                return reqs[i]

            get_req.side_effect = update_get_req

            pushmanager.core.git.GitQueue.requeue_pickmes_for_push(1, pushmanager_url, conflicting_only=True)

            calls = [mock.call(GitTaskAction.TEST_PICKME_CONFLICT, 1, pushmanager_url=pushmanager_url, requeue=False)]

            enqueue_req.assert_has_calls(calls)

    def test_requeue_all_pickmes(self):
        with nested(
            mock.patch.object(GitQueue, '_get_request_ids_in_push'),
            mock.patch.object(GitQueue, '_get_request'),
            mock.patch.object(GitQueue, 'enqueue_request')
        ) as (ids_in_push, get_req, enqueue_req):

            reqs = [
                {'id': 1, 'tags': 'git-ok,conflict-pickme'},
                {'id': 2, 'tags': 'git-ok,conflict-master'},
                {'id': 3, 'tags': 'git-ok,feature'}
            ]

            ids_in_push.return_value = [0, 1, 2]
            get_req.return_value = reqs[0]

            def update_get_req(i):
                return reqs[i]

            get_req.side_effect = update_get_req

            pushmanager.core.git.GitQueue.requeue_pickmes_for_push(1, pushmanager_url)

            calls = [
                mock.call(GitTaskAction.TEST_PICKME_CONFLICT, 1, pushmanager_url=pushmanager_url, requeue=False),
                mock.call(GitTaskAction.TEST_PICKME_CONFLICT, 2, pushmanager_url=pushmanager_url, requeue=False),
                mock.call(GitTaskAction.TEST_PICKME_CONFLICT, 3, pushmanager_url=pushmanager_url, requeue=False),
            ]

            enqueue_req.assert_has_calls(calls)

    def test_stale_module_check(self):
        test_settings = copy.deepcopy(Settings)
        repo_path = tempfile.mkdtemp(prefix="pushmanager")
        submodule_path = tempfile.mkdtemp(prefix="pushmanager")
        self.temp_git_dirs.append(repo_path)
        self.temp_git_dirs.append(submodule_path)
        test_settings['git']['local_repo_path'] = repo_path

        # Create main repo
        GitCommand('init', repo_path, cwd=repo_path).run()
        # Prevent Git complaints about names
        GitCommand('config', 'user.email', 'test@pushmanager', cwd=repo_path).run()
        GitCommand('config', 'user.name', 'pushmanager tester', cwd=repo_path).run()
        with open(os.path.join(repo_path, "code.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Hello World!")\nPrint("Goodbye!")\n')
        GitCommand('add', repo_path, cwd=repo_path).run()
        GitCommand('commit', '-a', '-m', 'Master Commit', cwd=repo_path).run()

        # Create repo to use as submodule
        GitCommand('init', submodule_path, cwd=submodule_path).run()
        # Prevent Git complaints about names
        GitCommand('config', 'user.email', 'test@pushmanager', cwd=submodule_path).run()
        GitCommand('config', 'user.name', 'pushmanager tester', cwd=submodule_path).run()
        with open(os.path.join(submodule_path, "codemodule.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Hello World!")\nPrint("Goodbye!")\n')
        GitCommand('add', submodule_path, cwd=submodule_path).run()
        GitCommand('commit', '-a', '-m', 'Master Commit', cwd=submodule_path).run()

        # Make two incompatible branches in the submodule
        GitCommand('checkout', '-b', 'change_german', cwd=submodule_path).run()
        with open(os.path.join(submodule_path, "codemodule.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Hallo Welt!")\nPrint("Goodbye!")\n')
        GitCommand('commit', '-a', '-m', 'verpflichten', cwd=submodule_path).run()
        GitCommand('checkout', 'master', cwd=submodule_path).run()

        GitCommand('checkout', '-b', 'change_welsh', cwd=submodule_path).run()
        with open(os.path.join(submodule_path, "codemodule.py"), 'w') as f:
            f.write('#!/usr/bin/env python\n\nprint("Helo Byd!")\nPrint("Goodbye!")\n')
        GitCommand('commit', '-a', '-m', 'ymrwymo', cwd=submodule_path).run()
        GitCommand('checkout', 'master', cwd=submodule_path).run()

        # Add submodule at master to main repo
        GitCommand('submodule', 'add', submodule_path, cwd=repo_path).run()
        GitCommand('commit', '-a', '-m', 'Add submodule', cwd=repo_path).run()

        # Create branches in main repo, have each switch submodule to different branch
        internal_submodule_path = os.path.join(repo_path, submodule_path.split("/")[-1:][0])
        GitCommand('checkout', '-b', 'change_german', cwd=repo_path).run()
        GitCommand('checkout', 'change_german', cwd=internal_submodule_path).run()
        GitCommand('commit', '-a', '-m', 'verpflichten', cwd=repo_path).run()
        GitCommand('checkout', 'master', cwd=repo_path).run()

        GitCommand('checkout', '-b', 'change_welsh', cwd=repo_path).run()
        GitCommand('commit', '-a', '-m', 'ymrwymo', cwd=repo_path).run()
        GitCommand('checkout', 'change_welsh', cwd=internal_submodule_path).run()
        GitCommand('checkout', 'master', cwd=repo_path).run()

        T.assert_raises(GitException, pushmanager.core.git._stale_submodule_check, repo_path)

    def test_update_req_sha_and_queue_pickme_requested(self):
        new_sha = "1"*40
        request = copy.deepcopy(self.fake_request)
        request['state'] = 'requested'
        with mock.patch('pushmanager.core.git.GitQueue.enqueue_request') as enqueue_req:
            GitQueue._update_req_sha_and_queue_pickme(request, new_sha)

            result = [None]

            def on_db_return(success, db_results):
                assert success, "Database error"
                result[0] = db_results.first()

            request_info_query = db.push_requests.select().where(
                db.push_requests.c.id == self.fake_request['id']
            )
            db.execute_cb(request_info_query, on_db_return)
            T.assert_equals(enqueue_req.call_count, 1)
            T.assert_equal(result[0][5], new_sha)

    def test_update_req_sha_and_queue_pickme_pickme_test_pickme_conflict(self):
        new_sha = "1"*40
        pickme_request = copy.deepcopy(self.fake_request)
        pickme_request['state'] = 'pickme'
        pickme_request['tags'] = 'no-conflicts'
        with mock.patch('pushmanager.core.git.GitQueue.enqueue_request') as enqueue_req:
            with mock.patch.dict(Settings, MockedSettings):
                GitQueue._update_req_sha_and_queue_pickme(pickme_request, new_sha)

                result = [None]

                def on_db_return(success, db_results):
                    assert success, "Database error"
                    result[0] = db_results.first()

                request_info_query = db.push_requests.select().where(
                    db.push_requests.c.id == self.fake_request['id']
                )
                db.execute_cb(request_info_query, on_db_return)
                T.assert_equal(result[0][5], new_sha)
                T.assert_equals(enqueue_req.call_count, 2)
                enqueue_req.assert_has_calls([
                    mock.call(
                        GitTaskAction.TEST_PICKME_CONFLICT,
                        1,
                        pushmanager_url='https://%s:%s' % (
                            MockedSettings['main_app']['servername'],
                            MockedSettings['main_app']['port']
                        )
                    )
                ])

    def test_update_req_sha_and_queue_pickme_added_test_conflicting_pickmes(self):
        new_sha = "1"*40
        pickme_request = copy.deepcopy(self.fake_request)
        pickme_request['state'] = 'added'
        pickme_request['tags'] = 'conflict-pickme'
        with mock.patch('pushmanager.core.git.GitQueue.enqueue_request') as enqueue_req:
            with mock.patch.dict(Settings, MockedSettings):
                GitQueue._update_req_sha_and_queue_pickme(pickme_request, new_sha)

                result = [None]

                def on_db_return(success, db_results):
                    assert success, "Database error"
                    result[0] = db_results.first()

                request_info_query = db.push_requests.select().where(
                    db.push_requests.c.id == self.fake_request['id']
                )
                db.execute_cb(request_info_query, on_db_return)
                T.assert_equal(result[0][5], new_sha)
                T.assert_equals(enqueue_req.call_count, 2)
                enqueue_req.assert_has_calls([
                    mock.call(
                        GitTaskAction.TEST_CONFLICTING_PICKMES,
                        GitQueue._get_push_for_request(pickme_request['id'])['push'],
                        pushmanager_url='https://%s:%s' % (
                            MockedSettings['main_app']['servername'],
                            MockedSettings['main_app']['port'])
                        )
                ])

    def test_stderr_and_stdout_in_conflict_text(self):
        welsh_req = {
            'id': 2,
            'user': 'test',
            'tags': 'git-ok',
            'title': 'Welsh',
            'repo': '.',
            'branch': 'change_welsh',
        }
        with nested(
            mock.patch('pushmanager.core.git.GitQueue.create_or_update_local_repo'),
            mock.patch('pushmanager.core.git.GitQueue.git_merge_pickme'),
            mock.patch('pushmanager.core.git.git_branch_context_manager'),
            mock.patch('pushmanager.core.git.git_merge_context_manager'),
        ) as (update_repo, merge_pickme, branch_mgr, merge_mgr):

            def throw_gitexn(*args):
                raise GitException(
                    "GitException!",
                    gitret=1,
                    giterr="some_stderr_string",
                    gitout="some_stdout_string",
                )
            merge_mgr.side_effect = throw_gitexn

            (conflict, details) = GitQueue._test_pickme_conflict_master(
                0,
                welsh_req,
                'testing_pickme_branch',
                '/local/repo/path/',
                pushmanager_url,
                False
            )

            assert conflict is True
            assert "some_stderr_string" in details['conflicts']
            assert "some_stdout_string" in details['conflicts']
