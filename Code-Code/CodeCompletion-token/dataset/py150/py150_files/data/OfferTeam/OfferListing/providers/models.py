import os
import uuid
from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.text import slugify
from sorl.thumbnail import get_thumbnail
from django_countries.fields import CountryField
from offers.models import Offer, Plan


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('provider_logos', filename)


class Provider(models.Model):
    name = models.CharField(max_length=250, unique=True)
    name_slug = models.SlugField(max_length=255, unique=True, editable=False)

    start_date = models.DateField()
    website = models.URLField(max_length=255)
    logo = models.ImageField(upload_to=get_file_path, blank=True, max_length=255)

    tos = models.URLField(max_length=255, verbose_name='Terms of service')
    aup = models.URLField(max_length=255, verbose_name='Acceptable usage policy')
    sla = models.URLField(max_length=255, verbose_name='Service level agreement', blank=True, null=True)
    billing_agreement = models.URLField(max_length=255, verbose_name='Billing agreement', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('provider:detail', args=[self.name_slug])

    def offer_count(self):
        """
        Gets the total count of all the offers related to this provider. It only returns the number of published
        offers (Offers with the status of PUBLISHED).
        """
        return Offer.visible_offers.for_provider(self).count()

    def active_offer_count(self):
        """
        Gets the total count of all the offers related to this provider. It only returns the number of published
        offers (Offers with the status of PUBLISHED) that are active.
        """
        return Offer.active_offers.for_provider(self).count()

    def plan_count(self):
        """
        Returns the number of plans this provider has associated. It only returns plans related to a published article
        (and article with the status PUBLISHED).
        """
        return Plan.active_plans.for_provider(self).count()

    def get_small_profile_image(self):
        if not self.logo:
            image = settings.STATIC_URL + 'img/no_logo_small.png'
            return {
                "url": image,
                "width": 200,
                "height": 200,
            }
        image = get_thumbnail(self.logo, '200x200', crop='center')
        return image

    def get_large_profile_image(self):
        if not self.logo:
            image = settings.STATIC_URL + 'img/no_logo_large.png'
            return {
                "url": image,
                "width": 400,
                "height": 400,
            }
        image = get_thumbnail(self.logo, '400x400', crop='center')
        return image

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.name_slug = slugify(self.name)
        super(Provider, self).save(force_insert, force_update, using, update_fields)


class Datacenter(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Location(models.Model):
    city = models.CharField(max_length=255)
    country = CountryField()
    datacenter = models.ForeignKey(Datacenter)
    looking_glass = models.URLField(max_length=255, null=True, blank=True)

    provider = models.ForeignKey(Provider, related_name='locations')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u"{0}, {1}".format(self.city, self.country.name.__unicode__())


class TestIP(models.Model):
    IPV4 = 'v4'
    IPV6 = 'v6'

    IP_TYPES = (
        (IPV4, 'IPv4'),
        (IPV6, 'IPv6'),
    )

    location = models.ForeignKey(Location, related_name='test_ips')
    ip_type = models.CharField(max_length=2, choices=IP_TYPES)
    ip = models.GenericIPAddressField(verbose_name='IP Address')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TestDownload(models.Model):
    location = models.ForeignKey(Location, related_name='test_downloads')
    url = models.URLField(max_length=255)
    size = models.BigIntegerField()  # In Megabytes

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
