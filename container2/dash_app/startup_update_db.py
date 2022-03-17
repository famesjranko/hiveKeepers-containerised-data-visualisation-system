# HiveKeepers - container2 - dash_app/startup_update_db.py
# written by: Andrew McDonald
# initial: 26/01/22
# current: 17/03/22
# version: 0.9

import pandas as pd
import hivekeepers_helpers as hp

import sqlalchemy as db
from sqlalchemy import func

import hivekeepers_config as hc
import time

import logging

## =================
## Configure Logging 
## =================

# build logger
logger = logging.getLogger()

# set stdout and file log handlers
handler_stdout = logging.StreamHandler()
handler_file = logging.FileHandler('/home/hivekeeper/persistent/logs/container2/app.log')

# set log format
formatter = logging.Formatter('%(asctime)s [PYTHON] [%(levelname)s] %(filename)s: %(message)s')

# add formatters
handler_stdout.setFormatter(formatter)
handler_file.setFormatter(formatter)

# add handlers
logger.addHandler(handler_stdout)
logger.addHandler(handler_file)

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

## =====================
## get remote MySQL data
## =====================

# build database connection url
connect_url = db.engine.url.URL.create(
    drivername='mysql+pymysql',
    username=credentials['username'],
    password=credentials['password'],
    host=credentials['host'],
    database=credentials['database'])

logger.debug(f'remote MySQL url: {connect_url}')

# create MySQL db engine - set pool config
try:
    logger.info('connecting to remote MySQL server...')
    engine = db.create_engine(connect_url, pool_size=10, max_overflow=10, pool_recycle=3600, pool_pre_ping=True, echo=hc.SQL_VERBOSE)
except Exception as e:
    logger.error(f'MySQL database exception: {e}')

# construct SQL query
query = f'select {", ".join(str(column) for column in hc.SQLite_default_columns)} from sync_data'
logger.debug(f'MySQL query1 = {query}')

# open db connection, send query, store in dataframe
try:
    with engine.connect() as conn:
        logger.info('sending query to remote MySQL server')
        hivekeepers_data = pd.read_sql(query, conn)
except Exception as e:
    logger.error(f'MySQL database exception: {e}')

## ================================
## prepare data for local SQLite DB
## ================================

# clean data:
#   1. add temp_delta column
#   2. convert timestamp to human-readable
hivekeepers_data = hp.clean_data_db(hivekeepers_data)

## ==========================================================
## store data in local SQLite DB
## ==========================================================
#
# build SQLite database for local storage
#
#   working dir: /home/hivekeeper/dash_app/
#   database has two tables: hivedata, hivedata_3d
#       hivedata     is the cleaned 2d data schemes
#       hivedata_3d  is the built 3d/4d data scheme (removed)
## ==========================================================

# create SQLite db engine
try:
    logger.info('connecting to local SQLite server...')
    sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=hc.SQL_VERBOSE)
except Exception as e:
    logger.error(f'SQLite database exception: {e}')

# update db with 2d data - options: append, replace
try:
    with sql_lite_engine.connect() as conn:
        logger.info('updating local SQLite server with response data from MySQL server')
        hivekeepers_data.to_sql(hc.SQLite_2d_table_name, conn, if_exists='replace', index = False)
except Exception as e:
    logger.error(f'SQLite database exception: {e}')

# construct SQLite queries 
sql_lite_query = f'SELECT COUNT(id) FROM {hc.SQLite_2d_table_name}'
logger.debug(f'SQLite query1 = {sql_lite_query}')

# open db connection, send query
try:
    with sql_lite_engine.connect() as conn:
        logger.info('sending count(id) query to local SQLite server')
        result = conn.execute(sql_lite_query)
        local_index_count = result.fetchone()[0]
except Exception as e:
    logger.error(f'SQLite database exception: {e}')

logger.debug(f'SQLite local_index_count = {local_index_count}')

# print database size status
print(f'database has been created! Rows added: ', local_index_count)

time.sleep(1)