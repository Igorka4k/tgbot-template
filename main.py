from dotenv import load_dotenv
from os import path

if path.exists('.env'):  # Переменные окружения хранятся в основной директории проекта
    load_dotenv('.env')
else:
    raise ImportError("Can't import environment variables")

from base_template.bot import *

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
    # updater.job_queue.start()
