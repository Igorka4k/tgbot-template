from os import environ, path
from dotenv import load_dotenv
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters, Updater, CallbackQueryHandler
from telegram import *

from functions.payments.example import keyboard_callback_handler, show_carousel
from functions.timetable.db.queries import get_user_last_date, delete_appointment
from functions.timetable.example import get_dates, timetable_script_begin, timetable_admin_menu_choice, \
    month_choosing, day_choosing, time_choosing, timetable_connect
from functions.timetable.tools import db_connect
from functions.timetable.db import queries

from base_template.keyboards import *

if path.exists('../.env'):  # Переменные окружения хранятся в основной директории проекта
    load_dotenv('../.env')
else:
    raise ImportError("Can't import environment variables")

ADMIN_CHAT = list(map(int, environ.get('ADMIN_CHAT').split(',')))


def start(update, ctx):
    ctx.user_data["is_authorized"] = True
    ctx.user_data["tg_account"] = update.message.from_user["username"]
    ctx.user_data["is_admin"] = True if update.effective_chat.id in ADMIN_CHAT else False
    if update.message.from_user["full_name"] is None:
        ctx.user_data["full_name"] = "Аноним"
    else:
        ctx.user_data["full_name"] = update.message.from_user["full_name"]

    connection = db_connect()

    text = ""

    if not queries.is_authorized(connection, update.message.from_user["tg_account"]):
        queries.new_user_adding(connection, ctx.user_data["full_name"], ctx.user_data["tg_account"])
        text += "Добро пожаловать к нам в бота!!!\n"
    else:
        text += "Вы уже авторизованы, я вас запомнил.\n"
    text += "Вы находитесь в главном меню."

    if ctx.user_data["is_admin"]:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(
            MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(
            MAIN_MENU_KEYBOARD__user, resize_keyboard=True))

    return 'menu'


def menu(update, ctx):
    msg = update.message.text

    if msg == "Онлайн-запись":
        if ctx.user_data["is_admin"]:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Открыто меню администратора онлайн-записей.",
                                 reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu,
                                                                  resize_keyboard=True))
        else:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы находитесь в пользовательском меню"
                                                                        " онлайн-записи.",
                                 reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_user_menu, resize_keyboard=True))
        return 'online_appointment'

    if msg == "Сертификаты":
        if ctx.user_data["is_admin"]:
            ctx.bot.send_message(chat_id=update.message.chat_id,
                                 text="Добро пожаловать в редактор витрины Вашего магазина!\n\n"
                                      "Выберите один из вариантов ниже.",
                                 reply_markup=ReplyKeyboardMarkup(INVOICE_EDITOR_KEYBOARD,
                                                                  resize_keyboard=True))
            return 'certificates'
        else:
            ctx.bot.send_message(chat_id=update.message.chat_id,
                                 text="Добро пожаловать в наш магазин сертификатов!\n\nНаши товары:",
                                 reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True))

            show_carousel(update, ctx)
            return 'menu'

    if msg == "Рассылка спец. предложений":
        if ctx.user_data["is_admin"]:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Pass")
            return 'menu'
    return 'menu'


def online_appointment(update, ctx):
    msg = update.message.text
    if msg == "<< Назад в меню":
        if ctx.user_data["is_admin"]:
            keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True)
        else:
            keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True)

        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в главное меню.",
                             reply_markup=keyboard)
        return 'menu'

    elif ctx.user_data["is_admin"]:
        if msg == "Текущие записи":
            get_dates(update, ctx)  # функция из timetable.example

        elif msg == "Настройки":
            keyboard = ReplyKeyboardMarkup(ONLINE_TIMETABLE_SETTINGS, resize_keyboard=True)
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы перешли в раздел редактирования"
                                                                        "режима онлайн-записи",
                                 reply_markup=keyboard)
            return "online_appointment_settings"

    elif not ctx.user_data["is_admin"]:

        if msg == "Записаться":
            last_date = get_user_last_date(db_connect(), ctx.user_data["tg_account"])
            if last_date:
                # пока записаться можно только один раз:
                msg_to_send = f"Невозможно записаться, т.к.\n" \
                              f"Вы уже записаны на {last_date['date']}, {last_date['time']}."
                ctx.bot.send_message(chat_id=update.effective_chat.id,
                                     text=msg_to_send)
            else:
                return timetable_script_begin(update, ctx)  # сценарий записи на приём

        elif msg == "Инфо моей записи":
            last_date = get_user_last_date(db_connect(), ctx.user_data["tg_account"])
            if not last_date:
                msg_to_send = "У вас нет текущей записи на данный момент."
            else:
                msg_to_send = f"Вы записаны на {last_date['date']}, {last_date['time']}."
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=msg_to_send)

        elif msg == "Отменить запись":
            last_date = get_user_last_date(db_connect(), ctx.user_data["tg_account"])
            if not last_date:
                msg_to_send = "Вы и так не записаны."
            else:
                delete_appointment(db_connect(), ctx.user_data["tg_account"])
                msg_to_send = f"Запись от {last_date['date']}, {last_date['time']} отменена."
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=msg_to_send)
    return 'online_appointment'


def online_appointment_settings(update, ctx):
    msg = update.message.text
    if msg == "<< Назад":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в меню онлайн-записей.",
                             reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True))
        return 'online_appointment'
    if msg == "Диапазон":
        keyboard = ReplyKeyboardMarkup(TIMETABLE_DURATION, resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Установите возможный диапазон для записи"
                                                                    "(пока недоступно, вернитесь в меню)",
                             reply_markup=keyboard)
    elif msg == "Часы работы":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Сюда не завезли функциональчик")
    elif msg == "Выходные":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Сюда не завезли функциональчик")
    elif msg == "Отпуск":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Сюда не завезли функциональчик")
    return "online_appointment_settings"


def certificates_admin(update, ctx):
    msg = update.message.text
    if msg == "<< Назад в меню":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в главное меню.",
                             reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
        return 'menu'
    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Сюда функционал ещё не завезли")
    return 'certificates'


def stop(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Stopped", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def unknown(update, ctx):
    """unknown command chat-exception"""
    # ctx.bot.send_message(chat_id=update.effective_chat.id, text="Неизвестная команда, нажмите сюда ==> /help")
    """Ignoring"""
    pass


start_handler = CommandHandler("start", start)
stop_handler = CommandHandler("stop", stop)
unknown_handler = MessageHandler(Filters.command, unknown)

main_menu_conv_handler = ConversationHandler(
    entry_points=[start_handler],
    states={
        "menu": [MessageHandler(
            Filters.regex('^(Онлайн-запись|Сертификаты|Рассылка спец. предложений)$') & (~Filters.command), menu)],
        "online_appointment": [
            MessageHandler(Filters.regex('^(Настройки|Текущие записи|<< Назад в меню)$')
                           & (~Filters.command), online_appointment),
            MessageHandler(Filters.regex('^(Записаться|Инфо моей записи|Отменить запись|<< Назад в меню)$'),
                           online_appointment)],
        "certificates": [

            MessageHandler(Filters.regex(
                '^(Добавление позиции|Изменение позиции|Удаление позиции|Просмотр позиций|<< Назад в меню)$')
                           & (~Filters.command), certificates_admin)],

        # below the handlers, that make an appointment:
        "month_choosing": [MessageHandler(Filters.text & (~Filters.command), month_choosing)],
        "day_choosing": [MessageHandler(Filters.text & (~Filters.command), day_choosing)],
        "time_choosing": [MessageHandler(Filters.text & (~Filters.command), time_choosing)],

        # =============================================

        # below the online_appointment_settings handlers:
        "online_appointment_settings": [MessageHandler(Filters.text & (~Filters.command),
                                                       online_appointment_settings)]

    },
    fallbacks=[stop_handler]
)

updater = Updater(token=environ.get('BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher

timetable_connect(updater)
dispatcher.add_handler(main_menu_conv_handler)

dispatcher.add_handler(CallbackQueryHandler(callback=keyboard_callback_handler, pass_chat_data=True))

dispatcher.add_handler(unknown_handler)

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
