# Copyright (c) 2013-2015 Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from datetime import datetime
from contextlib import contextmanager

import numpy as np

import siphon.testing
from siphon.ncss import NCSS, NCSSQuery, ResponseRegistry

recorder = siphon.testing.get_recorder(__file__)


def test_ncss_query_proj_box():
    nq = NCSSQuery().lonlat_point(1, 2).projection_box(-1, -2, -3, -4)
    query = str(nq)
    assert query.count('=') == 4
    assert 'minx=-1' in query
    assert 'maxx=-3' in query
    assert 'miny=-2' in query
    assert 'maxy=-4' in query


def test_ncss_query_vertical_level():
    nq = NCSSQuery().vertical_level(50000)
    assert str(nq) == 'vertCoord=50000'


def test_ncss_query_add_latlon():
    nq = NCSSQuery().add_lonlat(True)
    assert str(nq) == 'addLatLon=True'


def test_ncss_query_strides():
    nq = NCSSQuery().strides(5, 10)
    query = str(nq)
    assert 'timeStride=5' in query
    assert 'horizStride=10' in query


def test_ncss_query_accept():
    nq = NCSSQuery().accept('csv')
    assert str(nq) == 'accept=csv'


# This allows us to override the response handler registry, so we can test that we
# properly handle the case where we don't handle it
@contextmanager
def response_context():
    old_reg = siphon.ncss.response_handlers
    siphon.ncss.response_handlers = ResponseRegistry()
    yield siphon.ncss.response_handlers
    siphon.ncss.response_handlers = old_reg


# For testing unit handling
def tuple_unit_handler(data, units=None):
    return np.array(data).tolist(), units


class TestNCSS(object):
    server = 'http://thredds.ucar.edu/thredds/ncss/'
    urlPath = 'grib/NCEP/GFS/Global_0p5deg/GFS_Global_0p5deg_20150612_1200.grib2'

    @recorder.use_cassette('ncss_test_metadata')
    def setup(self):
        dt = datetime(2015, 6, 12, 15, 0, 0)
        self.ncss = NCSS(self.server + self.urlPath)
        self.nq = self.ncss.query().lonlat_point(-105, 40).time(dt)
        self.nq.variables('Temperature_isobaric', 'Relative_humidity_isobaric')

    def test_good_query(self):
        assert self.ncss.validate_query(self.nq)

    def test_bad_query(self):
        self.nq.variables('foo')
        assert not self.ncss.validate_query(self.nq)

    def test_bad_query_no_vars(self):
        self.nq.var.clear()
        assert not self.ncss.validate_query(self.nq)

    @recorder.use_cassette('ncss_gfs_xml_point')
    def test_xml_point(self):
        self.nq.accept('xml')
        xml_data = self.ncss.get_data(self.nq)

        assert 'Temperature_isobaric' in xml_data
        assert 'Relative_humidity_isobaric' in xml_data
        assert xml_data['lat'][0] == 40
        assert xml_data['lon'][0] == -105

    @recorder.use_cassette('ncss_gfs_csv_point')
    def test_csv_point(self):
        self.nq.accept('csv')
        csv_data = self.ncss.get_data(self.nq)

        assert 'Temperature_isobaric' in csv_data
        assert 'Relative_humidity_isobaric' in csv_data
        assert csv_data['lat'][0] == 40
        assert csv_data['lon'][0] == -105

    @recorder.use_cassette('ncss_gfs_csv_point')
    def test_unit_handler_csv(self):
        self.nq.accept('csv')
        self.ncss.unit_handler = tuple_unit_handler
        csv_data = self.ncss.get_data(self.nq)

        temp = csv_data['Temperature_isobaric']
        assert len(temp) == 2
        assert temp[1] == 'K'

        relh = csv_data['Relative_humidity_isobaric']
        assert len(relh) == 2
        assert relh[1] == '%'

    @recorder.use_cassette('ncss_gfs_xml_point')
    def test_unit_handler_xml(self):
        self.nq.accept('xml')
        self.ncss.unit_handler = tuple_unit_handler
        xml_data = self.ncss.get_data(self.nq)

        temp = xml_data['Temperature_isobaric']
        assert len(temp) == 2
        assert temp[1] == 'K'

        relh = xml_data['Relative_humidity_isobaric']
        assert len(relh) == 2
        assert relh[1] == '%'

    @recorder.use_cassette('ncss_gfs_netcdf_point')
    def test_netcdf_point(self):
        self.nq.accept('netcdf')
        nc = self.ncss.get_data(self.nq)

        assert 'Temperature_isobaric' in nc.variables
        assert 'Relative_humidity_isobaric' in nc.variables
        assert nc.variables['latitude'][0] == 40
        assert nc.variables['longitude'][0] == -105

    @recorder.use_cassette('ncss_gfs_netcdf4_point')
    def test_netcdf4_point(self):
        self.nq.accept('netcdf4')
        nc = self.ncss.get_data(self.nq)

        assert 'Temperature_isobaric' in nc.variables
        assert 'Relative_humidity_isobaric' in nc.variables
        assert nc.variables['latitude'][0] == 40
        assert nc.variables['longitude'][0] == -105

    @recorder.use_cassette('ncss_gfs_vertical_level')
    def test_vertical_level(self):
        self.nq.accept('csv').vertical_level(50000)
        csv_data = self.ncss.get_data(self.nq)

        assert str(csv_data['Temperature_isobaric'])[:6] == '263.39'

    @recorder.use_cassette('ncss_gfs_csv_point')
    def test_raw_csv(self):
        self.nq.accept('csv')
        csv_data = self.ncss.get_data_raw(self.nq)

        assert csv_data.startswith(b'date,lat')

    @recorder.use_cassette('ncss_gfs_csv_point')
    def test_unknown_mime(self):
        self.nq.accept('csv')
        with response_context():
            csv_data = self.ncss.get_data(self.nq)
            assert csv_data.startswith(b'date,lat')
