# pandas vers==1.4.0
import pandas as pd
import sqlite3

data_file = "../dash_app/data.csv"

# read file into dataframe
try :
    hivekkeepers_data = pd.read_csv(data_file)
except FileNotFoundError as error_msg:
    print(f'{data_file} File not found!{error_msg=}, {type(error_msg)=}')
except Exception as error_msg:
    print(f"Unexpected {error_msg=}, {type(error_msg)=}")

## ========================
## Wrangle Hivekeepers Data
## ========================

# drop unnecessary columns
hivekkeepers_data.drop(hivekkeepers_data.columns[[1,3,4,5,6,7,9,10,11,12,13,14,15,16,18,19,20,22,23,24,25,90,91]], axis=1, inplace=True)

# add internal/external temperature delta column - confirm which they want? 
# option1: int - ext                <- non-absolute delta of int and delta
# option2: abs(int - ext)           <- the absolute delta of and ext
# option3: int - abs(int - ext)     <- int - (the absolute difference of int and ext)

#hivekkeepers_data['temp_delta'] = hivekkeepers_data['bme680_internal_temperature'] - hivekkeepers_data['bme680_external_temperature']
hivekkeepers_data['temp_delta'] = abs(hivekkeepers_data['bme680_internal_temperature'] - hivekkeepers_data['bme680_external_temperature'])
#hivekkeepers_data['temp_delta'] = hivekkeepers_data['bme680_internal_temperature'] - abs(hivekkeepers_data['bme680_internal_temperature'] - hivekkeepers_data['bme680_external_temperature'])

# open connection to db - experienced permission issues in container!!!
connection = sqlite3.connect('hivekeeper.db')

# update db with hive data
hivekkeepers_data.to_sql('hivedata', connection, if_exists='replace', index = False)

# get current highest index value for comparing with off-site db for updates
cursor = connection.cursor()
cursor.execute('''SELECT MAX(id) FROM hivedata''')
sql_last_index = cursor.fetchall()[0][0]
print('the database latest index value is: ', sql_last_index)

# close db cursor and connection
cursor.close()
connection.close()