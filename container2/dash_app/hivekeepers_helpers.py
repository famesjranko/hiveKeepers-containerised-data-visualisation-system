# HiveKeepers - container2 - dash_app/hivekeepers_helpers.py
# written by: Andrew McDonald
# initial: 26/01/22
# current: 18/03/22
# version: 0.9

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

def get_apiary_names():
    logger.info('getting apiary name list from local SQLite server...')
    # create SQLite db engine

    try:
        sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=hc.SQL_VERBOSE)
    except Exception as e:
        logger.warning(f'SQLite database exception: {e}')

    query =  f'SELECT DISTINCT apiary_name FROM {hc.SQLite_2d_table_name}'
    logger.debug(f'get apiary names query: {query}')

    apiary_list_names = []

    try:
        with sql_lite_engine.connect() as conn:
            result = conn.execute(query)
            for row in result:
                apiary_list_names.append(row[0])
    except Exception as e:
        logger.warning(f'SQLite database exception: {e}')

    logger.debug(f'apiary_list: {apiary_list_names}')

    if apiary_list_names:
        logger.info('successfully got apiary id list from local SQLite server')
    else:
        logger.info('returned apiary id list from local SQLite server is empty')

    return apiary_list_names


def get_apiary_timestamps_name(apiary_name):
    logger.info('getting apiary name timestampes from SQLite server')
    # create SQLite db engine
    sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=hc.SQL_VERBOSE)

    query =  f'SELECT timestamp FROM {hc.SQLite_2d_table_name} WHERE apiary_name = "{apiary_name}"'

    with sql_lite_engine.connect() as conn:
        apiary_timestamp_df = pd.read_sql_query(query, conn)

    logger.debug(f'apiary_df: {apiary_timestamp_df.head()}')

    return apiary_timestamp_df


def get_data(apiary_name, start_date, end_date):
    logger.info('getting all data for apiary between start_date, end_date from SQLite server')
    # working dir: /home/hivekeeper/dash_app/
    # Create connection
    try:
        logger.info('opening connection to local SQLite database')
        engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=hc.SQL_VERBOSE)
        connection = engine.connect()
    except Exception as e:
        logger.warning(f'SQLite database exception: {e}')
    
    metadata = db.MetaData()
    logger.debug(f'SQLite metadata: {metadata}')

    hivedata = db.Table(hc.SQLite_2d_table_name, metadata, autoload=True, autoload_with=engine)
    logger.debug(f'SQLite tables: {hivedata}')

    query = db.select([hivedata]).where(db.and_(hivedata.columns.apiary_name == apiary_name),(func.DATE(hivedata.columns.timestamp).between(start_date, end_date)))
    logger.debug(f'SQLite query = {query}')

    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    
    logger.info('closing connection to local SQLite database...')
    connection.close()

    logger.debug(f'SQLite response = {ResultSet}')

    logger.info('converting SQLite response to 2d dataframe...')
    apiary_data_df = pd.DataFrame(ResultSet)

    logger.debug(f'2d dataframe: {apiary_data_df.head()}')

    return apiary_data_df


def clean_data_db(dataframe):
    logger.info('cleaning data before insert into SQLite server')
    logger.info('adding temperature delta column to data')

    # add internal/external temperature delta column
    dataframe['temp_delta'] = dataframe['bme680_internal_temperature'] - dataframe['bme680_external_temperature']

    logger.info('converting timestamp column to hunan readable format - eg from 1635249781 to 2021-10-26 12:03:01')
    
    # convert timestamp From Unix/Epoch time to Readable date format:
    # eg. from 1635249781 to 2021-10-26 12:03:01
    dataframe['timestamp'] = pd.to_datetime(dataframe['timestamp'], unit='s')

    logger.debug(f'cleaned_dataframe: {dataframe.head()}')

    return dataframe


def build_3d_data(dataframe):
    logger.info('building dataframe for 3d charts...')
    ## --------------------------------
    ## build new dataframe for 4d chart 
    ## takes hivekeepers dataframe, a list of the fft_bins and a list of the fft_amplitude values
    ## returns a dataframe where each index has each fft_bin and fft_amplitude value (total 64 per index)
    ## --------------------------------

    # get fft bin names and amplitude values
    logger.info('get fft bin name list...')
    bins = get_fft_bins(dataframe)
    logger.debug(f'fft bins: {bins}')

    # get fft bin names and amplitude values
    logger.info('get fft bin values list...')
    fft_amplitudes = dataframe[bins].values
    logger.debug(f'fft amplitude: {bins}')

    # get timestamp and internal temp data
    logger.info('get internal temperature values...')
    internal_temps = copy.deepcopy(dataframe['bme680_internal_temperature'])
    logger.debug(f'internal temperatures df: {internal_temps}')

    # build initial df with timestamp and apiary columns
    logger.info('build first part of 3d data... apiary and timestamps columns...')
    data_3d_1 = [copy.deepcopy(dataframe['timestamp']), copy.deepcopy(dataframe['apiary_name'])]
    headers_3d_1 = ['timestamp', 'apiary_name']
    df_3d_1 =  pd.concat(data_3d_1, axis=1, keys=headers_3d_1)
    logger.debug(f'df_3d_1: {df_3d_1}')

    # add internal temperate column and data - repeat for each bin per timestamp index
    logger.info('build second part of 3d data... for every timestamp, repeat the current rows 64 fft bins...')
    df_3d_2 = df_3d_1.loc[df_3d_1.index.repeat(len(bins))].assign(internal_temp=internal_temps).reset_index(drop=True)
    #df_3d_2 = copy.deepcopy(df_3d_1.loc[df_3d_1.index.repeat(len(bins))].assign(internal_temp=internal_temps).reset_index(drop=True))
    #df_3d_2 = df_3d_1.loc[df_3d_1.index.repeat(len(bins))].assign(internal_temp=internal_temps).reset_index(drop=True)
    logger.debug(f'df_3d_2: {df_3d_2}')

    # build lists for converting to dataframe
    logger.info('prepare lists of fftbins and amplitudes for converting to 3d dataframe...')
    amp_list = []
    bin_list = []
    for i in fft_amplitudes:
        n = 0
        for j in i:
            amp_list.append(j)
            bin_list.append(bins[n])
            n += 1

    logger.debug(f'amp_list: {amp_list}')
    logger.debug(f'bin_list: {bin_list}')

    # convert each list to dataframe
    logger.info('convert new amplitude list to dataframe')
    df_fft_amplitude = pd.DataFrame(amp_list, columns=['fft_amplitude'])

    logger.info('convert new fft bins list to dataframe')
    df_fft_band = pd.DataFrame(bin_list, columns=['fft_band'])

    # final 3d dataframe data
    logger.info('build final 3d dataframe using timestamp, apiary_name, internaltemp, fftammplitude, fftband')

    logger.info('define 3d dataframe data')
    data_3d = [df_3d_2['timestamp'],
               df_3d_2['apiary_name'],
               df_3d_2['internal_temp'],
               df_fft_amplitude['fft_amplitude'],
               df_fft_band['fft_band']]

    # final 3d dataframe headers
    logger.info('define 3d dataframe headers')
    headers_3d = ['timestamp',
                  'apiary_name',
                  'internal_temperature',
                  'fft_amplitude',
                  'fft_band']

    # build 3d dataframe
    logger.info('build final 3d dataframe')
    dataframe_3d = pd.concat(data_3d, axis=1, keys=headers_3d)

    logger.debug(f'final 3d dataframe: {dataframe_3d.head()}')

    return dataframe_3d


def get_uniques_in_column(dataframe, column):
    logger.info('building list of unique values from a dataframe column')
    unique_list = []
    
    for item in dataframe[column]:
        # check if exists in unique_list or not
        if item not in unique_list:
            unique_list.append(item)

    logger.debug(f'unique list: {unique_list}')

    return unique_list


def get_bin_range(bin_group, fft_bins):
    logger.info('setting the fft_bin range from user selection')
    logger.debug(f'fft bin_group: {bin_group}')
    logger.debug(f'fft fft_bins: {fft_bins}')
    logger.debug(f'fft fft_bins length: {len(fft_bins)}')
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


def get_fft_bins(dataframe):
    logger.info('building list of fft_bin column headers from dataframe')
    fft_bins = [col for col in dataframe if col.startswith('fft_bin')]
    logger.debug(f'fft_bins list: {fft_bins}')

    return fft_bins


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
    