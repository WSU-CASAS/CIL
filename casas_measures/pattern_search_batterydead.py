# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 13:54:43 2020

@author: Administrator
"""
import pathlib
import copy
import pandas as pd
import datetime
import pytz
import dateutil
import re
from collections import defaultdict

from casas_data_parse import SensorData, get_data, time_int, write_header, BatterySeq
from casas_measures import timedelta_median

def parse_duration_threshold(durationstring):
    try:
        # parse min_duration into datetime.timedelta object
        min_dur = pd.Timedelta(durationstring).to_pytimedelta()
        return min_dur
    except ValueError:
        print("Please input minimum duration in any of the following formats\n '5hr12m10s', '2h32m', '2 days 23:12:00 10 sec'\n A format like '4:13' does not work.", title="Error parsing time threshold.", easy_close=True)
        print(ValueError)
    

class Episodes:
    """
    List type iterable object used to hold episodes of contiguous sensor events. Each item in Episodes is a list of sensor events dicts.
    Has builtin functions to iterate through episodes one at a time for certain analysis tasks.
    """
    __slots__ = ("list", "iterindex")
    def __init__(self):
        self.list = list()
        self.iterindex = 0

    def append(self, value):
        self.list.append(value)

    def __iter__(self):
        return self

    def __next__(self):
        if self.iterindex >= len(self.list):
            raise StopIteration
        else:
            currentindex=self.iterindex
            self.iterindex += 1
        return self.list[currentindex]

    def __reset__(self, index=0):
        #reset iterator to 0 or specified index
        self.iterindex = index
        return self
    def __len__(self):
        return len(self.list)


class SensorSeries:
    """
    Generic object holds all instances of a series of contiguous sensor events associated with the sensor name patterns provided.
    
    The operation of finding every sensor pattern episode is separated from the initiation of the 
    class instance so that different pattern find criteria can be used on the same
    SensorSeries class intance.

    Parameters for __init__
    ----------
    data : LIST OF DICTS
        LIST OF DICTS CONTAINING SUCCESSIVE SMART HOME SENSOR EVENTS STORED AS
        KEY:VALUE PAIRS.TAKES A SensorData OBJECT OR THE OUTPUT OF get_data() or get_annotated_data()
    namepatterns : LIST OF STRINGS REPRESENTING STRING PATTERNS TO LOOK FOR AND INCLUDE IN THE EPISODES.

    """
    def __init__(self, data, namepatterns):
        if isinstance(data, SensorData):
            #self.data is a copy of a SensorData object
            self.data = copy.copy(data.data)
        else:
            self.data = copy.copy(data)
        assert type(namepatterns) is list, f"{type(namepatterns)}"
        assert len(namepatterns)>0, f"{namepatterns}"
        self.namepatterns=[]
        for i in namepatterns:
            pattern=re.compile(rf"{i}")
            self.namepatterns.append(pattern)
        self.episodes=Episodes()
        self.namesfound = []
    
    def _include_prevevent(self, i, prevevent):
        """
        Checks if prevevent is from one of the sensors to include in the pattern
        episode. If it is, prevevent is added to episode and function returns True.
        If it is not, episode is left unchanged and function returns False.

        Parameters
        ----------
        i : INT
            INDICATING INDEX ONE AHEAD OF PREVENT IN SELF.DATA.
        prevevent : DICT
            DICT OF SENSOR EVENT AT SELF.DATA[i-1].

        Returns
        -------
        bool

        """
        sensorname = prevevent['Sensor']
        if any(re.match(pattern, sensorname) for pattern in self.namepatterns):
            if sensorname not in self.namesfound:
                self.namesfound.append(sensorname)
            prevevent['index']=i-1
            self.episode.append(prevevent)
            #update sensor states with current sensor message
            self.sensor_states[prevevent['Sensor']] = prevevent['Message']
            return True
        else:
            return False
        
    def _is_episode_end(self, i, **kwargs):
        """
        Checks if prevevent should be considered the end of the episode or if the
        episode pattern continues within n number of events ahead.

        Parameters
        ----------
        i : INT
            INDICATING INDEX OF FIRST EVENT AFTER PREVENT IN SELF.DATA.
        look_ahead_count : INT, default: 2
            THIS IS THE NUMBER OF EVENTS TO LOOK AHEAD TOWARDS TO DECIDE WHETHER
            THE PATTERN EPISODE IS TRULY ENDED. DEFAULT IS 2.
        look_ahead_time : INT, default: 2
            NUMBER OF MINUTES TO LOOK AHEAD BEFORE THE END OF THE EPISODE. DEFAULT
            IS 2 MINUTES.
        include_end : BOOL, default: False
            INDICATES WHETHER THE FIRST SENSOR EVENT OCCURING AFTER THE END OF AN
            EPISODE SHOULD ALSO BE INCLUDED IN THE EPISODE EVEN IF IT DOES NOT COME
            FROM A SENSOR MATCHING THE NAME PATTERNS.

        Returns
        -------
        bool
            RETURNS FALSE IF THIS IS NOT THE END OF THE EPISODE AND MORE EVENTS 
            SHOULD BE ADDED TO THE EPISODE. RETURNS TRUE IF THIS SHOULD BE THE
            END OF THE EPISODE AND EPISODE SHOULD BE APPENDED TO SELF.EPISODES.

        """
        look_ahead_count = kwargs.get('look_ahead_count', 2)
        look_ahead_time = kwargs.get('look_ahead_time', 2)
        include_end = kwargs.get('include_end', False)
        ooh = kwargs.get('ooh', False)
        offline = kwargs.get('offline', False)
        # is this the end of the data?
        #if i == len(self.data) - 1:
        if i == len(self.data)-1:
            lastevent = self.data[i]
            # check if last sensor event in the data should be included in the episode
            if include_end:
                self.episode.append(lastevent)
                #return True
            elif any(re.match(pattern, lastevent['Sensor']) for pattern in self.namepatterns):
                self.episode.append(lastevent)
                #return True
            else:
                pass
            return True
        # are any target sensors still "ON"? creates list of sensor names whose last 
        # observed message was ON
        targetsON = [name for name, msg in self.sensor_states.items() if msg == "ON"]
        lastdatetime = copy.deepcopy(self.episode[-1]['DateTime'])
        curdatetime = copy.deepcopy(self.data[i]['DateTime'])
        # has it been less than 2 minutes since the last event included in the episode? 
        timesince = (curdatetime - lastdatetime) < datetime.timedelta(minutes=look_ahead_time)
        if offline and timesince:
            return False
        elif bool(targetsON) and timesince:
            return False
        else:
            for n in range(look_ahead_count+1):
                event=self.data[i+n]
                if any(re.match(pattern, event['Sensor']) for pattern in self.namepatterns):
                    return False  
                else:
                    continue
                
            # if instance of Offline sublcass then if timesince is True then not the end of the episode
            # if offline:
            #     if timesince:
            #         return False
            # if instance of OutofHome class then check the average frequency of non-target sensors
            # if >=10 minutes then continue looking
            # this allows for extended periods of absence with occasional spurious sensor events
            if ooh:
                avg_event_freq = (self.data[i+look_ahead_count]['DateTime'] - lastdatetime)/(look_ahead_count/2)
                # if average time between non-exit sensor events is >10 minutes then continue looking for end of ooh episode
                if avg_event_freq >= datetime.timedelta(minutes=10):
                    return False

            # since its end of episode;
            #add first event after prevevent to episode if include_end is True
            if include_end:
                self.episode.append(self.data[i])
            #reset all "ON" target sensor states to "OFF" 
            if bool(targetsON) and not timesince:
                for target in targetsON:
                    self.sensor_states[target] = "OFF"
            return True
                

    def find(self, **kwargs):
        """
        Function to find all contiguous episodes of sensors matching the namepatterns given in self.namepatterns
        Optional kwargs: morning_time, evening_time, and nighttime kwargs .

        Parameters
        ----------
        **kwargs : DICT, optional
            OPTIONAL KEYWORD ARGUMENTS TO SPECIFY HOW TO FIND EPISODES. SOME POSSIBLE OPTIONS
            LIST BELOW UNDER OTHER PARAMETERS.. 

        Returns
        -------
        None.
        
        Other Parameters
        ----------------
        look_ahead_count, include_end : OPTIONAL KWARGS FOR PASSING TO :func:`~pattern_search.SensorSeries._is_episode_end` SPECIFYING HOW TO DETERMINE THE END OF AN EPISODE
                    DEFAULTS ARE look_ahead_count=2 AND include_end=False
        morning_time, evening_time, nighttime : OPTIONS TO LIMIT PATTERN COLLECTION TO SPECIFIC TIME PERIODS OF THE DAY
            WHICH ARE TYPICALLY USED BY THE BEDROOM SUBCLASS. SEE :func:`~pattern_search.Bedroom.find`
        """
        
        #enter nighttime=True to limit pattern collection to times >evening_time and <morning_time

        #use include_end
        morning_time=kwargs.get('morning_time')
        evening_time=kwargs.get('evening_time')

        
        #self.episodes is a list of lists of dicts. each dict represents one sensor event
        #and each list of dicts represents one contiguous episode of pattern events.
        self.episodes=Episodes()
        self.episode=[]
        self.sensor_states = defaultdict(lambda: "OFF")
        if morning_time and evening_time:
            if type(morning_time) is datetime.time:
                self.morning_time=morning_time
            else:
                morning_parse=dateutil.parser.parse(kwargs['morning_time'], fuzzy=True, ignoretz=True)
                self.morning_time=morning_parse.time()
            if type(evening_time) is datetime.time:
                self.evening_time=evening_time
            else:
                evening_parse=dateutil.parser.parse(kwargs['evening_time'], fuzzy=True, ignoretz=True)
                self.evening_time=evening_parse.time()
            #get nighttime kwarg, default False
            self.nighttime=kwargs.get('nighttime', False)

            for i in range(1,len(self.data)):
                prevevent=self.data[i-1]
                prev_time=copy.deepcopy(prevevent['DateTime']).time()
                if self.nighttime:
                    if not self.morning_time <= prev_time < self.evening_time:
                        #event=self.data[i]
                        if self._include_prevevent(i, prevevent):
                            #check if end of episode
                            if self._is_episode_end(i, **kwargs):
                                self.episodes.append(self.episode)
                                #reset episode to empty list
                                self.episode=[]
                            else:
                                continue
                    elif self.morning_time <= prev_time < self.evening_time:
                        continue
                else:
                    if self.morning_time <= prev_time < self.evening_time:
                        #event=self.data[i]
                        #check if prevevent was added to self.episode
                        if self._include_prevevent(i, prevevent):
                            #check if end of episode
                            if self._is_episode_end(i, **kwargs):
                                self.episodes.append(self.episode)
                                self.episode=[]
                            else:
                                continue
                    elif not self.morning_time <= prev_time < self.evening_time:
                        continue
        else:
            for i in range(1,len(self.data)):
                prevevent=self.data[i-1]
                #event=self.data[i]
                #check if prevevent was added to self.episode
                if self._include_prevevent(i, prevevent):
                    #check if end of episode
                    if self._is_episode_end(i, **kwargs):
                        self.episodes.append(self.episode)
                        # reset episode to empty list to contain the next episode  
                        self.episode=[]
                    else:
                        continue
        self.iterepisodes=iter(self.episodes)
        #del(self.episode)
        return True

    def iterprint(self, start_date=None):
        try:
            nextepi=next(self.iterepisodes)
            if start_date:
                assert type(start_date) is datetime.date
                skip=True
                while skip==True:
                    date=copy.deepcopy(nextepi[0]['DateTime']).date()
                    if date < start_date:
                        nextepi=next(self.iterepisodes)
                    elif start_date <= date:
                        skip=False
            for e in nextepi:
                print(*e.values(), sep='\t')
        except StopIteration:
            print("No more episodes found in the data.")
            self.iterepisodes.__reset__()
            
    def summarize(self, countabove=datetime.timedelta(seconds=0), sumabove=datetime.timedelta(seconds=0)):
        """
        Takes all episodes found in self.data and summarizes them into a pandas dataframe.

        Parameters
        ----------
        countabove : DATETIME TIMEDELTA OBJECT, optional
            TIMEDELTA OBJECT INDICATING THE THRESHOLD TIME INTERVAL DURATION TO
            COUNT WITHIN EACH EPISODE.
            The default is datetime.timedelta(seconds=0).
        sumabove : DATETIME TIMEDELTA OBJECT, optional
            TIMEDELTA OBJECT INDICATING THE THRESHOLD TIME INTERVAL DURATION TO
            SUM ABOVE WITHIN EACH EPISODE.
            The default is datetime.timedelta(seconds=0).

        Returns
        -------
        df2 : PANDAS DATAFRAME
            DATAFRAME SUMMARIZING THE EPISODES.
        sumcolnames : LIST
            LIST OF THE COLUMN NAMES OF THE DATAFRAME.

        """
        self.dates=defaultdict(list)
        sumcolnames=['firstevent', 'lastevent', 'eventcount', 'min_timeint', 'max_timeint', 'med_timeint']
        self.iterepisodes.__reset__()
        # calculate summary stats for each episode in self.episodes
        for episode in self.episodes:
            first=copy.deepcopy(episode[0]['DateTime'])
            last=copy.deepcopy(episode[-1]['DateTime'])
            date=first.date()
            size=len(episode)
            duration=last-first
            timeints=[]
            skipfirst=False
            sensorcounts={}
            for e in episode:
                try:
                    timeints.append(e['Time_Interval'])
                except KeyError:
                    skipfirst=True
                    timeints.append(0)
                sensorname=e['Sensor']
                sencountstring=f'count{sensorname}'
                if sencountstring not in sumcolnames:
                    sumcolnames.append(sencountstring)
                sensorcounts[sencountstring] = sensorcounts.get(sencountstring, 0) + 1
            if skipfirst:
                if len(timeints[1:]) < 1:
                    timeintmin = 'NA'
                    timeintmax = 'NA'
                    timeintmedian = 'NA'
                    timeintabove = 'NA'
                else:
                    timeintmin=min(timeints[1:])
                    timeintmax=max(timeints[1:])
                    timeintmedian=timedelta_median(timeints[1:])
                    timeintabove=sum(i>=countabove for i in timeints[1:])
                    timeintsumabove=sum([i for i in timeints[1:] if i>=sumabove], datetime.timedelta(seconds=0))
            else:
                timeintmin=min(timeints)
                timeintmax=max(timeints)
                timeintmedian=timedelta_median(timeints)
                timeintabove=sum(i>=countabove for i in timeints)
                timeintsumabove=sum([i for i in timeints if i>=sumabove], datetime.timedelta(seconds=0))
            columns={"firstevent":first, "lastevent": last, "eventcount":size, 
                     "totalduration":duration, "min_timeint":timeintmin, 
                     "max_timeint":timeintmax, "med_timeint":timeintmedian, 
                     "timeint_above": timeintabove, "sum_timeint_above":timeintsumabove}
            #add dictionary containing counts of each sensor name to summary columns
            columns.update(sensorcounts)
            self.dates[date].append(columns)
            
        df=pd.DataFrame.from_dict(self.dates, orient='index').stack().to_frame()
        df2=pd.DataFrame(df[0].values.tolist(), index=df.index)
        if df2.size > 0:
            df2.index = df2.index.set_levels(df2.index.levels[0].astype('datetime64[ns]'), level=0)
        return df2, sumcolnames
    
    def __len__(self):
        return len(self.episodes)
    
    @classmethod
    def load_data(cls, file_to_read, namepatterns, tz='US/Pacific', header='N'):
        """
        reads smart home data from a tab delimited text file and returns a SensorSeries
        instance with the data stored as the attribute self.data

        Parameters
        ----------
        file_to_read : PATH OBJECT
            PATH TO DATA FILE TO LOAD.
        namepatterns : LIST OF STRINGS
            LIST OF STRINGS REPRESENTING STRING PATTERNS TO LOOK FOR AND INCLUDE IN THE EPISODES.
        tz : STRING
            STRING REPRESENTING THE TIME ZONE TO BE USED TO CREATE PYTZ TIMEZONE OBJECT.
            The default is 'US/Pacific'.
        header : STRING, optional
            USE 'header='Y'' IF THE DATA TO BE PARSED HAS BEEN ANNOTATED VIA clean_annotations.py
            The default is 'N'.

        Returns
        -------
        Instance of SensorSeries

        """
        data = get_data(file_to_read, tz=tz, header=header)
        if header=='N':
            time_int(data)
        return cls(data, namepatterns)

class Bedroom(SensorSeries):
    """
    Bedroom object holds all instances of a series of contiguous Bedroom associated sensor events.

    Parameters
    ----------
    data : LIST OF DICTS
        LIST OF DICTS CONTAINING SUCCESSIVE SMART HOME SENSOR EVENTS STORED AS
        KEY:VALUE PAIRS.TAKES A SensorData OBJECT OR THE OUTPUT OF get_data() or get_annotated_data()

    """
    def __init__(self, data, namepatterns=None):
        if namepatterns:
            SensorSeries.__init__(self, data, namepatterns)
        else:
            SensorSeries.__init__(self, data, ["Bed"])

    def find(self, morning_time, evening_time, nighttime=False, **kwargs):
        #nighttime tells whether the period between lower and upper crosses midnight or not
        #if nighttime==True, morning_time and evening_time will be reversed and episodes
        #will only count bedroom activity not occuring between morning_time and evening_time
        #e.g. if morning_time=2200 and evening_time=0600 and nighttime==True,
        #then only sensor events occuring between 2200 and midnight and midnight and 0600 will be included
        look_ahead_count = kwargs.get('look_ahead_count', 2)
        SensorSeries.find(self, morning_time=morning_time, evening_time=evening_time, nighttime=nighttime, look_ahead_count=look_ahead_count, **kwargs)

    def bed_to_toilet(self):
        self.bed_toilet_episodes = []
        for episode in self.episodes:
            index=episode[-1]['index']
            look_ahead=[]
            bathroomtransition=True
            for i in range(1,6):
                next_event=self.data[index+i]
                if i<5:
                    look_ahead.append(next_event)
                    if re.match('(Bathroom)', next_event['Sensor']):
                        break
                    else:
                        continue
                else:
                    look_ahead.append(next_event)
                    if re.match('(Bathroom)', next_event['Sensor']):
                        break
                    elif not re.match('(Bathroom)', next_event['Sensor']):
                        bathroomtransition=False
            if bathroomtransition:
                episode.extend(look_ahead)
                bed={}
                bathroom={}
                for event in episode:
                    if len(re.findall('(Bed)', event['Sensor'])) > 1:
                        bed=event
                    elif re.match('(Bathroom)', event['Sensor']):
                        bathroom=event
                    else:
                        continue
                if bathroom and bed:
                    self.bed_toilet_episodes.append({'bed_to_toilet_start':bed, 'bed_to_toilet_end':bathroom})
                else:
                    continue
    def sleep(self, morning_time=None, evening_time=None):
        #function under development. do not use at this time
        if not self.morning_time:
            self.morning_time = morning_time
        if not self.evening_time:
            self.evening_time = evening_time
        for episode in self.episodes:
            if not self.morning_time <= episode[0]['DateTime'] < self.evening_time:
                timeints=[]
                skipfirst=False
                sensorcounts={}
                for e in episode:
                    try:
                        timeints.append(e['Time_Interval'])
                    except KeyError:
                        skipfirst=True
                        timeints.append(0)


class OutofHome(SensorSeries):
    def __init__(self, data, entrynames):
        #entrynames should be list of sensor names associated with exterior entries to the home
        SensorSeries.__init__(self, data, entrynames)
        
    def find(self, min_duration=None, **kwargs):
        #nighttime tells whether the period between lower and upper crosses midnight or not
        #if nighttime==True, morning_time and evening_time will be reversed and episodes
        #will only count bedroom activity not occuring between morning_time and evening_time
        #e.g. if morning_time=2200 and evening_time=0600 and nighttime==True,
        #then only sensor events occuring between 2200 and midnight and midnight and 0600 will be included
        kwargs['look_ahead_count'] = kwargs.get('look_ahead_count', 20)
        #kwargs indicating this is an instance of OutofHome
        kwargs['ooh'] = True
        SensorSeries.find(self, **kwargs)
        if min_duration:
            # try:
            #     # parse min_duration into datetime.timedelta object
            #     min_dur = pd.Timedelta(min_duration).to_pytimedelta()
            # except ValueError:
            #     print("Please input minimum duration in any of the following formats\n '5hr12m10s', '2h32m', '2 days 23:12:00 10 sec'\n A format like '4:13' does not work.", title="Error parsing time threshold.", easy_close=True)
            #     print(ValueError)
            min_dur = parse_duration_threshold(min_duration)
            # put all episodes in a list and reset self.episodes to empty Episodes instance
            episodes = copy.deepcopy(self.episodes)
            self.episodes = Episodes()
            # add episodes back to self.episodes only if the difference between 
            # their first and last sensor event is > min_duraiton
            for episode in episodes:
                first=copy.deepcopy(episode[0]['DateTime'])
                last=copy.deepcopy(episode[-1]['DateTime'])
                duration = last - first
                if duration > min_dur:
                    self.episodes.append(episode)
                else:
                    continue
            print("Removed ", len(episodes) - len(self.episodes), f"episodes shorter than {str(min_dur)} from original {len(episodes)} episodes")

class Offline(SensorSeries):
    
    def __init__(self, *args, **kwargs):

        SensorSeries.__init__(self, *args, **kwargs)
    def find(self, *args, **kwargs):
        kwargs['look_ahead_time'] = 60
        kwargs['look_ahead_count'] = 0
        kwargs['offline'] = True
        kwargs['include_end'] = True
        SensorSeries.find(self, *args, **kwargs)
class Fatigue:
    """
    fatigue() calculates time intervals between successive sensor events
    and returns a list of the time intervals which fall into the given range provided
    by the arguments 'lower' and 'upper'. If 'upper' is not provided then it is assumed
    the range of counted time intervals is all intervals greater than or equal to 'lower'.

    Parameters
    ----------
    data : LIST OF DICTS
        LIST OF DICTS CONTAINING SUCCESSIVE SMART HOME SENSOR EVENTS STORED AS
        KEY:VALUE PAIRS.
    lower : TIMEDELTA OBJECT
        TIMEDELTA OBJECT OF THE BUILTIN DATETIME MODULE REPRESENTING THE
        LOWER BOUND OF THE RANGE OF TIME INTERVALS TO BE INCLUDED.
    upper : TIMEDELTA OBJECT, optional
        IF GIVEN, TIMEDELTA OBJECT OF THE BUILTIN DATETIME MODULE REPRESENTING THE
        UPPER BOUND OF THE RANGE OF TIME INTERVALS TO BE INCLUDED. The default is None.

    Returns
    -------
    List of dicts.

    """
    def __init__(self, data, lower, upper=None):
        self.data=copy.deepcopy(data)
        assert type(lower) is datetime.timedelta
        self.lower=lower
        if upper:
            assert type(upper) is datetime.timedelta
            self.upper=upper
        else:
            self.upper=upper

    def calc(self):
        self.long_timeints= list()
        self.timeints=dict()
        for i in range(1,len(self.data)):
            event=self.data[i]
            prevevent=self.data[i-1]
            #current = copy.deepcopy(self.data[i]['DateTime'])
            #past= copy.deepcopy(self.data[i-1]['DateTime'])
            current = copy.deepcopy(event['DateTime'])
            past= copy.deepcopy(prevevent['DateTime'])
            timeint=current-past
            prevsen=prevevent['Sensor']
            prevmes=prevevent['Message']
            sensor=event['Sensor']
            mes=event['Message']
            prevsenstate='{}{}'.format(prevsen, prevmes)
            cursenstate='{}{}'.format(sensor, mes)
            #prevsenstate='{}{}'.format(self.data[i-1]['Sensor'], self.data[i-1]['Message'])
            #cursenstate='{}{}'.format(self.data[i]['Sensor'], self.data[i]['Message'])
            if timeint >= self.lower:
                if self.upper:
                    if timeint<= self.upper:
                        self.long_timeints.append({'Current_Time':current, 'Preced_Sen_State':prevsenstate, 'Cur_Sen_State':cursenstate, 'Time_Int':timeint})
                        self.timeints[current]=timeint
                    elif timeint > self.upper:
                        continue
                else:
                    self.long_timeints.append({'Current_Time':current, 'Preced_Sen_State':prevsenstate, 'Cur_Sen_State':cursenstate, 'Time_Int':timeint})
                    self.timeints[current]=timeint
            elif timeint < self.lower:
                continue

            #except IndexError:
                #print("cannot calculate time interval for data index {}".format(i))
                #continue
    def avg(self,):
        timeints=self.timeints.values()
        self.avgtimeint=sum(timeints, datetime.timedelta(0))/len(timeints)

    def write(self, output):
        """

        Parameters
        ----------
        output : PATHLIKE
            PATH OBJECT FOR THE OUTPUT FILE.

        Returns
        -------
        None.

        """
        write_header(output, form='fatigue')
        with open(output, 'a') as fwrite:
            for t in self.long_timeints:
                curtime=t.get('Current_Time')
                prevsenstate=t.get('Preced_Sen_State')
                cursenstate=t.get('Cur_Sen_State')
                curtimeint=t.get('Time_Int')
                fwrite.write('{}\t{}\t{}\t{}'.format(curtime, prevsenstate, cursenstate, curtimeint))
                fwrite.write('\n')
        #self.count=len(self.long_timeints)
        #self.max=max(self.timeints.values())
        #print(self.count)
        #print(self.max)

#%%
if __name__ == "__main__":
    import yaml
    with open("../cil_data_params.yml", 'r') as paramfile:
        data_params = yaml.safe_load(paramfile)
    FILELOCS = data_params['FILELOCS']

    SHDATA_DIR = pathlib.Path(data_params['SHDATA_DIR'])

    IGNORE_SENSORS = data_params['IGNORE_SENSORS']

    IGNORE_TIMEFRAMES = data_params['IGNORE_TIMEFRAMES']

    SENSORS_COMBINED = data_params['SENSORS_COMBINED']
    test_combined = False
    if test_combined:
        tm017_data_file = SHDATA_DIR / FILELOCS['tm017']
        tm017_data = SensorData(tm017_data_file, ignore=IGNORE_SENSORS['tm017'])
        tm017_lr_episodes = SensorSeries(tm017_data, ['KitchenARefrigerator', 'KitchenAArea', 'KitchenAStove'])
        tm017_lr_episodes.find()
        
    compare_subclasses = False
    if compare_subclasses:
        #get file path object
        data_dir = pathlib.Path(r'C:\\Users\\Wuestney\\Documents\\GitHub\\casas_measures\\tests\\')
    
        #data_folder = 'tm015\\'
        fname = 'tm000.multiday_absence.txt'
        #file_to_open = data_dir / data_folder / fname
        file_to_open = data_dir / fname
        PDT = pytz.timezone('US/Pacific')
        data=SensorData(file_to_open, header='N')
        minutes_low=1
        seconds_low=0
        lower=datetime.timedelta(minutes=minutes_low, seconds=seconds_low)
        minutes_up=None
        seconds_up=None
        if minutes_up or seconds_up:
            upper=datetime.timedelta(minutes=minutes_up, seconds=seconds_up)
        else:
            upper=None
        evening_time=datetime.time(hour=22, minute=30)
        morning_time=datetime.time(hour=7, minute=0)
        livingroomnames = ["LivingRoom", "KitchenAArea", 'KitchenASink']
        bathroomnames = ["BathroomAArea", "BathroomASink", "BathroomAToilet"]
        exitnames = ['MainEntryway', 'EntrywayB']
        data = data.data[-6:]
        # livingroom=SensorSeries(data, livingroomnames)
        # livingroom.find()
        # bedroomarea=SensorSeries(data, ["BedroomAArea"])
        # bedroomarea.find()
        ooh = OutofHome.load_data(file_to_open, exitnames)
        ooh.find(min_duration='15min')
            
        """
        bedroom=Bedroom(data.data)
        bedroom.find(morning_time, evening_time, nighttime=False)
        print(bedroom.episodes.list[0])
        bedroom.summarize()
    #%%
        bedroom.iterprint()
        bedroom.iterprint(datetime.date(2021,1,21))
        #fatigue = Fatigue(data, lower, upper)
        #fatigue.calc()
    
        # confirm whitespace characters used
        for i in range(5):
            line=fhand.readline()
            print(repr(line))
        #create dataframe
        df = pd.read_csv(file_to_open, sep='\t', index_col=False, names=("datetime","sensor", "message"))
        df.set_index('datetime', inplace=True)
        df[bed_event]=
        """
    test_Offline = True
    if test_Offline:
        shdata_dir = pathlib.Path(r"C:\Users\Wuestney\Documents\SHdata_raw\\")
        #dict storing the location of the full data file for each pt_id
        filelocs = {"tm015" : r"tm015\tm015.20190510-20210928_20221116.040751.txt", "test":r"test_data\tm000.20211107-20211108_20230321.230407.txt", "tm029":r"tm029\tm029.20230312-20230313_20230318.011245.txt"}
        #fpath = shdata_dir / r"test_data\tm000.20160915-20161111_20230413.010603_utc_everything.txt"
        fpath = shdata_dir / r"test_data\tm000.20160917-20160918_utc2pst_radio_short.txt"
        fpath.resolve()
        bat1 = BatterySeq(fpath, tz='US/Pacific')
        bat1.data
        deadbedroom = Offline(bat1, ['BedroomAArea'])
        deadbedroom.find()
        print(deadbedroom.episodes.list)
        print(deadbedroom.episode)
        deadbedroom_df, colnames = deadbedroom.summarize()
        # for sensor in bat1.sensors:
        #     sensor_dead = SensorSeries(bat1)