# -*- coding: utf-8 -*-
from __future__ import print_function
from operator import add
from functools import reduce
from itertools import groupby
from easy_karabiner import util
from easy_karabiner import exception
from easy_karabiner.lookup import DefQuery
from easy_karabiner.xml_base import XML_base


class BaseFilter(XML_base, util.Hashable):
    def __init__(self, *vals, **kwargs):
        self.type = kwargs.get('type', 'only')
        self.vals = vals
        self.kwargs = kwargs

    def get_vals(self):
        return self.vals

    def get_tag_name(self):
        header = self.get_clsname().lower().rsplit('filter', 1)[0]
        tag_name = '%s_%s' % (header, self.type)
        return tag_name

    def to_xml(self):
        xml_tree = self.create_tag(self.get_tag_name())
        xml_tree.text = ',\n'.join(self.get_vals())
        return xml_tree

    def __add__(self, another):
        if self.get_tag_name() == another.get_tag_name():
            self.vals += another.vals
            return self
        else:
            tagname1 = self.get_tag_name()
            tagname2 = another.get_tag_name()
            errmsg = "Can't add %s with %s" % (tagname1, tagname2)
            raise TypeError(errmsg)

    @property
    def id(self):
        return (self.get_tag_name(), tuple(self.get_vals()))


class Filter(BaseFilter):
    '''
    >>> print(Filter('SKIM'))
    <only>SKIM</only>
    >>> print(Filter('SKIM', type='not'))
    <not>SKIM</not>
    '''

    def get_tag_name(self):
        return self.type


class ReplacementFilter(Filter):
    pass


class DeviceFilter(BaseFilter):
    def get_tag_name(self):
        tag_name = 'device_%s' % self.type
        return tag_name


class DeviceProductFilter(DeviceFilter):
    pass


class DeviceVendorFilter(DeviceFilter):
    pass


class WindowNameFilter(BaseFilter):
    pass


class UIElementRoleFilter(BaseFilter):
    pass


class InputSourceFilter(BaseFilter):
    pass


class ModifierFilter(BaseFilter):
    def get_tag_name(self):
        tag_name = 'modifier_%s' % self.type
        return tag_name


_CLASSES = util.find_all_subclass_of(BaseFilter, globals())

def split_type_and_val(val):
    if val.startswith('!'):
        type = 'not'
        val = val[1:]
    else:
        type = 'only'

    if val.startswith('{{') and val.endswith('}}'):
        val = val[2:-2]

    return (type, val)

def get_ground_truth_val(clsname, val):
    if clsname == 'ReplacementFilter':
        val = '{{%s}}' % val
    elif clsname == 'DeviceProductFilter':
        val = 'DeviceProduct::%s' % val
    elif clsname == 'DeviceVendorFilter':
        val = 'DeviceVendor::%s' % val
    elif clsname == 'ModifierFilter':
        val = 'ModifierFlag::%s' % val

    return val

def create_filter(clsname, val, type):
    filter = None

    for cls in _CLASSES:
        if clsname == cls.__name__:
            filter = cls(val, type=type)
            break

    return filter

# @return [Filter]
def parse_filter(vals):
    '''
    Parse `[val1, val2, ...]` format string list and return relative filters
    '''
    type_val_pairs = map(split_type_and_val, vals)

    # create filters
    filters = []
    for type, val in type_val_pairs:
        clsname = DefQuery.query_filter(val)
        if clsname is None:
            errmsg = "%s" % (vals)
            raise exception.UndefinedFilterException(errmsg)

        val = get_ground_truth_val(clsname, val)
        filter = create_filter(clsname, val, type)
        filters.append(filter)

    get_key = lambda filter: filter.get_tag_name()
    grouped = groupby(sorted(filters, key=get_key), get_key)
    # merge filters in the same group
    filters = [reduce(add, group) for _, group in grouped]
    return filters


if __name__ == "__main__":
    import doctest
    doctest.testmod()