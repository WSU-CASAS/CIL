# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 17:20:35 2022

@author: Wuestney

Module for summarizing sensor event counts from full observation period of CIL participants
"""


import pathlib
import sys
import datetime
import pandas as pd
import numpy as np
#import json
import yaml


#from memory_profiler import profile

from casas_measures.casas_data_parse import InactivitySeq, make_foutpath, SensorData, RoomTranSeq, BatterySeq

with open("../cil_data_params_corrected.yml", 'r') as paramfile:
    data_params = yaml.safe_load(paramfile)
FILELOCS = data_params['FILELOCS']

UTCFILELOCS = data_params['UTCFILELOCS']

SHDATA_DIR = pathlib.Path(data_params['SHDATA_DIR'])

IGNORE_SENSORS = data_params['IGNORE_SENSORS']

IGNORE_TIMEFRAMES = data_params['IGNORE_TIMEFRAMES']

SENSORS_COMBINED = data_params['SENSORS_COMBINED']

INCLUDE_TIMEFRAMES = data_params['INCLUDE_TIMEFRAMES']

BIWEEKLYWINDOW = data_params['BIWEEKLYWINDOW']
#%%
def get_fullobs_file(ptid, utc=True, **kwargs):
    #dict storing the location of the full data file for each pt_id

    #utc = True
    if utc:
        fpath = SHDATA_DIR / UTCFILELOCS[ptid]
        fpath.resolve()
        
    #local = False
    #if local:
    else:
        fpath = SHDATA_DIR / FILELOCS[ptid]
        fpath.resolve()
    return fpath

def add_inverse_code_col(data, sh_df):
    #adds a column with an integer code assigned to each sensor name
    sensorseq = data.get_sensor_seq()
    eventnames, inverse_coded = np.unique(sensorseq, return_inverse=True)
    sh_df = sh_df.assign(Inverse_Coded=inverse_coded)
    sh_df['Inverse_Coded'] = sh_df['Inverse_Coded'].astype('int8', copy=False)
    return sh_df

def get_data_df(ptid, file=None, load_as='Base', inverse_coded=True, ignore=False, combine=None, **kwargs):
    #wrapper to initiate SensorData instance from raw data file and return as pandas dataframe
    #inverse_coded = kwargs.get('inverse_coded', True)
    load_as_dict = {'Base':SensorData, 'InactivitySeq':InactivitySeq, 'RoomTranSeq':RoomTranSeq, 'BatterySeq':BatterySeq}
    pkl_df = kwargs.get('pkl_df', None)
    if pkl_df:
        fpath = file
        sh_df = pd.read_pickle(fpath)
    else:
        if file:
            fpath = pathlib.Path(file)
        else:
            fpath = get_fullobs_file(ptid, **kwargs)
        if ignore:
            data = load_as_dict[load_as](fpath, ignore=IGNORE_SENSORS[ptid], **kwargs)
        else:
            data = load_as_dict[load_as](fpath, **kwargs)
        if combine:
            try:
                combine_names = SENSORS_COMBINED[ptid]
                for new_name, old_names in combine_names.items():
                    print("For ", ptid, " combining ", old_names, " into ", new_name)
                data.combine_sensors(old_names, new_name, inplace=True)
            except KeyError:
                pass
        print(f"{ptid} sensor set: {data.sensors}")
        print(f"{ptid} number of sensors: {len(data.sensors)}")
    
        sh_df = pd.DataFrame.from_records(data.data, index='DateTime')
        if inverse_coded:
            sh_df = add_inverse_code_col(data, sh_df)
    return sh_df

def get_inactivity_df(ptid, file=None, inverse_coded=True, ignore=False, combine=False, **kwargs):
    # wrapper to load InactivitySeq instance from file and return as panda dataframe
    # if ignore is True, will ignore the sensors listed for ptid in the default yaml file
    # all sensor events from ignored sensors will be removed from the dataset entirely and time intervals will be calculated accordingly
    # if combine is True, then will combine sensors to the new name listed for ptid in the default yaml file
    
    if file:
        fpath = pathlib.Path(file)
    else:
        fpath = get_fullobs_file(ptid, **kwargs)
        
    if ignore:
        data = InactivitySeq(fpath, ignore=IGNORE_SENSORS[ptid], **kwargs)
    else:
        data = InactivitySeq(fpath, **kwargs)
        
    if combine:
        try:
            combine_names = SENSORS_COMBINED[ptid]
            for new_name, old_names in combine_names.items():
                print("For ", ptid, " combining ", old_names, " into ", new_name)
            data.combine_sensors(old_names, new_name, inplace=True)
        except KeyError:
            pass
    print(f"{ptid} sensor set: {data.sensors}")
    print(f"{ptid} number of sensors: {len(data.sensors)}")

    sh_df = pd.DataFrame.from_records(data.data, index='DateTime')
    # sensorseq = data.get_sensor_seq()
    # eventnames, inverse_coded = np.unique(sensorseq, return_inverse=True)
    # sh_df['inverse_coded'] = inverse_coded
    # sh_df['inverse_coded'] = sh_df['inverse_coded'].astype('int8', copy=False)
    if inverse_coded:
        sh_df = add_inverse_code_col(data, sh_df)
    return sh_df

def list_of_included_dfs(ptid, inverse_coded):
    # WILL THROW ERROR FOR TEST DATA
    included = []

    for timeframe in INCLUDE_TIMEFRAMES[ptid]:
        included.append(inverse_coded.loc[timeframe[0]:timeframe[1]])
    #inverse_coded = inverse_coded.loc[inverse_coded.index.difference(inverse_coded.index[inverse_coded.index.slice_indexer(timeframe[0], timeframe[1])])]
    #ignored_seg = inverse_coded[~inverse_coded.loc[timeframe[0]:timeframe[1]]]
    #print(included)
    return included

def pkl_all_dfs(**kwargs):
    utc = kwargs.get('utc', True)
    #print(utc)
    file_suffix = kwargs.get('file_suffix', '')
    if file_suffix:
        file_suffix = "_" + file_suffix
    if utc:
        kwargs['tz'] = 'utc'
        kwargs['localtz'] = 'US/Pacific'
        for ptid in UTCFILELOCS.keys():
            sh_df = get_data_df(ptid, inverse_coded=True, **kwargs)
            print(sh_df.head())
            print(sh_df.shape)
            outdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
            outname = f"{ptid}_utc2pst_df{file_suffix}.pkl"
            outpath = outdir / outname
            sh_df.to_pickle(outpath)
            outname2 = f"{ptid}_utc2pst_inversecoded{file_suffix}.pkl"
            outpath2 = outdir / outname2
            sh_df['Inverse_Coded'].to_pickle(outpath2)
    else:
        for ptid in FILELOCS.keys():
            sh_df = get_data_df(ptid, inverse_coded=True, **kwargs)
                
            outdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data\local_dfs")
            outname = f"{ptid}_local_df{file_suffix}.pkl"
            outpath = outdir / outname
            sh_df.to_pickle(outpath)
            outname2 = f"{ptid}_inversecoded{file_suffix}.pkl"
            outpath2 = outdir / outname2
            sh_df['Inverse_Coded'].to_pickle(outpath2)

def pkl_all_inactivity_coded(**kwargs):
    # for each participant, load a pandas dataframe, add inactivity labels, and add inverse integer code column
    # then pickle the dataframe
    utc = kwargs.get('utc', False)
    kwargs['ignore'] = kwargs.get('ignore', True)
    file_suffix = kwargs.get('file_suffix', '')
    if file_suffix:
        file_suffix = "_" + file_suffix
    if utc:
        kwargs['tz']='utc'
        kwargs['localtz'] = 'US/Pacific'
        for ptid in UTCFILELOCS.keys():
            sh_df = get_inactivity_df(ptid, inverse_coded=True, combine=False, **kwargs)
            
            outdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
            outname = f"{ptid}_utc2pst_df_inactseq{file_suffix}.pkl"
            outpath = outdir / outname
            sh_df.to_pickle(outpath)
            outname2 = f"{ptid}_utc2pst_inversecoded_inactseq{file_suffix}.pkl"
            outpath2 = outdir / outname2
            sh_df['Inverse_Coded'].to_pickle(outpath2)
    else:
        for ptid in FILELOCS.keys():
            sh_df = get_inactivity_df(ptid, inverse_coded=True, ignore=True, combine=False, **kwargs)
            
            outdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data\inactivity_integer_coded")
            outname = f"{ptid}_inactivityseq_integercoded.pkl"
            outpath = outdir / outname
            sh_df['Inverse_Coded'].to_pickle(outpath)
        

def rolling_unique(sh_df, ptid):
    # only works with inverse coded column
    #rollingunique = sh_df.rolling(50, step=5).apply(lambda arr: pd.Series.nunique(arr))
    rollingunique = sh_df['Inverse_Coded'].rolling(50, step=5).apply(lambda arr: len(np.unique(arr)[0]), raw=True)
    return rollingunique

def summarize_rolling_fixed(sh_df, ptid, window_size, step_size):
    included = list_of_included_dfs(ptid, sh_df)
    windowcounted = []
    for ser in included:
        window_index = ser.index[::step_size]
        count_sers = []
        for window in ser.rolling(window_size, step=step_size, closed='left'):
            if len(window) < window_size:
                pass
            else:
                index = window.index[-1]
                arr = window['Sensor'].value_counts()
                arr = arr.rename(index)
                count_sers.append(arr)
        windowcounts = pd.DataFrame(count_sers)
        windowcounted.append(windowcounts)
    windowcounts_df = pd.concat(windowcounted)
    return windowcounts_df

def summarize_sh_df(sh_df, ptid, outdir=None, file_suffix="", **kwargs):
    summary_dfs = {}
    weeklycounts = sh_df.resample("W-MON").count()
    summary_dfs['weeklycounts'] = weeklycounts
    summary_dfs['dailycounts'] = sh_df.resample("D").count()

    summary_dfs['weeklysensorcounts'] = (sh_df.groupby('Sensor')
                        .resample('W-MON').count().unstack('Sensor'))['Sensor']
    
    summary_dfs['dailysensorcounts'] = (sh_df.groupby('Sensor')
                        .resample('D').count().unstack('Sensor'))['Sensor']
    if outdir:
        if file_suffix:
            file_suffix = "_" + file_suffix
        outdir = outdir / "summarized_data"
        if not outdir.is_dir():
            outdir.mkdir(parents=True)
        weeklytotal_outpath = outdir/ f"{ptid}_weeklycounts{file_suffix}.csv"
        weeklytotal_outpath.resolve()
        weeklycounts.to_csv(weeklytotal_outpath)
        dailytotal_outpath = outdir / f"{ptid}_dailycounts{file_suffix}.csv"
        dailytotal_outpath.resolve()
        summary_dfs['dailycounts'].to_csv(dailytotal_outpath)
        weeklysensor_outpath = outdir / f"{ptid}_weeklysensorcounts{file_suffix}.csv"
        weeklysensor_outpath.resolve()
        summary_dfs['weeklysensorcounts'].to_csv(weeklysensor_outpath)
        dailysensor_outpath = outdir / f"{ptid}_dailysensorcounts{file_suffix}.csv"
        dailysensor_outpath.resolve()
        summary_dfs['dailysensorcounts'].to_csv(dailysensor_outpath)
    return summary_dfs

def summarize_battery_df(sh_df, ptid, outdir=None, file_suffix="", **kwargs):
    summary_dfs = {}
    battery_pct = sh_df.loc[sh_df['SensorType'].isin(['Control4-BatteryPercent']), :]
    #%%
    battery_pct['Message'] = battery_pct['Message'].astype('int64')
    weeklymeans = (battery_pct.groupby('Sensor').resample("W-MON").mean().unstack('Sensor')['Message'])
    dailymeans = (battery_pct.groupby('Sensor').resample("D").mean().unstack('Sensor')['Message'])
    summary_dfs['weeklymeans'] = weeklymeans
    summary_dfs['dailymeans'] = dailymeans
    
    if outdir:
        if file_suffix:
            file_suffix = "_" + file_suffix
        outdir = outdir / "summarized_data"
        if not outdir.is_dir():
            outdir.mkdir(parents=True)
        weeklytotal_outpath = outdir/ f"{ptid}_battery_weeklymeans{file_suffix}.csv"
        weeklytotal_outpath.resolve()
        weeklymeans.to_csv(weeklytotal_outpath)
        dailytotal_outpath = outdir / f"{ptid}_battery_dailymeans{file_suffix}.csv"
        dailytotal_outpath.resolve()
        summary_dfs['dailymeans'].to_csv(dailytotal_outpath)
    return summary_dfs


def summarize_inact_sh_df(sh_df, ptid, outdir=None, file_suffix="", **kwargs):
    summary_dfs = {}
    #inact_labels = ['T1', 'T2', 'T3', 'T4', 'T5']
    inact_labels = sh_df[sh_df['Sensor'].isin(['T1', 'T2', 'T3', 'T4', 'T5'])]
    weeklycounts = inact_labels.resample("W-MON").count()
    summary_dfs['weeklycounts'] = weeklycounts
    summary_dfs['dailycounts'] = inact_labels.resample("D").count()

    summary_dfs['weeklysensorcounts'] = (inact_labels.groupby('Sensor')
                        .resample('W-MON').count().unstack('Sensor'))['Sensor']
    
    summary_dfs['dailysensorcounts'] = (inact_labels.groupby('Sensor')
                        .resample('D').count().unstack('Sensor'))['Sensor']
    if outdir:
        if file_suffix:
            file_suffix = "_" + file_suffix
        outdir = outdir / "summarized_data"
        if not outdir.is_dir():
            outdir.mkdir(parents=True)
        weeklytotal_outpath = outdir/ f"{ptid}_inact_weeklycounts{file_suffix}.csv"
        weeklytotal_outpath.resolve()
        weeklycounts.to_csv(weeklytotal_outpath)
        dailytotal_outpath = outdir / f"{ptid}_inact_dailycounts{file_suffix}.csv"
        dailytotal_outpath.resolve()
        summary_dfs['dailycounts'].to_csv(dailytotal_outpath)
        weeklysensor_outpath = outdir / f"{ptid}_inact_weeklysensorcounts{file_suffix}.csv"
        weeklysensor_outpath.resolve()
        summary_dfs['weeklysensorcounts'].to_csv(weeklysensor_outpath)
        dailysensor_outpath = outdir / f"{ptid}_inact_dailysensorcounts{file_suffix}.csv"
        dailysensor_outpath.resolve()
        summary_dfs['dailysensorcounts'].to_csv(dailysensor_outpath)
    return summary_dfs


def get_summary_dfs(ptid, inact=False, file_suffix="", **kwargs):
    #file_suffix allows the addition of any other info to end of csv filename
    #default is empty string
    if file_suffix:
        file_suffix = "_" + file_suffix
    if inact:
        outdir = SHDATA_DIR / "summarized_data"
        summary_dfs = {}
        weeklytotal_outpath = outdir/ f"{ptid}_inact_weeklycounts{file_suffix}.csv"
        weeklytotal_outpath.resolve()
        summary_dfs['weeklycounts'] = pd.read_csv(weeklytotal_outpath)
        dailytotal_outpath = outdir / f"{ptid}_inact_dailycounts{file_suffix}.csv"
        dailytotal_outpath.resolve()
        summary_dfs['dailycounts'] = pd.read_csv(dailytotal_outpath)
        weeklysensor_outpath = outdir / f"{ptid}_inact_weeklysensorcounts{file_suffix}.csv"
        weeklysensor_outpath.resolve()
        summary_dfs['weeklysensorcounts'] = pd.read_csv(weeklysensor_outpath)
        dailysensor_outpath = outdir / f"{ptid}_inact_dailysensorcounts{file_suffix}.csv"
        dailysensor_outpath.resolve()
        summary_dfs['dailysensorcounts'] = pd.read_csv(dailysensor_outpath)
    else:
        outdir = SHDATA_DIR / "summarized_data"
        summary_dfs = {}
        weeklytotal_outpath = outdir/ f"{ptid}_weeklycounts{file_suffix}.csv"
        weeklytotal_outpath.resolve()
        summary_dfs['weeklycounts'] = pd.read_csv(weeklytotal_outpath)
        dailytotal_outpath = outdir / f"{ptid}_dailycounts{file_suffix}.csv"
        dailytotal_outpath.resolve()
        summary_dfs['dailycounts'] = pd.read_csv(dailytotal_outpath)
        weeklysensor_outpath = outdir / f"{ptid}_weeklysensorcounts{file_suffix}.csv"
        weeklysensor_outpath.resolve()
        summary_dfs['weeklysensorcounts'] = pd.read_csv(weeklysensor_outpath)
        dailysensor_outpath = outdir / f"{ptid}_dailysensorcounts{file_suffix}.csv"
        dailysensor_outpath.resolve()
        summary_dfs['dailysensorcounts'] = pd.read_csv(dailysensor_outpath)
    return summary_dfs


def summarize_inactivity_counts(ptid, from_file=False, file_suffix="", **kwargs):
    
    # ignore and combine parameters used to compute for raw data
    # ignore = False
    # combine = False
    
    # ignore and combine parameters used to compute for data data
    if from_file:
        summary_dfs = get_summary_dfs(ptid, inact=True, file_suffix=file_suffix)
        weeklycounts = summary_dfs['weeklycounts']
    else:
        sh_df = get_inactivity_df(ptid, inverse_coded=False, **kwargs)
        summary_dfs = summarize_inact_sh_df(sh_df, ptid, outdir=SHDATA_DIR, file_suffix=file_suffix, **kwargs)
        weeklycounts = summary_dfs['weeklycounts']
    with pd.option_context('display.max_rows', None):
        print("Summary of ", ptid)
        print("Count of Sensor and Inactivity Events per Week")
        print(weeklycounts)
        #print("Count of Sensor and Inactivity Events per Day")
        #print(summary_dfs['dailycounts'])
        print("Count of Sensor and Inactivity Events per Sliding 2-Week Window")
        print(weeklycounts.rolling(2).sum())
        print("Minimum Weekly Count: ", weeklycounts["Sensor"].min())
        print("Maximum Weekly Count: ", weeklycounts["Sensor"].max())
        print("Mean Weekly Count: ", weeklycounts["Sensor"].mean())
        #print("Mean Weekly Count Excluding Weeks with <10000 events: ", weeklycounts["Sensor"][weeklycounts["Sensor"]>10000].mean())
        print("Summary Table of Weekly Counts")
        print(weeklycounts.describe(percentiles=[.25, .5, .75]))
        print("Weekly Counts of Each Inactivity Level")
        print(summary_dfs['weeklysensorcounts'].loc[:,'T1':'T5'])
        print("Summary Table of Weekly Inactivity Counts")
        print(summary_dfs['weeklysensorcounts'].loc[:,'T1':'T5'].describe(percentiles=[.25, .5, .75]))
        print("--------------------------------")
        print("\n")
   
def summarize_sensor_counts(ptid, from_file=False, file_suffix="", **kwargs):
    if from_file:
        summary_dfs = get_summary_dfs(ptid, file_suffix= file_suffix)
        weeklycounts = summary_dfs['weeklycounts']
    else:
        sh_df = get_data_df(ptid, inverse_coded=False, **kwargs)
        summary_dfs = summarize_sh_df(sh_df, ptid, outdir=SHDATA_DIR, file_suffix=file_suffix, **kwargs)
        weeklycounts = summary_dfs['weeklycounts']
    with pd.option_context('display.max_rows', None):
        print("Summary of ", ptid)
        print("Count of Sensor Events per Week")
        print(weeklycounts)
        print("Count of Sensor Events per Day")
        print(summary_dfs['dailycounts'])
        print("Count of Sensor Events per Sliding 2-Week Window")
        print(weeklycounts.rolling(2).sum())
        print("Minimum Weekly Count: ", weeklycounts["Sensor"].min())
        print("Maximum Weekly Count: ", weeklycounts["Sensor"].max())
        print("Mean Weekly Count Excluding Weeks: ", weeklycounts["Sensor"].mean())
        print("Mean Weekly Count Excluding Weeks with <10000 events: ", weeklycounts["Sensor"][weeklycounts["Sensor"]>10000].mean())
        print("Summary Table of Weekly Counts")
        print(weeklycounts.describe(percentiles=[.25, .5, .75]))
        print("Summary Table of Weekly Counts per Sensor")
        print(summary_dfs['weeklysensorcounts'].describe(percentiles=[.25, .5, .75]))
        print("--------------------------------")
        print("\n")
        
        
def summarize_sensor_and_inact_counts(ptid, from_file=False, file_suffix="", **kwargs):
    kwargs['load_as'] = kwargs.get('load_as', 'InactivitySeq')
    if from_file:
        # outdir = SHDATA_DIR / "summarized_data"
        # summary_dfs = {}
        # weeklytotal_outpath = outdir/ f"{ptid}_weeklycounts.csv"
        # weeklytotal_outpath.resolve()
        # weeklycounts = pd.read_csv(weeklytotal_outpath)
        # dailytotal_outpath = outdir / f"{ptid}_dailycounts.csv"
        # dailytotal_outpath.resolve()
        # summary_dfs['dailycounts'] = pd.read_csv(dailytotal_outpath)
        # weeklysensor_outpath = outdir / f"{ptid}_weeklysensorcounts.csv"
        # weeklysensor_outpath.resolve()
        # summary_dfs['weeklysensorcounts'] = pd.read_csv(weeklysensor_outpath)
        # dailysensor_outpath = outdir / f"{ptid}_dailysensorcounts.csv"
        # dailysensor_outpath.resolve()
        # summary_dfs['dailysensorcounts'] = pd.read_csv(dailysensor_outpath)
        summary_dfs = get_summary_dfs(ptid, file_suffix=file_suffix)
        weeklycounts = summary_dfs['weeklycounts']
    else:
        sh_df = get_data_df(ptid, inverse_coded=True, **kwargs)
        summary_dfs = summarize_sh_df(sh_df, ptid, outdir=SHDATA_DIR, file_suffix=file_suffix, **kwargs)
        weeklycounts = summary_dfs['weeklycounts']
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print("Summary of ", ptid)
        #print("Count of Sensor and Inactivity Events per Week")
        #print(weeklycounts)
        print("Count of Sensor and Inactivity Events per Sliding 2-Week Window")
        print(weeklycounts.rolling(2).sum())
        print("Minimum Weekly Count: ", weeklycounts["Sensor"].min())
        print("Maximum Weekly Count: ", weeklycounts["Sensor"].max())
        print("Mean Weekly Count Excluding Weeks: ", weeklycounts["Sensor"].mean())
        #print("Mean Weekly Count Excluding Weeks with <10000 events: ", weeklycounts["Sensor"][weeklycounts["Sensor"]>10000].mean())
        print("Summary Table of Weekly Counts")
        print(weeklycounts.describe(percentiles=[.25, .5, .75]))
        print("Summary Table of Weekly Counts per Sensor")
        print(summary_dfs['weeklysensorcounts'].describe(percentiles=[.25, .5, .75]))
        print("Summary Table of Daily Counts per Sensor")
        print(summary_dfs['dailysensorcounts'].describe(percentiles=[.25, .5, .75]))
        print("--------------------------------")
        print("\n")


if __name__ == "__main__":
    get_timeints = False
    if get_timeints:
        for ptid in FILELOCS.keys():
            fdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
            fname = f'{ptid}_utc2pst_df_sensorsonly_ignored.pkl'
            fpath = fdir / fname
            sh_df = pd.read_pickle(fpath)
            timeints = sh_df['Time_Interval']
            outpath = fdir / f'{ptid}_utc2pst_timeints_sensorsonly_ignored.pkl'
            timeints.to_pickle(outpath)
            
    get_timeints_ONonly = False
    if get_timeints_ONonly:
        for ptid in FILELOCS.keys():
            fdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
            fname = f"{ptid}_utc2pst_df_ONsensorsonly_ignored.pkl"
            fpath = fdir / fname
            sh_df = pd.read_pickle(fpath)
            timeints = sh_df['Time_Interval']
            outpath = fdir / f'{ptid}_utc2pst_timeints_ONsensorsonly_ignored.pkl'
            timeints.to_pickle(outpath)
            
    pickle_inactivity_ignore = False
    # ptid = "tm015"
    # sh_df = get_fullobs_df(ptid)
    #summary_dfs = summarize_sh_df(sh_df, outdir=SHDATA_DIR)
    if pickle_inactivity_ignore:
        pkl_all_inactivity_coded(utc=True, file_suffix='ignored_newcutofs', ignore=True)
        
    
    run_roomtran_counts = False
    if run_roomtran_counts:
        for ptid in FILELOCS.keys():
            summarize_sensor_and_inact_counts(ptid, load_as='RoomTranSeq', from_file=False, ignore=True, file_suffix='_roomtran_utc2pst_ignored', utc=True, localtz='US/Pacific')
    
    run_summarize_sensor_counts = False
    if run_summarize_sensor_counts:
        #summarize_sensor_counts("tm017", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm017\tm017.20191209-20210428_20230425.233443_utc_everything.txt"), file_suffix='everything_utc', ignore=False, utc=True, load_as='BatterySeq', localtz='US/Pacific')
        #summarize_sensor_counts("tm033", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm033\tm033.20220824-20231128_20240130.170833.txt"), ignore=False, utc=False, localtz='US/Pacific')
        #summarize_sensor_counts("tm003", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm003\tm003.20161122-20181227_20240130.205126.txt"), ignore=False, utc=False, localtz='US/Pacific')
        #summarize_sensor_counts("tm014", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm014\tm014.20190322-20200702_20240130.211035.txt"), ignore=False, utc=False, localtz='US/Pacific')
        #summarize_sensor_counts("tm024", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm024\tm024.20210927-20221104_20240130.211526.txt"), ignore=False, utc=False, localtz='US/Pacific')
        #summarize_sensor_counts("tm029", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm029\tm029.20220419-20230428_20240130.212216.txt"), ignore=False, utc=False, localtz='US/Pacific')
        #summarize_sensor_counts("tm030", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm030\tm030.20220428-20230502_20240130.213204.txt"), ignore=False, utc=False, localtz='US/Pacific')
        summarize_sensor_counts("tm040", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm040\tm040.20230215-20231016_20240130.214815.txt"), ignore=False, utc=False, localtz='US/Pacific')
    
    run_raw_counts = False
    if run_raw_counts:
        for ptid in FILELOCS.keys():
            summarize_sensor_and_inact_counts(ptid, from_file=True)
            
    #summarize_sensor_and_inact_counts("test", from_file=False, file_suffix="sensors_ignored", ignore=True)
    run_ignore_inact_counts = False
    if run_ignore_inact_counts:
        for ptid in FILELOCS.keys():
            summarize_inactivity_counts(ptid, from_file=False, file_suffix="sensors_ignored", ignore=True)
    
    run_ignore_combine_counts = False
    if run_ignore_combine_counts:
        combine_pt = ['tm006', 'tm017', 'tm021']
        for ptid in combine_pt:
            summarize_inactivity_counts(ptid, from_file=False, file_suffix="sensors_ignored_combined", ignore=True, combine=True)
    
    test_dst = False
    if test_dst:
        
        #sh_df = get_data_df("test", inverse_coded=True)
        # localized_df = get_inactivity_df("tm019", utc=True, tz='utc', localtz='US/Pacific')
        # print("Is localized index monotic increasing?", localized_df.index.is_monotonic_increasing)
        # bool_mask = localized_df.sort_index().index == localized_df.index
        # print("Non-increasing dates", localized_df.loc[np.invert(bool_mask)])
        # utc_df = get_inactivity_df("tm019", utc=True, tz='utc')
        # print("Is utc index monotic increasing?", utc_df.index.is_monotonic_increasing)
        # bool_mask2 = utc_df.sort_index().index == utc_df.index
        # print("Non-increasing dates", utc_df.loc[np.invert(bool_mask2)])
        fpath = get_fullobs_file("tm019", utc=True)
        data = InactivitySeq(fpath, tz='utc')
        sh_df = pd.DataFrame.from_records(data.data, index='DateTime')
        
    pickle_dfs_ignored = False
    if pickle_dfs_ignored:
        pkl_all_dfs(utc=True, file_suffix='sensorsonly_ignored', ignore=True, load_as='Base')
        
    pickle_dfs = False
    if pickle_dfs:
        pkl_all_dfs(utc=True, file_suffix='sensorsonly_all', ignore=False, load_as='Base')
        
    pickle_roomtrans = False
    if pickle_roomtrans:
        pkl_all_dfs(utc=True, file_suffix='roomtran_all', load_as='RoomTranSeq', ignore=False)
        
    pickle_roomtrans_ignore = False
    if pickle_roomtrans_ignore:
        pkl_all_dfs(utc=True, file_suffix='roomtran_ignored_newcutoffs', ignore=True, load_as='RoomTranSeq')
        
    pickle_roomtrans_ignore_sensonly = False
    if pickle_roomtrans_ignore_sensonly:
        print(UTCFILELOCS)
        pkl_all_dfs(utc=True, file_suffix='roomtran_sensorsonly_ignored', ignore=True, load_as='RoomTranSeq', insert_inact=False)
        
    pickle_roomtrans_ignore_4rooms = False
    if pickle_roomtrans_ignore_4rooms:
        print(UTCFILELOCS)
        pkl_all_dfs(utc=True, file_suffix='roomtran_4rooms_ignored', ignore=True, load_as='RoomTranSeq', insert_inact=False, rooms=['BedroomA', 'BathroomA', 'LivingRoomA', 'KitchenA'])
        
    pickle_coded_from_roomtrans_dfs = False
    if pickle_coded_from_roomtrans_dfs:
        for ptid in FILELOCS.keys():
            fdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data\utc_dfs")
            fname = f"{ptid}_utc_df_roomtran.pkl"
            fpath = fdir / fname
            sh_df = pd.read_pickle(fpath)
            outdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data\roomtran_integer_coded")
            outname = f"{ptid}_utc_roomtran_integercoded.pkl"
            outpath = outdir / outname
            sh_df['Inverse_Coded'].to_pickle(outpath)
            
    summarize_from_roomtrans_dfs = False
    if summarize_from_roomtrans_dfs:
        for ptid in FILELOCS.keys():
            if ptid == 'test':
                continue
            else:
                fdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
                fname = f"{ptid}_utc2pst_df_roomtran_sensorsonly_ignored.pkl"
                fpath = fdir / fname
                sh_df = pd.read_pickle(fpath)
                outdir = pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\summarized_data")
                #summary_dfs = summarize_sh_df(sh_df, ptid, outdir=SHDATA_DIR, file_suffix="roomtran")
                summary_dfs = get_summary_dfs(ptid, file_suffix="roomtran")
                weeklycounts = summary_dfs['weeklycounts']
                biweeklywin = weeklycounts['Sensor'].rolling(2).sum().max()
                biweeklywin = int(biweeklywin)
                biweeklycounts = summarize_rolling_fixed(sh_df, ptid, biweeklywin, step_size=None)
                biweeklycounts.to_csv(f'{ptid}_utc_biweekly_roomtrans_counts.csv')
                with pd.option_context('display.max_rows', None):
                    print("Summary of ", ptid)
                    print("Count of Sensor Events per Week")
                    print(weeklycounts)
                    print("Count of Sensor Events per Day")
                    print(summary_dfs['dailycounts'])
                    print("Count of Sensor Events per Sliding 2-Week Window")
                    print(weeklycounts.rolling(2).sum())
                    print("Minimum Weekly Count: ", weeklycounts["Sensor"].min())
                    print("Maximum Weekly Count: ", weeklycounts["Sensor"].max())
                    print("Mean Weekly Count Excluding Weeks: ", weeklycounts["Sensor"].mean())
                    print("Mean Weekly Count Excluding Weeks with <10000 events: ", weeklycounts["Sensor"][weeklycounts["Sensor"]>10000].mean())
                    print("Summary Table of Weekly Counts")
                    print(weeklycounts.describe(percentiles=[.25, .5, .75]))
                    print("Summary Table of Weekly Counts per Sensor")
                    print(summary_dfs['weeklysensorcounts'].describe(percentiles=[.25, .5, .75]))
                    print("Summary Table of Counts per Sensor per Sliding Window")
                    print(biweeklycounts.describe(percentiles=[.25, .5, .75]))
                    print("--------------------------------")
                    print("\n")
       
    summarize_sensor_counts_biweekly = False
    if summarize_sensor_counts_biweekly:
        for ptid in FILELOCS.keys():
            if ptid == 'test':
                continue
            else:
                fdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
                #file suffix associated with inverse coded used for analysis for GSA paper
                fname = f"{ptid}_utc2pst_df_ONsensorsonly_ignored.pkl"
                fpath = fdir / fname
                sh_df = pd.read_pickle(fpath)
            
                WINDOW_SIZE = BIWEEKLYWINDOW[ptid][0]
                
                STEP_SIZE = WINDOW_SIZE // 4
                biweeklycounts = summarize_rolling_fixed(sh_df, ptid, WINDOW_SIZE, step_size=STEP_SIZE)
                print(f"{ptid}")
                print(biweeklycounts.head())
                print("-----------------------------")
                biweeklycounts.to_csv(SHDATA_DIR/ f'{ptid}_utc2pst_biweekly_Onsensorsonly_counts.csv')
                
        
    check_data_dfs = False
    if check_data_dfs:
        ptid = 'test'
        base_df = get_data_df(ptid, load_as='Base')
        inact_df = get_data_df(ptid, load_as="InactivitySeq")
        inact_df2 = get_inactivity_df(ptid)
        room_tran_df = get_data_df(ptid, load_as='RoomTranSeq', utc=False)
        
    summarize_battery = False
    if summarize_battery:
        # sh_df = get_data_df("tm017", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm017\tm017.20191209-20210428_20230425.233443_utc_everything.txt"), utc=True, load_as='BatterySeq', localtz='US/Pacific',ignore=False)
        # summarize_battery_df(sh_df, "tm017", outdir=SHDATA_DIR, file_suffix='everything_utc')
        sh_df = get_data_df("tm002", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm002\tm002.20180101-20190101_20230618.225831_utc_everything.txt"), utc=True, load_as='BatterySeq', localtz='US/Pacific',ignore=False)
        #%%

        #summary_dfs['weeklymeans'] = weeklymeans
        #summary_dfs['dailymeans'] = dailymeans
        radio_errors = sh_df.loc[sh_df['SensorType'].isin(['Control4-Radio_error']), :]
        #summary_dfs = summarize_sh_df(sh_df, 'tm002', outdir=SHDATA_DIR, file_suffix='everything_utc_radioall')
        summary_dfs = summarize_battery_df(sh_df, "tm002", outdir=SHDATA_DIR, file_suffix='everything_utc_batpercent')
        #%%
    summarize_tm019_battery = False
    if summarize_tm019_battery:
        # sh_df = get_data_df("tm017", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm017\tm017.20191209-20210428_20230425.233443_utc_everything.txt"), utc=True, load_as='BatterySeq', localtz='US/Pacific',ignore=False)
        # summarize_battery_df(sh_df, "tm017", outdir=SHDATA_DIR, file_suffix='everything_utc')
        sh_df = get_data_df("tm019", file=pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\tm019\tm019.20210708-20220602_20230622.215358_everything_utc.txt"), utc=True, load_as='BatterySeq', localtz='US/Pacific',ignore=False)
        #%%

        #summary_dfs['weeklymeans'] = weeklymeans
        #summary_dfs['dailymeans'] = dailymeans
        radio_errors = sh_df.loc[sh_df['SensorType'].isin(['Control4-Radio_error']), :]
        summarize_sh_df(sh_df, 'tm019', outdir=SHDATA_DIR, file_suffix='everything_utc_radioall')
        summarize_sh_df(radio_errors, 'tm019', outdir=SHDATA_DIR, file_suffix='everything_utc_radioerrors')
        summarize_battery_df(sh_df, "tm019", outdir=SHDATA_DIR, file_suffix='everything_utc_batpercent')
        
    ignore_sensorsonly_ignoreOFF = False
    if ignore_sensorsonly_ignoreOFF:
        for ptid in FILELOCS.keys():
            load_as_dict = {'Base':SensorData, 'InactivitySeq':InactivitySeq, 'RoomTranSeq':RoomTranSeq, 'BatterySeq':BatterySeq}
            #for ptid in FILELOCS.keys():
            fpath = get_fullobs_file(ptid, utc=True)
            kwargs = {}
            kwargs['tz']='utc'
            kwargs['localtz'] = 'US/Pacific'
            data = SensorData(fpath, ignore={'Sensor':IGNORE_SENSORS[ptid], 'Message':['OFF', 'CLOSE']}, **kwargs)
    
            print(f"{ptid} sensor set: {data.sensors}")
            print(f"{ptid} number of sensors: {len(data.sensors)}")
        
            sh_df = pd.DataFrame.from_records(data.data, index='DateTime')
            #sh_df = sh_df.loc['2019-12-10':]
            #add inverse coded column
            sh_df = add_inverse_code_col(data, sh_df)
                
            outdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
            outname = f"{ptid}_utc2pst_df_ONsensorsonly_ignored.pkl"
            outpath = outdir / outname
            sh_df.to_pickle(outpath)
            outname2 = f"{ptid}_utc2pst_inversecoded_ONsensorsonly_ignored.pkl"
            outpath2 = outdir / outname2
            sh_df['Inverse_Coded'].to_pickle(outpath2)
    
    ignore_inact_ignoreOFF = False
    if ignore_inact_ignoreOFF:
        for ptid in FILELOCS.keys():
            #load_as_dict = {'Base':SensorData, 'InactivitySeq':InactivitySeq, 'RoomTranSeq':RoomTranSeq, 'BatterySeq':BatterySeq}
            #for ptid in FILELOCS.keys():
            fpath = get_fullobs_file(ptid, utc=True)
            kwargs = {}
            kwargs['tz']='utc'
            kwargs['localtz'] = 'US/Pacific'
            data = InactivitySeq(fpath, ignore={'Sensor':IGNORE_SENSORS[ptid], 'Message':['OFF', 'CLOSE']}, **kwargs)
    
            print(f"{ptid} sensor set: {data.sensors}")
            print(f"{ptid} number of sensors: {len(data.sensors)}")
        
            sh_df = pd.DataFrame.from_records(data.data, index='DateTime')
            #sh_df = sh_df.loc['2019-12-10':]
            #add inverse coded column
            sh_df = add_inverse_code_col(data, sh_df)
                
            outdir = pathlib.Path(r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data")
            outname = f"{ptid}_utc2pst_df_ONinact_ignored.pkl"
            outpath = outdir / outname
            sh_df.to_pickle(outpath)
            outname2 = f"{ptid}_utc2pst_inversecoded_ONinact_ignored.pkl"
            outpath2 = outdir / outname2
            sh_df['Inverse_Coded'].to_pickle(outpath2)
            
    tm026_unique_included = False
    if tm026_unique_included:
        ptid = 'tm026'
        sh_df = get_data_df(ptid, file=r"C:\Users\Wuestney\Documents\GitHub\casas_measures\data\tm026_utc2pst_df_ONsensorsonly_ignored.pkl",
                            pkl_df=True, inverse_coded=False)
        included = list_of_included_dfs(ptid, sh_df)
        included_df = pd.concat(included)
        included_codes = included_df['Inverse_Coded'].unique()
        included_codes.sort()
        print(included_codes)
        #print(included_df['Sensor'].unique())
        print(sh_df[sh_df['Inverse_Coded'] == 4]['Sensor'])
        
    run_summarize_sensor_counts_tm010 = False
    if run_summarize_sensor_counts_tm010:
        ptid = 'tm010'
        fpath = get_fullobs_file(ptid, utc=True)
        kwargs = {}
        kwargs['tz']='utc'
        kwargs['localtz'] = 'US/Pacific'
        data = SensorData(fpath, ignore={'Sensor':IGNORE_SENSORS[ptid], 'Message':['OFF', 'CLOSE']}, **kwargs)

        print(f"{ptid} sensor set: {data.sensors}")
        print(f"{ptid} number of sensors: {len(data.sensors)}")
    
        sh_df = pd.DataFrame.from_records(data.data, index='DateTime')
        included = list_of_included_dfs(ptid, sh_df)
        included_df = pd.concat(included)
        
        file_suffix = 'ONsensorsonly_visitors_rm'
        summary_dfs = summarize_sh_df(included_df, ptid, outdir=SHDATA_DIR, file_suffix=file_suffix, **kwargs)
        weeklycounts = summary_dfs['weeklycounts']
        with pd.option_context('display.max_rows', None):
            print("Summary of ", ptid)
            print("Count of Sensor Events per Sliding 2-Week Window")
            print(weeklycounts.rolling(2).sum())
            print("Maximum 2-week Sliding Window")
            print(weeklycounts.rolling(2).sum().max())
            print("Minimum Weekly Count: ", weeklycounts["Sensor"].min())
            print("Maximum Weekly Count: ", weeklycounts["Sensor"].max())
            print("Mean Weekly Count Excluding Weeks: ", weeklycounts["Sensor"].mean())
            print("Mean Weekly Count Excluding Weeks with <10000 events: ", weeklycounts["Sensor"][weeklycounts["Sensor"]>10000].mean())
            print("Summary Table of Weekly Counts")
            print(weeklycounts.describe(percentiles=[.25, .5, .75]))
            print("Summary Table of Weekly Counts per Sensor")
            print(summary_dfs['weeklysensorcounts'].describe(percentiles=[.25, .5, .75]))
            print("--------------------------------")
            print("\n")
            
    run_summarize_sensor_counts_tm006 = False
    if run_summarize_sensor_counts_tm006:
        ptid = 'tm006'
        fpath = get_fullobs_file(ptid, utc=True)
        kwargs = {}
        kwargs['tz']='utc'
        kwargs['localtz'] = 'US/Pacific'
        data = SensorData(fpath, ignore={'Sensor':IGNORE_SENSORS[ptid], 'Message':['OFF', 'CLOSE']}, **kwargs)
    
        print(f"{ptid} sensor set: {data.sensors}")
        print(f"{ptid} number of sensors: {len(data.sensors)}")
    
        sh_df = pd.DataFrame.from_records(data.data, index='DateTime')
        included = list_of_included_dfs(ptid, sh_df)
        included_df = pd.concat(included)
        
        file_suffix = 'ONsensorsonly_visitors_rm'
        summary_dfs = summarize_sh_df(included_df, ptid, outdir=SHDATA_DIR, file_suffix=file_suffix, **kwargs)
        weeklycounts = summary_dfs['weeklycounts']
        with pd.option_context('display.max_rows', None):
            print("Summary of ", ptid)
            print("Count of Sensor Events per Sliding 2-Week Window")
            print(weeklycounts.rolling(2).sum())
            print("Maximum 2-week Sliding Window")
            print(weeklycounts.rolling(2).sum().max())
            print("Minimum Weekly Count: ", weeklycounts["Sensor"].min())
            print("Maximum Weekly Count: ", weeklycounts["Sensor"].max())
            print("Mean Weekly Count Excluding Weeks: ", weeklycounts["Sensor"].mean())
            print("Mean Weekly Count Excluding Weeks with <10000 events: ", weeklycounts["Sensor"][weeklycounts["Sensor"]>10000].mean())
            print("Summary Table of Weekly Counts")
            print(weeklycounts.describe(percentiles=[.25, .5, .75]))
            print("Summary Table of Weekly Counts per Sensor")
            print(summary_dfs['weeklysensorcounts'].describe(percentiles=[.25, .5, .75]))
            print("--------------------------------")
            print("\n")
    #if check_indexes:
        #for ptid in FILELOCS.keys():
            
    # sh_df = add_inverse_code_col(data, sh_df)
    
    #sh_df = get_inactivity_df("test")
    #countsensors = sh_df.nunique()
    #rollingcounts = rolling_unique(sh_df['inverse_coded'], 'test')
        
    run_summarize_sensor_counts_fulldata = True
    if run_summarize_sensor_counts_fulldata:
        fileloc = pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\full_datasets")
        ids = ["tm005", "tm004", "tm008", "tm009", "tm011", "tm012", "tm020", "tm022", "tm027", "tm036", "tm037", "tm038", "tm039", "tm041"]
        ids2 = ["tm035", "tm042", "tm043"]
        for ptid in ids2:
            file = list(fileloc.glob(f"{ptid}*.txt"))
            print(file)
            summarize_sensor_counts(ptid, file=file[0], ignore=False, utc=False, localtz='US/Pacific')
    
        