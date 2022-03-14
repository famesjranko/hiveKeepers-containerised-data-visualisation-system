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
formatter = logging.Formatter('%(asctime)s [PYTHON] [%(levelname)s] %(filename)s: %(message)s')

# add formatter
handler.setFormatter(formatter)

# add handler
logger.addHandler(handler)

# get logging level from system environment variable
log_level = hc.APP_LOG_LEVEL

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
else:
    logger.setLevel(logging.INFO)

## ===============================
## MYSQL REMOTE SERVER CREDENTIALS
## ===============================

credentials = {
    'username': hc.MYSQL_USER,
    'password': hc.MYSQL_PASS ,
    'host': hc.MYSQL_HOST,
    'database': hc.MYSQL_DB,
}

if 'missing' in credentials.values():
    logger.critical(f'missing MySQL database credentials')

logger.debug(f'remote MySQL credentials: {credentials}')

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

logger.debug(f'remote MySQL url: {connect_url}')

# create MySQL db engine - set pool config
try:
    logger.info('connecting to remote MySQL server...')
    engine = db.create_engine(connect_url, pool_size=10, max_overflow=10, pool_recycle=3600, pool_pre_ping=True, echo=hc.SQL_VERBOSE)
except Exception as e:
    logger.error(f'MySQL database exception: {e}')

# construct SQL query
query1 = 'SELECT COUNT(id) FROM sync_data'
logger.debug(f'MySQL query1 = {query1}')

# open db connection, send query
try:
    with engine.connect() as conn:
        logger.info('get index length of remote MySQL database')
        result = conn.execute(query1)
        remote_index_count = result.fetchone()[0]
        logger.debug(f'MySQL response: {remote_index_count}')
except Exception as e:
    logger.error(f'MySQL database exception: {e}')

## =============================
## get local SQLite INDEX length
## =============================

# create SQLite db engine
try:
    logger.info('connecting to local SQLite server...')
    sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=hc.SQL_VERBOSE)
except Exception as e:
    logger.error(f'SQLite database exception: {e}')

# construct SQL query
query2 =  f'SELECT COUNT(id) FROM {hc.SQLite_2d_table_name}'
logger.debug(f'SQLite query2 = {query2}')

# open db connection, send query
try:
    with sql_lite_engine.connect() as conn:
        logger.info('get index length of local SQLite database')
        result = conn.execute(query2)
        local_index_count = result.fetchone()[0]
        logger.debug(f'SQLite response: {local_index_count}')
except Exception as e:
    logger.error(f'SQLite database exception: {e}')

logger.debug(f'MySQL index count: {remote_index_count}, SQLite index count: {local_index_count}')
logger.debug(f'remote_index_count > local_index_count: {remote_index_count > local_index_count}')

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
    logger.debug(f'index_diff: {index_diff}')
   
    # calc the final expected local database index count after update
    update_count = local_index_count + index_diff
    logger.debug(f'sanity test values: update_count = {update_count}, remote_index_count = {remote_index_count} [test passed if equal]')

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
        query3 = f'select {", ".join(str(column) for column in hc.SQLite_default_columns)} from sync_data WHERE id > {local_index_count}'
        logger.debug(f'SQLite query3 = {query3}')

        # open db connection, send query, store in dataframe
        try:
            with engine.connect() as conn:
                logger.info('getting new data from remote MySQL database')
                update_data = pd.read_sql(query3, conn)
        except Exception as e:
            logger.error(f'append to SQLite database failed: {e}')
        
        # clean update data:
        #   1. add temp_delta column
        #   2. convert timestamp to human-readable
        update_data = hp.clean_data_db(update_data)
        
        ## ======================================
        ## append update datasets to local SQLite
        ## ======================================

        # update SQLite with 2d data - options: append, replace
        try:
            with sql_lite_engine.connect() as conn:
                logger.info('appending new data from remote MySQL database to local SQLite database')
                update_data.to_sql(hc.SQLite_2d_table_name, conn, if_exists='append', index = False)
        except Exception as e:
            logger.error(f'append to SQLite database failed: {e}')
        
        ## =====================================
        ## print status to be shown in Dashboard
        ## =====================================
        logger.info('database update completed.')
        print(f'database has been updated! New rows added: {index_diff}')
