from functions.timetable.tools import db_connect
from queries import *

connection = db_connect()

make_an_appointment(connection)
# delete_appointment(connection)
# clear_appointments(connection)
