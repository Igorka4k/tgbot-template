import pymysql

from tools import db_connect
from config import *
from queries import *

connection = db_connect()

make_an_appointment(connection)
data_print(connection)
# delete_appointment(connection)
clear_appointments(connection)
