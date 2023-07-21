#
# Copyright (c) 2014 Chris Jerdonek. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

from textwrap import dedent
import unittest

from openrcv.counting import get_lowest, get_majority, get_winner
from openrcv.models import RoundResults
from openrcv.utils import StringInfo
from openrcv.utiltest.helpers import UnitCase


class ModuleTest(UnitCase):

    @unittest.skip("TODO")
    def test_count_internal_ballots(self):
        # TODO: use this:
        # tabulator = Tabulator(contest.ballots_resource)
        # round_results = tabulator.count(candidate_numbers)
        internal_ballots = dedent("""\
        1 2
        3 1 4
        1 2
        """)
        openable = StringInfo(internal_ballots)
        result = count_internal_ballots(openable, (1, 2, 4))
        self.assertEqual(type(result), RoundResults)
        self.assertEqual(result.totals, {1: 3, 2: 2, 4: 0})

    def test_get_majority(self):
        cases = [
            (0, 1),
            (1, 1),
            (2, 2),
            (3, 2),
            (4, 3),
            (100, 51),
        ]
        for total, expected in cases:
            with self.subTest(total=total, expected=expected):
                self.assertEqual(get_majority(total), expected)

    def test_get_winner(self):
        self.assertIs(get_winner({1: 5, 2: 5}), None)
        cases = [
            ({1: 6, 2: 5}, 1),
            ({1: 5, 2: 6}, 2),
            ({1: 1, 2: 6, 3: 4}, 2),
        ]
        for totals, winner in cases:
            with self.subTest(totals=totals, winner=winner):
                self.assertEqual(get_winner(totals), winner)

    def test_get_lowest__no_totals(self):
        """Test passing an empty totals dict."""
        with self.assertRaises(ValueError):
            get_lowest({})

    def test_get_lowest(self):
        cases = [
            ({1: 6, 2: 5}, {2}),
            ({1: 5, 2: 6}, {1}),
            ({1: 1, 2: 6, 3: 4}, {1}),
            # Test ties.
            ({1: 5, 2: 5}, {1, 2}),
            ({1: 5, 2: 6, 3: 5}, {1, 3}),
        ]
        for totals, lowest in cases:
            with self.subTest(totals=totals, lowest=lowest):
                self.assertEqual(get_lowest(totals), lowest)


# TODO: remove this after incorporating the test.
class InternalBallotsNormalizerTest(UnitCase):

    def _test_parse(self):
        internal_ballots = dedent("""\
        1 2
        1 3
        4 1
        3
        1 2
        """)
        expected = dedent("""\
        3
        4 1
        2 2
        1 3
        """)
        output_stream = StringInfo()
        parser = InternalBallotsNormalizer(output_stream)
        ballot_stream = StringInfo(internal_ballots)
        parser.parse(ballot_stream)
        self.assertEqual(output_stream.value, expected)
