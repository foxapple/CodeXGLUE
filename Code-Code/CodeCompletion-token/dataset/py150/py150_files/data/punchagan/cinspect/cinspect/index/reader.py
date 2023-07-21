#!/usr/bin/env python
""" A class to read indexes and get source of specific objects. """

from __future__ import absolute_import, print_function

# Standard library
from os.path import abspath, exists

# Local library.
from .._types import (
    BuiltinFunction, BuiltinMethod, MethodDescriptor, Module, Type
)
from .serialize import get_index_path, read_index


class Reader(object):
    """ A class to read indexes and get source of specific objects. """

    #### 'Object' protocol ####################################################

    def __init__(self, index_path=None):
        if index_path is None:
            index_path = get_index_path(None, only_existing=True, allow_similar=True)
        self.index_path = abspath(index_path)

    #### 'Reader' protocol ####################################################

    def get_source(self, obj):
        """ Return the source for the object."""

        data = self._get_data(obj)
        return data['source']

    def get_file(self, obj):
        """ Return the file where the object has been defined. """

        data = self._get_data(obj)
        return data['path']

    #### 'Private' protocol ###################################################

    def _get_data(self, obj):
        """ Get the data for the given object. """

        if not exists(self.index_path):
            raise OSError('Index data not found at %s' % self.index_path)

        indexed_data = read_index(self.index_path)

        name = obj.name
        type_name = obj.type_name
        module_name = obj.module

        dummy_data = {'source': '', 'path': ''}


        if isinstance(obj, Type):
            objects = indexed_data.get('objects', {})
            data = objects.get(name, dummy_data)

        elif isinstance(obj, Module):
            modules = indexed_data.get('modules', {})
            data = modules.get(name, dummy_data)

        elif isinstance(obj, BuiltinFunction):
            module = indexed_data.get('modules', {}).get(module_name, {})
            # fixme: if we fail to get method_maps for the module, we could
            # look in all the maps.
            method_maps = module.get('method_maps', [])
            method_names = indexed_data.get('method_names', {})
            for mmap in method_maps:
                name_mapping = method_names[mmap]
                if name in name_mapping:
                    method_name = name_mapping[name]
                    break
            else:
                method_name = ''
            data = indexed_data.get('methods', {}).get(method_name, dummy_data)

        elif isinstance(obj, BuiltinMethod) or isinstance(obj, MethodDescriptor):
            type_ = indexed_data.get('objects', {}).get(type_name, {})
            # fixme: if we fail to get source for method from references, we
            # could look in all the maps.
            references = type_.get('references', [])
            method_names = indexed_data.get('method_names', {})
            for mmap in references:
                if mmap in method_names:
                    name_mapping = method_names[mmap]
                    if name in name_mapping:
                        method_name = name_mapping[name]
                        break
            else:
                method_name = ''
            data = indexed_data.get('methods', {}).get(method_name, dummy_data)

        else:
            raise RuntimeError('Cannot get source for %s' % obj)

        return data
