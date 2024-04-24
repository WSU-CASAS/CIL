# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 13:27:09 2022

@author: Wuestney
"""
import bisect
import copy
import csv
import datetime
import pytz
import pathlib
from tqdm import tqdm
import re

def parse_data(file_to_read, tz='US/Pacific'):
    """
    DEPRECATED VERSION. USE get_data() INSTEAD.
    reads smart home data from a tab delimited text file.

    Parameters
    ----------
    file_to_read : PATH OBJECT
        PATH OF CASAS FILE TO PARSE.
    tz : STRING
        STRING REPRESENTING THE TIME ZONE TO BE USED TO CREATE PYTZ TIMEZONE OBJECT.
        The default is 'US/Pacific'.

    Returns
    -------
    A list of dicts containing sensor event info stored as key:value pairs.

    """
    #PDT=pytz.timezone(tz)
    data=[]
    with open(file_to_read) as fread:
        try:
            for line in fread:
                if line.rstrip():
                    line_cells = line.rstrip().split('\t')
                    #local_stamp = PDT.localize(datetime.fromisoformat(line_cells[0]))
                    local_stamp = datetime.datetime.fromisoformat(line_cells[0])
                    event={'DateTime': local_stamp, 'Sensor': line_cells[1],  'Message': line_cells[2]}
                    data.append(event)
        except Exception as exc:
            raise RuntimeError("Invalid input.") from exc

    return data


def get_header(fread):
    line_str=fread.readline()
    line=line_str.rstrip().split()
    return line

def get_annotated_data(data, fread):
    """
    This function takes a file object corresponding to a previously annotated CASAS tab delimited data file
    and reads the header names and data lines and returns a list of dicts where each key in the dict is a column name
    and the value is the data occuring at that index of that column in the file line.

    This function is used inside get_data() if user indicates file header present.

    Parameters
    ----------
    data : LIST
        LIST OF DICTS OR EMPTY LIST TO CONTAIN THE KEY/VALUE PAIRS OF THE DATA FILE.
    fread : OPEN FILE HANDLE
        FILE OBJECT CONTAINING THE PREVIOUSLY CLEANED AND ANNOTATED CASAS DATA.

    Returns
    -------
    None.

    """
    headers=get_header(fread)
    dtime=headers.index('DateTime')
    sensor=headers.index('Sensor')
    message=headers.index('Message')
    tint=headers.index('Time_Interval')
    try:
        primhs=headers.index('Prim_HS')
    except ValueError:
        primhs=None
    try:
        sechs=headers.index('Sec_HS')
    except ValueError:
        sechs=None
    try:
        otherhs=headers.index('Other_HS')
    except ValueError:
        otherhs=None
    try:
        tx=headers.index('TX')
    except ValueError:
        tx=None
    try:
        activity=headers.index('Activity')
    except ValueError:
        activity=None
    try:
        notes=headers.index('Notes')
    except ValueError:
        notes=None
    for line in fread:
        if line.rstrip():
            line_cells = line.split('\t')
            #local_stamp = PDT.localize(datetime.datetime.fromisoformat(line_cells[0]))
            local_stamp = datetime.datetime.fromisoformat(line_cells[dtime])
            event={'DateTime': local_stamp, 'Sensor': line_cells[sensor],  'Message': line_cells[message], 'Time_Interval':line_cells[tint]}
            if primhs:
                event['Prim_HS']=line_cells[primhs]
            else:
                event['Prim_HS']=None
            if sechs:
                event['Sec_HS']=line_cells[sechs]
            else:
                event['Sec_HS']=None
            if otherhs:
                event['Other_HS']=line_cells[otherhs]
            else:
                event['Other_HS']=None
            if tx:
                event['TX']=line_cells[tx]
            else:
                event['TX']=None
            if activity:
                event['Activity'] = line_cells[activity]
            else:
                event['Activity']=None
            if notes:
                event['Notes'] = line_cells[notes]
            else:
                event['Notes']=None
            data.append(event)
    return

def get_data(file_to_read, tz='US/Pacific', header='N', ignore=None, inverse_ignore=False, localtz=None, everything=False, **kwargs):
    """
    reads smart home data from a tab delimited text file.

    Parameters
    ----------
    file_to_read : PATH OBJECT
        PATH OBJECT POINTING TO THE FILE CONTAINING CASAS DATA TO LOAD AND PARSE.
    tz : STRING
        STRING REPRESENTING THE TIME ZONE TO BE USED TO CREATE PYTZ TIMEZONE OBJECT.
        The default is 'US/Pacific'.
    header : STRING, optional
        USE 'header='Y'' IF THE DATA TO BE PARSED HAS BEEN ANNOTATED VIA header_template.xlsm
        The default is 'N'.
    ignore : STRING, LIST OF STRINGS, OR DICT, optional
        SENSOR NAMES TO IGNORE WHEN PARSING RAW DATA. ANY SENSOR EVENT
        WHICH MATCHES ONE OF THE SENSOR NAMES IN IGNORE WILL NOT BE ADDED TO THE LIST
        OF DATA. SENSOR NAMES MUST MATCH EXACTLY. DEFAULT IS NONE.
        IF STRING, SHOULD BE THE NAME OF A SINGLE SENSOR NAME TO IGNORE
        IF LIST, THEN SHOULD BE LIST OF SENSOR NAMES
        IF DICT, KEYS SHOULD INDICATE WHICH COLUMN TO SEARCH IN FOR NAME MATCHES.
            OPTIONS ARE, 'Sensor', 'Message', or 'SensorType'. IF 'SensorType', THEN
            EVERYTHING MUST BE SET TO TRUE, OTHERWISE WILL THROW AN ERROR. TO 
            EXCLUDE A MESSAGE FROM A PARTICULAR SENSOR NAME ONLY MAKE SURE THE KEY IS
            'Message' AND THE VALUE IS A LIST OF TUPLES OF THE FORM (SensorName, MessageName)
            *FUNCTIONALITY TO IGNORE MESSAGES IS NOT STABLE YET*
    localtz : STRING OR NONE, optional
        OPTIONAL LOCAL TIMEZONE TO LOCALIZE THE TIMESTAMPS TO IF tz IS DIFFERENT FROM 
        THE LOCAL TIMEZONE OF THE TESTBED (I.E. UTC).
    everything : BOOL, optional
        IF DATASET IS DOWNLOADED USING THE EVERYTHING SET (IE INCLUDING RELAY AND BATTERY AND RADIO MESSAGES)
        THEN USE THIS PARAMETER TO ENSURE THE 4TH COLUMN OF DATA IS CORRECTLY PARSED
    Returns
    -------
    A list of dicts containing sensor event info stored as key:value pairs.
    If names supplied to ignore, then will print the counts of each name that 
    were ignored to the console.

    """
    # is pytz timezone object for the tz parameter
    TZ = pytz.timezone(tz)
    if ignore:
        ignored = {}
        if type(ignore) is str:
            ignore = {'Sensor': [ignore]}
        elif type(ignore) is list:
            ignore = {'Sensor': ignore}
        for nameslist in ignore.values():
            names = dict.fromkeys(nameslist, 0)
            ignored.update(names)
    data=[]
    with open(file_to_read) as fread:
        try:
            if header.upper()=="Y":
                #header_skip=True
                get_annotated_data(data, fread)
            elif header.upper()=="N":
                #tqdm() wrapper prints a progress bar to the terminal
                for line in tqdm(fread):
                    if line.rstrip():
                        line_cells = line.rstrip().split('\t')
                        if ignore:
                            # ignore_sensor = line_cells[1] in ignored
                            # ignore_message = line_cells[2] in ignored
                            # ignore_sensormessage = (line_cells[1], line_cells[2]) in ignored
                            # ignore_
                            # check if Sensor name is in ignored first
                            if line_cells[1] in ignored:
                                ignored[line_cells[1]] = ignored.get(line_cells[1], 0 ) + 1
                                skip = True
                            # then check if row should be ignored based on the value in Message
                            elif line_cells[2] in ignored:
                                ignored[line_cells[2]] = ignored.get(line_cells[2], 0) + 1
                                skip = True
                            # then check if row should be ignored based on the
                            # combination of Sensor name and Message
                            elif (line_cells[1], line_cells[2]) in ignored:
                                ignored[(line_cells[1], line_cells[2])] = ignored.get((line_cells[1], line_cells[2]), 0) + 1
                                skip = True
                            # ensure there is a 4th column by checking that everything kwarg is True
                            # if the SensorType name is a key in the ignored dict then skip line
                            elif everything and line_cells[3] in ignored:
                                ignored[line_cells[3]] = ignored.get(line_cells[3], 0) + 1
                                skip = True
                            # don't skip the row
                            else:
                                skip = False
                        elif not ignore:
                            skip = False
                        if skip:
                            continue
                        else:
                            stamp = datetime.datetime.fromisoformat(line_cells[0])
                            if stamp.tzinfo is None or stamp.tzinfo.utcoffset(stamp) is None:
                                stamp = TZ.normalize(TZ.localize(stamp))
                            if localtz:
                                LOCAL = pytz.timezone(localtz)
                                local_stamp = LOCAL.normalize(stamp.astimezone(LOCAL))
                            else:
                                local_stamp = stamp
                            #local_stamp = datetime.datetime.fromisoformat(line_cells[0])
                            #event={'DateTime': local_stamp, 'UTCStamp': utc_stamp, 'Sensor': line_cells[1],  'Message': line_cells[2]}
                            # if everything is True then will include the fourth column of data under the key 'SensorType'
                            if everything:
                                event={'DateTime': local_stamp, 'Sensor': line_cells[1],  'Message': line_cells[2], 'SensorType': line_cells[3]}
                            else:
                                event={'DateTime': local_stamp, 'Sensor': line_cells[1],  'Message': line_cells[2]}
                            data.append(event)
        except Exception as exc:
            print(repr(exc))
            raise RuntimeError("Invalid input.") from exc
    if ignore:
        print("\nSensors ignored:\n", ignored)
    return data

def time_int(data, inplace=True):
    """
    takes data in the format output by get_data() or get_annotated_data().
    Default is to add a column to data containing the time intervals. To have
    time_int output a dict containing the time intervals with the keys being
    the index of the time interval instead of adding it to data, then enter
    inplace=False.

    Parameters
    ----------
    data : LIST OF DICTS
        IN THE FORMAT OF THE OUTPUT FROM get_data() or get_annotated_data().
    inplace : BOOL, optional
        DETERMINES WHETHER TO ADD THE TIME INTERVALS AS A NEW DATA COLUMN IN data,
        OR RETURN AS STAND ALONE DICT.
        The default is True.

    Returns
    -------
    timeints : TYPE
        DESCRIPTION.

    """
    if inplace:
        for i in range(1,len(data)):
            try:
                current = copy.deepcopy(data[i]['DateTime'])
                past= copy.deepcopy(data[i-1]['DateTime'])
                timeint=current-past
                data[i]['Time_Interval']=timeint
            except IndexError:
                print("cannot calculate time interval for data index {}".format(i))
                continue
        return
    else:
        timeints={}
        for i in range(1,len(data)):
            try:
                current = copy.deepcopy(data[i]['DateTime'])
                past= copy.deepcopy(data[i-1]['DateTime'])
                timeint=current-past
                timeints[i]=timeint
            except IndexError:
                print("cannot calculate time interval for data index {}".format(i))
                continue
        return timeints

def write_header(foutname, form=None):
    output = open(foutname, 'w')
    if form == 'CASAS':
        output.write('local_timestamp\tevent_name\tevent_info')
        output.write('\n')
        output.close()
    elif form == 'Annotated':
        output.write('DateTime\tSensor\tMessage\tTime_Interval\tPrim_HS\tSec_HS\tOther_HS\tTX\tActivity\tNotes')
        output.write('\n')
        output.close()
    elif form=='fatigue':
        output.write('Current_Time\tPreced_Sen_State\tCur_Sen_State\tTime_Int')
        output.write('\n')
        output.close()
    else:
        output.write('utc_timestamp,epoch,local_timestamp,event_name,event_info')
        output.write('\n')
        output.close()
    return

def get_inactivity_lab(timeint, breakpoints=[datetime.timedelta(minutes=1), datetime.timedelta(minutes=3), 
                                             datetime.timedelta(minutes=6), datetime.timedelta(minutes=20), 
                                             datetime.timedelta(minutes=60)]):
    # returns the inactivity label associated with intra-event time interval range that timeint falls within  
    #breakpoints is list of timeint breakpoints for the levels of inactivity
    # first thresholds used for breakpoints are 
    #breakpoints = [datetime.timedelta(seconds=10), datetime.timedelta(minutes=3), 
    #                   datetime.timedelta(minutes=6), datetime.timedelta(minutes=20), 
    #                   datetime.timedelta(minutes=60)]
    
    # second thresholds used for breakpoints are
    # breakpoints = [datetime.timedelta(seconds=30), datetime.timedelta(minutes=1), datetime.timedelta(minutes=2),
    #                    datetime.timedelta(minutes=3), datetime.timedelta(minutes=4), datetime.timedelta(minutes=5), datetime.timedelta(minutes=6),
    #                    datetime.timedelta(minutes=8), datetime.timedelta(minutes=10), datetime.timedelta(minutes=15), datetime.timedelta(minutes=20), 
    #                    datetime.timedelta(minutes=30), datetime.timedelta(minutes=45), datetime.timedelta(minutes=60)]
    # second intlabs
    #int_labs = [None, "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12", "T13", "T14"]
    
    #list of timeint inactivity labels to insert into sequence
    int_labs = [None, "T1", "T2", "T3", "T4", "T5"]
    i = bisect.bisect(breakpoints, timeint)
    return int_labs[i]

def make_foutpath(sensordata, suffix="inactivityseq.csv"):
    # data is instance of SensorData object
    startdate = sensordata.data[0]['DateTime']
    enddate = sensordata.data[-1]['DateTime']
    foutname = f"{sensordata.ptid}_{startdate.strftime('%Y%m%d')}_{enddate.strftime('%Y%m%d')}_{suffix}"
    outdir = pathlib.Path(sensordata.file_to_read).parent
    foutpath = outdir / foutname
    return foutpath
    
def write_data_to_csv(data, foutname=None, fieldnames=None, **kwargs):
    if not foutname:
        foutname = make_foutpath(data)
    if not fieldnames:
        fieldnames = data[0].keys()
    with open(foutname, 'w', newline='') as fout:
        writer = csv.DictWriter(fout, fieldnames, **kwargs)
        writer.writeheader()
        for event in data:
            writer.writerow(event)
    return

def write_to_bcd_format(data, foutname=None, **kwargs):
    """
    Writes casas SensorData object to data format specified by Diane for 
    behavior change detection analysis for Bfit study:
        - timezone naive timestamps
        - fields separated by single space
        - file names are either "tmXXX_baseline" or "tmXXX_intervention"

    Parameters
    ----------
    data : SensorData object.
        DESCRIPTION.
    foutname : STRING, optional
        FILENAME FOR OUTPUT FILE. The default is None.
    **kwargs : ADDITIONAL KWARGS
        DESCRIPTION.

    Returns
    -------
    Saves text file to location specified by foutname.

    """
    if not foutname:
        foutname = make_foutpath(data)
        
    with open(foutname, 'w') as fout:
        for event in data.data:
            fout.write(f"{event['DateTime'].strftime('%Y-%m-%d %H:%M:%S.%f')} {event['Sensor']} {event['Message']}\n")
        fout.close()
    return
        
        
#@profile
def insert_inactivity(data, file=None, filetype='csv', header=None):
    #take data from SensorData instance and return new sequence of timestamped activities with inactivity levels inserted
    #returns list of dicts containing only datetime stamp and activity_type (either name of sensor or inactivity label)
    # if a proper file handle to a writeable text file is provided to file, then will write the inactivity seq to file instead
    
    inactivity_seq = [data.data[0]]
    for i in tqdm(range(1, len(data))):
        #if i % 50000 == 0:
            #print(f"{(i/len(data))*100:0.0f}% complete")
        try:
            current = data.data[i]
            past= data.data[i-1]
            timeint=copy.deepcopy(current['Time_Interval'])
            inactivity_lab = get_inactivity_lab(timeint)
            if inactivity_lab:
                inactivity_datetime = past["DateTime"] + datetime.timedelta(microseconds=1)
                inactivity_seq.append({"DateTime":inactivity_datetime, "Sensor":inactivity_lab, "Time_Interval":None})
                #inactivity_seq.append({"DateTime":current["DateTime"], "Event_Name":current["Sensor"], "Time_Interval":current["Time_Interval"]})
                inactivity_seq.append(current)
            else:
                #inactivity_lab will be None if timeint is < 10 seconds, in which case no inactivity is assumed and no label inserted
                #inactivity_seq.append({"DateTime":current["DateTime"], "Event_Name":current["Sensor"], "Time_Interval":current["Time_Interval"]})
                inactivity_seq.append(current)
                
        except IndexError:
            if i == len(data):
                print("reached end of data")
            else:
                print("cannot calculate time interval for date {} at data index {}".format(current["DateTime"], i))
                continue
    return inactivity_seq

class SensorData:
    """
    Object that holds loaded sensor data as a list of dicts where each dict represents one sensor event.
    """
    __slots__ = ("file_to_read", "tz", "header", "data", "ptid", "sensors", "localtz")
    def __init__(self, file_to_read, tz='US/Pacific', ignore=None, combine=None, localtz=None, header='N', add_timeint=True, **kwargs):
        #file_to_read must be a path object pointing to a tab delimited CASAS sensor data file
        #combine should be a dict where each key is the new sensor name and the value is a list of the old sensor names to combine under the new name
        self.file_to_read=pathlib.Path(file_to_read)
        self.tz=tz
        self.localtz = localtz
        self.header=header
        self.data = get_data(self.file_to_read, tz=self.tz, header=self.header, ignore=ignore, localtz=localtz, **kwargs)
        
        if add_timeint==True:
            time_int(self.data)

        self.ptid = str(file_to_read.name)[0:5]
        self.sensors = self.get_sensor_set()
        
    def __len__(self):
        return len(self.data)
    
    def get_sensor_seq(self):
        sensor_seq = []
        for event in self.data:
            sensor_seq.append(event['Sensor'])
        return sensor_seq
    
    def get_sensor_set(self):
        sensor_seq = self.get_sensor_seq()
        names = set(sensor_seq)
        #names = {name.lower():name for name in names}
        return names
    
    def combine_sensors(self, old_names, new_name, inplace=False):
        """
        Takes a list or set of sensor names which currently exist in the data and renames
        each instance of that sensor name with the new, shared name.

        Parameters
        ----------
        old_names : LIST OR SET OF STRINGS
            LIST OF SENSOR NAMES TO BE CONSOLIDATED WITH NEW COMBINED NAME.
        new_name : STRING
            NEW NAME TO REPLACE THE OLD NAMES.
        inplace : BOOL, optional
            Default is False. WHETHER OR NOT THE NEW RENAMED SENSOR SEQUENCE SHOULD REPLACE THE
            EXISTING DATA IN THE SENSORDATA INSTANCE.

        Returns
        -------
        New SensorData object if inplace is False.

        """
        
        # to protect from sensors being missed due to spelling errors in old_names,
        # all sensors in old_names must be present in the sensor set of the SensorData instance
        old_names = set(old_names)
        assert self.sensors.issuperset(old_names), f"AT LEAST ONE SENSOR IN old_names NOT FOUND IN THE SENSOR DATA: {old_names.difference(self.sensors)}"
        assert type(new_name) is str, f"new_name IS {type(new_name)} NOT STRING"
        new_data = []
        for event in self.data:
            if event['Sensor'] in old_names:
                new_event = copy.deepcopy(event)
                new_event['Sensor'] = new_name
                new_data.append(new_event)
            else:
                new_data.append(event)
        if inplace:
            self.data = new_data
            self.sensors = self.get_sensor_set()
            return
        else:
            return new_data
        
    def write_to_csv(self, foutname, fieldnames=['DateTime', 'Sensor', 'Message', 'Time_Interval']):
        #wrapper for function write_data_to_csv()
        write_data_to_csv(self.data, foutname, fieldnames=fieldnames)
        
    @classmethod
    def straight_to_file(cls, file_to_read, outfile=None, **kwargs):
        # take raw data file, insert inactivity labels and write to file. does not return class instance
        # **kwargs takes any keyword arguments meant for SensorData.__init__() or combine_sensors()
        if not outfile:
            outfile = True
        seq = cls(file_to_read, write=outfile)
        return
#%%
class InactivitySeq(SensorData):
    """
    Object that holds loaded inactivity sequence data as a list of dicts
    """
    def __init__(self, file_to_read, from_raw=True, tz='US/Pacific', header='N', write=False, ignore=None, localtz=None, **kwargs):
        #from_raw : bool to indicate if file to read is raw sh data or data with inactivity already inserted.
        if from_raw:
            SensorData.__init__(self, file_to_read, tz=tz, header=header, ignore=ignore, localtz=localtz, **kwargs)
            write = kwargs.get('write', False)
            inactseq = self.insert_inactivity(self, write=write, **kwargs)
            self.data = inactseq
        # else:
        #     with open(file_to_read) as fhand:
        #         reader = csv.DictReader(fhand, fieldnames=['DateTime', 'Sensor', 'Message', 'Time_Interval'])
        #         for row in reader:
                    
    @staticmethod
    def insert_inactivity(data, write=False, **kwargs):
        #take data from SensorData instance and return new sequence of timestamped activities with inactivity levels inserted
        #returns list of dicts containing only datetime stamp and activity_type (either name of sensor or inactivity label)
        # if write is True, then will write the inactivity seq to file as well with filename created from ptid and dates
        # can also supply file string to write
        
        if write:
            try:
                fout = pathlib.Path(write)
            except TypeError:
                fout = make_foutpath(data)
                
            fhand = open(fout, 'w+')
            writer = csv.DictWriter(fhand, fieldnames=['DateTime', 'Sensor', 'Message', 'Time_Interval'])
            writer.writeheader()

        inactivity_seq = []
        for i in (range(1, len(data.data))):
            #if i % 50000 == 0:
             #   print(f"{(i/len(data.data))*100:0.0f}% complete")
            try:
                current = data.data[i]
                past= data.data[i-1]
                timeint=copy.deepcopy(current['Time_Interval'])
                inactivity_lab = get_inactivity_lab(timeint)
                if inactivity_lab:
                    inactivity_datetime = past["DateTime"] + datetime.timedelta(microseconds=1)
                    if write:
                        writer.writerow({"DateTime":inactivity_datetime, "Sensor":inactivity_lab, "Message":None, "Time_Interval":None})
                        writer.writerow(current)

                    inactivity_seq.append({"DateTime":inactivity_datetime, "Sensor":inactivity_lab, "Message":None, "Time_Interval":None})
                    #inactivity_seq.append({"DateTime":current["DateTime"], "Event_Name":current["Sensor"], "Time_Interval":current["Time_Interval"]})
                    inactivity_seq.append(current)
                else:
                    #inactivity_lab will be None if timeint is < 10 seconds, in which case no inactivity is assumed and no label inserted
                    #inactivity_seq.append({"DateTime":current["DateTime"], "Event_Name":current["Sensor"], "Time_Interval":current["Time_Interval"]})
                    if write:
                        writer.writerow(current)
                    inactivity_seq.append(current)
                    
            except IndexError:
                if i == len(data.data):
                    print("reached end of data")
                else:
                    print("cannot calculate time interval for date {} at data index {}".format(current["DateTime"], i))
                    continue
        if write:
            fhand.close()
        return inactivity_seq
    
#%%
def room_name(sensorname):
    room = re.compile("[A-Za-z]+?A|[A-Za-z]+?B|[A-Za-z]+?C|[A-Za-z]+?D")
    mainentry = re.compile("^Main")
    if mainentry.match(sensorname):
        roomname = 'MainEntry'
    elif room.match(sensorname):
        roomname = room.match(sensorname).group()
    else:
        roomname = sensorname
    return roomname

def convert_to_room_names(event):
    # takes raw sensor name in a sensor event and outputs same event with new sensor name 
    # new sensor name is either the room name and the target dropped or if MainEntryway or MainDoor the name is MainEntry
    # if no regex match then sensor name is unchanged
    room = re.compile("[A-Za-z]+?A|[A-Za-z]+?B|[A-Za-z]+?C|[A-Za-z]+?D")
    mainentry = re.compile("^Main")
    if mainentry.match(event['Sensor']):
        event['Sensor'] = "MainEntry"
        return event
    elif room.match(event['Sensor']):
        event['Sensor'] = room.match(event['Sensor']).group()
        return event
    else:
        return event
    
class RoomTranSeq(SensorData):
    
    def __init__(self, *args, insert_inact=True, rooms='all', include=True, **kwargs):
        kwargs['add_timeint'] = False
        #insert_inact = kwargs.get('insert_inact', True)
        SensorData.__init__(self, *args, **kwargs)
        #print(self.data[0])
        rooms_all = set([room_name(sensor) for sensor in self.sensors])
        if rooms == 'all':
            rooms = rooms_all
        else:
            if isinstance(rooms, str):
                rooms = {rooms}
            elif isinstance(rooms, list):
                rooms = set(rooms)
            if not include:
                rooms = rooms_all.difference(rooms)
                

        encoded = []
        encoded.append(convert_to_room_names(self.data[0]))
        for i in tqdm(range(1,len(self.data))):
            renamed_event = convert_to_room_names(self.data[i])
            if renamed_event['Sensor'] not in rooms:
                continue
            else:
                if encoded[-1]['Sensor'] != renamed_event['Sensor']:
                    encoded.append(renamed_event)
                else:
                    continue
        self.data = encoded
        self.sensors = self.get_sensor_set()
        time_int(self.data, inplace=True)
        if insert_inact:
            inactseq = insert_inactivity(self)
            self.data = inactseq
        
class BatterySeq(SensorData):
    
    def __init__(self, *args, **kwargs):
        kwargs['everything'] = True
        ignore = kwargs.get('ignore', {})
        if type(ignore) is not dict:
            if type(ignore) is str:
                ignore = {'Sensor': [ignore]}
            elif type(ignore) is list:
                ignore = {'Sensor': ignore}
            else:
                raise TypeError("Unrecognized datatype for ignore. Must be a string, list, or dict")
        ignored_types = ['Control4-Motion', 'Control4-LightSensor', 'Control4-Temperature']
        sensortypes = ignore.get('SensorType', [])
        sensortypes.extend(ignored_types)
        ignore['SensorType'] = sensortypes
        kwargs['ignore'] = ignore
        SensorData.__init__(self, *args, **kwargs)
    
    def write_to_csv(self, foutname):
        fieldnames = ['DateTime', 'Sensor', 'Message', 'SensorType', 'Time_Interval']
        SensorData.write_to_csv(self, foutname, fieldnames=fieldnames)
            
if __name__ == "__main__":
    shdata_dir = pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\\")
    #dict storing the location of the full data file for each pt_id
    filelocs = {"tm015" : r"tm015\tm015.20190510-20210928_20221116.040751.txt", "test":r"test_data\tm000.20211107-20211108_20230321.230407.txt", "tm029":r"tm029\tm029.20230312-20230313_20230318.011245.txt"}
    test_ignore = False
    if test_ignore:
        fpath = shdata_dir / r"test_data\tm000.20160915-20161111_20230413.010603_utc_everything.txt"
        fpath.resolve()
        data1 = SensorData(fpath, ignore={'SensorType': ['Control4-Motion', 'Control4-LightSensor']}, everything=True)
        dataseq1 = data1.data
        data2 = SensorData(fpath, everything=True)
        dataseq2 = data2.data
        
    test_battery = False
    if test_battery:
        #fpath = shdata_dir / r"test_data\tm000.20160915-20161111_20230413.010603_utc_everything.txt"
        #fpath = shdata_dir / r"tm001\tm001.20160915-20171107_20230413.030825_utc_everything.txt"
        fpath = shdata_dir / r"test_data\tm000.20160917-20160918_20230416.231055_utc_everything.txt"
        fpath.resolve()
        bat1 = BatterySeq(fpath, tz='utc', localtz='US/Pacific')
        batseq = bat1.data
        fout = shdata_dir / r"test_data\tm000.20160917-20160918_utc2pst_radio.csv"
        bat1.write_to_csv(fout)
        
    
    test_roomtrans = True
    if test_roomtrans:
        fpath = shdata_dir / filelocs['test']
        fpath.resolve()
        seq1 = SensorData(fpath)
        seq2 = RoomTranSeq(fpath)
        seq3 = RoomTranSeq(fpath, rooms=['BedroomA', 'BathroomA', 'LivingRoomA', 'KitchenA'])
        data1 = seq1.data
        data2 = seq2.data
        data3 = seq3.data
        # for sensor in sensors:
        #     print(sensor)
        #     try:
        #         print(re.match("[A-Za-z]+?A|[A-Za-z]+?B|[A-Za-z]+?C|[A-Za-z]+?D", sensor).group())
        #     except:
        #         print(re.match("[A-Za-z]+?A|[A-Za-z]+?B|[A-Za-z]+?C|[A-Za-z]+?D", sensor))
    
    test_roomtrans_inactivity = False
    if test_roomtrans_inactivity:
        fname = "tm015.20210322-20210420_20211212.024757.txt"
        fpath = shdata_dir / "tm015" / fname
        #get sequence of roomtran without inactivity levels inserted
        seq = RoomTranSeq(fpath, insert_inact=False)
        outname = shdata_dir / "tm015" / 'tm015.20210322-20210420_roomtran_noinact.csv'
        seq.write_to_csv(outname)
    
    test_Inactivity = False
    if test_Inactivity:
        fpath = shdata_dir / filelocs['test']
        fpath.resolve()
        seq2 = InactivitySeq(fpath)
        seq2.write_to_csv("tm000.20160207_20160207_inactivityseq2.csv")
        seq3 = InactivitySeq(fpath, write=True)
        InactivitySeq.straight_to_file(fpath, outfile="tm000.20160207_20160207_inactivityseq3.csv")
        
    test_get_data = False
    if test_get_data:
        fpath = shdata_dir / filelocs['test']
        fpath.resolve()
        rawdata = get_data(fpath)
        cleandata = get_data(fpath, ignore=['BedroomAArea'])
        seq1 = SensorData(fpath)
        seq2 = seq1.combine_sensors(['BedroomABed', 'BedroomAArea', 'BedroomADoor'], 'Bedroom', inplace=True)
        seq1.write_to_csv("tm000.20160207_20160207_bedroomcombined.csv")
        
    test_utc = False
    if test_utc:
        utc_file = r"C:\Users\Wuestney\Documents\SHdata_raw\tm019\tm019.20211107-20211108_20230321.225843_utc.txt"
        local_file = r"C:\Users\Wuestney\Documents\SHdata_raw\tm019\tm019.20211107-20211108_20230321.230212_local.txt"
        utc = pytz.utc
        local_seq = get_data(local_file)
        utc2loc_seq = get_data(utc_file, tz='utc', localtz='US/Pacific')
        utc_seq = get_data(utc_file, tz='utc')
        
        print("-------")
        print("The following 2 datetimes should be the same.")
        print("Datetime for first timestamp of utc file:", utc_seq[0]['DateTime'].strftime("%m/%d/%Y, %H:%M:%S"))
        print("Datetime for first timestamp of local file converted to utc:", local_seq[0]['DateTime'].astimezone(utc).strftime("%m/%d/%Y, %H:%M:%S"))
        print("-------")
        print("The following 2 datetimes should be the same.")
        print("Datetime for first timestamp of utc file converted to local time:", utc2loc_seq[0]['DateTime'].strftime("%m/%d/%Y, %H:%M:%S"))
        print("Datetime for first timestamp of local file:", local_seq[0]['DateTime'].strftime("%m/%d/%Y, %H:%M:%S"))

    
        