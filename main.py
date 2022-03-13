from dotenv import load_dotenv
from os import path, environ

try:
    # Убрать условие снизу, если переменные окружения находятся в config vars.
    if path.exists('.env'):  # Переменные окружения хранятся в основной директории проекта
        load_dotenv('.env')
    else:
        raise ImportError("Can't import environment variables")
except ImportError as ex:
    print(ex)

if __name__ == "__main__":
    from base_template.bot import *
    from base_template.db.sql_init import initialize

    # initialize(db_connect())  # инициализация таблиц базы данных.
    updater.start_polling()
    updater.idle()
    # updater.job_queue.start()  # для теста уведомлений
