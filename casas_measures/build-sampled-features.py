import argparse
import copy
import datetime
import os
import pgpasslib
import psycopg2
import pytz
import sys

DATA_TYPES = dict({
    'motion': ['Motion-01', 'MotionArea-01', 'Control4-Motion', 'Control4-MotionArea'],
    'door': ['Door-01', 'Control4-Door'],
    'item': ['Item-01', 'Control4-Item'],
    'light': ['Insteon', 'Insteon-Relay', 'Control4-Light', 'Control4-LightLevel'],
    'temperature': ['Temperature', 'Control4-Temperature'],
    'lightsensor': ['Control4-LightSensor'],
    'battery': ['Control4-BatteryPercent']})


def get_utc_stamp(db_conn, tbname, local_stamp):
    """
    This function converts a 'local' timestamp to the UTC value given the testbed.
    """
    utc_stamp = copy.deepcopy(local_stamp)
    sql = "SELECT timezone('utc', timestamp %s at time zone testbed.timezone) "
    sql += "FROM testbed WHERE tbname=%s;"
    data = (local_stamp, tbname,)
    with db_conn:
        with db_conn.cursor() as cr:
            cr.execute(sql, data)
            result = cr.fetchone()
            utc_stamp = result[0]
            utc_stamp = utc_stamp.replace(tzinfo=pytz.utc)
    return utc_stamp


def get_testbed_timezone(db_conn, tbname):
    timezone = None
    sql = 'SELECT timezone FROM testbed WHERE tbname=%s;'
    data = (tbname,)
    with db_conn:
        with db_conn.cursor() as cr:
            cr.execute(sql, data)
            row = cr.fetchone()
            if row is not None:
                timezone = pytz.timezone(row[0])
    return timezone


def get_testbed_sensors(db_conn, tbname, sensor_types):
    print('get_testbed_sensors({}, sensor_types)'.format(tbname))
    testbed_sensors = list()
    sql = ('SELECT target, sensor_type FROM all_sensors WHERE tbname=%s AND sensor_type=ANY(%s) '
           'GROUP BY target, sensor_type ORDER BY sensor_type, target;')
    data = (tbname, sensor_types,)
    with db_conn:
        with db_conn.cursor() as cr:
            # print('{}'.format(cr.mogrify(sql, data)))
            cr.execute(sql, data)
            row = cr.fetchone()
            while row is not None:
                testbed_sensors.append(dict({'target': row[0],
                                             'sensor_type': row[1],
                                             'sen_key': '{}{}'.format(row[0], row[1])}))
                row = cr.fetchone()
    return testbed_sensors


def build_initial_sensor_state(db_conn, tbname, sensor_types, utc_start, number_days):
    print('build_initial_sensor_state({}, sensor_types, {})'.format(tbname, utc_start))
    testbed_sensors = get_testbed_sensors(db_conn=db_conn,
                                          tbname=tbname,
                                          sensor_types=sensor_types)
    print('Building the initial states of each sensor by looking back {} days.'.format(number_days))
    sensor_state = dict()
    for sen_dict in testbed_sensors:
        sensor_state[sen_dict['sen_key']] = ''

    sql = ('SELECT target, sensor_type, message FROM all_events WHERE tbname=%s AND '
           'sensor_type=ANY(%s) AND stamp BETWEEN (%s - interval \'%s\' day) AND %s '
           'ORDER BY stamp;')
    data = (tbname, sensor_types, utc_start, number_days, utc_start,)
    with db_conn:
        with db_conn.cursor() as cr:
            # print('{}'.format(cr.mogrify(sql, data)))
            cr.execute(sql, data)
            row = cr.fetchone()
            while row is not None:
                sen_key = '{}{}'.format(row[0], row[1])
                sensor_state[sen_key] = row[2]
                row = cr.fetchone()
    return testbed_sensors, sensor_state


def write_header(output, testbed_sensors):
    output.write('utc_timestamp,utc_epoch,local_timestamp')
    for sen_dict in testbed_sensors:
        output.write(',{}_{}'.format(sen_dict['target'], sen_dict['sensor_type']))
    output.write('\n')
    return


def write_state(output, stamp, testbed_sensors, sensor_state, timezone):
    output.write('{}'.format(stamp))
    output.write(',{}'.format(make_epoch(stamp)))
    output.write(',{}'.format(localize_stamp(utc_datetime=stamp,
                                             timezone=timezone)))
    for sen_dict in testbed_sensors:
        output.write(',{}'.format(sensor_state[sen_dict['sen_key']]))
    output.write('\n')
    return


def make_epoch(utc_datetime):
    epoch = None
    if utc_datetime is not None:
        if utc_datetime.tzinfo is None:
            raise TypeError('make_epoch(utc_datetime) is naive, '
                            'datetime.datetime.tzinfo is not set!')
        elif utc_datetime.tzinfo != pytz.utc:
            raise TypeError("make_epoch(utc_datetime) is not UTC!")
        epoch = (utc_datetime - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
    return epoch


def localize_stamp(utc_datetime, timezone):
    stamp_local = pytz.utc.localize(utc_datetime.replace(tzinfo=None),
                                    is_dst=None).astimezone(timezone)
    return stamp_local


def gather_raw_sensor_data(db_conn, tbname, utc_start, utc_end, sensors):
    sql = ('SELECT stamp_utc, stamp_local, target, message, sensor_type FROM all_events WHERE '
           'tbname=%s AND stamp BETWEEN %s AND %s AND sensor_type=ANY(%s);')
    data = (tbname,
            utc_start,
            utc_end,
            sensors,)
    raw_data = list()
    with db_conn:
        with db_conn.cursor() as cr:
            # print(str(cr.mogrify(sql, data)))
            cr.execute(sql, data)
            row = cr.fetchone()
            count = 0
            while row is not None:
                if (count % 1000) == 0:
                    print('    loading from database at {}'.format(row[1]))
                count += 1
                stamp_utc = row[0].replace(tzinfo=pytz.utc)
                event = dict({'stamp_utc': stamp_utc,
                              'stamp_local': row[1],
                              'target': row[2],
                              'message': row[3],
                              'sensor_type': row[4],
                              'sen_key': '{}{}'.format(row[2], row[4])})
                raw_data.append(copy.deepcopy(event))
                row = cr.fetchone()
    return raw_data


def build_features(cli_args):
    db_conn = psycopg2.connect(database=cli_args.dbname,
                               host=cli_args.dbhost,
                               port=cli_args.dbport,
                               user=cli_args.dbuser,
                               password=cli_args.dbpass)

    timezone = get_testbed_timezone(db_conn=db_conn,
                                    tbname=cli_args.testbed)
    if timezone is None:
        print("ERROR! Given testbed '{}' does not exist in the database!".format(cli_args.testbed))
        sys.exit(1)
    sensors = list()
    for sen_item in cli_args.sensor:
        for data_item in DATA_TYPES[sen_item]:
            if data_item not in sensors:
                sensors.append(copy.deepcopy(data_item))

    print('db sensor types to use: {}'.format(sensors))
    utc_start = get_utc_stamp(db_conn=db_conn,
                              tbname=cli_args.testbed,
                              local_stamp=cli_args.start)
    utc_end = get_utc_stamp(db_conn=db_conn,
                            tbname=cli_args.testbed,
                            local_stamp=cli_args.end)

    testbed_sensors, sensor_state = build_initial_sensor_state(
        db_conn=db_conn,
        tbname=cli_args.testbed,
        sensor_types=sensors,
        utc_start=utc_start,
        number_days=cli_args.initialStateDays)
    raw_data = gather_raw_sensor_data(db_conn=db_conn,
                                      tbname=cli_args.testbed,
                                      utc_start=utc_start,
                                      utc_end=utc_end,
                                      sensors=sensors)

    print('Beginning iteration through the data at intervals of {} {}...'.format(cli_args.size,
                                                                                 cli_args.scale))
    write_header(output=cli_args.output,
                 testbed_sensors=testbed_sensors)

    time_delta_dict = dict({'hours': datetime.timedelta(hours=cli_args.size),
                            'minutes': datetime.timedelta(minutes=cli_args.size),
                            'seconds': datetime.timedelta(seconds=cli_args.size),
                            'microseconds': datetime.timedelta(microseconds=cli_args.size)})
    time_delta = copy.deepcopy(time_delta_dict[cli_args.scale])
    print('time delta you have selected is: {}'.format(time_delta))
    current_time = copy.deepcopy(utc_start)
    raw_pointer = 0
    count = 0
    while current_time < utc_end:
        while raw_pointer < len(raw_data) and raw_data[raw_pointer]['stamp_utc'] <= current_time:
            sensor_state[raw_data[raw_pointer]['sen_key']] = raw_data[raw_pointer]['message']
            raw_pointer += 1
        write_state(output=cli_args.output,
                    stamp=current_time,
                    testbed_sensors=testbed_sensors,
                    sensor_state=sensor_state,
                    timezone=timezone)
        if (count % 10000) == 0:
            print('    iteration at {}, with a range of {} left to go.'.format(
                current_time, (utc_end-current_time)))
        count += 1
        current_time = current_time + time_delta

    cli_args.output.close()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CASAS Build Sampled Features Tool')
    parser.add_argument('--testbed',
                        dest='testbed',
                        type=str,
                        required=True,
                        help='The testbed to pull the data from.')
    parser.add_argument('--scale',
                        dest='scale',
                        type=str,
                        choices=['hours', 'minutes', 'seconds', 'microseconds'],
                        help='The scale at which to create the sampling.',
                        default='seconds')
    parser.add_argument('--size',
                        dest='size',
                        type=float,
                        help='The value of the given scale to wait between samples, default=1.0.',
                        default=1.0)
    parser.add_argument('--sensor',
                        dest='sensor',
                        nargs='+',
                        choices=['entity', 'entity-temp', 'motion', 'door', 'item',
                                 'light', 'temperature', 'lightsensor', 'battery'],
                        help='This identifies the sensor(s) that you would like sampled. '
                             'entity is a meta list containing motion, door, item, and light. '
                             'entity-temp adds temperature sensors to the list. '
                             'You can list multiple sensors for this argument, ex: '
                             '"--sensor motion door temperature".',
                        default=['entity'])
    parser.add_argument('--output',
                        dest='output',
                        type=argparse.FileType('w'),
                        required=True,
                        help='The file to write the results to.')
    parser.add_argument('--start',
                        dest='start',
                        required=True,
                        help='Start date for the sampling data.')
    parser.add_argument('--end',
                        dest='end',
                        required=True,
                        help='End date for the sampling data.')
    parser.add_argument('--initialStateDays',
                        dest='initialStateDays',
                        type=int,
                        help='Optionally set how many days back to look for loading the sensor '
                             'initial states from the database, default is 90 (days).',
                        default=90)
    parser.add_argument('--dbhost',
                        dest='dbhost',
                        type=str,
                        help='Optionally override the database hostname adbpg.ailab.wsu.edu.',
                        default='adbpg.ailab.wsu.edu')
    parser.add_argument('--dbport',
                        dest='dbport',
                        type=str,
                        help='Optionally override the database port 5432.',
                        default='5432')
    parser.add_argument('--dbname',
                        dest='dbname',
                        type=str,
                        help='Optionally override the name of the database to connect to.',
                        default='smarthomedata')
    parser.add_argument('--dbuser',
                        dest='dbuser',
                        type=str,
                        required=True,
                        help='The username to use for connecting to the database.')
    parser.add_argument('--dbpass',
                        dest='dbpass',
                        help='The program will attempt to use pgpasslib to get your password '
                             'unless you provide one here (not recommended on public machines!).')
    args = parser.parse_args()
    if args.dbpass is None:
        args.dbpass = pgpasslib.getpass(host=args.dbhost,
                                        port=args.dbport,
                                        dbname=args.dbname,
                                        user=args.dbuser)
    sensor_list = list()
    for item in args.sensor:
        if item == 'entity':
            entity_sensors = ['motion', 'door', 'item', 'light']
            for entity_item in entity_sensors:
                if entity_item not in sensor_list:
                    sensor_list.append(copy.deepcopy(entity_item))
        elif item == 'entity-temp':
            entity_sensors = ['motion', 'door', 'item', 'light', 'temperature']
            for entity_item in entity_sensors:
                if entity_item not in sensor_list:
                    sensor_list.append(copy.deepcopy(entity_item))
        else:
            if item not in sensor_list:
                sensor_list.append(copy.deepcopy(item))
    args.sensor = sensor_list
    build_features(cli_args=args)

