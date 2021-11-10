def table_create(connection, title):
    """table init"""
    with connection.cursor() as cursor:
        try:
            table_create_query = f"CREATE TABLE `{title}` (" \
                                 "`id` int auto_increment," \
                                 "`begin` varchar(32) NOT NULL," \
                                 "`end` varchar(32) NOT NULL," \
                                 "PRIMARY KEY  (`id`));"
            cursor.execute(table_create_query)
            connection.commit()
            print("table added...")
        except Exception as ex:
            print(ex)


def get_data(connection):
    with connection.cursor() as cursor:  # Поработать над форматом вывода информации о клиентах, чтобы было красиво.
        get_data_query = "SELECT * FROM online_dates"
        cursor.execute(get_data_query)
        rows = cursor.fetchall()
        count = len(rows)
        formatting_data = []
        for row in rows:
            formatting_data.append(f"######\n\nИмя: {row['name']}\n\n"
                                   f"Дата: {row['date']}\n\n"
                                   f"Время: {row['time']}\n\n"
                                   f"######")

        return f"Кол-во записей: {count}\n\n" + '\n\n'.join(formatting_data)


def get_user_last_date(connection, tg_account):
    with connection.cursor() as cursor:
        get_users_query = f"SELECT * FROM online_dates WHERE `tg_account` = '{tg_account}'"
        cursor.execute(get_users_query)
        last_date = cursor.fetchone()
        return last_date


def working_time_adding(connection, begin_time, end_time):
    with connection.cursor() as cursor:
        clear_query = "DELETE FROM `working_hours` WHERE id"
        cursor.execute(clear_query)
        adding_query = f"INSERT INTO `working_hours` (begin, end)" \
                       f" VALUES ('{begin_time}', '{end_time}');"
        cursor.execute(adding_query)
        connection.commit()
        print("new working time set...")


def is_authorized(connection, tg_account):
    """ does the user exist in db? """
    with connection.cursor() as cursor:
        check_query = f"SELECT * FROM `bot_subscribers` WHERE `tg_account` = '{tg_account}'"
        cursor.execute(check_query)
        result = cursor.fetchone()
        if result is not None:
            return True
        return False


def make_an_appointment(connection, full_name, date, time, tg_account):
    """appointment making"""
    with connection.cursor() as cursor:
        appointment_add_query = "INSERT INTO online_dates (name, date, time, tg_account)" \
                                f" VALUES ('{full_name}', '{date}'," \
                                f" '{time}', '{tg_account}');"
        cursor.execute(appointment_add_query)
        connection.commit()
        print("appointment added...")


def new_user_adding(connection, full_name, tg_account):
    """ user registration into db"""
    with connection.cursor() as cursor:
        user_add_query = f"INSERT INTO bot_subscribers (full_name, tg_account) VALUES ('{full_name}', '{tg_account}');"
        cursor.execute(user_add_query)
        connection.commit()
        print("new user added...")


def delete_appointment(connection, tg_account):
    with connection.cursor() as cursor:
        try:
            delete_query = f"DELETE FROM `online_dates` " \
                           f"WHERE (`tg_account` = '{tg_account}');"
            cursor.execute(delete_query)
            connection.commit()
        except Exception as ex:
            print(ex)


def clear_appointments(connection):
    with connection.cursor() as cursor:
        clear_query = "DELETE FROM `online_dates` WHERE id"
        cursor.execute(clear_query)
        connection.commit()


# place for query tests:
# from functions.timetable.tools import db_connect
#
# from os import environ, path
# from dotenv import load_dotenv
#
# if path.exists('../../../.env'):  # Переменные окружения хранятся в основной директории проекта
#     load_dotenv('../../../.env')
# else:
#     raise ImportError("Can't import environment variables")
#
# connection = db_connect()
