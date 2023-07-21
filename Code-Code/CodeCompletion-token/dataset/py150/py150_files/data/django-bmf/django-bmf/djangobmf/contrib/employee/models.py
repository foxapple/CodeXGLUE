#!/usr/bin/python
# ex:set fileencoding=utf-8:

from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from djangobmf.conf import settings as bmfsettings
from djangobmf.models import BMFModel

from djangobmf.contrib.product.models import PRODUCT_SERVICE

from .serializers import EmployeeSerializer


class BaseEmployee(BMFModel):
    user = models.OneToOneField(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        blank=True,
        null=True,
        unique=True,
        related_name="bmf_employee",
        on_delete=models.SET_NULL,
    )

    class Meta(BMFModel.Meta):  # only needed for abstract models
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')
        abstract = True
        swappable = "BMF_CONTRIB_EMPLOYEE"


@python_2_unicode_compatible
class AbstractEmployee(BaseEmployee):
    """
    """
    contact = models.ForeignKey(  # TODO: make optional
        bmfsettings.CONTRIB_CUSTOMER,
        verbose_name=("Contact"),
        blank=True,
        null=True,
        related_name="bmf_employee",
        limit_choices_to={'is_company': False},
        on_delete=models.PROTECT,
    )
    product = models.ForeignKey(  # TODO: make optional
        bmfsettings.CONTRIB_PRODUCT,
        verbose_name=("Product"),
        null=True,
        blank=True,
        related_name="bmf_employee",
        limit_choices_to={'type': PRODUCT_SERVICE},
        on_delete=models.PROTECT,
    )

    name = models.CharField(_("Name"), max_length=255, null=True, blank=False, )
    email = models.EmailField(_('Email'), null=True, blank=True)
    phone_office = models.CharField(
        _("Phone office"), max_length=255, null=True, blank=True,
    )
    phone_mobile = models.CharField(
        _("Phone mobile"), max_length=255, null=True, blank=True,
    )
    fax = models.CharField(
        _("Fax"), max_length=255, null=True, blank=True,
    )

    # TODO: Add validator or modify queryset so that an employee cant be the supervisor of him/her-self
    supervisor = models.ForeignKey(
        'self',
        verbose_name=_("Supervisor"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta(BaseEmployee.Meta):
        ordering = ['name']
        abstract = True

    class BMFMeta:
        search_fields = ['name', 'email', 'user__username']
        serializer = EmployeeSerializer

    def __str__(self):
        return self.name or '%s' % self.user


class Employee(AbstractEmployee):
    pass
