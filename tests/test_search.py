# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 15:39:26 2022

@author: Wuestney
"""
import copy
from collections import defaultdict
import datetime
import re
from casas_measures.pattern_search import SensorData, Episodes


# class Bedroom:
#     """
#     Bedroom object holds all instances of a series of contiguous Bedroom associated sensor events.
#     Version of Bedroom when it was its own class before becoming subclass of SensorSeries

#     Parameters
#     ----------
#     data : LIST OF DICTS
#         LIST OF DICTS CONTAINING SUCCESSIVE SMART HOME SENSOR EVENTS STORED AS
#         KEY:VALUE PAIRS.TAKES A SensorData OBJECT OR THE OUTPUT OF get_data() or get_annotated_data()

#     """
#     def __init__(self, data):
#         if isinstance(data, SensorData):
#             #self.data is a copy of a SensorData object
#             self.data = copy.copy(data.data)
#         else:
#             self.data = copy.copy(data)
#         self.episodes=Episodes()

#     def find(self, morning_time, evening_time, nighttime=False):
#         #nighttime tells whether the period between lower and upper crosses midnight or not
#         #if nighttime==True, morning_time and evening_time will be reversed and episodes
#         #will only count bedroom activity not occuring between morning_time and evening_time
#         #e.g. if morning_time=2200 and evening_time=0600 and nighttime==True,
#         #then only sensor events occuring between 2200 and midnight and midnight and 0600 will be included
#         assert type(morning_time) is datetime.time
#         assert type(evening_time) is datetime.time
#         self.morning_time=morning_time
#         self.evening_time=evening_time
#         self.nighttime=nighttime
#         """
#         if self.nighttime:
#             morning_time=self.evening_time
#             evening_time=self.morning_time
#         else:
#             morning_time=self.morning_time
#             evening_time=self.evening_time

#         """
#         #self.episodes is a list of lists of dicts. each dict represents one sensor event
#         #and each list of dicts represents one contiguous episode of bedroom events.
#         self.episodes=Episodes()
#         episode=[]
#         for i in range(1,len(self.data)):
#             prevevent=self.data[i-1]
#             prev_time=copy.deepcopy(prevevent['DateTime']).time()
#             if self.nighttime:
#                 if not morning_time <= prev_time < evening_time:
#                     event=self.data[i]
#                     if re.match('(Bed)', prevevent['Sensor']):
#                         prevevent['index']=i-1
#                         episode.append(prevevent)
#                         if re.match('(Bed)', event['Sensor']):
#                             continue
#                         elif re.match('(Bed)', self.data[i+1]['Sensor']) or re.match('(Bed)', self.data[i+2]['Sensor']):
#                             continue
#                         else:
#                             self.episodes.append(episode)
#                             episode=[]
#                 elif morning_time <= prev_time < evening_time:
#                     continue
#             else:
#                 if morning_time <= prev_time< evening_time:
#                     event=self.data[i]
#                     if re.match('(Bed)', prevevent['Sensor']):
#                         prevevent['index']=i-1
#                         episode.append(prevevent)
#                         if re.match('(Bed)', event['Sensor']):
#                             continue
#                         elif re.match('(Bed)', self.data[i+1]['Sensor']) or re.match('(Bed)', self.data[i+2]['Sensor']):
#                             continue
#                         else:
#                             self.episodes.append(episode)
#                             episode=[]
#                 elif not morning_time <= prev_time < evening_time:
#                     continue
#         self.iterepisodes=iter(self.episodes)

#     def summarize(self):
#         self.dates=defaultdict(list)
#         self.iterepisodes.__reset__()
#         for episode in self.episodes:
#             first=copy.deepcopy(episode[0]['DateTime'])
#             last=copy.deepcopy(episode[-1]['DateTime'])
#             date=first.date()
#             size=len(episode)
#             duration=last-first
#             timeints=[]
#             skipfirst=False
#             countbeds=0
#             countarea=0
#             countdoor=0
#             countother=0
#             for e in episode:
#                 try:
#                     timeints.append(e['Time_Interval'])
#                 except KeyError:
#                     skipfirst=True
#                     timeints.append(0)
#                 if re.match('Bed.+Bed$', e['Sensor']):
#                     countbeds += 1
#                 elif re.match('Bed.+Door$', e['Sensor']):
#                     countdoor += 1
#                 elif re.match('Bed.+Area$', e['Sensor']):
#                     countarea += 1
#                 else:
#                     countother += 1
#             if skipfirst:
#                 timeintmin=min(timeints[1:])
#                 timeintmax=max(timeints[1:])
#                 timeintmedian=timedelta_median(timeints[1:])
#             else:
#                 timeintmin=min(timeints)
#                 timeintmax=max(timeints)
#                 timeintmedian=timedelta_median(timeints)
#             self.dates[date].append({"firstevent":first, "lastevent": last, "eventcount":size, "totalduration":duration, "min_timeint":timeintmin, "max_timeint":timeintmax, "med_timeint":timeintmedian, "bedcount":countbeds, "areacount":countarea, "doorcount":countdoor, "othercount":countother})
#         return self.dates

#     def iterprint(self, start_date=None):
#         try:
#             nextepi=next(self.iterepisodes)
#             if start_date:
#                 assert type(start_date) is datetime.date
#                 skip=True
#                 while skip==True:
#                     date=copy.deepcopy(nextepi[0]['DateTime']).date()
#                     if date < start_date:
#                         nextepi=next(self.iterepisodes)
#                     elif start_date <= date:
#                         skip=False
#             for e in nextepi:
#                 print(*e.values(), sep='\t')
#         except StopIteration:
#             print("No more episodes found in the data.")
#             self.iterepisodes.__reset__()

#     def bed_to_toilet(self):
#         self.bed_toilet_episodes = []
#         for episode in self.episodes:
#             index=episode[-1]['index']
#             look_ahead=[]
#             bathroomtransition=True
#             for i in range(1,6):
#                 next_event=self.data[index+i]
#                 if i<5:
#                     look_ahead.append(next_event)
#                     if re.match('(Bathroom)', next_event['Sensor']):
#                         break
#                 else:
#                     look_ahead.append(next_event)
#                     if re.match('(Bathroom)', next_event['Sensor']):
#                         break
#                     elif not re.match('(Bathroom)', next_event['Sensor']):
#                         bathroomtransition=False
#             if bathroomtransition:
#                 episode.extend(look_ahead)
#                 bed={}
#                 bathroom={}
#                 for event in episode:
#                     if len(re.findall('(Bed)', event['Sensor'])) > 1:
#                         bed=event
#                     elif re.match('(Bathroom)', event['Sensor']):
#                         bathroom=event
#                     else:
#                         continue
#                 if bathroom and bed:
#                     self.bed_toilet_episodes.append({'bed_to_toilet_start':bed, 'bed_to_toilet_end':bathroom})
#                 else:
#                     continue