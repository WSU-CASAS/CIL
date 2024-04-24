# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 15:43:57 2023

@author: Wuestney
"""

import pathlib
import sys
import datetime
import pandas as pd
import numpy as np
#import json
import yaml

from casas_measures import casas_data_parse, pattern_search

out_folder = pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\bfit_bcd_data")

ptids = ["tm006", "tm010", "tm013", "tm014", "tm019", "tm024", "tm025", "tm029", "tm030",
         "tm031", "tm032", "tm033", "tm034", "tm040"]
ptids2 = ["tm002", "tm003", "tm007", "tm033", "tm034", "tm015", "tm017", "tm018"]

ptids3 = ["tm007"]

data_locs = {"tm002": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm002\tm002.20180426-20180524_bfitbaseline.txt",
                      "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm002\tm002.20180524-20180705_bfitintervention.txt"},
             "tm003": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm003\tm003.20180426-20180524_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm003\tm003.20180524-20180705_bfitintervention.txt"},
             "tm006": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm006\tm006.20180424-20180522_bfitbaseline.txt", 
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm006\tm006.20180522-20180703_bfitintervention.txt"},
             "tm007": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm007\tm007.20180503-20180531_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm007\tm007.20180531-20180705_bfitintervention.txt"},
             "tm010": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm010\tm010.20190422-20190520_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm010\tm010.20190520-20190624_bfitintervention.txt"},
             "tm013": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm013\tm013.20190422-20190520_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm013\tm013.20190520-20190624_bfitintervention.txt"},
             "tm014": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm014\tm014.20190422-20190520_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm014\tm014.20190520-20190624_bfitintervention.txt"},
             "tm015": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm015\tm015.20200828-20200925_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm015\tm015.20200925-20201030_bfitintervention.txt"},
             "tm017": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm017\tm017.20200615-20200720_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm017\tm017.20200720-20200902_bfitintervention.txt"},
             "tm018": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm018\tm018.20210827-20210924_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm018\tm018.20210924-20211029_bfitintervention.txt"},
             "tm019": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm019\tm019.20210924-20211022_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm019\tm019.20211022-20211218_bfitintervention.txt"},
             "tm024": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm024\tm024.20220207-20220307_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm024\tm024.20220307-20220419_bfitintervention.txt"},
             "tm025": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm024\tm025.20220221-20220321_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm024\tm025.20220321-20220509_bfitintervention.txt"},
             "tm029": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm029\tm029.20220602-20220630_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm029\tm029.20220630-20220812_bfitintervention.txt"},
             "tm030": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm030\tm030.20220923-20221021_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm030\tm030.20221021-20221123_bfitintervention.txt"},
             "tm031": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm030\tm031.20220920-20221018_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm030\tm031.20221018-20221123_bfitintervention.txt"},
             "tm032": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm032\tm032.20230619-20230717_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm032\tm032.20230717-20230814_bfitintervention.txt"},
             "tm033": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm033\tm033.20230103-20230131_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm033\tm033.20230509-20230607_bfitintervention.txt"},
             "tm034": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm033\tm034.20230106-20230203_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm033\tm034.20230428-20230614_bfitintervention.txt"},
             "tm040": {"pre": r"C:\Users\Wuestney\Documents\SHdata_raw\tm040\tm040.20230517-20230614_bfitbaseline.txt",
                       "sesh": r"C:\Users\Wuestney\Documents\SHdata_raw\tm040\tm040.20230614-20230728_bfitintervention.txt"}}
tm018_pre = r"C:\Users\Wuestney\Documents\SHdata_raw\tm018\tm018.20210827-20210924_bfitbaseline.txt"
tm018_sesh = r"C:\Users\Wuestney\Documents\SHdata_raw\tm018\tm018.20210924-20211029_bfitintervention.txt"

tm017_pre = r"C:\Users\Wuestney\Documents\SHdata_raw\tm017\tm017.20200615-20200720_bfitbaseline.txt"
tm017_sesh = r"C:\Users\Wuestney\Documents\SHdata_raw\tm017\tm017.20200720-20200902_bfitintervention.txt"

tm015_pre = r"C:\Users\Wuestney\Documents\SHdata_raw\tm015\tm015.20200828-20200925_bfitbaseline.txt"
tm015_sesh = r"C:\Users\Wuestney\Documents\SHdata_raw\tm015\tm015.20200925-20201030_bfitintervention.txt"

def extract_bfit_windows(file, outpath):
    filepath = pathlib.Path(file)
    
    data = casas_data_parse.SensorData(filepath, add_timeint=False)
    
    namepatterns = list(data.get_sensor_set())
    memorybook = pattern_search.SensorSeries(data, namepatterns, namepatterns_tag='all')
    morningtime = datetime.time(10, 0)
    eveningtime = datetime.time(18, 0)
    memorybook.find(morning_time=morningtime, evening_time=eveningtime)
    
    #%%
    episodes = memorybook.episodes.list
    day1 = episodes[0]
    flat_episodes = []
    for episode in episodes:
        flat_episodes += episode
        
    casas_data_parse.write_data_to_csv(flat_episodes, foutname=outpath, fieldnames=['DateTime', 'Sensor', 'Message'], extrasaction='ignore', dialect='excel-tab')
    
def format_bfit_bcd(file, outpath):
    filepath = pathlib.Path(file)
    
    data = casas_data_parse.SensorData(filepath, add_timeint=False)
    
    casas_data_parse.write_to_bcd_format(data, foutname=outpath)
    return

for ptid in ptids3:
    pre_out = out_folder / f"{ptid}_baseline"
    sesh_out = out_folder / f"{ptid}_intervention"
    format_bfit_bcd(data_locs[ptid]['pre'], pre_out)
    format_bfit_bcd(data_locs[ptid]['sesh'], sesh_out)
#extract_bfit_windows(tm018_pre, tm018_pre_out)
