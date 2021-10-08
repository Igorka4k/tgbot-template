def table_create(connection, title):
    """table init"""
    with connection.cursor() as cursor:
        try:
            table_create_query = f"CREATE TABLE `{title}` (" \
                                 "`id` int auto_increment," \
                                 "`full_name` varchar(32) NOT NULL," \
                                 "`tg_account` varchar(32) NOT NULL," \
                                 "`address` varchar(255) NULL," \
                                 "`phone` varchar(32) NULL," \
                                 "PRIMARY KEY  (`id`));"
            cursor.execute(table_create_query)
            connection.commit()
            print("table added...")
        except Exception as ex:
            print(ex)


def get_data(connection):
    with connection.cursor() as cursor:  # Поработать над форматом вывода информации о клиентах, чтобы было красиво.
        check = "SELECT * FROM online_dates"
        cursor.execute(check)
        rows = cursor.fetchall()
        count = len(rows)
        formatting_data = []
        for row in rows:
            formatting_data.append(f"######\n\nИмя: {row['name']}\n\n"
                                   f"Дата: {row['date']}\n\n"
                                   f"Время: {row['time']}\n\n"
                                   f"######")

        return f"Кол-во записей: {count}\n\n" + '\n\n'.join(formatting_data)


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


def delete_appointment(connection, full_name, tg_account):
    with connection.cursor() as cursor:
        try:
            delete_query = f"DELETE FROM `online_dates` WHERE (`name` = '{full_name}' AND `tg_account` = '{tg_account}'" \
                           f" AND`id` = 1);"
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

# connection = db_connect()
