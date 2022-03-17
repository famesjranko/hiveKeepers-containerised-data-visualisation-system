# HiveKeepers - container2 - dash_app/hivekeepers_config.py
# written by: Andrew McDonald
# initial: 26/01/22
# current: 15/03/22
# version: 0.9

## ====================================================
## Hivekeepers app system environment variables storage
## ====================================================

import os
import logging

# set log level from user input - default INFO if non given
app_log_level = os.environ.get('APP_LOG_LEVEL', 'INFO').upper()

if app_log_level == 'DEBUG':
    APP_LOG_LEVEL = 'DEBUG'
elif app_log_level == 'INFO':
    APP_LOG_LEVEL = 'INFO'
elif app_log_level == 'WARNING':
    APP_LOG_LEVEL = 'WARNING'
elif app_log_level == 'ERROR':
    APP_LOG_LEVEL = 'ERROR'
elif app_log_level == 'CRITICAL':
    APP_LOG_LEVEL = 'CRITICAL'
else:
    APP_LOG_LEVEL = 'INFO'

## =================
## Configure Logging 
## =================

logger = logging.getLogger()

# get/set Dash app port from user input - default 8050 if none given
APP_PORT = os.environ.get('APP_PORT', 8050)

# get sql verbosity from user input
sql_logging = os.environ.get('SQL_VERBOSE', 'NO').upper()

if sql_logging == 'YES':
    SQL_VERBOSE = True
else:
    SQL_VERBOSE = False

logger.debug(f'SQL_LOGGING: {SQL_VERBOSE}')

# get/set MySQL credentials from user - default 'missing' if none given
MYSQL_USER = os.environ.get('MYSQL_USER', 'missing')
MYSQL_PASS = os.environ.get('MYSQL_PASS', 'missing')
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'missing')
MYSQL_DB = os.environ.get('MYSQL_DB', 'missing')

logger.debug(f'MYSQL_USER: {MYSQL_USER}')
logger.debug(f'MYSQL_USER: {MYSQL_PASS}')
logger.debug(f'MYSQL_USER: {MYSQL_HOST}')
logger.debug(f'MYSQL_USER: {MYSQL_DB}')

# set SQLite database name, table names
SQLite_db_name = '/home/hivekeeper/persistent/db/hivekeepers.db'  ## << ----- testing!
SQLite_2d_table_name = 'hivedata2d'

logger.debug(f'SQLite_db_name: {SQLite_db_name}')
logger.debug(f'SQLite_2d_table_name: {SQLite_2d_table_name}')

# set local SQLite database headers
SQLite_default_columns = ['id', 'apiary_id', 'apiary_name', 'timestamp', 'bme680_internal_temperature',
                        'bme680_external_temperature', 'fft_bin1', 'fft_bin2', 'fft_bin3',
                        'fft_bin4', 'fft_bin5', 'fft_bin6', 'fft_bin7', 'fft_bin8', 'fft_bin9',
                        'fft_bin10', 'fft_bin11', 'fft_bin12', 'fft_bin13', 'fft_bin14',
                        'fft_bin15', 'fft_bin16', 'fft_bin17', 'fft_bin18', 'fft_bin19',
                        'fft_bin20', 'fft_bin21', 'fft_bin22', 'fft_bin23', 'fft_bin24',
                        'fft_bin25', 'fft_bin26', 'fft_bin27', 'fft_bin28', 'fft_bin29',
                        'fft_bin30', 'fft_bin31', 'fft_bin32', 'fft_bin33', 'fft_bin34',
                        'fft_bin35', 'fft_bin36', 'fft_bin37', 'fft_bin38', 'fft_bin39',
                        'fft_bin40', 'fft_bin41', 'fft_bin42', 'fft_bin43', 'fft_bin44',
                        'fft_bin45', 'fft_bin46', 'fft_bin47', 'fft_bin48', 'fft_bin49',
                        'fft_bin50', 'fft_bin51', 'fft_bin52', 'fft_bin53', 'fft_bin54',
                        'fft_bin55', 'fft_bin56', 'fft_bin57', 'fft_bin58', 'fft_bin59',
                        'fft_bin60', 'fft_bin61', 'fft_bin62', 'fft_bin63', 'fft_bin64']

logger.debug(f'SQLite_default_columns: {SQLite_default_columns}')
