from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APIClient

from openslides.core.config import config
from openslides.users.models import Group, User
from openslides.utils.test import TestCase


class UserGetTest(TestCase):
    """
    Tests to receive a users via REST API.
    """
    def test_get_with_user_who_is_in_group_with_pk_1(self):
        """
        It is invalid, that a user is in the group with the pk 1. But if the
        database is invalid, the user should nevertheless be received.
        """
        admin = User.objects.get(pk=1)
        group1 = Group.objects.get(pk=1)
        admin.groups.add(group1)
        self.client.login(username='admin', password='admin')

        response = self.client.get('/rest/users/user/1/')

        self.assertEqual(response.status_code, 200)


class UserCreate(TestCase):
    """
    Tests creation of users via REST API.
    """
    def test_simple_creation(self):
        self.client.login(username='admin', password='admin')

        response = self.client.post(
            reverse('user-list'),
            {'last_name': 'Test name keimeiShieX4Aekoe3do'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username='Test name keimeiShieX4Aekoe3do')
        self.assertEqual(response.data['id'], new_user.id)

    def test_creation_with_group(self):
        self.client.login(username='admin', password='admin')
        # These are the builtin groups 'Delegates' and 'Staff'. The pks are valid.
        group_pks = (3, 4,)

        self.client.post(
            reverse('user-list'),
            {'last_name': 'Test name aedah1iequoof0Ashed4',
             'groups_id': group_pks})

        user = User.objects.get(username='Test name aedah1iequoof0Ashed4')
        self.assertTrue(user.groups.filter(pk=group_pks[0]).exists())
        self.assertTrue(user.groups.filter(pk=group_pks[1]).exists())

    def test_creation_with_anonymous_or_registered_group(self):
        self.client.login(username='admin', password='admin')
        # These are the builtin groups 'Anonymous' and 'Registered'.
        # The pks are valid. But these groups can not be added to users.
        group_pks = (1, 2,)

        response = self.client.post(
            reverse('user-list'),
            {'last_name': 'Test name aedah1iequoof0Ashed4',
             'groups_id': group_pks})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'groups_id': ["Invalid pk \"%d\" - object does not exist." % group_pks[0]]})


class UserUpdate(TestCase):
    """
    Tests update of users via REST API.
    """
    def test_simple_update_via_patch(self):
        """
        Test to only update the last_name with a patch request.

        The field username *should not* be changed by the request.
        """
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        # This is the builtin user 'Administrator' with username 'admin'. The pk is valid.
        user_pk = 1

        response = admin_client.patch(
            reverse('user-detail', args=[user_pk]),
            {'last_name': 'New name tu3ooh5Iez5Aec2laefo'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(pk=user_pk)
        self.assertEqual(user.last_name, 'New name tu3ooh5Iez5Aec2laefo')
        self.assertEqual(user.username, 'admin')

    def test_simple_update_via_put(self):
        """
        Test to only update the last_name with a put request.

        The field username *should* be changed by the request.
        """
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        # This is the builtin user 'Administrator'. The pk is valid.
        user_pk = 1

        response = admin_client.put(
            reverse('user-detail', args=[user_pk]),
            {'last_name': 'New name Ohy4eeyei5'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(pk=1).username, 'New name Ohy4eeyei5')

    def test_update_deactivate_yourselfself(self):
        """
        Tests that an user can not deactivate himself.
        """
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        # This is the builtin user 'Administrator'. The pk is valid.
        user_pk = 1

        response = admin_client.patch(
            reverse('user-detail', args=[user_pk]),
            {'username': 'admin',
             'is_active': False},
            format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserDelete(TestCase):
    """
    Tests delete of users via REST API.
    """
    def test_delete(self):
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        User.objects.create(username='Test name bo3zieT3iefahng0ahqu')

        response = admin_client.delete(reverse('user-detail', args=['2']))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(username='Test name bo3zieT3iefahng0ahqu').exists())

    def test_delete_yourself(self):
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        # This is the builtin user 'Administrator'. The pk is valid.
        admin_user_pk = 1

        response = admin_client.delete(reverse('user-detail', args=[admin_user_pk]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserResetPassword(TestCase):
    """
    Tests resetting users password via REST API by a manager.
    """
    def test_reset(self):
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        user = User.objects.create(username='Test name ooMoa4ou4mohn2eo1ree')
        user.default_password = 'new_password_Yuuh8OoQueePahngohy3'
        user.save()
        response = admin_client.post(
            reverse('user-reset-password', args=[user.pk]),
            {'password': 'new_password_Yuuh8OoQueePahngohy3_new'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(pk=user.pk).check_password(
            'new_password_Yuuh8OoQueePahngohy3_new'))

    def test_reset_to_default(self):
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        user = User.objects.create(username='Test name ooMoa4ou4mohn2eo1ree')
        user.default_password = 'new_password_Yuuh8OoQueePahngohy3'
        user.save()
        response = admin_client.post(
            reverse('user-reset-password', args=[user.pk]), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(pk=user.pk).check_password(
            'new_password_Yuuh8OoQueePahngohy3'))


class GroupReceive(TestCase):
    def test_get_groups_as_anonymous_deactivated(self):
        """
        Test to get the groups with an anonymous user, when they are deactivated.
        """
        response = self.client.get('/rest/users/group/')

        self.assertEqual(response.status_code, 403)

    def test_get_groups_as_anonymous_user_activated(self):
        """
        Test to get the groups with an anonymous user, when they are activated.
        """
        config['general_system_enable_anonymous'] = True

        response = self.client.get('/rest/users/group/')

        self.assertEqual(response.status_code, 200)

    def test_logged_in_user_with_no_permission(self):
        """
        Test to get the groups with an logged in user with no permissions.
        """
        user = User(username='test')
        user.set_password('test')
        user.save()
        registered_group = Group.objects.get(pk=2)
        registered_group.permissions.all().delete()
        self.client.login(username='test', password='test')

        response = self.client.get('/rest/users/group/')

        self.assertEqual(response.status_code, 200)


class GroupCreate(TestCase):
    """
    Tests creation of groups via REST API.
    """
    def test_creation(self):
        self.client.login(username='admin', password='admin')
        # This contains two valid permissions of the users app.
        permissions = ('users.can_see_name', 'users.can_see_extra_data')

        response = self.client.post(
            reverse('group-list'),
            {'name': 'Test name la8eephu9vaecheiKeif',
             'permissions': permissions})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group = Group.objects.get(name='Test name la8eephu9vaecheiKeif')
        for permission in permissions:
            app_label, codename = permission.split('.')
            self.assertTrue(group.permissions.get(content_type__app_label=app_label, codename=codename))

    def test_failed_creation_invalid_value(self):
        self.client.login(username='admin', password='admin')
        permissions = ('invalid_permission',)

        response = self.client.post(
            reverse('group-list'),
            {'name': 'Test name ool5aeb6Rai2aiLaith1',
             'permissions': permissions})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {'permissions': ['Incorrect value "invalid_permission". Expected app_label.codename string.']})

    def test_failed_creation_invalid_permission(self):
        self.client.login(username='admin', password='admin')
        permissions = ('invalid_app.invalid_permission',)

        response = self.client.post(
            reverse('group-list'),
            {'name': 'Test name wei2go2aiV3eophi9Ohg',
             'permissions': permissions})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {'permissions': ['Invalid permission "invalid_app.invalid_permission". Object does not exist.']})


class GroupUpdate(TestCase):
    """
    Tests update of groups via REST API.
    """
    def test_simple_update_via_patch(self):
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        # This is the builtin group 'Delegates'. The pk is valid.
        group_pk = 3
        # This contains one valid permission of the users app.
        permissions = ('users.can_see_name',)

        response = admin_client.patch(
            reverse('group-detail', args=[group_pk]),
            {'permissions': permissions})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group = Group.objects.get(pk=group_pk)
        for permission in permissions:
            app_label, codename = permission.split('.')
            self.assertTrue(group.permissions.get(content_type__app_label=app_label, codename=codename))

    def test_simple_update_via_put(self):
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        # This is the builtin group 'Delegates'. The pk is valid.
        group_pk = 3
        # This contains one valid permission of the users app.
        permissions = ('users.can_see_name',)

        response = admin_client.put(
            reverse('group-detail', args=[group_pk]),
            {'permissions': permissions})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'name': ['This field is required.']})


class GroupDelete(TestCase):
    """
    Tests delete of groups via REST API.
    """
    def test_delete(self):
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        group = Group.objects.create(name='Test name Koh4lohlaewoog9Ahsh5')

        response = admin_client.delete(reverse('group-detail', args=[group.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(name='Test name Koh4lohlaewoog9Ahsh5').exists())

    def test_delete_builtin_groups(self):
        admin_client = APIClient()
        admin_client.login(username='admin', password='admin')
        # The pks of builtin groups 'Anonymous' and 'Registered'
        group_pks = (1, 2,)

        for group_pk in group_pks:
            response = admin_client.delete(reverse('group-detail', args=[group_pk]))
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
