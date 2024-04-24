# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 16:49:23 2020

@author: wuest
"""

import pathlib
import datetime
import pytz
import yaml
import copy
#import sqlite3
#from itertools import repeat

with open("../cil_data_params_strict.yml", 'r') as paramfile:
    data_params = yaml.safe_load(paramfile)
FILELOCS = data_params['FILELOCS']

UTCFILELOCS = data_params['UTCFILELOCS']

SHDATA_DIR = pathlib.Path(data_params['SHDATA_DIR'])


def write_header(foutname, testbed_sensors):
    with open(foutname, 'w') as output:
        output.write('utc_timestamp,utc_epoch,local_timestamp')
        for sen_dict in testbed_sensors:
            output.write(',{}_{}'.format(sen_dict['target'], sen_dict['sensor_type']))
        output.write('\n')
    #output.close()
    return

def write_state(output, stamp, testbed_sensors, sensor_state, timezone):
    epoch = (stamp - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
    stamp_local = pytz.utc.localize(stamp.replace(tzinfo=None),is_dst=None).astimezone(timezone)
    output.write('{}'.format(stamp))
    output.write(',{}'.format(epoch))
    output.write(',{}'.format(stamp_local))
    for sen_dict in testbed_sensors:
       output.write(',{}'.format(sensor_state[sen_dict['sen_key']]))
    output.write('\n')
    return    

file_to_open = SHDATA_DIR / UTCFILELOCS['test']


#get timezone
TZ = pytz.utc
LOCAL = pytz.timezone('US/Pacific')
#dt_end=PDT.localize(datetime.datetime(2018, 4, 6, 0, 0, 0))

#get data from file
sen_keys = list()
testbed_sensors = list()
raw_data = list()
with open(file_to_open) as fhand:
    for line in fhand:
        line = line.rstrip().split('\t')
        sen_key='{}{}'.format(line[1], line[3])
        stamp_utc = datetime.datetime.fromisoformat(line[0])
        stamp_utc = TZ.normalize(TZ.localize(stamp_utc))
        local_stamp = copy.deepcopy(stamp_utc)
        local_stamp = LOCAL.normalize(local_stamp.astimezone(LOCAL))
        event = {'stamp_utc':stamp_utc, 'stamp_local':local_stamp, 'target': line[1], 'message': line[2], 'sensor_type':line[3], 'sen_key':sen_key}

        #since we are parsing all of the data we don't need to build in a stop date
        #if local_stamp > dt_end:
            #break
        #else:
        raw_data.append(event)
        if sen_key not in sen_keys:
            sen_keys.append(sen_key)
            testbed_sensors.append(dict({'target': line[1], 'sensor_type':line[3], 'sen_key':sen_key}))
    print("RAW DATA", raw_data[0:2], "...", raw_data[-2:])
    print("TESTBED SENSORS", testbed_sensors[0:10])

#create dict containing current sensor state
#assume initial sensor state is 'OFF"  
sensor_state = dict()
for sen_dict in testbed_sensors:
    sensor_state[sen_dict['sen_key']]='OFF'




#get the sensor state at the start of the data from the first 5000 events
# for row in raw_data[0:8000]:
#     sen_key = row['sen_key']
#     sensor_state[sen_key]=row['message']
# print(sensor_state)

foutname = 'test_upsampled.csv'

#write output header
write_header(foutname, testbed_sensors)

#%%
#open output file for appending
with open(foutname, 'a') as output:

    #sample at 1 second intervals
    utc_end = raw_data[-1]['stamp_utc']     
    time_delta = datetime.timedelta(seconds=1)
    current_time = raw_data[0]['stamp_utc']
    raw_pointer = 0
    count=0
    while current_time < utc_end:
        while raw_pointer<len(raw_data) and raw_data[raw_pointer]['stamp_utc'] <= current_time:
            sensor_state[raw_data[raw_pointer]['sen_key']]=raw_data[raw_pointer]['message']
            raw_pointer +=1
        write_state(output=output, stamp=current_time, testbed_sensors=testbed_sensors, sensor_state=sensor_state, timezone=LOCAL)
        if (count % 100)==0:
            print('iteration at {}, with a range of {} left to go.'.format(current_time, (utc_end-current_time)))
        count +=1
        current_time = current_time + time_delta

print(output.closed)

# if __name__ == '__main__':
#     if run = True:
        