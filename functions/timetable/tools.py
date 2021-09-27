import pymysql
from functions.timetable.db.config import *
import datetime


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


class CalendarCog:
    def __init__(self):
        pass

    def get_year(self, choice: int):
        if datetime.datetime.now().month > choice:
            return datetime.datetime.now().year + 1
        return datetime.datetime.now().year

    def get_days_keyboard(self, year, month):
        d1 = datetime.date(year, month, 1)
        d2 = datetime.date(year, month + 1, 1)
        days_keyboard = [str((d1 + datetime.timedelta(days=x)).day) for x in range((d2 - d1).days)]
        return days_keyboard

    def get_hours(self):
        """сущик потом поменяет это на нормальный алгоритм с использованием datetime"""
        hours_keyboard = []
        for i in range(2):
            for hour in range(0, 24):
                if i == 0:
                    hours_keyboard.append([f"{str(hour)}:00"])
                else:
                    hours_keyboard.append([f"{str(hour)}:30"])
        return sorted(hours_keyboard, key=lambda x: x[0])
