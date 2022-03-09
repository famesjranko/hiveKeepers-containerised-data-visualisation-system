import pandas as pd
import hivekeepers_helpers as hp
import sqlite3

## this section needs to be converted to connecting to remote MySQL server
## note: use connection pooling
## =======================================================================

data_file = 'data.csv'
hivekeepers_data = pd.read_csv(data_file)

## =======================================================================

# remove unneeded columns, 
# convert timestamp to human-readable,
# and add temp_delta column
hivekeepers_data = hp.clean_data(hivekeepers_data)

# working dir: /home/hivekeeper/dash_app/
# database has two tables: hivedata, hivedata_3d
#       hivedata     is the cleaned 2d data schemes
#       hivedata_3d  is the built 3d/4d data scheme

# open connection to db - experienced permission issues in container!!!
connection = sqlite3.connect('hivekeepers.db')

# update db with 2d data - options: append, replace
hivekeepers_data.to_sql('hivedata', connection, if_exists='replace', index = False)

# build 3d dataset
#================= start

# get fft bin names and amplitude values
fft_bins = hp.get_fft_bins(hivekeepers_data)

# get fft bin names and amplitude values
fft_amplitudes = hivekeepers_data[fft_bins].values

hivekeepers_data_3d = hp.build_3d_data(hivekeepers_data, fft_bins, fft_amplitudes)

#================= end

# update db with 3d data - options: append, replace
hivekeepers_data_3d.to_sql('hivedata_3d', connection, if_exists='replace', index = False)

# open db cursor to make queries
cursor = connection.cursor()

# get current highest index value for comparing with off-site db for updates
cursor.execute('''SELECT MAX(id) FROM hivedata''')
sql_last_index = cursor.fetchall()[0][0]

cursor.execute('''SELECT COUNT(id) FROM hivedata''')
sql_total_index = cursor.fetchall()[0][0]

cursor.execute('''SELECT * FROM hivedata_3d''')
sql_total_index_3d = len(cursor.fetchall())

# close db cursor and connection
cursor.close()
connection.close()

print('last index: ', sql_last_index)
print('total index: ', sql_total_index)
print('total index 3d: ', sql_total_index_3d)
