import pymysql
from config import *


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

except Exception as ex:
    print("connection refused.")
    print(ex)
