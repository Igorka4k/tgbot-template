import pymysql
import datetime
from os import environ


def db_connect():
    try:
        connection = pymysql.connect(
            host=environ.get('MYSQL_URL'),
            port=int(environ.get('MYSQL_PORT')),
            password=environ.get('MYSQL_PASS'),
            database=environ.get('MYSQL_BASE_NAME'),
            user=environ.get('MYSQL_USER'),
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
        days_keyboard = [[str((d1 + datetime.timedelta(days=x)).day)] for x in range((d2 - d1).days)]
        return days_keyboard

    def get_hours_keyboard(self):
        # Бизнесу надо будет добавить возможность устанавливать нерабочие часы, например 20:00-10:00 + обед 13:30-14:00
        hours_keyboard = []
        one_hour = datetime.timedelta(minutes=0)

        for i in range(0, 24 * 2):
            total_seconds = int(one_hour.total_seconds())
            hours, remainder = divmod(total_seconds, 60 * 60)
            minutes, seconds = divmod(remainder, 60)

            hours_keyboard.append([datetime.time(hours, minutes, 0).strftime("%H:%M")])
            one_hour = one_hour + datetime.timedelta(minutes=30)
        return hours_keyboard


# cog = CalendarCog()
# result = cog.get_hours_keyboard()
# print(result)
