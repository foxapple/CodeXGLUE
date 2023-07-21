from django.test import TestCase
from offers.models import Offer, Plan, Provider
from django.contrib.auth.models import User
from model_mommy import mommy
from django.core.urlresolvers import reverse


class ProviderOnlyAccess(TestCase):
    def _pre_setup(self):
        super(ProviderOnlyAccess, self)._pre_setup()

        self.provider = mommy.make(Provider)

        self.user = User.objects.create_user('user', 'test@example.com', 'pass')
        self.user.user_profile.provider = self.provider
        self.user.user_profile.save()

        self.offer = mommy.make(
            Offer,
            status=Offer.REQUEST_INCOMPLETE,
            provider=self.provider,
            creator=self.user
        )
        self.plan = mommy.make(Plan, offer=self.offer, location__provider=self.provider)

        self.client.login(username='user', password='pass')
        self.offer_only = False

    def setUp(self):
        self.offer_only = False

    def get_url(self, offer, plan):
        return reverse('offer:admin_requests')

    def _url(self, offer=None, plan=None):
        if offer is None:
            offer = self.offer

        if plan is None:
            plan = self.plan

        return self.get_url(offer, plan)

    def login_url(self):
        return reverse('login') + '?next=' + self._url()

    def test_can_view_page_with_correct_permissions(self):
        """
        Test that a correctly authenticated provider can view the page
        """

        response = self.client.get(self._url(), follow=True)
        self.assertEqual(len(response.redirect_chain), 0)  # No redirects
        self.assertEqual(response.status_code, 200)  # Page did not 404

    def test_logged_out_user_can_not_view_page(self):
        """
        Test that a logged out user can not view the page
        """
        self.client.logout()

        response = self.client.get(self._url(), follow=True)
        self.assertRedirects(response, self.login_url())
        self.assertEqual(response.status_code, 200)  # Page did not 404

    def test_can_not_view_page_with_no_provider(self):
        """
        Test that the user can not view the page if they have no provider
        """
        self.user.user_profile.provider = None
        self.user.user_profile.save()

        response = self.client.get(self._url(), follow=True)
        self.assertRedirects(response, self.login_url())
        self.assertEqual(response.status_code, 200)  # Page did not 404

    def test_can_not_view_page_with_different_provider(self):
        """
        Test that the user can not view the page if they have no provider
        """

        if not self.offer_only:
            return

        self.user.user_profile.provider = mommy.make(Provider)
        self.user.user_profile.save()

        response = self.client.get(self._url(), follow=True)
        self.assertEqual(len(response.redirect_chain), 0)  # No redirects
        self.assertEqual(response.status_code, 404)  # Page did 404

    def test_can_not_view_page_with_wrong_offer(self):
        """
        Test that the user can not view the page if the offer does not exist
        """

        if not self.offer_only:
            return

        url = self._url()

        self.offer.delete()

        response = self.client.get(url, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)  # No redirects
        self.assertEqual(response.status_code, 404)  # Page did 404

    def test_can_not_view_page_with_published_offer(self):
        """
        Test that the user can not view the page if the offer is published
        """

        if not self.offer_only:
            return

        self.offer.status = Offer.PUBLISHED
        self.offer.save()

        response = self.client.get(self._url(), follow=True)
        self.assertEqual(len(response.redirect_chain), 0)  # No redirects
        self.assertEqual(response.status_code, 404)  # Page did 404

    def test_can_not_view_page_with_not_request_offer(self):
        """
        Test that the user can not view the page if the offer is not a request
        """

        if not self.offer_only:
            return

        self.offer.status = Offer.UNPUBLISHED
        self.offer.save()

        response = self.client.get(self._url(), follow=True)
        self.assertEqual(len(response.redirect_chain), 0)  # No redirects
        self.assertEqual(response.status_code, 404)  # Page did 404

    def test_can_not_view_page_with_different_offer(self):
        """
        Test that a user can not view a page with an offer that is not theirs
        """
        if not self.offer_only:
            return

        self.offer = mommy.make(Offer)

        response = self.client.get(self._url(), follow=True)
        self.assertEqual(len(response.redirect_chain), 0)  # No redirects
        self.assertEqual(response.status_code, 404)  # Page did 404


class RequestEditTest(ProviderOnlyAccess):
    def setUp(self):
        self.offer_only = True

    def get_url(self, offer, plan):
        return reverse('offer:admin_request_edit', args=[offer.pk])


class RequestMarkTest(ProviderOnlyAccess):
    def setUp(self):
        self.offer_only = True

    def get_url(self, offer, plan):
        return reverse('offer:admin_request_mark', args=[offer.pk])

    def test_can_view_page_with_correct_permissions(self):
        """
        Test that a correctly authenticated provider can view the page
        """

        response = self.client.get(self._url(), follow=True)
        self.assertRedirects(response, reverse('offer:admin_requests'))


class RequestDeleteTest(ProviderOnlyAccess):
    def setUp(self):
        self.offer_only = True

    def get_url(self, offer, plan):
        return reverse('offer:admin_request_delete', args=[offer.pk])


class RequestNewTest(ProviderOnlyAccess):
    def setUp(self):
        self.offer_only = False

    def get_url(self, offer, plan):
        return reverse('offer:admin_request_new')
