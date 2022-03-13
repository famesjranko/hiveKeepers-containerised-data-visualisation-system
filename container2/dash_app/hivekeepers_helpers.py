# pandas vers==1.4.0
import sqlite3
import sqlalchemy as db
from sqlalchemy import func
import copy

import pandas as pd
import hivekeepers_config as hc

import logging

## =================
## Configure Logging 
## =================

logger = logging.getLogger()

## ====================
## APP helper functions
## ====================

def convert_csv_to_df(csv_file):
    logger.info('converting csv file to dataframe')
    # read file into dataframe
    try :
        hivekeepers_data = pd.read_csv(csv_file)
    except FileNotFoundError as error_msg:
        print(f'{csv_file} File not found!{error_msg=}, {type(error_msg)=}')
    except Exception as error_msg:
        print(f'{csv_file} Unexpected! {error_msg=}, {type(error_msg)=}')
    
    return hivekeepers_data
    
def get_db_data(db_path):
    logger.info('getting all data from local SQLite database')
    # working dir: /home/hivekeeper/dash_app/
    # Create your connection.
    connect_db = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM {hc.SQLite_2d_table_name}", connect_db)
    connect_db.close()

    return df

def get_db():
    logger.info('getting all data from local SQLite database')
    # working dir: /home/hivekeeper/dash_app/
    # Create your connection.
    sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)
    connection = sql_lite_engine.connect()

    metadata = db.MetaData()
    hivedata = db.Table(hc.SQLite_2d_table_name, metadata, autoload=True, autoload_with=sql_lite_engine)

    query = db.select([hivedata]) 

    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    
    connection.close()

    df = pd.DataFrame(ResultSet)

    return df

def get_apiarys():
    logger.info('getting apiary id list from local SQLite server...')
    # create SQLite db engine
    sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)

    query =  f'SELECT DISTINCT apiary_id FROM {hc.SQLite_2d_table_name}'

    apiary_list = []

    with sql_lite_engine.connect() as conn:
        result = conn.execute(query)
        for row in result:
            apiary_list.append(row[0])

    if apiary_list:
        logger.info('successfully got apiary id list from local SQLite server')
    else:
        logger.info('returned apiary id list from local SQLite server is empty')

    return apiary_list

def check_apiary_timestamps(apiary_id, start_date, end_date):
    logger.info('checking that user selected apiaryid and date range has data in SQLite database')
    # working dir: /home/hivekeeper/dash_app/
    # Create connection.
    sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)

    query =  f'SELECT timestamp FROM {hc.SQLite_2d_table_name} WHERE apiary_id = {apiary_id} AND timestamp BETWEEN {start_date} AND {end_date}'

    with sql_lite_engine.connect() as conn:
        result = conn.execute(query)

    if int(result.rowcount) == 0:
        logger.info('No data found for user selected apiaryid and date range in SQLite database')
        return False
    else:
        logger.info('Data found for user selected apiaryid and date range in SQLite database')
        return True

def get_apiary_timestamps(apiary_id):
    logger.info('getting apiary id timestampes from SQLite server')
    # create SQLite db engine
    sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)

    query =  f'SELECT timestamp FROM {hc.SQLite_2d_table_name} WHERE apiary_id = {apiary_id}'

    with sql_lite_engine.connect() as conn:
        apiary_df = pd.read_sql_query(query, conn)

    return apiary_df

def get_timestamps():
    logger.info('getting all timestampes from SQLite server')
    # create SQLite db engine
    sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)

    query =  f'SELECT DISTINCT timestamp FROM {hc.SQLite_2d_table_name}'

    timestamp_list = []

    with sql_lite_engine.connect() as conn:
        result = conn.execute(query)
        for row in result:
            timestamp_list.append(row[0])

    timestamp_df = pd.DataFrame(timestamp_list, columns=['timestamp'])

    return timestamp_df

def get_data_2d(apiary_id, start_date, end_date):
    logger.info('getting all data for apiary between start_date, end_date from SQLite server')
    # working dir: /home/hivekeeper/dash_app/
    # Create connection.
    engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)
    connection = engine.connect()
    
    metadata = db.MetaData()
    hivedata = db.Table(hc.SQLite_2d_table_name, metadata, autoload=True, autoload_with=engine)

    query = db.select([hivedata]).where(db.and_(hivedata.columns.apiary_id == apiary_id),(func.DATE(hivedata.columns.timestamp).between(start_date, end_date)))
    
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    
    connection.close()

    df = pd.DataFrame(ResultSet)

    return df

def get_data_3d(apiary_id, start_date, end_date):
    logger.info('getting all 3d data for apiary between start_date, end_date from SQLite server')
    # working dir: /home/hivekeeper/dash_app/
    # Create connection.
    engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)
    connection = engine.connect()
    
    metadata = db.MetaData()
    hivedata = db.Table(hc.SQLite_3d_table_name, metadata, autoload=True, autoload_with=engine)

    query = db.select([hivedata]).where(db.and_(hivedata.columns.apiary_id == apiary_id),(func.DATE(hivedata.columns.timestamp).between(start_date, end_date)))
    
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    
    connection.close()

    df = pd.DataFrame(ResultSet)

    return df

def clean_data_csv(dataframe):
    logger.info('cleaning data before insert into SQLite server')
    # drop unnecessary columns
    dataframe.drop(dataframe.columns[[1,3,4,5,6,7,9,10,11,12,13,14,15,16,18,19,20,22,23,24,25,90,91]], axis=1, inplace=True)
    
    # add internal/external temperature delta column
    dataframe['temp_delta'] = dataframe['bme680_internal_temperature'] - dataframe['bme680_external_temperature']

    # convert timestamp From Unix/Epoch time to Readable date format:
    # eg. from 1635249781 to 2021-10-26 12:03:01
    dataframe['timestamp'] = pd.to_datetime(dataframe['timestamp'], unit='s')

    return dataframe

def clean_data_db(dataframe):
    logger.info('cleaning data before insert into SQLite server')
    logger.info('adding temperature delta column to data')
    # add internal/external temperature delta column
    dataframe['temp_delta'] = dataframe['bme680_internal_temperature'] - dataframe['bme680_external_temperature']

    logger.info('converting timestamp column to hunan readable format - eg from 1635249781 to 2021-10-26 12:03:01')
    # convert timestamp From Unix/Epoch time to Readable date format:
    # eg. from 1635249781 to 2021-10-26 12:03:01
    dataframe['timestamp'] = pd.to_datetime(dataframe['timestamp'], unit='s')

    return dataframe

def add_delta_column(dataframe):
    logger.info('adding delta temperate column to dataframe')
    dataframe['temp_delta'] = dataframe['bme680_internal_temperature'] - dataframe['bme680_external_temperature']

    return dataframe

def get_last_index_df(dataframe):
    logger.info('getting last index value from dataframe')
    return dataframe['id'].iloc[-1]

def update_sql_db(dataframe, database, table):
    logger.info('inserting dataframe into local SQLite databse')
    # open connection to db - experienced permission issues in container!!!
    connection = sqlite3.connect(database)

    # update db with dataframe data
    dataframe.to_sql(table, connection, if_exists='replace', index = False)
    
    # close db connection
    connection.close()

    return None

def get_last_index_db(database):
    logger.info('getting last index value from local SQLite databse')
    # open connection to db - experienced permission issues in container!!!
    connection = sqlite3.connect(database)
    
    # get current highest index value for comparing with off-site db for updates
    cursor = connection.cursor()
    cursor.execute('''SELECT COUNT(id) FROM hivedata2d''')
    sql_last_index = cursor.fetchall()[0][0]
    
    # close db cursor and connection
    cursor.close()
    connection.close()
    
    return sql_last_index

def get_uniques_in_column(dataframe, column):
    logger.info('building list of unique values from a dataframe column')
    unique_list = []
    
    for item in dataframe[column]:
        # check if exists in unique_list or not
        if item not in unique_list:
            unique_list.append(item)

    return unique_list

def get_bin_range(bin_group, fft_bins):
    logger.info('setting the fft_bin range from user selection')
    ## takes int value representing a selected grouping
    ## returns list of selected fft_bin names
    if bin_group == 1:
        return fft_bins[0:16]
    elif bin_group == 2:
        return fft_bins[16:32]
    elif bin_group == 3:
        return fft_bins[32:48]
    elif bin_group == 4:
        return fft_bins[48:64]
    else:
        return fft_bins
    
def build_3d_data(dataframe):
    logger.info('building dataframe for 3d charts...')
    ## --------------------------------
    ## build new dataframe for 4d chart 
    ## takes hivekeepers dataframe, a list of the fft_bins and a list of the fft_amplitude values
    ## returns a dataframe where each index has each fft_bin and fft_amplitude value (total 64 per index)
    ## --------------------------------

    # get fft bin names and amplitude values
    bins = get_fft_bins(dataframe)

    # get fft bin names and amplitude values
    fft_amplitudes = dataframe[bins].values

    # get timestamp and internal temp data
    internal_temps = copy.deepcopy(dataframe['bme680_internal_temperature'])

    # build initial df with timestamp and apiary columns
    data_4d_1 = [copy.deepcopy(dataframe['timestamp']), copy.deepcopy(dataframe['apiary_id'])]
    headers_4d_1 = ['timestamp', 'apiary_id']
    df_4d_1 =  pd.concat(data_4d_1, axis=1, keys=headers_4d_1)

    # add internal temperate column and data - repeat for each bin per timestamp index
    df_4d_2 = df_4d_1.loc[df_4d_1.index.repeat(len(bins))].assign(internal_temp=internal_temps).reset_index(drop=True)
    #df_4d_2 = copy.deepcopy(df_4d_1.loc[df_4d_1.index.repeat(len(bins))].assign(internal_temp=internal_temps).reset_index(drop=True))
    #df_4d_2 = df_4d_1.loc[df_4d_1.index.repeat(len(bins))].assign(internal_temp=internal_temps).reset_index(drop=True)

    # build lists for converting to dataframe
    amp_list = []
    bin_list = []
    for i in fft_amplitudes:
        n = 0
        for j in i:
            amp_list.append(j)
            bin_list.append(bins[n])
            n += 1

    # convert each list to dataframe
    df_fft_amplitude = pd.DataFrame(amp_list, columns=['fft_amplitude'])
    df_fft_band = pd.DataFrame(bin_list, columns=['fft_band'])

    # final 4d dataframe data
    data_4d = [df_4d_2['timestamp'],
               df_4d_2['apiary_id'],
               df_4d_2['internal_temp'],
               df_fft_amplitude['fft_amplitude'],
               df_fft_band['fft_band']]

    # final 4d dataframe headers
    headers_4d = ['timestamp',
                  'apiary_id',
                  'internal_temperature',
                  'fft_amplitude',
                  'fft_band']

    # build 4d dataframe
    dataframe_4d = pd.concat(data_4d, axis=1, keys=headers_4d)

    return dataframe_4d

def convert_timestamp(dataframe, column):
    logger.info('converting dataframe timestampe column data from unix to human-readable format')
    return pd.to_datetime(dataframe[column], unit='s')

def get_fft_bins(dataframe):
    logger.info('building list of fft_bin column headers from dataframe')
    return [col for col in dataframe if col.startswith('fft_bin')]

def get_2d_xrangeslider():
    logger.info('getting 2d chart rangeslider')
    hr = dict(count=1,
                label="1h",
                step="hour",
                stepmode="backward")
        
    day = dict(count=1,
                label="1d",
                step="day",
                stepmode="backward")
    
    week = dict(count=7,
                label="1w",
                step="day",
                stepmode="backward")
                
    month = dict(count=1,
                label="1m",
                step="month",
                stepmode="backward")
    
    half_yr = dict(count=6,
                label="6m",
                step="month",
                stepmode="backward")
    
    ytd = dict(count=1,
                label="YTD",
                step="year",
                stepmode="todate")
          
    year = dict(count=1,
                label="1y",
                step="year",
                stepmode="backward")
                
    all = dict(step="all")
    
    buttons_list = list([hr, day, week, month, half_yr, ytd, year, all]) 

    return dict(buttons=buttons_list)
    