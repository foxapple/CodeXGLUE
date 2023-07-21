#!/usr/bin/python
# ex:set fileencoding=utf-8:
# flake8: noqa

from __future__ import unicode_literals

from django.test import TestCase

from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.utils import six
from django.utils.translation import activate

from django.utils.translation import ugettext_lazy as _

from djangobmf.currency import BaseCurrency
from djangobmf.currency import Wallet

from decimal import Decimal


class ClassTests(TestCase):
    def test_definitions_missing_iso(self):
        activate('en')
        msg = "missing iso"
        with self.assertRaises(ImproperlyConfigured, msg=msg):
            class TestCurrency(BaseCurrency):
                name = 'Currency'
                symbol = 'c'

    def test_definitions_missing_name(self):
        activate('en')
        msg = "missing name"
        with self.assertRaises(ImproperlyConfigured, msg=msg):
            class TestCurrency(BaseCurrency):
                iso = "XTE"
                symbol = 'c'

    def test_definitions_missing_symbol(self):
        activate('en')
        msg = "missing symbol"
        with self.assertRaises(ImproperlyConfigured, msg=msg):
            class TestCurrency(BaseCurrency):
                iso = "XTE"
                name = 'Currency'

    def test_definitions_invalid_precision(self):
        activate('en')
        msg = "invalid precision"
        with self.assertRaises(ImproperlyConfigured, msg=msg):
            class TestCurrency(BaseCurrency):
                iso = "XTE"
                name = 'Currency'
                symbol = 'c'
                base_precision = 'invalid'

    def test_definitions_negative_precision(self):
        activate('en')
        msg = "negative precision"
        with self.assertRaises(ImproperlyConfigured, msg=msg):
            class TestCurrency(BaseCurrency):
                iso = "XTE"
                name = 'Currency'
                symbol = 'c'
                base_precision = -3

    def test_logic(self):
        # valid models
        class TestCurrency(BaseCurrency):
            iso = "XTE"
            name = 'Currency'
            symbol = 'c'
            # symbol = six.u('¢') # LOOK test unicode-characters
            base_precision = 3

        class DemoCurrency(BaseCurrency):
            iso = "XDL"
            name = 'Dollar'
            symbol = '$'
            # symbol = _('ł') # LOOK test translations
            base_precision = 2

        # logic

        self.assertFalse(TestCurrency(0))
        self.assertTrue(TestCurrency(1))
        self.assertFalse(TestCurrency())

        self.assertTrue(TestCurrency(1) == TestCurrency(1))
        self.assertTrue(TestCurrency(1) != TestCurrency(2))

        self.assertTrue(TestCurrency(1) >= TestCurrency(1))
        self.assertTrue(TestCurrency(2) > TestCurrency(1))
        self.assertTrue(TestCurrency(1) <= TestCurrency(1))
        self.assertTrue(TestCurrency(1) < TestCurrency(2))

        self.assertFalse(TestCurrency(1) == DemoCurrency(1))
        self.assertFalse(TestCurrency(1) == TestCurrency(2))

        with self.assertRaises(TypeError):
            TestCurrency(1) > DemoCurrency(1)
        with self.assertRaises(TypeError):
            TestCurrency(1) >= DemoCurrency(1)
        with self.assertRaises(TypeError):
            TestCurrency(1) < DemoCurrency(1)
        with self.assertRaises(TypeError):
            TestCurrency(1) <= DemoCurrency(1)

    def test_math(self):
        # valid models
        class TestCurrency(BaseCurrency):
            iso = "XTE"
            name = 'Currency'
            symbol = 'c'
            # symbol = six.u('¢') # LOOK test unicode-characters
            base_precision = 3

        class DemoCurrency(BaseCurrency):
            iso = "XDL"
            name = 'Dollar'
            symbol = '$'
            # symbol = _('ł') # LOOK test translations
            base_precision = 2
        # math

        with self.assertRaises(TypeError):
            TestCurrency(1) + str()
        with self.assertRaises(TypeError):
            TestCurrency(1) - str()

        self.assertEqual(DemoCurrency(1) + DemoCurrency(2), DemoCurrency(3))
        self.assertEqual(DemoCurrency(3) - DemoCurrency(2), DemoCurrency(1))

        self.assertEqual(2 * DemoCurrency(2), DemoCurrency(4))
        self.assertEqual(DemoCurrency(2) * 2, DemoCurrency(4))
        self.assertEqual(DemoCurrency(2) * 2.0, DemoCurrency(4))
        self.assertEqual(DemoCurrency(2) * Decimal('2.0'), DemoCurrency(4))

        with self.assertRaises(TypeError):
            TestCurrency(1) * TestCurrency(1)

        self.assertEqual(DemoCurrency(8) // Decimal('2.0'), DemoCurrency(4))
        self.assertEqual(DemoCurrency(8) // 2.0, DemoCurrency(4))
        self.assertEqual(DemoCurrency(8) // 2, DemoCurrency(4))
        self.assertEqual(DemoCurrency(8) // DemoCurrency(2), Decimal(4))

        self.assertTrue(isinstance(DemoCurrency(8) // DemoCurrency(2), Decimal))

        with self.assertRaises(TypeError):
            TestCurrency(1) // DemoCurrency(1)

    def test_output(self):
        # valid models
        class TestCurrency(BaseCurrency):
            iso = "XTE"
            name = 'Currency'
            symbol = 'c'
            # symbol = six.u('¢') # LOOK test unicode-characters
            base_precision = 3

        class DemoCurrency(BaseCurrency):
            iso = "XDL"
            name = 'Dollar'
            symbol = '$'
            # symbol = _('ł') # LOOK test translations
            base_precision = 2

        # math

        # text output
        test = TestCurrency()
        self.assertEqual(repr(test), "<TestCurrency object at 0x%x>" % id(test))
        test = DemoCurrency(1)
        self.assertEqual(repr(test), "<DemoCurrency object at 0x%x>" % id(test))

        obj1 = TestCurrency()
        self.assertEqual(str(obj1), "Currency")

        obj1.set('23.00')
        obj2 = TestCurrency(Decimal(23))
        self.assertEqual(str(obj1), str(obj2))

    def test_wallet(self):
        class TestCurrency(BaseCurrency):
            iso = "XTE"
            name = 'Currency'
            symbol = 'c'
            # symbol = six.u('¢') # LOOK test unicode-characters
            base_precision = 3

        class DemoCurrency(BaseCurrency):
            iso = "XDL"
            name = 'Dollar'
            symbol = '$'
            # symbol = _('ł') # LOOK test translations
            base_precision = 2
        # wallet

        wallet = Wallet()
        self.assertEqual(repr(wallet), "<Wallet object at 0x%x>" % id(wallet))

        with self.assertRaises(TypeError):
            wallet + str()
        with self.assertRaises(TypeError):
            wallet - str()
        with self.assertRaises(TypeError):
            wallet * str()
        with self.assertRaises(TypeError):
            str() * wallet
        with self.assertRaises(TypeError):
            wallet // str()

        self.assertFalse(wallet)

        # math with currencies 

        wallet += TestCurrency(1)
        wallet += TestCurrency(2)
        wallet -= DemoCurrency(1)
        wallet -= TestCurrency(1)

        self.assertTrue(wallet)
        self.assertNotEqual(wallet, dict)

        self.assertEqual(wallet[TestCurrency.iso], TestCurrency(2))
        self.assertEqual(wallet[DemoCurrency.iso], DemoCurrency(-1))

        # math with wallets

        double_wallet = wallet + wallet
        self.assertEqual(double_wallet[TestCurrency.iso], TestCurrency(4))
        self.assertEqual(double_wallet[DemoCurrency.iso], DemoCurrency(-2))

        self.assertNotEqual(double_wallet, wallet)

        self.assertEqual(double_wallet, 2 * wallet)
        self.assertEqual(double_wallet, 2.0 * wallet)
        self.assertEqual(double_wallet, Decimal(2) * wallet)

        self.assertEqual(double_wallet // 2, wallet)
        self.assertEqual(double_wallet // 2.0, wallet)
        self.assertEqual(double_wallet // Decimal(2), wallet)

        self.assertEqual(double_wallet - wallet, wallet)

        # comparison of wallets

        new_wallet = Wallet()
        new_wallet += TestCurrency(1)

        self.assertNotEqual(new_wallet, wallet)
        self.assertNotEqual(wallet, new_wallet)

        test_wallet = new_wallet + wallet
        self.assertEqual(test_wallet[TestCurrency.iso], TestCurrency(3))
        self.assertEqual(test_wallet[DemoCurrency.iso], DemoCurrency(-1))

        test_wallet = new_wallet - wallet
        self.assertEqual(test_wallet[TestCurrency.iso], TestCurrency(-1))
        self.assertEqual(test_wallet[DemoCurrency.iso], DemoCurrency(1))

        test_wallet = new_wallet * 2
        self.assertNotEqual(test_wallet, wallet)
        self.assertNotEqual(wallet, test_wallet)
