from django.test import TestCase
from django.core.urlresolvers import reverse
from model_mommy import mommy
from offers.models import Comment
from captcha.models import CaptchaStore
from ..models import User


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.client.login(username='some_user', password='password')

    def test_logged_in_user_can_logout(self):
        """
        Tests that a logged in user can log out and is redirected to the login page
        """
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][0], 'http://testserver' + reverse('login'))
        self.assertEqual(response.redirect_chain[0][1], 302)

    def test_logged_out_user_can_logout(self):
        """
        Test that a logged out user can still view the logout page and will be redirected to the login form
        """
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][0], 'http://testserver' + reverse('login'))
        self.assertEqual(response.redirect_chain[0][1], 302)


class SelfProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.user.save()
        self.client.login(username='some_user', password='password')

    def test_can_view_own_profile(self):
        """
        Test that the user can view their own profile when they are logged in
        """
        response = self.client.get(reverse('self_profile'))

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Joe')
        self.assertContains(response, 'Bill')
        self.assertContains(response, 'some_user')

    def test_can_not_view_profile_when_logged_out(self):
        """
        Test that the user can not view the profile page when logged out
        """
        self.client.logout()

        response = self.client.get(reverse('self_profile'), follow=True)

        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(reverse('login') in response.redirect_chain[0][0])
        self.assertEqual(response.redirect_chain[0][1], 302)


class OtherUserViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.comments = mommy.make(Comment, commenter=self.user, _quantity=20)
        self.user.save()

    def test_can_view_other_user_profile(self):
        """
        Test that another user's profile can be viewed
        """
        response = self.client.get(reverse('profile', args=[self.user.username]))

        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.username + '\'s Profile')

    def test_profile_page_contains_first_5_comments(self):
        """
        Test that the profile page contains only the first 5 comments
        """
        response = self.client.get(reverse('profile', args=[self.user.username]))

        for comment in self.comments[15:20]:
            self.assertContains(response, comment.content)

        for comment in self.comments[0:15]:
            self.assertNotContains(response, comment.content)

    def test_profile_second_page_contains_next_5_comments(self):
        """
        Test that the next profile page contains the next 5 comments
        """
        response = self.client.get(reverse('profile', args=[self.user.username]) + '?page=2')

        for comment in self.comments[10:15]:
            self.assertContains(response, comment.content)

        for comment in self.comments[0:10]:
            self.assertNotContains(response, comment.content)

        for comment in self.comments[15:20]:
            self.assertNotContains(response, comment.content)

    def test_profile_page_with_large_page_number(self):
        """
        Test that a profile page with a page number greater than the highest page gets the last page
        """
        response = self.client.get(reverse('profile', args=[self.user.username]) + '?page=10')

        for comment in self.comments[0:5]:
            self.assertContains(response, comment.content)

        for comment in self.comments[5:20]:
            self.assertNotContains(response, comment.content)


class AuthenticatedOtherUserViewTests(OtherUserViewTests):
    def setUp(self):
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.comments = mommy.make(Comment, commenter=self.user, _quantity=20)
        self.user.save()

        self.client.login(username='some_user', password='password')


class EditAccountViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.user.save()
        self.client.login(username='some_user', password='password')

    def test_can_view_edit_form(self):
        """
        Test that a user can view their own edit page
        """
        response = self.client.get(reverse('edit_account'))
        self.assertEqual(response.status_code, 200)

    def test_logged_out_user_can_not_view_edit_form(self):
        """
        Test that a logged out user can not view the edit form of a profile.
        """
        self.client.logout()

        response = self.client.get(reverse('edit_account'), follow=True)

        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(reverse('login') in response.redirect_chain[0][0])
        self.assertEqual(response.redirect_chain[0][1], 302)

    def test_form_updates_user_correctly(self):
        """
        Test that posting the form data correctly updates the user
        """
        data = {
            "first_name": "New_name",
            "last_name": "Last_name",
            "email": "test2@example.com",
        }
        response = self.client.post(reverse('edit_account'), data)

        user = User.objects.get(pk=self.user.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.first_name, data["first_name"])
        self.assertEqual(user.last_name, data["last_name"])
        self.assertEqual(user.email, data["email"])

        self.assertContains(response, 'You account has been successfully updated!')

    def test_form_incorrect_does_not_update_user(self):
        """
        Test that posting incorrect form data will not update the user
        """
        data = {
            "first_name": "",  # Empty name
            "last_name": "Last_name",
            "email": "test2@example",  # Invalid email
        }
        response = self.client.post(reverse('edit_account'), data)

        user = User.objects.get(pk=self.user.pk)

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(user.first_name, data["first_name"])
        self.assertNotEqual(user.last_name, data["last_name"])
        self.assertNotEqual(user.email, data["email"])

        self.assertEqual(user.first_name, self.user.first_name)
        self.assertEqual(user.last_name, self.user.last_name)
        self.assertEqual(user.email, self.user.email)

        self.assertContains(response, 'The form had errors. Please correct them and submit again.')


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.user.save()
        self.client.login(username='some_user', password='password')

    def test_can_view_change_password_form(self):
        """
        Test that a user can view their own change password page
        """
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)

    def test_logged_out_user_can_not_view_change_password_form(self):
        """
        Test that a logged out user can not view the change password form
        """
        self.client.logout()

        response = self.client.get(reverse('change_password'), follow=True)

        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(reverse('login') in response.redirect_chain[0][0])
        self.assertEqual(response.redirect_chain[0][1], 302)

    def test_can_change_password(self):
        """
        Test that a user can change their password using the password
        """

        data = {
            "new_password1": 'new_password',
            "new_password2": "new_password",
            "old_password": "password",
        }
        response = self.client.post(reverse('change_password'), data)

        user = User.objects.get(pk=self.user.pk)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You password has been changed!")
        self.assertNotEqual(user.password, self.user.password)

    def test_cant_change_password_with_incorrect_old_password(self):
        """
        Test that the user can not change their password if their old password is not correct
        """
        data = {
            "new_password1": 'new_password',
            "new_password2": "new_password",
            "old_password": "wrong_password",
        }
        response = self.client.post(reverse('change_password'), data)

        user = User.objects.get(pk=self.user.pk)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            'form',
            'old_password',
            'Your old password was entered incorrectly. Please enter it again.',
        )
        self.assertEqual(user.password, self.user.password)

    def test_cant_change_password_with_incorrect_matching_passwords(self):
        """
        Test that the user can not change their password if the two new passwords provided did not match
        """
        data = {
            "new_password1": 'new_password',
            "new_password2": "new_password_wrong",
            "old_password": "password",
        }
        response = self.client.post(reverse('change_password'), data)

        user = User.objects.get(pk=self.user.pk)

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            'form',
            'new_password2',
            'The two password fields didn\'t match.',
        )
        self.assertEqual(user.password, self.user.password)


class DeactivateAccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.user.save()
        self.client.login(username='some_user', password='password')

    def test_can_view_deactivate_account_form(self):
        """
        Test that a user can view their own deactivate account page
        """
        response = self.client.get(reverse('deactivate_account'))
        self.assertEqual(response.status_code, 200)

    def test_logged_out_user_can_not_view_deactivate_account_form(self):
        """
        Test that a logged out user can not view the deactivate account page
        """
        self.client.logout()

        response = self.client.get(reverse('deactivate_account'), follow=True)

        self.assertEqual(200, response.status_code)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(reverse('login') in response.redirect_chain[0][0])
        self.assertEqual(response.redirect_chain[0][1], 302)

    def test_user_can_deactivate_their_own_account(self):
        """
        Test that a user can deactivate their own account with the correct account data
        """

        self.assertTrue(self.user.is_active)

        data = {
            "username": 'some_user',
            "password": "password",
        }
        response = self.client.post(reverse('deactivate_account'), data, follow=True)

        user = User.objects.get(pk=self.user.pk)

        # Make sure the user was redirected home
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(reverse('home'), response.redirect_chain[0][0])
        self.assertEqual(302, response.redirect_chain[0][1])

        self.assertEqual(response.status_code, 200)
        self.assertFalse(user.is_active)

    def test_user_can_not_deactivate_with_incorrect_credentials(self):
        """
        Test that a user can not deactivate their account when they have the wrong username or password
        """
        self.assertTrue(self.user.is_active)

        data = {
            "username": 'some_user',
            "password": "password_wrong",
        }
        response = self.client.post(reverse('deactivate_account'), data)

        user = User.objects.get(pk=self.user.pk)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password!')
        self.assertTrue(user.is_active)

    def test_user_can_not_deactivate_with_other_credentials(self):
        """
        Test that a user can not deactivate their account (or someone else's) with the incorrect user credentials
        """
        other_user = User.objects.create_user('some_user2', 'test@example.com', 'password')

        data = {
            "username": 'some_user2',
            "password": "password",
        }
        response = self.client.post(reverse('deactivate_account'), data)

        user = User.objects.get(pk=self.user.pk)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password!')
        self.assertTrue(user.is_active)
        self.assertTrue(other_user.is_active)


class CommentAccountViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.user.save()
        self.client.login(username='some_user', password='password')

        self.comments = mommy.make(Comment, commenter=self.user, _quantity=5)

    def test_user_can_view_own_comments(self):
        """
        Test that a user can view their own comments
        """
        response = self.client.get(reverse('my_comments'))

        for comment in self.comments:
            self.assertContains(response, comment.content)

        self.assertContains(response, self.user.username)

    def test_user_can_not_see_unpublished_comments(self):
        """
        Test that a user can not see unpublished or deleted comments
        """

        unpublished_comments = mommy.make(Comment, commenter=self.user, status=Comment.UNPUBLISHED, _quantity=20)
        deleted_comments = mommy.make(Comment, commenter=self.user, status=Comment.DELETED, _quantity=20)

        response = self.client.get(reverse('my_comments'))

        for comment in self.comments:
            self.assertContains(response, comment.content)

        for comment in unpublished_comments:
            self.assertNotContains(response, comment.content)

        for comment in deleted_comments:
            self.assertNotContains(response, comment.content)

        self.assertContains(response, self.user.username)

    def test_user_can_not_see_other_users_comments(self):
        """
        Test that the user can not see other user's comments on their page
        """
        other_comments = mommy.make(Comment, _quantity=20)

        response = self.client.get(reverse('my_comments'))

        for comment in self.comments:
            self.assertContains(response, comment.content)

        for comment in other_comments:
            self.assertNotContains(response, comment.content)

        self.assertContains(response, self.user.username)


class RegisterViewTests(TestCase):
    def test_logged_in_user_can_not_register(self):
        """
        Test that a user who is logged in can not register and is redirected home
        """
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.user.save()
        self.client.login(username='some_user', password='password')

        response = self.client.get(reverse('register'), follow=True)
        self.assertRedirects(response, reverse('home'))

    def test_user_can_view_register_page(self):
        """
        Test that a user can successfully view the register page
        """

        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_register(self):
        """
        Test that a user can register an account
        """
        self.client.get(reverse('register'))
        captcha = CaptchaStore.objects.all()[0]

        self.assertEqual(User.objects.count(), 0)

        data = {
            "first_name": "Man",
            "last_name": "Tan",
            "email": "test2@example.com",
            "username": "some_user2",
            "password1": "password",
            "password2": "password",
            'captcha_0': captcha.hashkey,
            'captcha_1': captcha.response,
        }

        response = self.client.post(reverse('register'), data=data, follow=True)
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(User.objects.count(), 1)

        user = User.objects.all()[0]

        self.assertEqual(user.first_name, "Man")
        self.assertEqual(user.last_name, "Tan")
        self.assertEqual(user.email, "test2@example.com")
        self.assertEqual(user.username, "some_user2")

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_user_can_not_register_with_duplicate_username(self):
        """
        Test that a user can not register with a duplicate username
        """
        self.user = User.objects.create_user('some_user', 'test@example.com', 'password')
        self.user.first_name = 'Joe'
        self.user.last_name = 'Bill'
        self.user.save()

        self.client.get(reverse('register'))
        captcha = CaptchaStore.objects.all()[0]

        self.assertEqual(User.objects.count(), 1)

        data = {
            "first_name": "Man",
            "last_name": "Tan",
            "email": "test2@example.com",
            "username": "some_user",  # Duplicate user
            "password1": "password",
            "password2": "password",
            'captcha_0': captcha.hashkey,
            'captcha_1': captcha.response,
        }

        response = self.client.post(reverse('register'), data=data, follow=True)
        self.assertContains(response, "You had errors in your details. Please fix them and submit again.")
        self.assertFormError(response, 'form', 'username', 'A user with that username already exists.')

        self.assertEqual(User.objects.count(), 1)

    def test_user_can_not_register_with_mismatched_password(self):
        """
        Test that a user can not register with passwords that do not match
        """
        self.client.get(reverse('register'))
        captcha = CaptchaStore.objects.all()[0]

        self.assertEqual(User.objects.count(), 0)

        data = {
            "first_name": "Man",
            "last_name": "Tan",
            "email": "test2@example.com",
            "username": "some_user",
            "password1": "password",
            "password2": "password_mismatch",
            'captcha_0': captcha.hashkey,
            'captcha_1': captcha.response,
        }

        response = self.client.post(reverse('register'), data=data, follow=True)
        self.assertContains(response, "You had errors in your details. Please fix them and submit again.")
        self.assertFormError(response, 'form', 'password2', 'The two password fields didn\'t match.')

        self.assertEqual(User.objects.count(), 0)