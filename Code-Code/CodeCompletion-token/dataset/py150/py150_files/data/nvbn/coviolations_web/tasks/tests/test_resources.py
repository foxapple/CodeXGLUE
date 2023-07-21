import sure
from django.contrib.auth.models import User
from tastypie.test import ResourceTestCase
from projects.tests.factories import ProjectFactory
from tools.mongo import MongoFlushMixin
from tools.tests import MockGithubMixin
from .. import models, const


class BaseTaskResourceCase(MockGithubMixin, MongoFlushMixin, ResourceTestCase):
    """Base task resource case"""
    mongo_flush = ['tasks']

    def setUp(self):
        super(BaseTaskResourceCase, self).setUp()
        self.project = ProjectFactory(name='test', is_enabled=True)

    def _create_task(self, project='test', seed=0, **kwargs):
        """Create single task"""
        defaults = dict(
            service={
                'name': 'dummy',
            },
            project=project,
            status=const.STATUS_SUCCESS,
            commit={
                'branch': 'develop',
                'commit': 'asdfg',
                'author': 'nvbn',
            },
            violations=[{
                'name': 'dummy',
                'raw': '1',
                'status': 1,
                'prepared': '123{}'.format(seed),
            }],
        )
        defaults.update(kwargs)
        return models.Tasks.save(defaults)


class RawTaskResourceCase(BaseTaskResourceCase):
    """Create task case"""

    def setUp(self):
        super(RawTaskResourceCase, self).setUp()
        self.url = '/api/v1/tasks/raw/'

    def test_create_on_post(self):
        """Test create on post"""
        self.api_client.post(self.url, data={
            'service': {
                'name': 'dummy',
            },
            'project': 'test',
            'commit': {
                'branch': 'develop',
                'commit': 'asdfg',
                'author': 'nvbn',
            },
            'violations': [
                {'name': 'dummy', 'raw': '1'},
            ]
        })
        models.Tasks.count().should.be.equal(1)

    def test_error_on_wrong_service(self):
        """Test error on wrong service"""
        response = self.api_client.post(self.url, data={
            'service': {
                'name': 'dummy!!!',
            },
            'project': 'test',
            'commit': {
                'branch': 'develop',
                'commit': 'asdfg',
                'author': 'nvbn',
            },
            'violations': [
                {'name': 'dummy', 'raw': '1'},
            ]
        })
        response.status_code.should.be.equal(404)

    def test_error_on_wrong_project(self):
        """Test error on wrong project"""
        response = self.api_client.post(self.url, data={
            'service': {
                'name': 'dummy',
            },
            'project': 'test!!',
            'commit': {
                'branch': 'develop',
                'commit': 'asdfg',
                'author': 'nvbn',
            },
            'violations': [
                {'name': 'dummy', 'raw': '1'},
            ]
        })
        response.status_code.should.be.equal(404)

    def test_has_url_to_status_on_post(self):
        """Test has url to status on post"""
        response = self.api_client.post(self.url, data={
            'service': {
                'name': 'dummy',
            },
            'project': 'test',
            'commit': {
                'branch': 'develop',
                'commit': 'asdfg',
                'author': 'nvbn',
            },
            'violations': [
                {'name': 'dummy', 'raw': '1'},
            ]
        })
        data = self.deserialize(response)
        'tasks/status'.should.be.within(data['resource_uri'])


class TaskResourceCase(BaseTaskResourceCase):
    """Get tasks resource case"""

    def setUp(self):
        super(TaskResourceCase, self).setUp()
        self.url = '/api/v1/tasks/task/'

    def _create_tasks(self, project='test', count=20, **kwargs):
        """Create tasks"""
        return [
            self._create_task(project, n, **kwargs) for n in range(count)
        ]

    def _create_user(self):
        """Create user"""
        user = User.objects.create_user('test', 'test@test.test', 'test')
        self.api_client.client.login(
            username='test',
            password='test',
        )
        return user

    def test_get_all(self):
        """Test get all"""
        self._create_tasks()
        response = self.api_client.get(self.url)
        data = self.deserialize(response)
        data['meta']['total_count'].should.be.equal(20)
        data['objects'][0]['violations'].should.be.none

    def test_get_all_with_violations(self):
        """Test get all with violations"""
        self._create_tasks()
        response = self.api_client.get('{}?with_violations=1'.format(self.url))
        data = self.deserialize(response)
        data['objects'][0]['violations'][0]['name'].should.be.ok
        data['objects'][0]['violations'][0]['status'].should.be.ok

    def test_get_with_full_violations(self):
        """Test get with full violations"""
        self._create_tasks()
        response = self.api_client.get(
            '{}?with_full_violations=1'.format(self.url),
        )
        data = self.deserialize(response)
        data['objects'][0]['violations'][0]['raw'].should.be.ok
        data['objects'][0]['violations'][0]['prepared'].should.be.ok

    def test_filter_by_project(self):
        """Test filter by project"""
        self._create_tasks('test', 5)
        self._create_tasks('nope', 10)
        response = self.api_client.get('{}?project=test'.format(self.url))
        data = self.deserialize(response)
        data['meta']['total_count'].should.be.equal(5)

    def test_owner_access_private(self):
        """Test owner access private"""
        user = self._create_user()
        ProjectFactory(owner=user, is_private=True, name='test')
        self._create_tasks(is_private=True, allowed_users=[user.id])
        response = self.api_client.get(self.url)
        data = self.deserialize(response)
        data['meta']['total_count'].should.be.equal(20)

    def test_organization_member_access_private(self):
        """Test organization member access private"""
        user = self._create_user()
        project = ProjectFactory(
            owner=user, is_private=True,
            name='test', organization__users=[user],
        )
        self._create_tasks(
            is_private=True, organization=project.organization.id,
        )
        response = self.api_client.get(self.url)
        data = self.deserialize(response)
        data['meta']['total_count'].should.be.equal(20)

    def test_other_user_cant_access_private(self):
        """Test other user cant access private"""
        user = self._create_user()
        ProjectFactory(
            owner=user, is_private=True, name='test',
        )
        self._create_tasks(is_private=True)
        response = self.api_client.get(self.url)
        data = self.deserialize(response)
        data['meta']['total_count'].should.be.equal(0)

    def test_get_single_task(self):
        """Test get single task"""
        task = self._create_task()
        response = self.api_client.get('{}{}/'.format(self.url, task))
        response.status_code.should.be.equal(200)

    def test_404_when_task_without_project(self):
        """Test 404 when task without project"""
        task = self._create_task('not exists')
        response = self.api_client.get('{}{}/'.format(self.url, task))
        response.status_code.should.be.equal(404)

    def test_404_if_not_accessible(self):
        """Test 404 if not accessible"""
        self.project.is_private = True
        self.project.save()
        task = self._create_task()
        response = self.api_client.get('{}{}/'.format(self.url, task))
        response.status_code.should.be.equal(404)

    def test_filter_by_author(self):
        """Test filter tasks by author"""
        for _ in range(5):
            self._create_task(commit={'author': 'cat'})
        for _ in range(10):
            self._create_task(commit={'author': 'dog'})
        response = self.api_client.get('{}?author=cat'.format(self.url))
        response.status_code.should.be.equal(200)
        data = self.deserialize(response)
        data['meta']['total_count'].should.be.equal(5)


class TaskStatusResourceCase(BaseTaskResourceCase):
    """Task status resource case"""

    def setUp(self):
        super(TaskStatusResourceCase, self).setUp()
        self.url = '/api/v1/tasks/status/'

    def test_can_get_task_status(self):
        """Test can get task status"""
        task = self._create_task(status=const.STATUS_FAILED)
        response = self.api_client.get('{}{}/'.format(self.url, task))
        response.status_code.should.be.equal(200)
        data = self.deserialize(response)
        data['status'].should.be.equal(const.STATUS_FAILED)

    def test_cant_list_task_statuses(self):
        """Test can't list task statuses"""
        response = self.api_client.get(self.url)
        response.status_code.should.be.equal(405)
