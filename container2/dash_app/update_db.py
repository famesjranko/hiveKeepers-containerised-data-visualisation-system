import pandas as pd
import hivekeepers_helpers as hp

import sqlalchemy as db
from sqlalchemy import func

import config

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
    database=credentials['database']
)

# create MySQL db engine - set pool config
engine = db.create_engine(connect_url, pool_size=10, max_overflow=10, pool_recycle=3600, pool_pre_ping=True, echo=False)

# construct SQL query
query1 = 'SELECT COUNT(id) FROM sync_data'

# open db connection, send query, store in dataframe
with engine.connect() as conn:
        result = conn.execute(query1)
        remote_index_count = result.fetchone()[0]

# create SQLite db engine
sql_lite_engine = db.create_engine(f'sqlite:///{config.SQLite_db_name}', echo=False)

query3 =  f'SELECT COUNT(id) FROM {config.SQLite_2d_table_name}'

with sql_lite_engine.connect() as conn:
    result = conn.execute(query3)
    local_index_count = result.fetchone()[0]


if not (remote_index_count > local_index_count):
    print(f'database is already up to date...')
else:
    index_diff = remote_index_count - local_index_count
    #print('TRUE')
    #print('number of rows remote has more than local is: ', index_diff)
    
    update_count = local_index_count + index_diff

    if update_count == remote_index_count:

        # construct SQL query for database updates
        query4 = f'select {", ".join(str(column) for column in config.SQLite_default_columns)} from sync_data WHERE id > {local_index_count}'

        # open db connection, send query, store in dataframe
        with engine.connect() as conn:
            update_data = pd.read_sql(query4, conn)
        
        # add temp_delta column
        # convert timestamp to human-readable
        update_data = hp.clean_data_db(update_data)

        # build 3d dataset
        update_data_3d = hp.build_3d_data(update_data)
        
        # create SQLite db engine
        sql_lite_engine = db.create_engine(f'sqlite:///{config.SQLite_db_name}', echo=False)

        # update db with 2d data - options: append, replace
        with sql_lite_engine.connect() as conn:
            update_data.to_sql(config.SQLite_2d_table_name, conn, if_exists='append', index = False)

        # update db with 3d data - options: append, replace
        with sql_lite_engine.connect() as conn:
            update_data_3d.to_sql(config.SQLite_3d_table_name, conn, if_exists='append', index = False)
        
        print(f'database has been updated with {index_diff} new rows!')
        
        # construct SQLite queries
        #sql_lite_queries = [['2D', f'SELECT COUNT(id) FROM {config.SQLite_2d_table_name}'],
        #                    ['3D', f'SELECT COUNT(timestamp) FROM {config.SQLite_3d_table_name}']]

        #print('update_count: ', update_count)
        #print('remote_index_count: ', remote_index_count)
        #print('remote_index_max: ', remote_index_max)
        # for label,query in sql_lite_queries:
        #     with sql_lite_engine.connect() as conn:
        #         result = conn.execute(query)
                #for row in result:
                #    print(row)
                #print(f'number of rows in {label} table: ', result.fetchone()[0])
