from django.test import TestCase
from model_mommy import mommy
from offers.models import Offer, Provider
from offers.tasks import publish_offer, publish_latest_offer
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.core import mail
from datetime import timedelta


class OfferTaskTests(TestCase):

    def setUp(self):
        self.provider = mommy.make(Provider)
        self.offer = mommy.make(Offer, provider=self.provider, status=Offer.PUBLISHED)

        self.user = User.objects.create_user('user', 'test@example.com', 'pass')
        self.user.user_profile.provider = self.provider
        self.user.user_profile.save()

    def test_publish_offer_adds_provider_as_follower(self):
        """
        Test that the publish_offer task adds all users who manage a provider as followers
        """
        self.assertEqual(self.offer.followers.count(), 0)

        result = publish_offer.delay(self.offer.pk)

        self.assertTrue(result.successful())

        self.assertIn(self.user, self.offer.followers.all())
        self.assertEqual(self.offer.followers.count(), 1)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user.email)

    def test_publish_offer_does_nothing_with_invalid_offer(self):
        """
        Test that the publish_offer task does nothing with an invalid (unpublished) offer
        """
        self.offer.status = Offer.REQUEST_COMPLETE
        self.offer.save()

        self.assertEqual(self.offer.followers.count(), 0)

        result = publish_offer.delay(self.offer.pk)

        self.assertTrue(result.successful())

        self.assertNotIn(self.user, self.offer.followers.all())
        self.assertEqual(self.offer.followers.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_publish_latest_offer_publishes_oldest_offer(self):
        """
        Test that publish_latest_offer publishes the oldest offer
        """
        self.offer.delete()

        offers = mommy.make(
            Offer,
            _quantity=3,
            status=Offer.REQUEST_COMPLETE,
            provider=self.provider,
            creator=self.user
        )
        # Create some offers who should not be affected since they are invalid
        mommy.make(Offer, status=Offer.REQUEST_INCOMPLETE)
        mommy.make(Offer, status=Offer.UNPUBLISHED)
        mommy.make(Offer, status=Offer.PUBLISHED)

        # Set the oldest to newest
        offers[0].readied_at -= timedelta(days=3)
        offers[1].readied_at -= timedelta(days=2)
        offers[2].readied_at -= timedelta(days=1)

        self.assertTrue(publish_latest_offer.delay().successful())

        new_offer = Offer.objects.get(pk=offers[0].pk)

        self.assertEqual(new_offer.status, Offer.PUBLISHED)
        self.assertFalse(new_offer.is_request)

        self.assertEqual(Offer.objects.filter(status=Offer.PUBLISHED, is_request=False).count(), 2)

    def test_publish_latest_offer_does_not_publish_empty_offers(self):
        """
        Test that publish_latest_offer does not publish any offers if there are no applicable offers
        """
        self.offer.delete()

        mommy.make(
            Offer,
            _quantity=3,
            is_ready=False,
            is_request=True,
            status=Offer.UNPUBLISHED,
        )

        mommy.make(
            Offer,
            _quantity=3,
            is_ready=True,
            is_request=False,
            status=Offer.UNPUBLISHED,
        )

        self.assertTrue(publish_latest_offer.delay().successful())
        self.assertEqual(Offer.objects.filter(status=Offer.PUBLISHED).count(), 0)
