from django.test import TestCase
from offers.models import Offer, Provider, Plan, Comment, Location, Like
from model_mommy import mommy
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import User
import os
from datetime import timedelta
from decimal import Decimal
from django.utils.text import slugify
from django.core.urlresolvers import reverse


class OfferMethodTests(TestCase):

    def setUp(self):
        self.provider = mommy.make(Provider)

        self.offer = mommy.make(Offer, provider=self.provider, status=Offer.PUBLISHED)

        self.user = User.objects.create_user('user', 'test@example.com', 'pass')
        self.user.user_profile.provider = self.provider
        self.user.user_profile.save()

    def test_unicode_string(self):
        """
        Test that the string version of the offer is correct
        """
        name = "{0} ({1})".format(self.offer.name, self.offer.provider.name)
        self.assertEqual(name, self.offer.__unicode__())

    def test_plan_count(self):
        """
        Test that the plan count method returns the correct number of plans
        """
        mommy.make(Plan, _quantity=4, offer=self.offer)
        self.assertEqual(self.offer.plan_count(), 4)

    def test_min_cost(self):
        """
        Test that the minimum cost method gets the true minimum cost
        """

        # Not minimum
        mommy.make(Plan, offer=self.offer, cost=100)
        mommy.make(Plan, offer=self.offer, cost=50)
        mommy.make(Plan, offer=self.offer, cost=11)
        mommy.make(Plan, offer=self.offer, cost=10.01)

        # True minimum
        mommy.make(Plan, offer=self.offer, cost=10)

        self.assertEqual(10, self.offer.min_cost())

    def test_min_cost_with_other(self):
        """
        Test that the minimum cost method gets the true minimum cost and not that of other offers
        """

        # Other plans with cheaper costs that are not related
        mommy.make(Plan, cost=5)
        mommy.make(Plan, cost=10)
        mommy.make(Plan, cost=20)

        # Not minimum
        mommy.make(Plan, offer=self.offer, cost=100)
        mommy.make(Plan, offer=self.offer, cost=50)
        mommy.make(Plan, offer=self.offer, cost=11)
        mommy.make(Plan, offer=self.offer, cost=10.01)

        # True minimum
        mommy.make(Plan, offer=self.offer, cost=10)

        self.assertEqual(10, self.offer.min_cost())

    def test_max_cost(self):
        """
        Test that the maximum cost method gets the true maximum cost
        """

        # Not maximum
        mommy.make(Plan, offer=self.offer, cost=50)
        mommy.make(Plan, offer=self.offer, cost=100)
        mommy.make(Plan, offer=self.offer, cost=2000)
        mommy.make(Plan, offer=self.offer, cost=2999.99)

        # True maximum
        mommy.make(Plan, offer=self.offer, cost=3000)

        self.assertEqual(3000, self.offer.max_cost())

    def test_max_cost_with_other(self):
        """
        Test that the maximum cost method gets the true maximum cost and not that of other offers
        """

        # Generate other plans with more expensive costs
        mommy.make(Plan, cost=100)
        mommy.make(Plan, cost=3000)
        mommy.make(Plan, cost=10000)

        # Not maximum
        mommy.make(Plan, offer=self.offer, cost=50)
        mommy.make(Plan, offer=self.offer, cost=100)
        mommy.make(Plan, offer=self.offer, cost=2000)
        mommy.make(Plan, offer=self.offer, cost=2999.99)

        # True maximum
        mommy.make(Plan, offer=self.offer, cost=3000)

        self.assertEqual(3000, self.offer.max_cost())

    def test_get_comments_published(self):
        """
        Test the get comments method only gets published comments relating to the current offer
        """

        # Generate random comments that should not show up
        mommy.make(Comment, _quantity=20)

        comments = mommy.make(Comment, offer=self.offer, _quantity=10, status=Comment.PUBLISHED)
        self.assertEqual(10, self.offer.get_comments().count())

        for comment in comments:
            self.assertIn(comment, self.offer.get_comments())

    def test_get_comments_unpublished(self):
        """
        Test the get comments method only gets published comments relating to the current offer
        """

        # Generate random comments as well
        mommy.make(Comment, _quantity=20)

        comments = mommy.make(Comment, offer=self.offer, _quantity=20, status=Comment.UNPUBLISHED)
        self.assertEqual(self.offer.get_comments().count(), 0)

    def test_get_comments_deleted(self):
        """
        Test the get comments method only gets published comments relating to the current offer
        """

        # Generate random comments as well
        mommy.make(Comment, _quantity=20)

        comments = mommy.make(Comment, offer=self.offer, _quantity=20, status=Comment.DELETED)
        self.assertEqual(self.offer.get_comments().count(), 0)

    def test_get_min_max_gets_correct_values_for_monthly(self):
        """
        Test that the min max gets the correct values for monthly plans
        """
        plan_min = mommy.make(Plan, offer=self.offer, billing_time=Plan.MONTHLY, cost=10.00)
        plan_mid = mommy.make(Plan, offer=self.offer, billing_time=Plan.MONTHLY, cost=15.50)
        plan_max = mommy.make(Plan, offer=self.offer, billing_time=Plan.MONTHLY, cost=20.83)

        min_max = self.offer.get_min_max_cost()

        self.assertEqual(len(min_max), 1)  # Only got monthly

        self.assertEqual(min_max[0]["name"], plan_mid.get_billing_time_display())
        self.assertEqual(min_max[0]["code"], Plan.MONTHLY)
        self.assertEqual(min_max[0]["min_cost"], '10.00')
        self.assertEqual(min_max[0]["max_cost"], '20.83')
        self.assertFalse(min_max[0]["same"])

    def test_get_min_max_gets_correct_values_for_yearly(self):
        """
        Test that the min max gets the correct values for monthly plans
        """
        plan_min = mommy.make(Plan, offer=self.offer, billing_time=Plan.YEARLY, cost=10.00)
        plan_mid = mommy.make(Plan, offer=self.offer, billing_time=Plan.YEARLY, cost=15.50)
        plan_max = mommy.make(Plan, offer=self.offer, billing_time=Plan.YEARLY, cost=20.83)

        min_max = self.offer.get_min_max_cost()

        self.assertEqual(len(min_max), 1)  # Only got yearly

        self.assertEqual(min_max[0]["name"], plan_mid.get_billing_time_display())
        self.assertEqual(min_max[0]["code"], Plan.YEARLY)
        self.assertEqual(min_max[0]["min_cost"], '10.00')
        self.assertEqual(min_max[0]["max_cost"], '20.83')
        self.assertFalse(min_max[0]["same"])

    def test_get_min_max_sets_same_with_one_plan(self):
        """
        Test that the min max gets the correct values for monthly plans
        """
        plan = mommy.make(Plan, offer=self.offer, billing_time=Plan.MONTHLY, cost=10.00)

        min_max = self.offer.get_min_max_cost()

        self.assertEqual(len(min_max), 1)  # Only got monthly

        self.assertEqual(min_max[0]["name"], plan.get_billing_time_display())
        self.assertEqual(min_max[0]["code"], Plan.MONTHLY)
        self.assertEqual(min_max[0]["min_cost"], '10.00')
        self.assertEqual(min_max[0]["max_cost"], '10.00')
        self.assertTrue(min_max[0]["same"])

    def test_get_min_max_gets_correct_values_two_billing_periods(self):
        """
        Test that the min max gets the correct values for monthly plans
        """
        plan_month_min = mommy.make(Plan, offer=self.offer, billing_time=Plan.MONTHLY, cost=10.00)
        plan_month_mid = mommy.make(Plan, offer=self.offer, billing_time=Plan.MONTHLY, cost=15.50)
        plan_month_max = mommy.make(Plan, offer=self.offer, billing_time=Plan.MONTHLY, cost=20.83)

        plan_year_min = mommy.make(Plan, offer=self.offer, billing_time=Plan.YEARLY, cost=100.00)
        plan_year_mid = mommy.make(Plan, offer=self.offer, billing_time=Plan.YEARLY, cost=155.10)
        plan_year_max = mommy.make(Plan, offer=self.offer, billing_time=Plan.YEARLY, cost=208.30)

        min_max = self.offer.get_min_max_cost()

        self.assertEqual(len(min_max), 2)  # Got both monthly and yearly

        self.assertEqual(min_max[0]["name"], plan_month_mid.get_billing_time_display())
        self.assertEqual(min_max[0]["code"], Plan.MONTHLY)
        self.assertEqual(min_max[0]["min_cost"], '10.00')
        self.assertEqual(min_max[0]["max_cost"], '20.83')
        self.assertFalse(min_max[0]["same"])

        self.assertEqual(min_max[1]["name"], plan_year_mid.get_billing_time_display())
        self.assertEqual(min_max[1]["code"], Plan.YEARLY)
        self.assertEqual(min_max[1]["min_cost"], '100.00')
        self.assertEqual(min_max[1]["max_cost"], '208.30')
        self.assertFalse(min_max[1]["same"])

    def test_offer_active_gives_correct_offer_for_active_offer(self):
        """
        Test that the offer_active method returns true for an active offer
        """
        self.offer.is_active = True
        self.offer.status = Offer.PUBLISHED
        self.offer.save()

        self.assertTrue(self.offer.offer_active())

    def test_offer_active_gives_result_for_inactive_offer(self):
        """
        Test that the offer_active method returns false for an inactive offer
        """
        self.offer.is_active = False
        self.offer.status = Offer.PUBLISHED
        self.offer.save()

        self.assertFalse(self.offer.offer_active())

        self.offer.is_active = True
        self.offer.status = Offer.UNPUBLISHED
        self.offer.save()

        self.assertFalse(self.offer.offer_active())

    def test_queue_position_gives_correct_position(self):
        """
        Test that queue_position gives the correct position based on when the offer was readied at
        """
        self.offer.delete()

        offers = mommy.make(Offer, _quantity=5, status=Offer.REQUEST_COMPLETE)

        # Create some offers that should not be included
        mommy.make(Offer, _quantity=2, status=Offer.REQUEST_INCOMPLETE)
        mommy.make(Offer, _quantity=2, status=Offer.PUBLISHED)
        mommy.make(Offer, _quantity=2, status=Offer.UNPUBLISHED)

        offers[0].readied_at -= timedelta(days=5)
        offers[1].readied_at -= timedelta(days=4)
        offers[2].readied_at -= timedelta(days=3)
        offers[3].readied_at -= timedelta(days=2)
        offers[4].readied_at -= timedelta(days=1)

        for offer in offers:
            offer.save()

        self.assertEqual(offers[0].queue_position(), 1)
        self.assertEqual(offers[1].queue_position(), 2)
        self.assertEqual(offers[2].queue_position(), 3)
        self.assertEqual(offers[3].queue_position(), 4)
        self.assertEqual(offers[4].queue_position(), 5)

    def test_queue_position_with_not_ready_offer(self):
        """
        Test that the queue position returns None for an invalid queue position
        """

        self.offer.is_ready = False
        self.offer.save()

        self.assertEqual(self.offer.queue_position(), None)

    def test_queue_position_with_published_offer(self):
        """
        Test that the queue position returns None for an invalid queue position
        """

        self.offer.status = Offer.PUBLISHED
        self.offer.save()

        self.assertEqual(self.offer.queue_position(), None)

    def test_queue_position_with_not_request_offer(self):
        """
        Test that the queue position returns None for an invalid queue position
        """

        self.offer.is_request = False
        self.offer.save()

        self.assertEqual(self.offer.queue_position(), None)

    def test_get_plan_locations_gets_correct_unique_locations(self):
        """
        Test that the get plan locations methods gets the correct and unique locations of the plans
        """

        location1 = mommy.make(Location, provider=self.provider)
        location2 = mommy.make(Location, provider=self.provider)
        location3 = mommy.make(Location, provider=self.provider)

        mommy.make(Plan, _quantity=5, locations=[location1], offer=self.offer)
        mommy.make(Plan, _quantity=5, locations=[location2], offer=self.offer)
        mommy.make(Plan, _quantity=5, locations=[location3], offer=self.offer)

        locations = self.offer.get_plan_locations()

        self.assertEqual(len(locations), 3)

        self.assertIn(location1, locations)
        self.assertIn(location2, locations)
        self.assertIn(location3, locations)

    def test_get_plan_locations_does_not_get_other_locations(self):
        """
        Test that the get plan locations methods gets the correct and unique locations of the plans
        """

        location1 = mommy.make(Location, provider=self.provider)
        location2 = mommy.make(Location, provider=self.provider)
        location3 = mommy.make(Location, provider=self.provider)

        mommy.make(Plan, _quantity=5, locations=[location1], offer=self.offer)
        mommy.make(Plan, _quantity=5, locations=[location2], offer=self.offer)
        mommy.make(Plan, _quantity=5, locations=[location3], offer=self.offer)

        # Fake locations
        mommy.make(Plan, _quantity=10)

        locations = self.offer.get_plan_locations()

        self.assertEqual(len(locations), 3)

        self.assertIn(location1, locations)
        self.assertIn(location2, locations)
        self.assertIn(location3, locations)

    def test_get_absolute_url_gets_slugified_url(self):
        """
        Test that the get_absolute_url method of an offer returns the slug version of the url
        """
        self.assertEqual(
            self.offer.get_absolute_url(),
            reverse('offer:view_slug', args=[self.offer.pk, slugify(self.offer.name)])
        )

    def test_comment_count_gets_correct_comment_count(self):
        """
        Test comment_count only gives the number of published comments
        """
        mommy.make(Comment,_quantity=5, offer=self.offer, status=Comment.PUBLISHED)
        mommy.make(Comment,_quantity=5, offer=self.offer, status=Comment.UNPUBLISHED)
        mommy.make(Comment,_quantity=5, offer=self.offer, status=Comment.DELETED)

        self.assertEqual(self.offer.comment_count(), 5)

    def test_active_plan_count_returns_correct_values_with_active_offer(self):
        """
        Test that the active plan count method returns the correct plan count value
        """
        mommy.make(Plan, offer=self.offer, is_active=True, _quantity=5)
        mommy.make(Plan, offer=self.offer, is_active=False, _quantity=5)

        self.assertEqual(self.offer.active_plan_count(), 5)

    def test_active_plan_count_with_inactive_offer_returns_zero(self):
        """
        Test that the active plan count method returns zero if the offer is inactive
        """
        mommy.make(Plan, offer=self.offer, is_active=True, _quantity=5)
        mommy.make(Plan, offer=self.offer, is_active=False, _quantity=5)

        self.offer.is_active = False
        self.offer.save()

        self.assertEqual(self.offer.active_plan_count(), 0)


class ProviderMethodTests(TestCase):
    def setUp(self):
        self.provider = mommy.make(Provider)

    def test_unicode_string(self):
        """
        Test that the unicode string of the provider is their name
        """
        self.assertEqual(self.provider.name, self.provider.__unicode__())

    def test_offer_count_with_published_active(self):
        """
        Test that the number of published offers for a provider is correctly shown even if the offer is not active
        """
        mommy.make(Offer, _quantity=20, provider=self.provider, status=Offer.PUBLISHED, is_active=True)
        self.assertEqual(self.provider.offer_count(), 20)

    def test_offer_count_with_unpublished_active(self):
        """
        Test that the number of published offers for a provider is correctly shown even if the offer is not active
        """
        mommy.make(Offer, _quantity=20, provider=self.provider, status=Offer.UNPUBLISHED, is_active=True)
        self.assertEqual(self.provider.offer_count(), 0)

    def test_offer_count_with_published_inactive(self):
        """
        Test that the number of published offers for a provider is correctly shown even if the offer is not active
        """
        mommy.make(Offer, _quantity=20, provider=self.provider, status=Offer.PUBLISHED, is_active=False)
        self.assertEqual(self.provider.offer_count(), 20)

    def test_offer_count_with_unpublished_inactive(self):
        """
        Test that the number of published offers for a provider is correctly shown even if the offer is not active
        """
        mommy.make(Offer, _quantity=20, provider=self.provider, status=Offer.UNPUBLISHED, is_active=False)
        self.assertEqual(self.provider.offer_count(), 0)

    def test_active_offer_count_with_published_active(self):
        """
        Test that the number of published and active offers of a provider are correctly shown
        """
        mommy.make(Offer, _quantity=20, provider=self.provider, status=Offer.PUBLISHED, is_active=True)
        self.assertEqual(self.provider.active_offer_count(), 20)

    def test_active_offer_count_with_unpublished_active(self):
        """
        Test that the number of published and active offers of a provider are correctly shown
        """
        mommy.make(Offer, _quantity=20, provider=self.provider, status=Offer.UNPUBLISHED, is_active=True)
        self.assertEqual(self.provider.active_offer_count(), 0)

    def test_active_offer_count_with_published_inactive(self):
        """
        Test that the number of published and active offers of a provider are correctly shown
        """
        mommy.make(Offer, _quantity=20, provider=self.provider, status=Offer.PUBLISHED, is_active=False)
        self.assertEqual(self.provider.active_offer_count(), 0)

    def test_active_offer_count_with_unpublished_inactive(self):
        """
        Test that the number of published and active offers of a provider are correctly shown
        """
        mommy.make(Offer, _quantity=20, provider=self.provider, status=Offer.UNPUBLISHED, is_active=False)
        self.assertEqual(self.provider.active_offer_count(), 0)

    def test_plan_count_with_active_offer_active_plan_published_offer(self):
        """
        Test that the total plan count is correct when the following conditions are met

        (F is False, T is true)

        If all is T, then the plan is part of the count else it is not

        +--------------+-------------+-----------------+
        | Active Offer | Active Plan | Published Offer |
        +==============+=============+=================+
        |       T      |      T      |        T        |
        +--------------+-------------+-----------------+
        """
        mommy.make(
            Plan,
            _quantity=20,
            offer__provider=self.provider,

            # Variables
            offer__is_active=True,
            is_active=True,
            offer__status=Offer.PUBLISHED,
        )
        self.assertEqual(self.provider.plan_count(), 20)

    def test_plan_count_with_inactive_offer_active_plan_published_offer(self):
        """
        Test that the total plan count is correct when the following conditions are met

        (F is False, T is true)

        If all is T, then the plan is part of the count else it is not

        +--------------+-------------+-----------------+
        | Active Offer | Active Plan | Published Offer |
        +==============+=============+=================+
        |       F      |      T      |        T        |
        +--------------+-------------+-----------------+
        """
        mommy.make(
            Plan,
            _quantity=20,
            offer__provider=self.provider,

            # Variables
            offer__is_active=False,
            is_active=True,
            offer__status=Offer.PUBLISHED,
        )
        self.assertEqual(self.provider.plan_count(), 0)

    def test_plan_count_with_active_offer_inactive_plan_published_offer(self):
        """
        Test that the total plan count is correct when the following conditions are met

        (F is False, T is true)

        If all is T, then the plan is part of the count else it is not

        +--------------+-------------+-----------------+
        | Active Offer | Active Plan | Published Offer |
        +==============+=============+=================+
        |       T      |      F      |        T        |
        +--------------+-------------+-----------------+
        """
        mommy.make(
            Plan,
            _quantity=20,
            offer__provider=self.provider,

            # Variables
            offer__is_active=True,
            is_active=False,
            offer__status=Offer.PUBLISHED,
        )
        self.assertEqual(self.provider.plan_count(), 0)

    def test_plan_count_with_active_offer_active_plan_unpublished_offer(self):
        """
        Test that the total plan count is correct when the following conditions are met

        (F is False, T is true)

        If all is T, then the plan is part of the count else it is not

        +--------------+-------------+-----------------+
        | Active Offer | Active Plan | Published Offer |
        +==============+=============+=================+
        |       T      |      T      |        F        |
        +--------------+-------------+-----------------+
        """
        mommy.make(
            Plan,
            _quantity=20,
            offer__provider=self.provider,

            # Variables
            offer__is_active=True,
            is_active=True,
            offer__status=Offer.UNPUBLISHED,
        )
        self.assertEqual(self.provider.plan_count(), 0)

    def test_plan_count_with_inactive_offer_inactive_plan_unpublished_offer(self):
        """
        Test that the total plan count is correct when the following conditions are met

        (F is False, T is true)

        If all is T, then the plan is part of the count else it is not

        +--------------+-------------+-----------------+
        | Active Offer | Active Plan | Published Offer |
        +==============+=============+=================+
        |       F      |      F      |        F        |
        +--------------+-------------+-----------------+
        """
        mommy.make(
            Plan,
            _quantity=20,
            offer__provider=self.provider,

            # Variables
            offer__is_active=False,
            is_active=False,
            offer__status=Offer.UNPUBLISHED,
        )
        self.assertEqual(self.provider.plan_count(), 0)

    def test_file_path_naming(self):
        """
        Test that the get_file_path() method returns a file with the correct extension
        """
        from offers.models import get_file_path
        filename = 'some_file.png'
        extension = 'png'

        resulting_filename = get_file_path(None, filename)
        self.assertTrue(resulting_filename.endswith(extension))


class PlanMethodTests(TestCase):
    def setUp(self):
        self.plans = mommy.make(Plan, _quantity=20)

    def test_data_format_from_MB_to_GB(self):
        """
        Test the data_format method converts correct MB values to GB
        """

        for i in range(100):
            value = i*1024
            plan = mommy.make(Plan)
            result = plan.data_format(value, 'megabytes')

            self.assertEqual("{0} GB".format(i), result)

    def test_data_format_from_GB_to_TB(self):
        """
        Test the data_format method converts correct GB values to TB
        """

        for i in range(100):
            value = i*1024
            plan = mommy.make(Plan)
            result = plan.data_format(value, 'gigabytes')

            self.assertEqual("{0} TB".format(i), result)

    def test_data_format_from_MB_to_MB(self):
        """
        Test the data_format method does not convert invalid MB values to GB
        """

        for i in range(100):
            value = (i*1024) + 1
            plan = mommy.make(Plan)
            result = plan.data_format(value, 'megabytes')

            self.assertEqual("{0} MB".format(value), result)

    def test_data_format_from_GB_to_GB(self):
        """
        Test the data_format method does not convert invalid GB values to TB
        """

        for i in range(100):
            value = (i*1024) + 1
            plan = mommy.make(Plan)
            result = plan.data_format(value, 'gigabytes')

            self.assertEqual("{0} GB".format(value), result)

    def test_get_memory(self):
        """
        Test that the get_memory method returns the correct result
        """

        for plan in self.plans:
            self.assertEqual(plan.get_memory(), plan.data_format(plan.memory, 'megabytes'))

    def test_get_bandwidth(self):
        """
        Test that the get_bandwidth method returns the correct result
        """

        for plan in self.plans:
            self.assertEqual(plan.get_bandwidth(), plan.data_format(plan.bandwidth, 'gigabytes'))

    def test_get_hdd(self):
        """
        Test that the get_hdd method returns the correct result
        """

        for plan in self.plans:
            self.assertEqual(plan.get_hdd(), plan.data_format(plan.disk_space, 'gigabytes'))

    def test_get_cost_for_decimal_gives_two_places_with_integer(self):
        """
        Test that the get_cost_for_decimal places returns 20.00 with decimal 20
        Integer -> Currency
        """

        self.assertEqual(Plan.get_cost_for_decimal(Decimal('20')), '20.00')

    def test_get_cost_for_decimal_gives_two_places_with_single_decimal_float(self):
        """
        Test that the get_cost_for_decimal places returns 20.10 with decimal 20.1
        Float -> Currency
        """

        self.assertEqual(Plan.get_cost_for_decimal(Decimal('20.1')), '20.10')

    def test_get_cost_for_decimal_gives_two_places_with_two_decimal_float(self):
        """
        Test that the get_cost_for_decimal places returns 20.14 with decimal 20.14
        Float -> Currency
        """

        self.assertEqual(Plan.get_cost_for_decimal(Decimal('20.14')), '20.14')

    def test_get_cost_for_decimal_gives_three_places_with_triple_decimal_float(self):
        """
        Test that the get_cost_for_decimal places returns 20.155 with decimal 20.155
        Float -> Currency
        """

        self.assertEqual(Plan.get_cost_for_decimal(Decimal('20.155')), '20.155')

    def test_get_cost_for_decimal_gives_three_places_with_quadruple_decimal_float_and_rounds(self):
        """
        Test that the get_cost_for_decimal places returns 20.108 with decimal 20.1076
        Float -> Currency
        """

        self.assertEqual(Plan.get_cost_for_decimal(Decimal('20.1076')), '20.108')

    def test_get_cost_for_decimal_gives_two_places_with_empty_decimal(self):
        """
        Test that the get_cost_for_decimal places returns 20.00 with decimal 20.000
        Float -> Currency
        """

        self.assertEqual(Plan.get_cost_for_decimal(Decimal('20.000')), '20.00')


class LocationMethodTests(TestCase):
    def setUp(self):
        self.location = mommy.make(Location)

    def test_location_name_with_unicode_name(self):
        """
        Test that the locations still work with unicode country names
        """
        location = mommy.make(Location, country='AX')
        self.assertIn(location.country.name.__unicode__(), location.__unicode__())

    def test_location_name_with_non_unicode_name(self):
        """
        Test that the location name works with a non unicode country name
        """
        location = mommy.make(Location, country='US')
        self.assertIn(location.country.name.__unicode__(), location.__unicode__())


class CommentMethodTests(TestCase):
    def setUp(self):
        self.comment = mommy.make(Comment)

    def test_like_count_correct_with_correct_offer(self):
        """
        Test that the like_count method returns the correct count
        """

        # Valid likes
        mommy.make(Like, _quantity=5, comment=self.comment)
        # Invalid likes
        mommy.make(Like, _quantity=5)

        self.assertEqual(self.comment.like_count(), 5)

    def test_like_count_returns_zero_on_no_likes(self):
        """
        Test that the like_count method returns 0 when there are no likes
        """

        # Invalid likes
        mommy.make(Like, _quantity=5)

        self.assertEqual(self.comment.like_count(), 0)

    def test_does_like_returns_true_if_user_likes_comment(self):
        """
        Test that the does_like method returns True if the user does like the comment
        """
        user = User.objects.create_user('user', 'test@example.com', 'pass')

        like = mommy.make(Like, user=user, comment=self.comment)
        self.assertTrue(self.comment.does_like(user))

    def test_does_like_returns_false_if_user_not_like_comment(self):
        """
        Test that the does_like method returns False if the user does not like the comment
        """
        user = User.objects.create_user('user', 'test@example.com', 'pass')
        self.assertFalse(self.comment.does_like(user))