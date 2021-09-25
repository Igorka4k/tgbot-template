import pymysql

from tools import db_connect
from functions.timetable.db.config import *
from queries import *

connection = db_connect()

make_an_appointment(connection)
get_data(connection)
# delete_appointment(connection)
# clear_appointments(connection)
