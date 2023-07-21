from __future__ import unicode_literals
import unittest
from nose.plugins.attrib import attr
from nose.tools import nottest

from tornado.testing import gen_test

from goblin.tests import BaseGoblinTestCase
from goblin._compat import PY2
from .base_tests import GraphPropertyBaseClassTestCase
from goblin.properties.properties import DateTime, GraphProperty
from goblin.properties.validators import DateTimeUTCValidator
from goblin.models import Vertex
from goblin.exceptions import ValidationError
from goblin._compat import print_
import datetime
from pytz import utc


@attr('unit', 'property', 'property_datetime_utc')
class DateTimePropertyTestCase(GraphPropertyBaseClassTestCase):
    klass = DateTime
    good_cases = (datetime.datetime.now(tz=utc), None, datetime.datetime.now())
    if PY2:
        bad_cases = (
            'val', [], (), {}, 0, long(1), False, 1.1)
    else:
        bad_cases = ('val', [], (), {}, 0, False, 1.1)

    def test_to_database_method(self):
        d = self.klass(strict=False)
        self.assertIsNone(d.to_database(None))
        self.assertIsInstance(d.to_database(100000), float)
        with self.assertRaises(ValidationError):
            d.to_database(lambda x: x)

    def test_input_output_equality(self):
        d = datetime.datetime(2014, 1, 1, tzinfo=utc)
        prop = self.klass()
        result = prop.to_python(prop.to_database(d))
        print_("Input: %s, Output: %s" % (d, result))
        self.assertEqual(d, result)


class DateTimeTestVertex(Vertex):
    element_type = 'test_datetime_vertex'

    test_val = DateTime()

CHOICES = (
    (datetime.datetime(2014, 1, 1, tzinfo=utc), 'A'),
    (datetime.datetime(2014, 2, 1, tzinfo=utc), 'B')
)


class DateTimeTestChoicesVertex(Vertex):
    element_type = 'test_datetime_choices_vertex'

    test_val = DateTime(choices=CHOICES)


@attr('unit', 'property', 'property_datetime_utc')
class DateTimeVertexTestCase(GraphPropertyBaseClassTestCase):

    @gen_test
    def test_datetime_io(self):
        print_("creating vertex")
        dt = yield DateTimeTestVertex.create(
            test_val=datetime.datetime(2014, 1, 1, tzinfo=utc))
        print_("getting vertex from vertex: %s" % dt)
        dt2 = yield DateTimeTestVertex.get(dt._id)
        print_("got vertex: %s\n" % dt2)
        self.assertEqual(dt2.test_val, dt.test_val)
        print_("deleting vertex")
        yield dt2.delete()

        dt = yield DateTimeTestVertex.create(
            test_val=datetime.datetime(2014, 1, 1, tzinfo=utc))
        print_("\ncreated vertex: %s with time: %s" % (dt, dt.test_val))
        dt2 = yield DateTimeTestVertex.get(dt._id)
        print_("Got vertex: %s" % dt2)
        self.assertEqual(
            dt2.test_val, datetime.datetime(2014, 1, 1, tzinfo=utc))
        print_("deleting vertex")
        yield dt2.delete()


@attr('unit', 'property', 'property_datetime_utc')
class TestVertexChoicesTestCase(BaseGoblinTestCase):

    @gen_test
    def test_good_choices_key_io(self):
        print_("creating vertex")
        dt = yield DateTimeTestChoicesVertex.create(
            test_val=datetime.datetime(2014, 1, 1, tzinfo=utc))
        print_("validating input")
        self.assertEqual(
            dt.test_val, datetime.datetime(2014, 1, 1, tzinfo=utc))
        print_("deleting vertex")
        yield dt.delete()

    @nottest
    @gen_test
    def test_good_choices_value_io(self):
        # Known to be a bug, all keys and choices must be int | long | datetime
        print_("creating vertex")
        dt = yield DateTimeTestChoicesVertex.create(test_val='B')
        print_("validating input")
        self.assertEqual(
            dt.test_val, datetime.datetime(2014, 2, 1, tzinfo=utc))
        print_("deleting vertex")
        yield dt.delete()

    @gen_test
    def test_bad_choices_io(self):
        with self.assertRaises(ValidationError):
            print_("creating vertex")
            dt = yield DateTimeTestChoicesVertex.create(
                test_val=datetime.datetime(2014, 3, 1, tzinfo=utc))
            print_("validating input")
            self.assertEqual(dt.test_val, 'C')
            print_("deleting vertex")
            yield dt.delete()
