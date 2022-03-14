import pandas as pd
import hivekeepers_helpers as hp

import sqlalchemy as db
from sqlalchemy import func

import hivekeepers_config as hc

import logging

## =================
## Configure Logging 
## =================

# build logger
logger = logging.getLogger()

# set stdout as log output
handler = logging.StreamHandler()

# set log format
formatter = logging.Formatter('%(asctime)s [PYTHON] %(filename)s %(levelname)s %(message)s')

# add formatter
handler.setFormatter(formatter)

# add handler
logger.addHandler(handler)

# get logging level from system environment variable
log_level = hc.APP_LOG_LEVEL
#print('log level env: ', log_level)

# set logging level from system environment variable
if log_level == 'DEBUG':
  logger.setLevel(logging.DEBUG)
elif log_level == 'INFO':
  logger.setLevel(logging.INFO)
elif log_level == 'WARNING':
  logger.setLevel(logging.WARNING)
elif log_level == 'ERROR':
  logger.setLevel(logging.ERROR)
elif log_level == 'CRITICAL':
  logger.setLevel(logging.CRITICAL)

## ===============================
## MYSQL REMOTE SERVER CREDENTIALS
## ===============================

credentials = {
    'username': hc.MYSQL_USER,
    'password': hc.MYSQL_PASS ,
    'host': hc.MYSQL_HOST,
    'database': hc.MYSQL_DB,
}

## =============================
## get remote MySQL INDEX length
## =============================

# build database connection url
connect_url = db.engine.url.URL.create(
    drivername='mysql+pymysql',
    username=credentials['username'],
    password=credentials['password'],
    host=credentials['host'],
    database=credentials['database']
)

# create MySQL db engine - set pool config
engine = db.create_engine(connect_url, pool_size=10, max_overflow=10, pool_recycle=3600, pool_pre_ping=True, echo=False)

# construct SQL query
query1 = 'SELECT COUNT(id) FROM sync_data'

# open db connection, send query
with engine.connect() as conn:
    logger.info('get index length of remote MySQL database')
    result = conn.execute(query1)
    remote_index_count = result.fetchone()[0]

#print('remote index = ', remote_index_count)

## =============================
## get local SQLite INDEX length
## =============================

# create SQLite db engine
sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)

# construct SQL query
query3 =  f'SELECT COUNT(id) FROM {hc.SQLite_2d_table_name}'

# open db connection, send query
with sql_lite_engine.connect() as conn:
    logger.info('get index length of local SQLite database')
    result = conn.execute(query3)
    local_index_count = result.fetchone()[0]

#print('local index = ', local_index_count)

if not (remote_index_count > local_index_count):
    logger.info('No update necessary as both remote and local indexers match')
    ## =====================================
    ## print status to be shown in Dashboard
    ## =====================================

    print(f'database is already up to date...')

else:
    logger.info('remote and local indexers do not match')
    # calc the the number of remote changes local doesn't have
    index_diff = remote_index_count - local_index_count

    #print('index difference = ', index_diff)
   
    # calc the final expected local database index count after update
    update_count = local_index_count + index_diff

    if not (update_count == remote_index_count):
        logger.warn('update aborted! Database update sanity test failed... expected local database length does not match remote database length')
        ## ===========
        ## sanity test
        ## ===========

        ## ========================================================================
        ## Could simply replace all data in local database here as working solution
        ## solution: call startup_update_db.py
        ##    all data will be pulled from remote MySQL database and local database
        ##    will be re instantiated with remote data.
        ##
        ## - very unlikely this situation will arise, but possible.
        ## ========================================================================

        ## the final index count after update should match between remote and local databases.
        ## possible fix would be to simply reset the local database from the remote source.
        print(f'remote and local database counts do not match!')
    
    else:
        logger.info('starting update...')
        ## ==========================================
        ## get MySQL rows where INDEXES not on local 
        ## ==========================================

        # construct SQL query for database updates
        query4 = f'select {", ".join(str(column) for column in hc.SQLite_default_columns)} from sync_data WHERE id > {local_index_count}'

        # open db connection, send query, store in dataframe
        with engine.connect() as conn:
            logger.info('getting new data from remote MySQL database')
            update_data = pd.read_sql(query4, conn)
        
        # clean update data:
        #   1. add temp_delta column
        #   2. convert timestamp to human-readable
        update_data = hp.clean_data_db(update_data)

        # translate update data to 3d data scheme 
        #update_data_3d = hp.build_3d_data(update_data)
        
        ## ======================================
        ## append update datasets to local SQLite
        ## ======================================

        # update SQLite with 2d data - options: append, replace
        with sql_lite_engine.connect() as conn:
            logger.info('appending new data from remote MySQL database to local SQLite database')
            update_data.to_sql(hc.SQLite_2d_table_name, conn, if_exists='append', index = False)

        # update SQLite with 3d data - options: append, replace
        #with sql_lite_engine.connect() as conn:
        #    update_data_3d.to_sql(hc.SQLite_3d_table_name, conn, if_exists='append', index = False)
        
        ## =====================================
        ## print status to be shown in Dashboard
        ## =====================================
        logger.info('database update completed.')
        print(f'database has been updated! New rows added: {index_diff}')
