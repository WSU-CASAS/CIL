# casas_measures
Repository contains python scripts for working with CASAS smart home sensor data.


To remove certain sensors from a CASAS series, use the "ignore" keyword when initiating the SensorData (or SensorData subclass) object.

To rename certain sensors in a CASAS series use SensorData.combine_sensors(oldnames, newname, inplace=False) or set inplace=True to permanently change the current SensorData instance.
**Location of class definitions is changed and description below not up to date**
The module casas_data_parse contains the classes 
* SensorData
* InactivitySeq (subclass of SensorData)

The module pattern_search contains the classes 
* Episodes
* SensorSeries
* Bedroom
* Fatigue

Base functions and classes to load sensor data from tab delimited text file are found in the module casas_data_parse. Load a basic CASAS tab delimited file using the SensorData class or load it with inactivity labels inserted use InactivitySeq class which is a special case of the SensorData class.

Load data as a SensorData object: 
```python
data = casas_data_parse.SensorData(filepath, tz='US/Pacific', header='N', ignore=None)
#or use header='Y' if the file has a header row
```

Here data is a SensorData object which contains a list of dicts where each dict is 
one sensor event from the smart home data series.

Otherwise, can load data directly into a SensorSeries object:
```python
livingroom = pattern_search.SensorSeries.load_data(filepath="data.txt", namepatterns=["LivingRoomAArea", "LivingRoomAChair"], tz='US/Pacific', header='N')
#initial SensorSeries object only contains the basic sensor data
#to find episodes, must call SensorSeries.find() method after instantiating object
livingroom.find()
```
To instantiate a SensorSeries object from existing SensorData object:
```python
bathroom = pattern_search.SensorSeries(data=data, namepatterns=["BathroomAArea", "BathroomASink", "BathroomAToilet"])
bathroom.find(look_ahead=2)
```

To find all episodes of being in the Bedroom:
```python
bedroom = pattern_search.Bedroom(data)
#data can either be a SensorData instance or a list of sensor events output from pattern_search.get_data()
bedroom.find(morning_time="06:00:00", evening_time="21:00:00", nighttime=True)
# finds all episodes of being in the Bedroom between 2100 and 0600
```

To find all episodes of out of home use the OutOfHome class which is a subclass of SensorSeries:
```python
ooh = pattern_search.OutOfHome(data=data, entrynames=["MainEntry", "MainDoor"])
ooh.find(min_duration="10m")
#finds all episodes of outside home lasting longer than 10 minutes
```

To summarize the episodes found and stored in the SensorSeries.episodes attribute, call the summarize() method:
```python
sumdf, colnames = livingroom.summarize(countabove=datetime.timedelta(minutes=5))
# sumdf is a pandas dataframe summarizing the episodes. 
# the column "timeint_above" shows the count of time intervals within the episode that are above the timedelta given in the countabove arg
```

### Examples of using the summary dataframe
Filter the summary df by a specific date:
```python
#filter df to just the episodes on 03/19/2021
sumdf.loc[datetime.date(2021,3,19)]
```
Filter the summary df to include only those episodes which meet a certain criteria
```python
# get only the episodes which had more than 4 sensor events in them
sumdf_4ev=sumdf[sumdf['eventcount']>4]
```
Resample the dataframe to summarize episodes across periods of time
```python
# 
lrfmdf2_days=lrfmdf2_4ev.resample("D", level=0)
