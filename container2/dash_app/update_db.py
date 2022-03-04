import pandas as pd
import hivekeepers_helpers as hp
import sqlite3

data_file = 'data.csv'
hivekeepers_data = pd.read_csv(data_file)

hivekeepers_data = hp.clean_data(hivekeepers_data)

# open connection to db - experienced permission issues in container!!!
connection = sqlite3.connect('hivekeepers.db')

# update db with dataframe data - options: append, replace
hivekeepers_data.to_sql('hivedata', connection, if_exists='replace', index = False)

# get current highest index value for comparing with off-site db for updates
cursor = connection.cursor()

cursor.execute('''SELECT MAX(id) FROM hivedata''')
sql_last_index = cursor.fetchall()[0][0]

cursor.execute('''SELECT COUNT(id) FROM hivedata''')
sql_total_index = cursor.fetchall()[0][0]

# close db cursor and connection
cursor.close()
connection.close()

print('last index: ', sql_last_index)
print('total index: ', sql_total_index)
