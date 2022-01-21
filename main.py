from dotenv import load_dotenv
from os import path, environ

from boto.s3.connection import S3Connection

try:
    if path.exists('.env'):  # Переменные окружения хранятся в основной директории проекта
        load_dotenv('.env')
    else:
        raise ImportError("Can't import environment variables")
except ImportError:
    s3 = S3Connection()

if __name__ == "__main__":
    from base_template.bot import *

    updater.start_polling()
    updater.idle()
    # updater.job_queue.start()
