import datetime, json, mock, unittest
from django.core.exceptions import ValidationError
from drf_to_s3.models import Policy, PolicyCondition
from drf_to_s3 import naive_serializers


class TestNaivePolicyConditionFieldToNative(unittest.TestCase):

    def setUp(self):
        self.field = naive_serializers.NaivePolicyConditionField()

    def test_starts_with(self):
        cond = PolicyCondition(
            operator='starts-with',
            element_name='key',
            value='user/eric/'
        )
        result = self.field.to_native(cond)
        expected = ['starts-with', '$key', 'user/eric/']
        self.assertEquals(result, expected)

    def test_eq(self):
        cond = PolicyCondition(
            operator='eq',
            element_name='acl',
            value='public-read'
        )
        result = self.field.to_native(cond)
        expected = ['eq', '$acl', 'public-read']
        self.assertEquals(result, expected)

    def test_no_oper(self):
        cond = PolicyCondition(
            element_name='acl',
            value='public-read'
        )
        result = self.field.to_native(cond)
        expected = {'acl': 'public-read'}
        self.assertEquals(result, expected)

    def test_range(self):
        cond = PolicyCondition(
            element_name='content-length-range',
            value_range=[1048579, 10485760]
        )
        result = self.field.to_native(cond)
        expected = ['content-length-range', 1048579, 10485760]
        self.assertEquals(result, expected)

class TestNaivePolicyConditionFieldFromNative(unittest.TestCase):

    def setUp(self):
        self.field = naive_serializers.NaivePolicyConditionField()      

    def test_starts_with(self):
        cond = [ "starts-with", "$key", "user/eric/" ]
        result = self.field.from_native(cond)
        self.assertIsInstance(result, PolicyCondition)
        self.assertEquals(result.operator, 'starts-with')
        self.assertEquals(result.element_name, 'key'),
        self.assertEquals(result.value, 'user/eric/')
        self.assertIsNone(result.value_range)

    def test_eq(self):
        cond = [ "eq", "$acl", "public-read" ]
        result = self.field.from_native(cond)
        self.assertIsInstance(result, PolicyCondition)
        self.assertEquals(result.operator, 'eq')
        self.assertEquals(result.element_name, 'acl'),
        self.assertEquals(result.value, 'public-read')
        self.assertIsNone(result.value_range)

    def test_range(self):
        cond = [ "content-length-range", 1048579, 10485760 ]
        result = self.field.from_native(cond)
        self.assertIsInstance(result, PolicyCondition)
        self.assertIsNone(result.operator)
        self.assertEquals(result.element_name, 'content-length-range'),
        self.assertIsNone(result.value)
        self.assertEquals(result.value_range, [1048579, 10485760])

    def test_empty_array(self):
        cond = []
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertTrue(exception.message.startswith('Empty condition array'))
        self.assertEquals(exception.params['condition'], cond)

    def test_missing_args(self):
        cond = ["content-length-range"]
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertTrue(exception.message.startswith('Missing values in condition array'))
        self.assertEquals(exception.params['condition'], cond)

    def test_missing_key(self):
        cond = ["eq"]
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertTrue(exception.message.startswith('Missing element in condition array'))
        self.assertEquals(exception.params['condition'], cond)

    def test_missing_dollar(self):
        cond = ["eq", "key"]
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertTrue(exception.message.startswith('Element name in condition array should start with $'))
        self.assertEquals(exception.params['element_name'], 'key')

    def test_extra_args(self):
        cond = ["content-length-range", 1, 2, 3, 4, 5]
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertTrue(exception.message.startswith('Too many values in condition array'))
        self.assertEquals(exception.params['condition'], cond)

    def test_dict(self):
        cond = {"acl": "public-read" }
        result = self.field.from_native(cond)
        self.assertIsInstance(result, PolicyCondition)
        self.assertIsNone(result.operator)
        self.assertEquals(result.element_name, 'acl')
        self.assertEquals(result.value, 'public-read')
        self.assertIsNone(result.value_range)

    def test_dict_extra_keys(self):
        cond = {"acl": "public-read", "foo": "bar"}
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertTrue(exception.message.startswith('Too many values in condition dictionary'))
        self.assertEquals(exception.params['condition'], cond)

    def test_dict_invalid_values(self):
        cond = {"acl": []}
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertEquals(exception.message, 'Values in condition dictionaries should be numbers or strings')

    def test_string(self):
        cond = 'foo-test'
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertTrue(exception.message.startswith('Condition must be array or dictionary'))
        self.assertEquals(exception.params['condition'], cond)

    def test_number(self):
        cond = 12345
        with self.assertRaises(ValidationError) as ctx:
            self.field.from_native(cond)
        exception = ctx.exception
        self.assertTrue(exception.message.startswith('Condition must be array or dictionary'))
        self.assertEquals(exception.params['condition'], cond)


class NaivePolicySerializerTest(unittest.TestCase):

    class TestSerializer(naive_serializers.NaivePolicySerializer):
        allowed_buckets = ['janesmith', 'johnsmith']

    def setUp(self):
        self.serializer_class = self.TestSerializer

    def test_that_serialize_with_bucket_and_key_succeeds(self):
        json_data = '''
        {
            "expiration": "2007-12-01T12:00:00.000Z",
            "conditions": [
                {"bucket": "johnsmith" },
                {"key": "/foo/bar/baz" }
            ]
        }
        '''
        data = json.loads(json_data)
        serializer = self.serializer_class(data=data)
        self.assertTrue(serializer.is_valid())

    def test_that_serialize_with_duplicate_condition_fails(self):
        json_data = '''
        {
            "expiration": "2007-12-01T12:00:00.000Z",
            "conditions": [
                {"bucket": "johnsmith" },
                {"bucket": "joesmith" },
                {"foo": "bar" }
            ]
        }
        '''
        data = json.loads(json_data)
        serializer = self.serializer_class(data=data)
        self.assertFalse(serializer.is_valid())
        expected = ['Duplicate element name']
        self.assertEquals(serializer.errors['conditions.bucket'], expected)

    def test_that_after_configuration_serialize_without_bucket_succeeds(self):
        json_data = '''
        {
            "expiration": "2007-12-01T12:00:00.000Z",
            "conditions": [
            ]
        }
        '''
        data = json.loads(json_data)
        serializer = self.serializer_class(data=data)
        serializer.required_conditions = []
        self.assertTrue(serializer.is_valid())

    def test_that_after_configuration_serialize_with_extra_condition_succeeds(self):
        json_data = '''
        {
            "expiration": "2007-12-01T12:00:00.000Z",
            "conditions": [
                {"foo": "bar" }
            ]
        }
        '''
        data = json.loads(json_data)
        serializer = self.serializer_class(data=data)
        serializer.required_conditions = []
        serializer.optional_conditions = ['foo']
        self.assertTrue(serializer.is_valid())

    def test_that_serializer_invokes_validate_expiration(self):
        json_data = '''
        {
            "expiration": "2007-12-01T12:00:00.000Z",
            "conditions": [
                {"bucket": "johnsmith" }
            ]
        }
        '''
        data = json.loads(json_data)
        serializer = self.serializer_class(data=data)
        serializer.validate_expiration = mock.MagicMock()
        serializer.is_valid()
        self.assertTrue(serializer.validate_expiration.called)

    def test_that_serializer_invokes_validate_condition_methods(self):
        json_data = '''
        {
            "expiration": "2007-12-01T12:00:00.000Z",
            "conditions": [
                {"bucket": "johnsmith" },
                {"foo": "bar" }
            ]
        }
        '''
        data = json.loads(json_data)
        serializer = self.serializer_class(data=data)
        serializer.optional_conditions = ['foo']
        serializer.validate_condition_bucket = mock.MagicMock()
        serializer.validate_condition_foo = mock.MagicMock()
        serializer.is_valid()
        self.assertTrue(serializer.validate_condition_bucket.called)
        self.assertTrue(serializer.validate_condition_foo.called)

    # FIXME Test that errors generated by condition validation methods
    # are returned

    # FIXME Test that when there's a missing key and a condition validation
    # error, both are returned

    def test_that_after_configuration_serialize_with_valid_content_type_succeeds(self):
        json_data = '''
        {
            "expiration": "2007-12-01T12:00:00.000Z",
            "conditions": [
                {"Content-Type": "image/jpeg"}
            ]
        }
        '''
        data = json.loads(json_data)
        serializer = self.serializer_class(data=data)
        serializer.required_conditions = []
        self.assertTrue(serializer.is_valid())

