import os
from unittest import TestCase
import pyexcel as pe
from base import create_sample_file2
from _compact import OrderedDict
from nose.tools import raises


class TestUtils(TestCase):
    def setUp(self):
        """
        Make a test csv file as:

        1,2,3,4
        5,6,7,8
        9,10,11,12
        """
        self.testfile = "testcsv.xls"
        create_sample_file2(self.testfile)

    def test_to_one_dimension_array(self):
        r = pe.Reader(self.testfile)
        result = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        actual = pe.utils.to_one_dimensional_array(r)
        self.assertEqual(result, actual)
        actual2 = pe.utils.to_one_dimensional_array(result)
        self.assertEqual(actual2, result)

    def test_to_array(self):
        r = pe.Reader(self.testfile)
        result = [
            [1, 2, 3, 4],
            [5, 6, 7, 8, ],
            [9, 10, 11, 12]
        ]
        actual = pe.utils.to_array(r)
        self.assertEqual(result, actual)
        
    def test_to_dict(self):
        """
        Note: data file with column headers are tested
        in test_filters.py
        """
        r = pe.Reader(self.testfile)
        result = OrderedDict()
        result.update({"Series_1": [1, 2, 3, 4]})
        result.update({"Series_2": [5, 6, 7, 8, ]})
        result.update({"Series_3": [9, 10, 11, 12]})
        actual = pe.to_dict(r.rows())
        assert actual.keys() == result.keys()
        self.assertEqual(result, actual)
        result = {
            "Series_1": 1,
            "Series_2": 2,
            "Series_3": 3,
            "Series_4": 4,
            "Series_5": 5,
            "Series_6": 6,
            "Series_7": 7,
            "Series_8": 8,
            "Series_9": 9,
            "Series_10": 10,
            "Series_11": 11,
            "Series_12": 12
        }
        actual = pe.to_dict(r.enumerate())
        self.assertEqual(result, actual)

    def tearDown(self):
        if os.path.exists(self.testfile):
            os.unlink(self.testfile)


class TestUtils2(TestCase):
    def setUp(self):
        """
        Make a test csv file as:

        1,2,3,4
        5,6,7,8
        9,10,11,12
        """
        self.testfile = "testcsv.xls"
        self.content = {
            "Sheet1": [[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]],
            "Sheet2": [[4, 4, 4, 4], [5, 5, 5, 5], [6, 6, 6, 6]],
            "Sheet3": [[u'X', u'Y', u'Z'], [1, 4, 7], [2, 5, 8], [3, 6, 9]]
        }
        pe.save_book_as(bookdict=self.content,
                        dest_file_name=self.testfile)

    def test_book_reader_to_dict(self):
        r = pe.BookReader(self.testfile)
        actual = pe.to_dict(r)
        self.assertEqual(self.content, actual)

    def test_book_reader_to_dict2(self):
        r = pe.load_book(self.testfile)
        actual = r.to_dict()
        self.assertEqual(self.content, actual)

    def tearDown(self):
        if os.path.exists(self.testfile):
            os.unlink(self.testfile)

class TestToRecord(TestCase):
    def setUp(self):
        """
        Make a test csv file as:

        1,2,3,4
        5,6,7,8
        9,10,11,12
        """
        self.testfile = "test.xls"
        self.content = {
            "X": [1, 2, 3],
            "Y": [4, 5, 6],
            "Z": [7, 8, 9]
        }
        pe.save_as(dest_file_name=self.testfile,
                   adict=self.content)

    def test_book_reader_to_records(self):
        r = pe.SeriesReader(self.testfile)
        result = [
            {u'Y': 4.0, u'X': 1.0, u'Z': 7.0},
            {u'Y': 5.0, u'X': 2.0, u'Z': 8.0},
            {u'Y': 6.0, u'X': 3.0, u'Z': 9.0}]
        actual = pe.to_records(r)
        self.assertEqual(result, actual)

    @raises(ValueError)
    def test_index_sheet1(self):
        """Invalid input"""
        s = pe.sheets.NominableSheet([[1,2,3]], "test")
        pe.to_records(s)
    
    def test_index_sheet2(self):
        s = pe.ColumnSeriesReader(self.testfile, series=0)
        actual = pe.to_records(s)
        result = [
            {'1': 4, 'X': 'Y', '3': 6, '2': 5},
            {'1': 7, 'X': 'Z', '3': 9, '2': 8}
        ]
        self.assertEqual(result, actual)
        
    def test_index_sheet3(self):
        s = pe.ColumnSeriesReader(self.testfile, series=0)
        headers = ["Row 1", "Row 2", "Row 3", "Row 4"]
        actual = pe.to_records(s, headers)
        print(actual)
        result = [
            {'Row 4': 6.0, 'Row 2': 4.0, 'Row 1': 'Y', 'Row 3': 5.0},
            {'Row 4': 9.0, 'Row 2': 7.0, 'Row 1': 'Z', 'Row 3': 8.0}
        ]
        self.assertEqual(result, actual)

    def test_book_reader_to_records_custom(self):
        """use custom header
        """
        r = pe.SeriesReader(self.testfile)
        custom_headers = ["O", "P", "Q"]
        result = [
            {u'P': 4.0, u'O': 1.0, u'Q': 7.0},
            {u'P': 5.0, u'O': 2.0, u'Q': 8.0},
            {u'P': 6.0, u'O': 3.0, u'Q': 9.0}]
        actual = pe.to_records(r, custom_headers)
        self.assertEqual(result, actual)

    @raises(NotImplementedError)
    def test_book_reader_to_records_with_wrong_args(self):
        r = pe.BookReader(self.testfile)
        pe.to_records(r)

    def test_from_records(self):
        """give an empty records array"""
        value = pe.utils.from_records([])
        assert value == None

    def tearDown(self):
        if os.path.exists(self.testfile):
            os.unlink(self.testfile)
