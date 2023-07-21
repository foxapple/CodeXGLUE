#!/usr/bin/python
# ex:set fileencoding=utf-8:
# flake8: noqa

from __future__ import unicode_literals

from .apps import PositionConfig
from .models import Position

from djangobmf.utils.testcases import DemoDataMixin
from djangobmf.utils.testcases import TestCase
from djangobmf.utils.testcases import ModuleMixin
from djangobmf.utils.testcases import ModuleTestFactory


class PositionFactory(ModuleTestFactory, DemoDataMixin, TestCase):
    app = PositionConfig


class PositionModuleTests(ModuleMixin, TestCase):

    def test_urls_user(self):
        """
        """
        self.model = Position

#       data = self.autotest_ajax_get('create', kwargs={'key': 'default'})
#       self.autotest_get('api', status_code=404)
#       self.autotest_post('api', status_code=302)

#       data = self.autotest_ajax_post('create', kwargs={'key': 'default'}, data={
#           'project': 1, 'name': 'Service', 'price': '100', 'product': 1, 'date': '2012-01-01', 'amount': '2.0', 'employee': 1, 'invoiceable': 1,
#       })
#       data = self.autotest_ajax_post('create', kwargs={'key': 'default'}, data={
#           'project': 2, 'name': 'Service', 'price': '100', 'product': 1, 'date': '2012-01-02', 'amount': '0.1', 'employee': 1, 'invoiceable': 1,
#       })
#       data = self.autotest_ajax_post('create', kwargs={'key': 'default'}, data={
#           'project': 1, 'name': 'Service', 'price': '100', 'product': 1, 'date': '2012-01-01', 'amount': '1.0', 'employee': 2, 'invoiceable': 1,
#       })
#       data = self.autotest_ajax_post('create', kwargs={'key': 'default'}, data={
#           'project': 2, 'name': 'Service', 'price': '100', 'product': 1, 'date': '2012-01-02', 'amount': '5.0', 'employee': 2, 'invoiceable': 1,
#       })
#       self.assertNotEqual(data["object_pk"], 0)

#       self.autotest_get('index')

#       obj = self.get_latest_object()
#       self.assertEqual(obj.has_invoice(), False)
#       a = '%s'%obj # check if object name has any errors

#       self.autotest_get('detail', kwargs={'pk': obj.pk}, api=False)
#       data = self.autotest_ajax_get('update', kwargs={'pk': obj.pk})
#       self.autotest_get('delete', kwargs={'pk': obj.pk})
#       self.autotest_post('delete', status_code=302, kwargs={'pk': obj.pk})

#       obj = Position.objects.filter(invoice__isnull=True)
#       data = {}
#       pks = []
#       for i in obj:
#           data['pk.%s' % i.pk] = 1
#           pks.append(i.pk)

#      #self.autotest_post('api', status_code=302, data=data)
#      #obj = Position.objects.filter(pk__in=pks)
#      #for i in obj:
#      #    self.assertEqual(bool(i.invoice_id), True)

    def test_cleans(self):
        """
        """
#       obj = Position()
#       obj.product_id = 1
#       obj.clean()
#       self.assertIsNotNone(obj.name, "name should be read from product")
#       self.assertIsNotNone(obj.price, "price should be read from product")
