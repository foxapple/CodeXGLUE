from eemeter.consumption import ConsumptionData
from eemeter.evaluation import Period

from datetime import timedelta
from datetime import datetime
import numpy as np
from numpy.testing import assert_allclose
import pandas as pd
import warnings

from pint.unit import UndefinedUnitError

import pytest

RTOL = 1e-3
ATOL = 1e-3

@pytest.fixture(params=["electricity",
                        "natural_gas",
                        "fuel_oil",
                        "propane",
                        "liquid_propane",
                        "kerosene",
                        "diesel",
                        "fuel_cell",
                        ])
def fuel_type(request):
    return request.param

@pytest.fixture(params=["kWh",
                        "therm"])
def unit_name(request):
    return request.param

@pytest.fixture(params=["arbitrary",
                        "billing"])
def record_type_arbitrary(request):
    return request.param

@pytest.fixture(params=["arbitrary_start",
                        "billing_start"])
def record_type_arbitrary_start(request):
    return request.param

@pytest.fixture(params=["arbitrary_end",
                        "billing_end"])
def record_type_arbitrary_end(request):
    return request.param

@pytest.fixture(params=[
        [{"start": datetime(2015,1,5,0,0,0), "value": 5},
         {"start": datetime(2015,1,4,0,0,0), "value": 4},
         {"start": datetime(2015,1,3,0,0,0), "value": 3},
         {"start": datetime(2015,1,2,0,0,0), "value": 2},
         {"start": datetime(2015,1,1,0,0,0), "value": 1, "estimated": True}],
        [{"start": datetime(2015,1,1,0,0,0), "value": 1, "estimated": True},
         {"start": datetime(2015,1,2,0,0,0), "value": 2},
         {"start": datetime(2015,1,3,0,0,0), "value": 3},
         {"start": datetime(2015,1,4,0,0,0), "value": 4},
         {"start": datetime(2015,1,5,0,0,0), "value": 5, "estimated": False}],
        [{"start": datetime(2015,1,2,0,0,0), "value": 2},
            {"start": datetime(2015,1,1,0,0,0), "value": 1, "estimated": True},
         {"start": datetime(2015,1,4,0,0,0), "value": 4},
         {"start": datetime(2015,1,5,0,0,0), "value": 5},
         {"start": datetime(2015,1,3,0,0,0), "value": 3}],
        ])
def records_interval_start_daily_all(request):
    return request.param

@pytest.fixture(params=[
        [{"end": datetime(2015,1,5,0,0,0), "value": 5},
         {"end": datetime(2015,1,4,0,0,0), "value": 4},
         {"end": datetime(2015,1,3,0,0,0), "value": 3},
         {"end": datetime(2015,1,2,0,0,0), "value": 2},
         {"end": datetime(2015,1,1,0,0,0), "value": 1}],
        [{"end": datetime(2015,1,1,0,0,0), "value": 1},
         {"end": datetime(2015,1,2,0,0,0), "value": 2},
         {"end": datetime(2015,1,3,0,0,0), "value": 3},
         {"end": datetime(2015,1,4,0,0,0), "value": 4},
         {"end": datetime(2015,1,5,0,0,0), "value": 5}],
        [{"end": datetime(2015,1,2,0,0,0), "value": 2},
         {"end": datetime(2015,1,1,0,0,0), "value": 1},
         {"end": datetime(2015,1,4,0,0,0), "value": 4},
         {"end": datetime(2015,1,5,0,0,0), "value": 5},
         {"end": datetime(2015,1,3,0,0,0), "value": 3}],
        ])
def records_interval_end_daily_all(request):
    return request.param

@pytest.fixture
def records_interval_start_daily_missing_date(request):
    records = [
        {"start": datetime(2015,1,1,0,0,0), "value": 1},
        {"start": datetime(2015,1,2,0,0,0), "value": 2},
        {"start": datetime(2015,1,4,0,0,0), "value": 4},
        {"start": datetime(2015,1,5,0,0,0), "value": 5}]
    return records

@pytest.fixture
def records_interval_start_daily_misaligned_date(request):
    records = [
        {"start": datetime(2015,1,1,0,0,0), "value": 1},
        {"start": datetime(2015,1,2,0,0,0), "value": 2},
        {"start": datetime(2015,1,3,0,0,1), "value": 3},
        {"start": datetime(2015,1,4,0,0,0), "value": 4},
        {"start": datetime(2015,1,5,0,0,0), "value": 5}]
    return records

@pytest.fixture
def records_interval_start_daily_overlapping_date(request):
    records = [
        {"start": datetime(2015,1,1,0,0,0), "value": 1},
        {"start": datetime(2015,1,2,0,0,0), "value": 2},
        {"start": datetime(2015,1,3,0,0,0), "value": 3},
        {"start": datetime(2015,1,3,0,0,0), "value": 3},
        {"start": datetime(2015,1,4,0,0,0), "value": 4},
        {"start": datetime(2015,1,5,0,0,0), "value": 5}]
    return records

@pytest.fixture
def records_interval_start_daily_missing_value(request):
    records = [
        {"start": datetime(2015,1,1,0,0,0), "value": 1},
        {"start": datetime(2015,1,2,0,0,0), "value": 2},
        {"start": datetime(2015,1,3,0,0,0)},
        {"start": datetime(2015,1,4,0,0,0), "value": 4},
        {"start": datetime(2015,1,5,0,0,0), "value": 5}]
    return records

@pytest.fixture
def records_interval_start_daily_missing_start_key(request):
    records = [
        {"start": datetime(2015,1,1,0,0,0), "value": 1},
        {"end": datetime(2015,1,2,0,0,0), "value": 2},
        {"start": datetime(2015,1,3,0,0,0), "value": 3},
        {"start": datetime(2015,1,4,0,0,0), "value": 4},
        {"start": datetime(2015,1,5,0,0,0), "value": 5}]
    return records

@pytest.fixture
def records_interval_start_15min(request):
    records = [
        {"start": datetime(2015,1,1,0,0,0), "value": 1},
        {"start": datetime(2015,1,1,0,15,0), "value": 2},
        {"start": datetime(2015,1,1,0,30,0), "value": 3},
        {"start": datetime(2015,1,1,0,45,0), "value": 4},
        {"start": datetime(2015,1,1,1,0,0), "value": 5},
        {"start": datetime(2015,1,1,1,15,0), "value": 6}]
    return records

@pytest.fixture
def records_arbitrary_basic(request):
    records = [
        {"start": datetime(2015,2,1,0,0,0), "end": datetime(2015,2,28), "value": 0},
        {"start": datetime(2015,1,2,0,0,0), "end": datetime(2015,2,1), "value": 0},
        {"start": datetime(2015,1,1,1,4,5), "end": datetime(2015,1,1,2,4,5), "value": 1},
        {"start": datetime(2015,1,1,0,4,5), "end": datetime(2015,1,1,1,4,5), "value": np.nan},
        {"start": datetime(2015,1,1,0,0,0), "end": datetime(2015,1,1,0,4,5), }]
    return records

@pytest.fixture
def records_arbitrary_overlap(request):
    records = [
        {"start": datetime(2015,1,20,0,0,0), "end": datetime(2015,2,28), "value": 0},
        {"start": datetime(2015,1,2,0,0,0), "end": datetime(2015,2,1), "value": 0},
        {"start": datetime(2015,1,1,1,4,5), "end": datetime(2015,1,1,2,4,5), "value": 1},
        {"start": datetime(2015,1,1,0,4,5), "end": datetime(2015,1,1,1,4,5), "value": np.nan},
        {"start": datetime(2015,1,1,0,0,0), "end": datetime(2015,1,1,0,4,5), }]
    return records

@pytest.fixture(params=[
        [{"start": datetime(2015,2,1),"value":0},
         {"start": datetime(2015,1,2,0,0,0), "value":1},
         {"start": datetime(2015,1,1,1,4,5), "value":0},
         {"start": datetime(2015,1,1,0,4,5), "value":0},
         {"start": datetime(2015,1,1,0,0,0), "value":0}],
        [{"start": datetime(2015,1,2,0,0,0), "end": datetime(2015,2,1), "value":1},
         {"start": datetime(2015,1,1,1,4,5), "value":0},
         {"start": datetime(2015,1,1,0,4,5), "value":0},
         {"start": datetime(2015,1,1,0,0,0), "value":0}],
        ])
def records_arbitrary_start(request):
    return request.param

@pytest.fixture(params=[
        [{"end": datetime(2015,2,1), "value":0},
         {"end": datetime(2015,1,2,0,0,0), "value":1},
         {"end": datetime(2015,1,1,1,4,5), "value":0},
         {"end": datetime(2015,1,1,0,4,5), "value":0},
         {"end": datetime(2015,1,1,0,0,0),  "start": datetime(2014,2,2), "value":0}],
        [{"end": datetime(2015,2,1), "value":0},
         {"end": datetime(2015,1,2,0,0,0), "value":1},
         {"end": datetime(2015,1,1,1,4,5), "value":0},
         {"end": datetime(2015,1,1,0,4,5), "value":0},
         {"end": datetime(2015,1,1,0,0,0),  "value":0},
         {"end": datetime(2014,2,2,0,0,0),  "value":0}]
        ])
def records_arbitrary_end(request):
    return request.param

@pytest.fixture
def records_pulse(request):
    records = [
        {"pulse": datetime(2015,2,1)},
        {"pulse": datetime(2015,1,2,0,0,0)},
        {"pulse": datetime(2015,1,1,1,4,5)},
        {"pulse": datetime(2015,1,1,0,4,5)},
        {"pulse": datetime(2015,1,1,0,0,0)}]
    return records

@pytest.fixture
def consumption_data_blank():
    return ConsumptionData([], "electricity", "kWh", "arbitrary_start")


@pytest.fixture
def consumption_data_kWh_interval():
    records = [{"start": datetime(2015,1,i+1), "value": 1} for i in range(10)]
    return ConsumptionData(records, "electricity", "kWh", freq="D")

@pytest.fixture
def consumption_data_kWh_arbitrary():
    records = [{"start": datetime(2015,1,i+1), "end": datetime(2015,1,i+2),
        "value": 1} for i in range(10)]
    return ConsumptionData(records, "electricity", "kWh", record_type="arbitrary")

##### tests #####

def test_consumption_data_interval_start_daily_all_has_correct_attributes(
        records_interval_end_daily_all, fuel_type, unit_name):
    cd = ConsumptionData(records_interval_end_daily_all, fuel_type, unit_name,
            freq="D")
    assert cd.fuel_type == fuel_type
    assert cd.unit_name == unit_name
    assert cd.freq == "D"
    assert cd.freq_timedelta == timedelta(days=1)
    assert type(cd.data.index) == pd.DatetimeIndex
    assert cd.data.index.shape == (5,)
    assert cd.data.values.shape == (5,)
    assert cd.pulse_value == None

def test_consumption_data_interval_start_daily_all_invalid_fuel_type(
        records_interval_end_daily_all, unit_name):
    with pytest.raises(ValueError):
        cd = ConsumptionData(records_interval_end_daily_all, "invalid", unit_name,
                freq="D")

def test_consumption_data_interval_start_daily_all_invalid_unit_name(
        records_interval_end_daily_all, fuel_type):
    with pytest.raises(ValueError):
        cd = ConsumptionData(records_interval_end_daily_all, fuel_type, "invalid",
                freq="D")

def test_consumption_data_interval_start_daily_all_freq_D(
        records_interval_start_daily_all, fuel_type, unit_name):
    cd = ConsumptionData(records_interval_start_daily_all,
            fuel_type, unit_name, freq="D")
    assert cd.freq_timedelta == timedelta(days=1)
    assert_allclose(cd.data.values,[1,2,3,4,5], rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)
    assert_allclose(cd.estimated,[True,False,False,False,False], rtol=RTOL, atol=ATOL)

def test_consumption_data_interval_end_daily_all_freq_D(
        records_interval_end_daily_all, fuel_type, unit_name):
    cd = ConsumptionData(records_interval_end_daily_all,
            fuel_type, unit_name, freq="D")
    assert cd.freq_timedelta == timedelta(days=1)
    assert_allclose(cd.data.values,[1,2,3,4,5], rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2014,12,31)

def test_consumption_data_interval_end_daily_all_freq_2D(
        records_interval_end_daily_all, fuel_type, unit_name):
    cd = ConsumptionData(records_interval_end_daily_all,
            fuel_type, unit_name, freq="2D")
    assert cd.freq_timedelta == timedelta(days=2)
    assert_allclose(cd.data.values,[1,3,5], rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2014,12,30)

def test_consumption_data_interval_end_daily_all_freq_12H(
        records_interval_end_daily_all, fuel_type, unit_name):
    cd = ConsumptionData(records_interval_end_daily_all,
            fuel_type, unit_name, freq="12H")
    assert cd.freq_timedelta == timedelta(seconds=60*60*12)
    assert_allclose(cd.data.values,[1,np.nan,2,np.nan,3,np.nan,4,np.nan,5],
            rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2014,12,31,12)

def test_consumption_data_interval_start_daily_missing_start_key_freq_D(
        records_interval_start_daily_missing_start_key, fuel_type, unit_name):
    with pytest.raises(ValueError):
        cd = ConsumptionData(records_interval_start_daily_missing_start_key,
                fuel_type, unit_name, freq="D")

def test_consumption_data_interval_start_daily_missing_date_freq_D(
        records_interval_start_daily_missing_date, fuel_type, unit_name):
    cd = ConsumptionData(records_interval_start_daily_missing_date,
            fuel_type, unit_name, freq="D")
    assert cd.freq_timedelta == timedelta(days=1)
    assert_allclose(cd.data.values,[1,2,np.nan,4,5], rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)

def test_consumption_data_interval_start_daily_misaligned_date_freq_D(
        records_interval_start_daily_misaligned_date, recwarn):
    cd = ConsumptionData(records_interval_start_daily_misaligned_date,
            "electricity", "kWh", freq="D")
    assert cd.freq_timedelta == timedelta(days=1)
    assert_allclose(cd.data.values,[1,2,np.nan,4,5], rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)
    w = recwarn.pop(UserWarning)
    assert issubclass(w.category, UserWarning)

def test_consumption_data_interval_start_daily_overlapping_date_freq_D(
        records_interval_start_daily_overlapping_date, recwarn):
    cd = ConsumptionData(records_interval_start_daily_overlapping_date,
            "electricity", "kWh", freq="D")
    assert cd.freq_timedelta == timedelta(days=1)
    assert_allclose(cd.data.values,[1,2,3,4,5], rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)
    w = recwarn.pop(UserWarning)
    assert issubclass(w.category, UserWarning)

def test_consumption_data_interval_start_daily_missing_value_freq_D(
        records_interval_start_daily_missing_value):
    cd = ConsumptionData(records_interval_start_daily_missing_value,
            "electricity", "kWh", freq="D")
    assert cd.freq_timedelta == timedelta(days=1)
    assert_allclose(cd.data.values,[1,2,np.nan,4,5], rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)

def test_consumption_data_interval_start_15min(
        records_interval_start_15min, fuel_type, unit_name):
    cd = ConsumptionData(records_interval_start_15min,
            fuel_type, unit_name, freq="15T")
    assert cd.freq_timedelta == timedelta(seconds=60*15)
    assert_allclose(cd.data.values,[1,2,3,4,5,6], rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)
    assert cd.pulse_value is None

def test_consumption_data_arbitrary_basic(records_arbitrary_basic,
        fuel_type, unit_name, record_type_arbitrary):
    cd = ConsumptionData(records_arbitrary_basic,
            fuel_type, unit_name, record_type=record_type_arbitrary)
    assert cd.freq is None
    assert cd.freq_timedelta is None
    assert cd.pulse_value is None
    assert_allclose(cd.data.values,[np.nan,np.nan,1,np.nan,0,0,np.nan],
            rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)

def test_consumtion_data_arbitrary_overlap(records_arbitrary_overlap, recwarn):
    cd = ConsumptionData(records_arbitrary_overlap,
            "electricity", "kWh", record_type="arbitrary")
    assert_allclose(cd.data.values,[np.nan,np.nan,1,np.nan,0,np.nan],
            rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)
    assert cd.data.index[5] == datetime(2015,2,1)
    w = recwarn.pop(UserWarning)
    assert issubclass(w.category, UserWarning)

def test_consumption_data_arbitrary_start(records_arbitrary_start,
        fuel_type, unit_name, record_type_arbitrary_start):
    cd = ConsumptionData(records_arbitrary_start,
            fuel_type, unit_name, record_type=record_type_arbitrary_start)
    assert_allclose(cd.data.values,[0,0,0,1,np.nan],
            rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)
    assert cd.data.index[4] == datetime(2015,2,1)
    assert cd.freq is None
    assert cd.freq_timedelta is None
    assert cd.pulse_value is None

    generated_records = cd.records(record_type=record_type_arbitrary_start)
    assert len(generated_records) == 5
    assert generated_records[0] == {"start": datetime(2015,1,1), "value": 0, "estimated": False}
    assert generated_records[4]["start"] == datetime(2015,2,1)
    assert pd.isnull(generated_records[4]["value"])
    assert len(generated_records[4].keys()) == 3

def test_consumption_data_arbitrary_end(records_arbitrary_end,
        fuel_type, unit_name, record_type_arbitrary_end):
    cd = ConsumptionData(records_arbitrary_end,
            fuel_type, unit_name, record_type=record_type_arbitrary_end)
    assert_allclose(cd.data.values,[0,0,0,1,0,np.nan],
            rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2014,2,2)
    assert cd.data.index[5] == datetime(2015,2,1)
    assert cd.freq is None
    assert cd.freq_timedelta is None
    assert cd.pulse_value is None

    generated_records = cd.records(record_type=record_type_arbitrary_end)
    assert len(generated_records) == 6
    assert generated_records[0] == {"end": datetime(2014,2,2),"value": np.nan, "estimated": False}
    assert generated_records[5] == {"end": datetime(2015,2,1),"value":0, "estimated": False}

def test_consumption_data_pulse(records_pulse,
        fuel_type, unit_name):
    with pytest.raises(ValueError):
        cd = ConsumptionData(records_pulse,
                fuel_type, unit_name, record_type="pulse")
    with pytest.raises(ValueError):
        cd = ConsumptionData(records_pulse,
                fuel_type, unit_name, record_type="pulse", pulse_value=0)
    with pytest.raises(ValueError):
        cd = ConsumptionData(records_pulse,
                fuel_type, unit_name, record_type="pulse", pulse_value=-1)
    cd = ConsumptionData(records_pulse,
            fuel_type, unit_name, record_type="pulse", pulse_value=1)
    assert cd.pulse_value == 1
    assert_allclose(cd.data.values,[np.nan,1,1,1,1],
            rtol=RTOL, atol=ATOL)
    assert cd.data.index[0] == datetime(2015,1,1)
    assert cd.data.index[4] == datetime(2015,2,1)
    assert cd.freq is None
    assert cd.freq_timedelta is None
    assert cd.pulse_value == 1

    generated_records = cd.records(record_type="pulse")
    sorted_records = sorted(records_pulse, key=lambda x: x["pulse"])
    assert len(generated_records) == len(sorted_records)
    for r1, r2 in zip(generated_records,sorted_records):
        assert r1 == r2

def test_consumption_data_empty_records(fuel_type, unit_name):
    cd = ConsumptionData([], fuel_type, unit_name, freq="S")
    assert_allclose(cd.data.values, [], rtol=RTOL, atol=ATOL)
    cd = ConsumptionData([], fuel_type, unit_name, record_type="arbitrary")
    assert_allclose(cd.data.values, [], rtol=RTOL, atol=ATOL)
    cd = ConsumptionData([], fuel_type, unit_name, record_type="arbitrary_start")
    assert_allclose(cd.data.values, [], rtol=RTOL, atol=ATOL)
    cd = ConsumptionData([], fuel_type, unit_name, record_type="arbitrary_end")
    assert_allclose(cd.data.values, [], rtol=RTOL, atol=ATOL)
    cd = ConsumptionData([], fuel_type, unit_name, record_type="pulse", pulse_value=1)
    assert_allclose(cd.data.values, [], rtol=RTOL, atol=ATOL)

def test_consumption_units(consumption_data_kWh_interval):
    original_data = consumption_data_kWh_interval.data

    # conversion to therm
    therm_data = consumption_data_kWh_interval.to("therm")
    assert type(therm_data) == np.ndarray
    assert_allclose(therm_data, np.tile(0.0341,original_data.shape),
            rtol=RTOL, atol=ATOL)

    # conversion to kWh
    kWh_data = consumption_data_kWh_interval.to("kWh")
    assert type(therm_data) == np.ndarray
    assert_allclose(kWh_data, np.tile(1,original_data.shape),
            rtol=RTOL, atol=ATOL)

def test_consumption_periods_interval(consumption_data_kWh_interval):
    periods = consumption_data_kWh_interval.periods()
    assert periods[0].start == datetime(2015,1,1)
    assert periods[9].end == datetime(2015,1,11)
    assert len(periods) == 10

def test_consumption_periods_arbitrary(consumption_data_kWh_arbitrary):
    periods = consumption_data_kWh_arbitrary.periods()
    assert periods[0].start == datetime(2015,1,1)
    assert periods[9].end == datetime(2015,1,11)
    assert len(periods) == 10

def test_consumption_data_average_daily_consumtions_interval(consumption_data_kWh_interval):
    values, n_days = consumption_data_kWh_interval.average_daily_consumptions()
    assert_allclose(values, np.tile(1, consumption_data_kWh_interval.data.values.shape),
            rtol=RTOL, atol=ATOL)
    assert_allclose(n_days, np.tile(1, consumption_data_kWh_interval.data.values.shape),
            rtol=RTOL, atol=ATOL)

def test_consumption_data_average_daily_consumtions_arbitrary(consumption_data_kWh_arbitrary):
    values, n_days = consumption_data_kWh_arbitrary.average_daily_consumptions()
    assert_allclose(values, np.tile(1, (10,)),
            rtol=RTOL, atol=ATOL)
    assert_allclose(n_days, np.tile(1, (10,)),
            rtol=RTOL, atol=ATOL)

def test_consumption_data_total_days_interval(consumption_data_kWh_interval):
    n_days = consumption_data_kWh_interval.total_days()
    assert_allclose(n_days, 10,
            rtol=RTOL, atol=ATOL)

def test_consumption_data_total_days_arbitrary(consumption_data_kWh_arbitrary):
    n_days = consumption_data_kWh_arbitrary.total_days()
    assert_allclose(n_days, 10,
            rtol=RTOL, atol=ATOL)

def test_total_days_blank_consumption(consumption_data_blank):
    consumption_data_blank = ConsumptionData([], "electricity", "kWh", "arbitrary_start")
    assert consumption_data_blank.total_days() == 0

def test_consumption_data_total_period_arbitrary(
        consumption_data_kWh_arbitrary):
    period = consumption_data_kWh_arbitrary.total_period()
    assert period.start == datetime(2015,1,1)
    assert period.end == datetime(2015,1,11)

def test_total_period_blank_consumption(consumption_data_blank):
    assert consumption_data_blank.total_period() == None

def test_consumption_data_filter_by_period_arbitrary(
        consumption_data_kWh_arbitrary):
    period = Period(datetime(2015,1,1), datetime(2015,1,3))
    filtered_data = consumption_data_kWh_arbitrary.filter_by_period(period).data
    assert_allclose(filtered_data, np.array([1,1,np.nan]),
            rtol=RTOL, atol=ATOL)
    assert filtered_data.index[0] == datetime(2015,1,1)
    assert filtered_data.index[2] == datetime(2015,1,3)

    period = Period(datetime(2014,1,1), datetime(2014,1,3,1))
    filtered_data = consumption_data_kWh_arbitrary.filter_by_period(period).data
    assert_allclose(filtered_data, [],
            rtol=RTOL, atol=ATOL)

    period = Period(None, datetime(2015,1,3))
    filtered_data = consumption_data_kWh_arbitrary.filter_by_period(period).data
    assert_allclose(filtered_data, np.array([1,1,np.nan]),
            rtol=RTOL, atol=ATOL)
    assert filtered_data.index[0] == datetime(2015,1,1)
    assert filtered_data.index[2] == datetime(2015,1,3)

    period = Period(datetime(2015,1,9),None)
    filtered_data = consumption_data_kWh_arbitrary.filter_by_period(period).data
    assert_allclose(filtered_data, np.array([1,1,np.nan]),
            rtol=RTOL, atol=ATOL)
    assert filtered_data.index[0] == datetime(2015,1,9)
    assert filtered_data.index[2] == datetime(2015,1,11)

    period = Period(None,None)
    filtered_data = consumption_data_kWh_arbitrary.filter_by_period(period).data
    assert_allclose(filtered_data, np.array([1,1,1,1,1,1,1,1,1,1,np.nan]),
            rtol=RTOL, atol=ATOL)
    assert filtered_data.index[0] == datetime(2015,1,1)
    assert filtered_data.index[10] == datetime(2015,1,11)

def test_consumption_data_filter_by_period_interval(
        consumption_data_kWh_interval):

    period = Period(datetime(2015,1,1), datetime(2015,1,3))
    filtered_data = consumption_data_kWh_interval.filter_by_period(period).data
    assert_allclose(filtered_data, np.array([1,1,1]),
            rtol=RTOL, atol=ATOL)
    assert filtered_data.index[0] == datetime(2015,1,1)
    assert filtered_data.index[2] == datetime(2015,1,3)

    period = Period(datetime(2014,1,1), datetime(2014,1,3,1))
    filtered_data = consumption_data_kWh_interval.filter_by_period(period).data
    assert_allclose(filtered_data, [],
            rtol=RTOL, atol=ATOL)

    period = Period(None, datetime(2015,1,3))
    filtered_data = consumption_data_kWh_interval.filter_by_period(period).data
    assert_allclose(filtered_data, np.array([1,1,1]),
            rtol=RTOL, atol=ATOL)
    assert filtered_data.index[0] == datetime(2015,1,1)
    assert filtered_data.index[2] == datetime(2015,1,3)

    period = Period(datetime(2015,1,9),None)
    filtered_data = consumption_data_kWh_interval.filter_by_period(period).data
    assert_allclose(filtered_data, np.array([1,1]),
            rtol=RTOL, atol=ATOL)
    assert filtered_data.index[0] == datetime(2015,1,9)
    assert filtered_data.index[1] == datetime(2015,1,10)

    period = Period(None,None)
    filtered_data = consumption_data_kWh_interval.filter_by_period(period).data
    assert_allclose(filtered_data, np.array([1,1,1,1,1,1,1,1,1,1]),
            rtol=RTOL, atol=ATOL)
    assert filtered_data.index[0] == datetime(2015,1,1)
    assert filtered_data.index[9] == datetime(2015,1,10)

def test_consumption_data_init_from_interval_data(
        consumption_data_kWh_interval):
    cd = ConsumptionData(records=None,
            fuel_type=consumption_data_kWh_interval.fuel_type,
            unit_name=consumption_data_kWh_interval.unit_name,
            data=consumption_data_kWh_interval.data,
            estimated=consumption_data_kWh_interval.estimated,
            freq=consumption_data_kWh_interval.freq)
    cd.freq_timedelta is not None

    with pytest.raises(ValueError):
        cd = ConsumptionData(records=None,
                fuel_type=consumption_data_kWh_interval.fuel_type,
                unit_name=consumption_data_kWh_interval.unit_name,
                data=consumption_data_kWh_interval.data,
                freq=consumption_data_kWh_interval.freq)

    with pytest.raises(ValueError):
        cd = ConsumptionData(records=[],
                fuel_type=consumption_data_kWh_interval.fuel_type,
                unit_name=consumption_data_kWh_interval.unit_name,
                data=consumption_data_kWh_interval.data,
                estimated=consumption_data_kWh_interval.estimated,
                freq=consumption_data_kWh_interval.freq)

def test_consumption_data_init_from_arbitrary_data(
        consumption_data_kWh_arbitrary):
    cd = ConsumptionData(records=None,
            fuel_type=consumption_data_kWh_arbitrary.fuel_type,
            unit_name=consumption_data_kWh_arbitrary.unit_name,
            data=consumption_data_kWh_arbitrary.data,
            estimated=consumption_data_kWh_arbitrary.estimated)
    cd.freq_timedelta is None

    with pytest.raises(ValueError):
        cd = ConsumptionData(records=None,
                fuel_type=consumption_data_kWh_arbitrary.fuel_type,
                unit_name=consumption_data_kWh_arbitrary.unit_name,
                data=consumption_data_kWh_arbitrary.data)

    with pytest.raises(ValueError):
        cd = ConsumptionData(records=[],
                fuel_type=consumption_data_kWh_arbitrary.fuel_type,
                unit_name=consumption_data_kWh_arbitrary.unit_name,
                data=consumption_data_kWh_arbitrary.data,
                estimated=consumption_data_kWh_arbitrary.estimated)


def test_unit_conversion():
    records = [{
        "start": datetime(2015, 1, i+1),
        "end": datetime(2015, 1, i+2),
        "value": 1
    } for i in range(3)]

    cd_Wh = ConsumptionData(records, "electricity", "Wh", record_type="arbitrary")
    cd_kWh = ConsumptionData(records, "electricity", "kWh", record_type="arbitrary")
    cd_kwh = ConsumptionData(records, "electricity", "kwh", record_type="arbitrary")
    cd_therm = ConsumptionData(records, "electricity", "therm", record_type="arbitrary")
    cd_therms = ConsumptionData(records, "electricity", "therms", record_type="arbitrary")
    assert_allclose(cd_Wh.data.values, [0.001, 0.001, 0.001, np.nan])
    assert_allclose(cd_kWh.data.values, [1, 1, 1, np.nan])
    assert_allclose(cd_kwh.data.values, [1, 1, 1, np.nan])
    assert_allclose(cd_therm.data.values, [1, 1, 1, np.nan])
    assert_allclose(cd_therms.data.values, [1, 1, 1, np.nan])
    assert cd_Wh.unit_name == "kWh"
    assert cd_kWh.unit_name == "kWh"
    assert cd_kwh.unit_name == "kWh"
    assert cd_therm.unit_name == "therm"
    assert cd_therms.unit_name == "therm"
