from __future__ import unicode_literals
import pytest
import os

from textx.metamodel import metamodel_from_file
from textx.export import metamodel_export, model_export


def test_import():
    """
    Test grammar import.
    """

    current_dir = os.path.dirname(__file__)
    mm = metamodel_from_file(os.path.join(current_dir,
                             'relativeimport', 'first.tx'))
    metamodel_export(mm, 'import_test_mm.dot')

    model = """
    first
        second "1" "2"
        third true false true 12 false
    endfirst
    """

    model = mm.model_from_str(model)
    model_export(model, 'import_test_model.dot')


def test_multiple_imports():
    """
    Test that rules grammars imported from multiple places
    results in the same meta-class objects.
    """

    current_dir = os.path.dirname(__file__)
    mm = metamodel_from_file(os.path.join(current_dir,
                             'multiple', 'first.tx'))

    print(mm['First']._tx_attrs)
    print(mm['First']._tx_attrs['first'].cls._tx_attrs['second'].cls.__name__)
    print(mm['Third'])
    print(type(mm['First']._tx_attrs['first']))
    assert mm['First']._tx_attrs['first'].cls._tx_attrs['second'].cls \
        is mm['relative.third.Third']
    metamodel_export(mm, 'multipleimport_test_mm.dot')

    model = """
        first 1 2
        third "one" "two"
    """

    model = mm.model_from_str(model)
    model_export(model, 'multipleimport_test_model.dot')
