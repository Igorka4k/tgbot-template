import os

from dotenv import load_dotenv
from os import path, environ

from boto.s3.connection import S3Connection
# s3 = S3Connection("AKIAZJNUYZQO2RYWC36S", 'yJNqQQsQHziLlKmvq01gtrHFjycnlPhuuo/0apql')

try:
    if path.exists('.env'):  # Переменные окружения хранятся в основной директории проекта
        load_dotenv('.env')
    else:
        raise ImportError("Can't import environment variables")
except ImportError as ex:
    s3 = S3Connection("AKIAZJNUYZQOVYNTUAN5", 'YhASakeGgVtpYUTFNxn/3Oa+L3fNil7MWH+iMMG/')
if __name__ == "__main__":
    from base_template.bot import *

    from base_template.db.sql_init import initialize
    initialize(db_connect())

    updater.start_polling()
    updater.idle()
    # updater.job_queue.start()


# mysql://b12116c5e68eb3:69ed2230@us-cdbr-east-05.cleardb.net/heroku_3e91460fccadc94?reconnect=true
