# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 14:36:05 2023

@author: Wuestney
"""

import pytest
import os, pathlib
import yaml
import pandas as pd

#from casas_measures.summarize_data import get_data_df

module_dir = pathlib.Path(os.path.dirname(__file__)).parent

paramspath = module_dir / 'cil_data_params.yml'
with open(os.path.join(module_dir, 'cil_data_params.yml'), 'r') as paramfile:
    data_params = yaml.safe_load(paramfile)

FILELOCS = data_params['FILELOCS']

UTCFILELOCS = data_params['UTCFILELOCS']

SHDATA_DIR = pathlib.Path(data_params['SHDATA_DIR'])

IGNORE_SENSORS = data_params['IGNORE_SENSORS']

IGNORE_TIMEFRAMES = data_params['IGNORE_TIMEFRAMES']

INCLUDE_TIMEFRAMES = data_params['INCLUDE_TIMEFRAMES']

SENSORS_COMBINED = data_params['SENSORS_COMBINED']

PTIDS = list(FILELOCS.keys())


@pytest.fixture(scope='session')
def module_dir():
    test_dir = pathlib.Path(os.path.dirname(__file__))
    module_dir = test_dir.parent / "casas_measures"
    return module_dir

@pytest.fixture(scope='session')
def pkg_dir():
    return pathlib.Path(os.path.dirname(__file__)).parent

@pytest.fixture(scope='session', params=PTIDS)
def utc_inverse_coded_paths(request, pkg_dir):
    ptid = request.param
    fname = f"data/inactivity_integer_coded/cleaned_from_utc_data/{ptid}_utc_inactivityseq_integercoded.pkl"
    path = pkg_dir / fname
    return path

@pytest.fixture(scope='session')
def cil_data_params(module_dir):
    with open(os.path.join(module_dir, 'cil_data_params.yml'), 'r') as paramfile:
        data_params = yaml.safe_load(paramfile)
    return data_params

@pytest.fixture(scope='session')
def shdata_dir():
    return SHDATA_DIR
    
@pytest.fixture(scope='session')
def pkldfs_dir(pkg_dir):
    data_dir = pkg_dir / "data"
    return data_dir

@pytest.fixture(scope='session')
def ignore_sensors():
    return IGNORE_SENSORS

@pytest.fixture(scope='session', params=PTIDS)
def localtz_df_locs(request, pkldfs_dir):
    ptid = request.param
    fileloc = f"local_dfs/{ptid}_local_df.pkl"
    path = pkldfs_dir / fileloc
    return path

@pytest.fixture(scope='session', params=PTIDS)
def utctz_df_locs(request, pkldfs_dir):
    ptid = request.param
    fileloc = f"utc_dfs/{ptid}_utc_df.pkl"
    path = pkldfs_dir / fileloc
    return path

@pytest.fixture(scope='session', params=PTIDS)
def utc_local_pairs(request, pkldfs_dir):
    ptid = request.param
    local_file = f"local_dfs/{ptid}_local_df.pkl"
    utc_file = f"utc_dfs/{ptid}_utc_df.pkl"
    path_local = pkldfs_dir / local_file
    path_utc = pkldfs_dir / utc_file

    local_df = pd.read_pickle(path_local)
    utc_df = pd.read_pickle(path_utc)
    if ptid == "tm015":
        local_df = local_df.loc['12/10/2019':]
        utc_df = utc_df.loc['12/10/2019':]
    elif ptid == 'tm018':
        local_df = local_df.loc['7/14/2021':]
        utc_df = utc_df.loc['7/14/2021':]
    else:
        pass
    return utc_df, local_df

@pytest.fixture(scope='session', params=PTIDS)
def localtz_file_locs(request, shdata_dir):
    ptid = request.param
    fileloc = FILELOCS[ptid]
    path = shdata_dir / fileloc
    return path

@pytest.fixture(scope='session', params=PTIDS)
def utctz_file_locs(request, shdata_dir):
    ptid = request.param
    fileloc = UTCFILELOCS[ptid]
    path = shdata_dir / fileloc
    return path

@pytest.fixture(scope='session', params=PTIDS)
def utc_local_raw_pairs(request, shdata_dir):
    ptid = request.param
    local_file = FILELOCS[ptid]
    utc_file = UTCFILELOCS[ptid]
    path_local = shdata_dir / local_file
    path_utc = shdata_dir / utc_file
    return path_utc, path_local