# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#  Package: Pikos toolkit
#  File: tests/test_cline_memory_monitor.py
#  License: LICENSE.TXT
#
#  Copyright (c) 2014, Enthought, Inc.
#  All rights reserved.
# -----------------------------------------------------------------------------
import unittest

from pikos.filters.on_value import OnValue
from pikos.tests.compat import TestCase
from pikos.tests.monitoring_helper import MonitoringHelper
from pikos.recorders.list_recorder import ListRecorder


class TestLineMemoryMonitor(TestCase):

    def setUp(self):
        self.check_for_psutils()
        try:
            from pikos.cymonitors.line_memory_monitor import (
                LineMemoryMonitor)
        except ImportError:
            self.skipTest('Cython LineMemoryMonitor is not available')
        from pikos.cymonitors.line_memory_monitor import LineMemoryMonitor
        self.maxDiff = None
        self.helper = MonitoringHelper()
        self.filename = self.helper.filename
        self.recorder = ListRecorder(
            filter_=OnValue('filename', self.filename))
        self.monitor = LineMemoryMonitor(self.recorder)
        self.helper.monitor = self.monitor

    def test_function(self):
        result = self.helper.run_on_function()
        self.assertEqual(result, 3)

        template = [
            "1 gcd 30             while x > 0: {0}",
            "2 gcd 31                 x, y = y % x, x {0}",
            "3 gcd 30             while x > 0: {0}",
            "4 gcd 31                 x, y = y % x, x {0}",
            "5 gcd 30             while x > 0: {0}",
            "6 gcd 32             return y {0}"]
        self.check_records(template, self.recorder)

    def test_recursive(self):
        result = self.helper.run_on_recursive_function()
        self.assertEqual(result, 1)

        template = [
            "1 gcd 50             return x if y == 0 else gcd(y, (x % y)) {0}",  # noqa
            "7 gcd 50             return x if y == 0 else gcd(y, (x % y)) {0}",  # noqa
            "13 gcd 50             return x if y == 0 else gcd(y, (x % y)) {0}",  # noqa
            "19 gcd 50             return x if y == 0 else gcd(y, (x % y)) {0}",  # noqa
            "25 gcd 50             return x if y == 0 else gcd(y, (x % y)) {0}",  # noqa
            "31 gcd 50             return x if y == 0 else gcd(y, (x % y)) {0}"]  # noqa
        self.check_records(template, self.recorder)

    def test_generator(self):
        result = self.helper.run_on_generator()
        output = (0, 1, 1, 2, 3, 5, 8, 13, 21, 34)
        self.assertSequenceEqual(result, output)

        template = [
            "2 fibonacci 65             x, y = 0, 1 {0}",
            "3 fibonacci 66             for i in range(items): {0}",  # noqa
            "4 fibonacci 67                 yield x {0}",
            "9 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "10 fibonacci 66             for i in range(items): {0}",  # noqa
            "11 fibonacci 67                 yield x {0}",
            "16 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "17 fibonacci 66             for i in range(items): {0}",  # noqa
            "18 fibonacci 67                 yield x {0}",
            "23 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "24 fibonacci 66             for i in range(items): {0}",  # noqa
            "25 fibonacci 67                 yield x {0}",
            "30 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "31 fibonacci 66             for i in range(items): {0}",  # noqa
            "32 fibonacci 67                 yield x {0}",
            "37 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "38 fibonacci 66             for i in range(items): {0}",  # noqa
            "39 fibonacci 67                 yield x {0}",
            "44 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "45 fibonacci 66             for i in range(items): {0}",  # noqa
            "46 fibonacci 67                 yield x {0}",
            "51 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "52 fibonacci 66             for i in range(items): {0}",  # noqa
            "53 fibonacci 67                 yield x {0}",
            "58 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "59 fibonacci 66             for i in range(items): {0}",  # noqa
            "60 fibonacci 67                 yield x {0}",
            "65 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "66 fibonacci 66             for i in range(items): {0}",  # noqa
            "67 fibonacci 67                 yield x {0}",
            "72 fibonacci 68                 x, y = y, x + y {0}",  # noqa
            "73 fibonacci 66             for i in range(items): {0}"]  # noqa

        self.check_records(template, self.recorder)

    def test_function_using_tuples(self):
        from pikos.monitors.line_memory_monitor import LineMemoryMonitor
        filename = self.filename
        # tuple records are not compatible with the default OnValue filters.
        recorder = ListRecorder(filter_=lambda x: x[-1] == filename)
        monitor = LineMemoryMonitor(recorder, record_type=tuple)
        helper = MonitoringHelper(monitor)
        result = helper.run_on_function()
        self.assertEqual(result, 3)
        template = [
            "0 gcd 30             while x > 0: {0}",
            "1 gcd 31                 x, y = y % x, x {0}",
            "2 gcd 30             while x > 0: {0}",
            "3 gcd 31                 x, y = y % x, x {0}",
            "4 gcd 30             while x > 0: {0}",
            "5 gcd 32             return y {0}"]
        self.check_records(template, recorder)

    def test_issue2(self):
        """ Test for issue #2.

        """
        monitor = self.monitor

        FOO = """
def foo():
    a = []
    for i in range(20):
        a.append(i+sum(a))

foo()
"""

        @monitor.attach
        def boo():
            code = compile(FOO, 'foo', 'exec')
            exec code in globals(), {}

        try:
            boo()
        except TypeError:
            msg = ("Issue #2 -- line monitor fails when exec is used"
                   " on code compiled from a string -- exists.")
            self.fail(msg)

    def get_records(self, recorder):
        """ Remove the memory related fields.
        """
        records = []
        for record in recorder.records:
            filtered = record[:3] + record[5:]
            records.append(' '.join([str(item) for item in filtered]))
        return records

    def check_for_psutils(self):
        try:
            import psutil  # noqa
        except ImportError:
            self.skipTest('Could not import psutils, skipping test.')

    def check_records(self, template, recorder):
        expected = [line.format(self.filename) for line in template]
        records = self.get_records(recorder)
        self.assertEqual(records, expected)


if __name__ == '__main__':
    unittest.main()
