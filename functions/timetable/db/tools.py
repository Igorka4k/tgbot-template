import pymysql
from config import *


def db_connect():
    try:
        connection = pymysql.connect(
            host=host,
            port=3306,
            password=password,
            database=db_name,
            user=user,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("successfully connected...")
        return connection
    except Exception as ex:
        print("connection refused.")
        print(ex)
        return False
