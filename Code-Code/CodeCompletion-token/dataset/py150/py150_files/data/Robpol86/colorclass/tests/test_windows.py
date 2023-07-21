"""Test Windows methods."""

from __future__ import print_function

import sys

import pytest

from colorclass.color import Color
from colorclass.windows import IS_WINDOWS, Windows

pytestmark = pytest.mark.skipif(not IS_WINDOWS, reason='Requires windows.')


def test_disable_safe():
    """Test for safety."""
    original_stderr_id, original_stdout_id = id(sys.stderr), id(sys.stdout)

    assert not Windows.is_enabled()
    assert not Windows.disable()

    assert not Windows.is_enabled()
    assert not Windows.disable()

    assert not Windows.is_enabled()
    assert not Windows.disable()

    assert original_stderr_id == id(sys.stderr)
    assert original_stdout_id == id(sys.stdout)


def test_enable_then_disable():
    """Test enabling then disabling on Windows."""
    original_stderr_id, original_stdout_id = id(sys.stderr), id(sys.stdout)

    assert not Windows.is_enabled()
    assert Windows.enable()
    assert original_stderr_id != id(sys.stderr)
    assert original_stdout_id != id(sys.stdout)

    assert Windows.disable()
    assert original_stderr_id == id(sys.stderr)
    # assert original_stdout_id == id(sys.stdout)  # pytest does some weird shit.


def test():
    """Basic test."""
    with Windows(auto_colors=True):
        print(Color('{autored}Test{/autored}.'))
        sys.stdout.flush()

    Windows.enable(reset_atexit=True)
    print(Color('{autored}{autobgyellow}Test{bgblack}2{/bg}.{/all}'))
