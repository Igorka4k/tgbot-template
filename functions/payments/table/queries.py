import pymysql
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


def payment_table_create(connection):
    with connection.cursor() as cursor:
        try:
            table_create_query = f"CREATE TABLE `invoice_table` (" \
                                 "`id` int auto_increment," \
                                 "`title` varchar(32) NOT NULL," \
                                 "`description` varchar(255) NOT NULL," \
                                 "`payload` varchar(32) NOT NULL," \
                                 "`price` int NOT NULL," \
                                 "PRIMARY KEY  (`id`));"
            cursor.execute(table_create_query)
            connection.commit()
            print(f"invoice_table table added...")
        except Exception as ex:
            print(ex)


def add_invoice(connection, title: str, description: str, payload: str, price: int):
    with connection.cursor() as cursor:
        add_query = "INSERT INTO invoice_table (title, description, payload, price)" \
                    f" VALUES ('{title}', '{description}'," \
                    f" '{payload}', {price});"
        cursor.execute(add_query)
        connection.commit()
        print("invoice added...")


def remove_invoice(connection, title: str):
    with connection.cursor() as cursor:
        add_query = f"DELETE FROM invoice_table WHERE title='{title}';"
        cursor.execute(add_query)
        connection.commit()
        print("invoice removed...")


def get_invoice(connection, id_: int):
    with connection.cursor() as cursor:
        add_query = f"SELECT * FROM invoice_table WHERE id={id_};"
        cursor.execute(add_query)
        connection.commit()
        print("invoice got...")
        result = cursor.fetchone()
        return result

