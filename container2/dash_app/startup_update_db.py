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

# credentials = {
#     'username': 'dev_hkapps_platform',
#     'password': 'R8]NbgN[y-V<L,5X',
#     'host': 'hivekeepers.cvn1llvgfho9.us-east-2.rds.amazonaws.com',
#     'database': 'rawdata',
# }

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

logger.info('')
# create MySQL db engine - set pool config
engine = db.create_engine(connect_url, pool_size=10, max_overflow=10, pool_recycle=3600, pool_pre_ping=True, echo=False)

# construct SQL query
query = f'select {", ".join(str(column) for column in hc.SQLite_default_columns)} from sync_data'

# open db connection, send query, store in dataframe
with engine.connect() as conn:
    logger.info('sending query to remote MySQL server')
    hivekeepers_data = pd.read_sql(query, conn)

## ================================
## prepare data for local SQLite DB
## ================================

# clean data:
#   1. add temp_delta column
#   2. convert timestamp to human-readable
hivekeepers_data = hp.clean_data_db(hivekeepers_data)

# translate data to 3d data scheme 
#hivekeepers_data_3d = hp.build_3d_data(hivekeepers_data)

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
sql_lite_engine = db.create_engine(f'sqlite:///{hc.SQLite_db_name}', echo=False)

# update db with 2d data - options: append, replace
with sql_lite_engine.connect() as conn:
    logger.info('updating local SQLite server with response data from MySQL server')
    hivekeepers_data.to_sql(hc.SQLite_2d_table_name, conn, if_exists='replace', index = False)

# update db with 3d data - options: append, replace
#with sql_lite_engine.connect() as conn:
#    hivekeepers_data_3d.to_sql(hc.SQLite_3d_table_name, conn, if_exists='replace', index = False)

# construct SQLite queries 
sql_lite_query = f'SELECT COUNT(id) FROM {hc.SQLite_2d_table_name}'

# open db connection, send query
with sql_lite_engine.connect() as conn:
    logger.info('sending count(id) query to local SQLite server')
    result = conn.execute(sql_lite_query)
    local_index_count = result.fetchone()[0]

# print database size status
print(f'number of rows in local database: ', local_index_count)

time.sleep(1)