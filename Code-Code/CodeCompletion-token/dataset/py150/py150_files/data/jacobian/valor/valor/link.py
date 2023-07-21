import re
import six
import json
import requests
from .model import model_factory
from .utils import is_ref, python_attr

PARAMETER_REGEX = re.compile(r'\{\([%\/a-zA-Z0-9_-]*\)\}')

class Link(object):

    def __init__(self, schema, session, url, link_schema):
        self._schema = schema
        self._session = session
        self._url = url
        self._link = link_schema
        self._name = python_attr(link_schema['title'])

    def __call__(self, *args, **kwargs):
        # Prepare a request object. We do this instead of using
        # session.request() so that we can re-use the prepared request further
        # down if the response is paginated.
        request = requests.Request(
            method = self._link['method'],
            url = self.interpolate_args(args),
            data = self.construct_body(kwargs)
        )
        request = self._session.prepare_request(request)

        # FIXME: verify SSL - don't want to just to verify=True because that
        # makes testing hard, but it should be true by default and overridable
        # by passing in a different session. Not sure how to make that work
        # though.
        response = self._session.send(request)

        # FIXME: are we 100% sure the response is always JSON?
        response_body = response.json()

        # Handle 206 (partial conteent) by paginating.
        # See https://devcenter.heroku.com/articles/platform-api-reference#ranges
        if response.status_code == 206:
            next_range = response.headers['Next-Range']
            while next_range:
                request.headers['range'] = next_range
                response = self._session.send(request)
                response_body.extend(response.json())
                next_range = response.headers.get('Next-Range', None)

        # FIXME: if-none-match???
        elif response.status_code not in (200, 201, 202):
            response.raise_for_status()

        # targetSchema is the schema for the object(s) returned by the API call.
        # It can either be an array, in which case the schema is actually
        # link.targetSchema.items, or it can be a dict in which case the
        # targetSchema itself is the schema.
        model_schema = self._link['targetSchema']
        if model_schema.get('type') == ['array']:
            target_type = 'multi'
            model_schema = model_schema['items']
        else:
            target_type = 'single'

        # If the target schema was a ref, resolve it.
        if is_ref(model_schema):
            model_schema = self._schema.resolve_ref(model_schema['$ref'])

        # If the target schema has patternProperties, the response is a plain
        # old dict, so just return that. I'm not sure if this is the right way
        # of handling this; we may want Model to understand patternProperties
        # instead.
        if 'patternProperties' in model_schema:
            return response_body

        # Create a Model subclass representing the expected return object.
        # FIXME: this feels super jank for a name, but is there a better way?
        name = model_schema['title'].split('-', 1)[-1]
        name = re.sub(r'[^\w]', '', name)

        # Python 3 excepts text class names; Python 2 expects bytes. No way to
        # to work around it without version checkking.
        if six.PY2:
            name = name.encode('ascii', 'ignore')

        cls = model_factory(name, self._schema, model_schema)

        if target_type == 'multi':
            return [cls(**i) for i in response_body]
        else:
            return cls(**response_body)

    def interpolate_args(self, args):
        """
        Interpolate arguments into the link's URL.
        """
        # This doesn't really validate the definition refs embedded in the URL
        # patterns, but in practice that doesn't seem to matter much.
        num_expected_args = len(PARAMETER_REGEX.findall(self._url))
        if num_expected_args != len(args):
            raise TypeError("%s() takes exactly %s arguments (%s given)" % (self._name, num_expected_args, len(args)))

        # I can't figure out how to get the match number in a re.sub() callback,
        # so sub one at a time. This feels inelegant, but I can't find a better
        # option, so (shrug).
        url = self._url
        for i, arg in enumerate(args):
            url = PARAMETER_REGEX.sub(format_path_parameter(arg), url, count=1)

        return url

    def construct_body(self, kwargs):
        """
        Construct a request body based on given arguments.
        """
        # This does do some light validation on the *keys* of the body params,
        # but doesn't validate the contents of the body. I'm not sure if this
        # will prove to matter in practice or not.
        if 'schema' not in self._link:
            if kwargs:
                raise TypeError("%s() got unexpected keyword arguments: %s" % (self._name, kwargs.keys()))
            return None

        # If we've got patternProperties, then this API takes arbitrary params,
        # so just punt on any sort of validation.
        if 'patternProperties' in self._link['schema']:
            return json.dumps(kwargs)

        given_keys = set(kwargs.keys())
        possible_keys = set(self._link['schema']['properties'].keys())
        required_keys = set(self._link['schema'].get('required', []))

        if required_keys - given_keys:
            raise TypeError("%s() missing required arguments: %s")

        if given_keys - possible_keys:
            raise TypeError("%s() got unepected keyword arguments: %s" % (self._name, list(given_keys - possible_keys)))

        # Is that really all?
        return json.dumps(kwargs)

def format_path_parameter(val):
    """
    Format a path paramater.

    Basically: convert to string, with a special rule for datetime objects.
    """
    if hasattr(val, 'identity'):
        val = val.identity()
    if hasattr(val, 'strftime'):
        val = val.strftime('%Y-%m-%dT%H:%M:%SZ')
    return six.text_type(val)
