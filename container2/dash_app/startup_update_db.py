import pandas as pd
import hivekeepers_helpers as hp

import sqlalchemy as db
from sqlalchemy import func

import config
import time

# MYSQL REMOTE SERVER CREDENTIALS
credentials = {
    'username': config.MYSQL_USER,
    'password': config.MYSQL_PASS ,
    'host': config.MYSQL_HOST,
    'database': config.MYSQL_DB,
}

# build database connection url
connect_url = db.engine.url.URL.create(
    drivername='mysql+pymysql',
    username=credentials['username'],
    password=credentials['password'],
    host=credentials['host'],
    database=credentials['database'])

# create MySQL db engine - set pool config
engine = db.create_engine(connect_url, pool_size=10, max_overflow=10, pool_recycle=3600, pool_pre_ping=True, echo=True)

# construct SQL query
query = f'select {", ".join(str(column) for column in config.SQLite_default_columns)} from sync_data'

# open db connection, send query, store in dataframe
with engine.connect() as conn:
    hivekeepers_data = pd.read_sql(query, conn)

# clean data:
# add temp_delta column
# convert timestamp to human-readable
hivekeepers_data = hp.clean_data_db(hivekeepers_data)

# build 3d dataset
hivekeepers_data_3d = hp.build_3d_data(hivekeepers_data)

## build SQLite database for local storage
#   working dir: /home/hivekeeper/dash_app/
#   database has two tables: hivedata, hivedata_3d
#       hivedata     is the cleaned 2d data schemes
#       hivedata_3d  is the built 3d/4d data scheme

# create SQLite db engine
sql_lite_engine = db.create_engine(f'sqlite:///{config.SQLite_db_name}', echo=True)

# update db with 2d data - options: append, replace
with sql_lite_engine.connect() as conn:
    hivekeepers_data.to_sql(config.SQLite_2d_table_name, conn, if_exists='replace', index = False)

# update db with 3d data - options: append, replace
with sql_lite_engine.connect() as conn:
    hivekeepers_data_3d.to_sql(config.SQLite_3d_table_name, conn, if_exists='replace', index = False)

# construct SQLite queries
sql_lite_queries = [['2D', f'SELECT COUNT(id) FROM {config.SQLite_2d_table_name}'],
                    ['3D', f'SELECT COUNT(timestamp) FROM {config.SQLite_3d_table_name}']]

for label,query in sql_lite_queries:
    with sql_lite_engine.connect() as conn:
        result = conn.execute(query)
        #for row in result:
        #    print(row)
        print(f'number of rows in {label} table: ', result.fetchone()[0])

time.sleep(1)