from functions.timetable.new_calendar.constants import weekdays_header_ru


def table_create(connection, title):
    """table init"""
    with connection.cursor() as cursor:
        try:
            table_create_query = f"CREATE TABLE {title} (" \
                                 "id INT AUTO_INCREMENT," \
                                 "between_range INT NOT NULL," \
                                 "PRIMARY KEY (id));"
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


def add_service_to_price(connection, title, price, description=None, img=None):
    # if description is None:
    #     description = "-"
    # if img is None:
    #     img = "-"
    with connection.cursor() as cursor:
        add_query = "INSERT INTO `price` (title,description,img,price)" \
                    f"VALUES('{title}', '{description}', '{img}', '{price}')"
        cursor.execute(add_query)
        connection.commit()
        print("new service has been added.")


def get_service_from_price(connection):
    with connection.cursor() as cursor:
        get_query = "SELECT * FROM `price`"
        cursor.execute(get_query)
        all_the_services = cursor.fetchall()
        return all_the_services


def delete_service_from_price(connection, title):
    with connection.cursor() as cursor:
        del_query = f"DELETE FROM `price` WHERE `title` = '{title}'"
        cursor.execute(del_query)
        connection.commit()
        print(f"{title} has been delete from the check_list.")


def get_working_hours(connection):
    with connection.cursor() as cursor:
        get_working_hours_query = f"SELECT * FROM working_hours"
        cursor.execute(get_working_hours_query)
        working_hours = cursor.fetchone()
        if working_hours is None:
            working_time_adding(connection, begin_time="08:00", end_time='21:00')
            return get_working_hours(connection)
        return working_hours


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
        print("new working time has been set...")


def set_timetable_range(connection, mode):
    with connection.cursor() as cursor:
        clear_query = "DELETE FROM `timetable_range` WHERE id"
        cursor.execute(clear_query)
        set_query = f"INSERT INTO `timetable_range` (mode)" \
                    f" VALUES('{mode}');"
        cursor.execute(set_query)
        connection.commit()
        print("new timetable_range has been set...")


def get_timetable_range(connection):
    with connection.cursor() as cursor:
        query = "SELECT * FROM `timetable_range`"
        cursor.execute(query)
        timetable_range = cursor.fetchone()
        if timetable_range is None:
            set_timetable_range(connection, mode=90)
            return get_timetable_range(connection)
        return int(timetable_range["mode"])


def get_notifies(connection):
    with connection.cursor() as cursor:
        query = "SELECT * FROM `notifies`"
        cursor.execute(query)
        notifies_data = cursor.fetchone()
        return notifies_data


def set_notifies(connection, mode_id, appointment_id):
    with connection.cursor() as cursor:
        query = "INSERT INTO `notifies` (mode_id, appointment_id)" \
                f"VALUES('{mode_id}', '{appointment_id}');"
        cursor.execute(query)
        connection.commit()


def set_days_off(connection, day):
    with connection.cursor() as cursor:
        choose_all_query = "SELECT * FROM `days_off`"
        cursor.execute(choose_all_query)
        all_the_weekdays = cursor.fetchall()
        if not all_the_weekdays:
            all_the_weekdays = {
                "ПН": False,
                "ВТ": False,
                "СР": False,
                "ЧТ": False,
                "ПТ": False,
                "СБ": False,
                "ВС": False
            }
            all_the_weekdays[day] = not all_the_weekdays[day]
            values = list()
            for i in all_the_weekdays.values():
                values.append(1) if i else values.append(0)
        else:
            abbr_to_month = {
                "ПН": "monday",
                "ВТ": "tuesday",
                "СР": "wednesday",
                "ЧТ": "thursday",
                "ПТ": "friday",
                "СБ": "saturday",
                "ВС": "sunday"
            }
            all_the_weekdays[0][abbr_to_month[day]] = 1 if int(all_the_weekdays[0][abbr_to_month[day]]) == 0 else 0
            values = []
            for i in list(all_the_weekdays[0].values())[1:]:
                values.append(1) if i else values.append(0)
            clear_query = "DELETE FROM `days_off` WHERE id"
            cursor.execute(clear_query)

        adding_query = "INSERT INTO `days_off` (monday, tuesday, wednesday, thursday, friday, saturday, sunday) " \
                       f"VALUES ('{values[0]}', '{values[1]}', '{values[2]}', '{values[3]}', '{values[4]}', " \
                       f"'{values[5]}', '{values[6]}');"
        cursor.execute(adding_query)
        connection.commit()
        return values


def get_days_off(connection):
    with connection.cursor() as cursor:
        query = "SELECT * FROM `days_off`"
        cursor.execute(query)
        values = cursor.fetchall()
        if not len(values):
            set_days_off(connection, day='ПН')
            return get_days_off(connection)
        values = list(values[0].values())[1:]
        days_off = [weekdays_header_ru[i] for i in range(len(weekdays_header_ru)) if values[i] == 1]
        return days_off


def set_holidays(connection, first_date, second_date):
    with connection.cursor() as cursor:
        clear_query = "DELETE FROM `holidays` WHERE id"
        cursor.execute(clear_query)
        query = "INSERT INTO `holidays` (begin_date, end_date) VALUES " \
                f"('{first_date}', '{second_date}');"
        cursor.execute(query)
        connection.commit()
        print("new holidays have been set..")


def get_holidays(connection):
    with connection.cursor() as cursor:
        query = "SELECT * FROM `holidays`"
        cursor.execute(query)
        current_holidays = cursor.fetchone()
        return current_holidays


def get_dates_between_range(connection):
    with connection.cursor() as cursor:
        query = "SELECT * FROM `between_range`"
        cursor.execute(query)
        current_range = cursor.fetchone()
        if current_range is None:
            return None
        return int(current_range["between_range"])


def set_dates_between_range(connection, data):
    with connection.cursor() as cursor:
        clear_query = "DELETE FROM `between_range` WHERE id"
        cursor.execute(clear_query)
        query = "INSERT INTO `between_range` (between_range) VALUES " \
                f"('{data}');"
        cursor.execute(query)
        connection.commit()
        print("new between_range have been set..")


def cancel_holidays(connection):
    with connection.cursor() as cursor:
        check_query = "SELECT * FROM `holidays`"
        cursor.execute(check_query)
        check = cursor.fetchone()
        if check is None:
            return None
        clear_query = "DELETE FROM `holidays` WHERE id"
        cursor.execute(clear_query)
        connection.commit()
        print("holidays have been canceled.")
        return check


def is_authorized(connection, tg_account):
    """ does the user exist in db? """
    with connection.cursor() as cursor:
        check_query = f"SELECT * FROM `bot_subscribers` WHERE `tg_account` = '{tg_account}'"
        cursor.execute(check_query)
        result = cursor.fetchone()
        if result is None:
            return False
        return True


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


def clear_subscribers(connection):  # USE WITH ATTENTION!
    """ clear all the bot_subscribers """
    with connection.cursor() as cursor:
        clear_query = "DELETE FROM `bot_subscribers` WHERE (id)"
        cursor.execute(clear_query)
        connection.commit()
        print("bot_subscribers cleared")


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


def clear_appointment(connection, info):
    time, date = [i for i in info]
    with connection.cursor() as cursor:
        clear_query = f"DELETE FROM `online_dates` WHERE time = '{time}' AND date = '{date}'"
        cursor.execute(clear_query)
        connection.commit()
        print(f"The appointment from {date}, {time} was cleared from database.")


# # place for query tests: (не удалять)
#
#
# from functions.timetable.tools import db_connect
#
# from os import environ, path
# from dotenv import load_dotenv
#
# if path.exists('../../.env'):  # Переменные окружения хранятся в основной директории проекта
#     load_dotenv('../../.env')
# else:
#     raise ImportError("Can't import environment variables")
# connection = db_connect()
#
#
