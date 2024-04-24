#!/usr/bin/env python

"""Tests for `casas_measures` package."""

import pytest
import datetime
import pytz
import pandas as pd

from casas_measures import casas_measures, casas_data_parse
#from casas_measures.summarize_data import get_data_df

@pytest.fixture(params=[('tm000.20211107-20211108_20230321.225843_utc.txt', 'tm000.20211107-20211108_20230321.230212_local.txt'),
                        ('tm000.20211107-20211108_20230321.230212_local.txt', 'tm019.20211107-20211108_20230321.230407.txt')])
def dstfilepairs(request):
    return request.param



def test_always_passes():
    # baseline passing test
    assert True
    
@pytest.mark.xfail
def test_always_fails():
    # baseline failing test
    assert False
    
    
def test_raw_dates(utc_local_raw_pairs):
    utc_path, local_path = utc_local_raw_pairs
    utc = pytz.UTC
    local = pytz.timezone('US/Pacific')
    with open(utc_path) as fhand:
        utc_line = fhand.readline()
        line_cells = utc_line.rstrip().split('\t')
        utc_date = utc.normalize(utc.localize(datetime.datetime.fromisoformat(line_cells[0])))
    with open(local_path) as fhand:
        local_line = fhand.readline()
        line_cells = local_line.rstrip().split('\t')
        local_date = local.normalize(local.localize(datetime.datetime.fromisoformat(line_cells[0])))
        
    assert utc_date == local_date
# def test_utcdata_is_utc(utc_local_pairs):
#     utc_df, local_df = utc_local_pairs
#     local2utc = local_df.index.tz_convert(pytz.utc)
#     assert utc_df.index[0] == local2utc[0]
    
def test_utcdata_is_not_local(utc_local_pairs):
    utc_df, local_df = utc_local_pairs
    #local2utc = local_df.index.tz_convert(pytz.utc)
    assert utc_df.index[0] == local_df.index[0]
    
def test_timezones_local_dfs(localtz_df_locs):
    df = pd.read_pickle(localtz_df_locs)
    assert df.index.tz == pytz.timezone('US/Pacific')
    
def test_timezones_utc_dfs(utctz_df_locs):
    df = pd.read_pickle(utctz_df_locs)
    assert df.index.tz == pytz.utc
    
def test_inverse_coded_index(utc_inverse_coded_paths):
    df = pd.read_pickle(utc_inverse_coded_paths)
    df.index.tz_convert(pytz.utc)
    assert df.index.is_monotonic_increasing
    
    
@pytest.fixture
def dst_days(dstfilepairs):
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')
    


def test_dst_parse(dst_days):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
