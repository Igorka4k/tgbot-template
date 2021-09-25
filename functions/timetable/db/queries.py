def table_create(connection):
    """table init"""
    with connection.cursor() as cursor:
        try:
            table_create_query = "CREATE TABLE `online_dates` (" \
                                 "`id` int auto_increment," \
                                 "`name` varchar(32) NOT NULL," \
                                 "`date` varchar(32) NOT NULL," \
                                 "`time` varchar(32) NOT NULL," \
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
    with connection.cursor() as cursor:
        check = "SELECT * FROM online_dates"
        cursor.execute(check)
        count = len(cursor.fetchall())
        return count


def make_an_appointment(connection):
    """appointment making"""
    with connection.cursor() as cursor:
        name = "smth"
        date = "01.09.2021"
        time = "12:30"
        tg_account = "@ak_47_com"
        appointment_add_query = "INSERT INTO online_dates (name, date, time, tg_account)" \
                                f" VALUES ('{name}', '{date}'," \
                                f" '{time}', '{tg_account}');"
        cursor.execute(appointment_add_query)
        connection.commit()
        print("appointment added...")


def delete_appointment(connection):
    with connection.cursor() as cursor:
        tg_account = "@ak_47_com"
        name = "smth"
        try:
            delete_query = f"DELETE FROM `online_dates` WHERE (`name` = '{name}' AND `tg_account` = '{tg_account}'" \
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
