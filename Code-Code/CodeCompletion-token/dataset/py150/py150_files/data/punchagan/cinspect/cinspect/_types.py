""" Types for the different kind of objects we want to inspect. """

from __future__ import absolute_import, print_function

import inspect

from ._patch_helpers import inspect_restored


class CInspectObject(object):
    """ A simple wrapper around the object we are trying to inspect. """

    def __init__(self, obj):
        self.obj = obj

    @property
    def module(self):
        return self.obj.__module__

    @property
    def name(self):
        return self.obj.__name__

    @property
    def type_name(self):
        return type(self.obj.__self__).__name__


class PythonObject(CInspectObject):
    pass


class BuiltinFunction(CInspectObject):
    @property
    def type_name(self):
        return None


class BuiltinMethod(CInspectObject):
    @property
    def type_name(self):
        if isinstance(self.obj.__self__, type):
            type_name = self.obj.__self__.__name__

        else:
            type_name = super(BuiltinMethod, self).type_name

        return type_name


class MethodDescriptor(BuiltinMethod):
    @property
    def module(self):
        return None

    @property
    def type_name(self):
        return self.obj.__objclass__.__name__


class Module(CInspectObject):
    @property
    def module(self):
        return None

    @property
    def type_name(self):
        return None


class Type(CInspectObject):
    @property
    def type_name(self):
        return self.name


def get_cinspect_object(obj):
    """ Returns the object wrapped in the appropriate CInspectObject class. """

    try:
        with inspect_restored():
            inspect.getsource(obj)

    except (TypeError, IOError):
        wrapped = _get_cinspect_object(obj)

    else:
        wrapped = PythonObject(obj)

    return wrapped


def _get_cinspect_object(obj):
    """ Return the object wrapped in the appropriate CInspectObject class.

    This function expects that the object is not a pure-Python object.

    """

    if inspect.isbuiltin(obj):
        if obj.__module__ is None:
            # fixme: we could possibly check in `types` to see if it's really a
            # built-in...
            return BuiltinMethod(obj)
        else:
            # Any builtin/compiled functions ...
            return BuiltinFunction(obj)

    elif inspect.ismethoddescriptor(obj):
        return MethodDescriptor(obj)

    elif inspect.ismodule(obj):
        return Module(obj)

    elif inspect.isclass(obj):
        return Type(obj)

    elif inspect.isclass(type(obj)):
        return Type(obj.__class__)

    else:
        raise NotImplementedError
