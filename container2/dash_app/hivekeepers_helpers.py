# pandas vers==1.4.0
import sqlite3
import sqlalchemy as db
from sqlalchemy import func
import copy

import pandas as pd

def convert_csv_to_df(csv_file):

    # read file into dataframe
    try :
        hivekeepers_data = pd.read_csv(csv_file)
    except FileNotFoundError as error_msg:
        print(f'{csv_file} File not found!{error_msg=}, {type(error_msg)=}')
    except Exception as error_msg:
        print(f'{csv_file} Unexpected! {error_msg=}, {type(error_msg)=}')
    
    return hivekeepers_data
    
def get_db_data(db_path):
    # working dir: /home/hivekeeper/dash_app/
    # Create your connection.
    connect_db = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM hivedata", connect_db)
    connect_db.close()

    return df

def get_db():
    # working dir: /home/hivekeeper/dash_app/
    # Create your connection.
    engine = db.create_engine('sqlite:///hivekeepers.db')
    connection = engine.connect()

    metadata = db.MetaData()
    hivedata = db.Table('hivedata', metadata, autoload=True, autoload_with=engine)

    query = db.select([hivedata]) 

    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    
    connection.close()

    df = pd.DataFrame(ResultSet)

    return df

def get_data_2d(apiary_id, start_date, end_date):
    # working dir: /home/hivekeeper/dash_app/
    # Create connection.
    engine = db.create_engine('sqlite:///hivekeepers.db')
    connection = engine.connect()
    
    metadata = db.MetaData()
    hivedata = db.Table('hivedata', metadata, autoload=True, autoload_with=engine)
    #print(hivedata.columns.keys())
    #print(repr(metadata.tables['hivedata']))

    query = db.select([hivedata]).where(db.and_(hivedata.columns.apiary_id == apiary_id),(func.DATE(hivedata.columns.timestamp).between(start_date, end_date)))
    #query = db.select([hivedata]).where(db.and_(hivedata.columns.apiary_id == apiary_id),hivedata.columns.timestamp.between(start_date, end_date))
    
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    
    connection.close()

    df = pd.DataFrame(ResultSet)

    return df

def get_data_3d(apiary_id, start_date, end_date):
    # working dir: /home/hivekeeper/dash_app/
    # Create connection.
    engine = db.create_engine('sqlite:///hivekeepers.db')
    connection = engine.connect()
    
    metadata = db.MetaData()
    hivedata = db.Table('hivedata_3d', metadata, autoload=True, autoload_with=engine)
    #print(hivedata.columns.keys())
    #print(repr(metadata.tables['hivedata']))

    query = db.select([hivedata]).where(db.and_(hivedata.columns.apiary_id == apiary_id),(func.DATE(hivedata.columns.timestamp).between(start_date, end_date)))
    #query = db.select([hivedata]).where(db.and_(hivedata.columns.apiary_id == apiary_id),hivedata.columns.timestamp.between(start_date, end_date))
    
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchall()
    
    connection.close()

    df = pd.DataFrame(ResultSet)

    return df

def clean_data(dataframe):
    # drop unnecessary columns
    dataframe.drop(dataframe.columns[[1,3,4,5,6,7,9,10,11,12,13,14,15,16,18,19,20,22,23,24,25,90,91]], axis=1, inplace=True)
    
    # add internal/external temperature delta column - confirm which they want? 
    # option1: int - ext                <- non-absolute delta of int and delta
    # option2: abs(int - ext)           <- the absolute delta of and ext
    # option3: int - abs(int - ext)     <- int - (the absolute difference of int and ext)
    
    #hivekkeepers_data['temp_delta'] = hivekkeepers_data['bme680_internal_temperature'] - hivekkeepers_data['bme680_external_temperature']
    dataframe['temp_delta'] = dataframe['bme680_internal_temperature'] - dataframe['bme680_external_temperature']
    #hivekkeepers_data['temp_delta'] = hivekkeepers_data['bme680_internal_temperature'] - abs(hivekkeepers_data['bme680_internal_temperature'] - hivekkeepers_data['bme680_external_temperature'])

    # convert timestamp From Unix/Epoch time to Readable date format:
    # eg. from 1635249781 to 2021-10-26 12:03:01
    dataframe['timestamp'] = pd.to_datetime(dataframe['timestamp'], unit='s')

    return dataframe

def get_last_index_df(dataframe):
    return dataframe['id'].iloc[-1]

def update_sql_db(dataframe, database, table):
    # open connection to db - experienced permission issues in container!!!
    connection = sqlite3.connect(database)

    # update db with dataframe data
    dataframe.to_sql(table, connection, if_exists='replace', index = False)
    
    # close db connection
    connection.close()

    return None

def get_last_index_db(database):
    # open connection to db - experienced permission issues in container!!!
    connection = sqlite3.connect(database)
    
    # get current highest index value for comparing with off-site db for updates
    cursor = connection.cursor()
    cursor.execute('''SELECT MAX(id) FROM hivedata''')
    sql_last_index = cursor.fetchall()[0][0]
    
    # close db cursor and connection
    cursor.close()
    connection.close()
    
    return sql_last_index

def get_uniques_in_column(dataframe, column):

    unique_list = []
    
    for item in dataframe[column]:
        # check if exists in unique_list or not
        if item not in unique_list:
            unique_list.append(item)

    return unique_list

def get_bin_range(bin_group, fft_bins):
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
    
def build_3d_data(dataframe, bins, amplitudes):
    ## --------------------------------
    ## build new dataframe for 4d chart 
    ## takes hivekeepers dataframe, a list of the fft_bins and a list of the fft_amplitude values
    ## returns a dataframe where each index has each fft_bin and fft_amplitude value (total 64 per index)
    ## --------------------------------

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
    for i in amplitudes:
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
    return pd.to_datetime(dataframe[column], unit='s')

def get_fft_bins(dataframe):    
    return [col for col in dataframe if col.startswith('fft_bin')]

def get_2d_xrangeslider():

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

def test(text):
    return text

if __name__ == '__main__':
    convert_csv_to_df()
    get_db_data()
    get_db()
    get_data_2d()
    get_data_3d()
    clean_data()
    get_last_index_df()
    update_sql_db()
    get_last_index_db()
    get_uniques_in_column()
    get_bin_range()
    build_3d_data()
    convert_timestamp()
    get_2d_xrangeslider()
    get_fft_bins()
    test()
    