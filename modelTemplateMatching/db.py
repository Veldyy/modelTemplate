# db.py
import pymysql

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'ktp',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_connection():
    return pymysql.connect(**db_config)
