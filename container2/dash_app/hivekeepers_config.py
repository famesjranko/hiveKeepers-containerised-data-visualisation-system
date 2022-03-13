import os

# App logging level
APP_LOG_LEVEL = os.environ['APP_LOG_LEVEL'].upper()

# MySQL credentials
MYSQL_USER = os.environ['MYSQL_USER']
MYSQL_PASS = os.environ['MYSQL_PASS']
MYSQL_HOST = os.environ['MYSQL_HOST']
MYSQL_DB = os.environ['MYSQL_DB']

# SQLite database name, table names
SQLite_db_name = 'hivekeepers.db'
SQLite_2d_table_name = 'hivedata2d'
SQLite_3d_table_name = 'hivedata3d'

SQLite_default_columns = ['id', 'apiary_id', 'timestamp', 'bme680_internal_temperature',
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
