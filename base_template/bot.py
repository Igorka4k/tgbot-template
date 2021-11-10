from os import environ, path
from dotenv import load_dotenv
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters, Updater, CallbackQueryHandler
from telegram import *

from functions.payments.example import keyboard_callback_handler, show_carousel
from functions.timetable.db.queries import get_user_last_date, delete_appointment
from functions.timetable.example import *
from functions.timetable.admin_example import *
from functions.timetable.tools import db_connect, CalendarCog
from functions.timetable.db import queries
from constants import *

from base_template.keyboards import *

if path.exists('../.env'):  # Переменные окружения хранятся в основной директории проекта
    load_dotenv('../.env')
else:
    raise ImportError("Can't import environment variables")

ADMIN_CHAT = list(map(int, environ.get('ADMIN_CHAT').split(',')))


def start(update, ctx):
    ctx.user_data["is_authorized"] = True
    ctx.user_data["state"] = 'main_menu'
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

    if msg == online_timetable_btn:
        ctx.user_data["state"] = "online_appointment"
        if ctx.user_data["is_admin"]:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Открыто меню администратора онлайн-записей.",
                                 reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu,
                                                                  resize_keyboard=True))
        else:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы находитесь в пользовательском меню"
                                                                        " онлайн-записи.",
                                 reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_user_menu, resize_keyboard=True))
        return 'online_appointment'

    if msg == certificates_btn:
        ctx.user_data["state"] = "certificates"
        if ctx.user_data["is_admin"]:
            ctx.bot.send_message(chat_id=update.message.chat_id,
                                 text="Добро пожаловать в редактор витрины Вашего магазина!\n\n"
                                      "Выберите один из вариантов ниже.",
                                 reply_markup=ReplyKeyboardMarkup(INVOICE_EDITOR_KEYBOARD,
                                                                  resize_keyboard=True))
            return 'certificates'
        else:
            ctx.user_data["state"] = "menu"
            ctx.bot.send_message(chat_id=update.message.chat_id,
                                 text="Добро пожаловать в наш магазин сертификатов!\n\nНаши товары:",
                                 reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True))

            show_carousel(update, ctx)
            return 'menu'

    if msg == "Рассылка спец. предложений":
        ctx.user_data["state"] = "menu"
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=pass_message)
    return 'menu'


def online_appointment(update, ctx):
    msg = update.message.text
    if msg == back_to_menu_btn:
        ctx.user_data['state'] = "menu"
        if ctx.user_data["is_admin"]:
            keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True)
        else:
            keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True)

        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в главное меню.",
                             reply_markup=keyboard)
        return 'menu'

    elif ctx.user_data["is_admin"]:
        if msg == check_appointments_btn:
            get_dates(update, ctx)  # функция из timetable.example

        elif msg == settings_btn:
            ctx.user_data["states"] = 'online_appointment_settings'
            keyboard = ReplyKeyboardMarkup(ONLINE_TIMETABLE_SETTINGS, resize_keyboard=True)
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы перешли в раздел редактирования"
                                                                        "режима онлайн-записи",
                                 reply_markup=keyboard)
            return "online_appointment_settings"

    elif not ctx.user_data["is_admin"]:

        if msg == make_appointment_btn:
            ctx.user_data["state"] = "time_choosing"
            last_date = get_user_last_date(db_connect(), ctx.user_data["tg_account"])
            if last_date:
                # пока записаться можно только один раз:
                msg_to_send = f"Невозможно записаться, т.к.\n" \
                              f"Вы уже записаны на {last_date['date']}, {last_date['time']}."
                ctx.bot.send_message(chat_id=update.effective_chat.id,
                                     text=msg_to_send)
            else:
                return timetable_script_begin(update, ctx)  # сценарий записи на приём

        elif msg == appointment_info_btn:
            last_date = get_user_last_date(db_connect(), ctx.user_data["tg_account"])
            if not last_date:
                msg_to_send = "У вас нет текущей записи на данный момент."
            else:
                msg_to_send = f"Вы записаны на {last_date['date']}, {last_date['time']}."
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=msg_to_send)

        elif msg == cancel_appointment_btn:
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
    if msg == back_btn:
        ctx.user_data["state"] = "online_appointment"
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в меню онлайн-записей.",
                             reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True))
        return 'online_appointment'
    if msg == timetable_range_btn:
        keyboard = ReplyKeyboardMarkup(TIMETABLE_DURATION, resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Установите возможный диапазон для записи"
                                                                    "(пока недоступно, вернитесь в меню)",
                             reply_markup=keyboard)
    elif msg == working_hours_btn:
        ctx.user_data["states"] = "work_begin_hours_choosing"
        keyboard = ReplyKeyboardMarkup(CalendarCog().get_hours_keyboard(), resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Выберите время начала работы:",
                             reply_markup=keyboard)
        return 'work_begin_hours_choosing'
    elif msg == weekends_btn:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=pass_message)
    elif msg == holidays_btn:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=pass_message)
    return "online_appointment_settings"


def certificates_admin(update, ctx):
    msg = update.message.text
    if msg == back_to_menu_btn:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в главное меню.",
                             reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
        return 'menu'
    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=pass_message)
    return 'certificates'


def yes_no_handler(update, ctx):
    msg = update.message.text
    return "menu"


def stop(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Stopped", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def unknown(update, ctx):
    """unknown command chat-passing"""
    pass


start_handler = CommandHandler("start", start)
stop_handler = CommandHandler("stop", stop)
unknown_handler = MessageHandler(Filters.command, unknown)

main_menu_conv_handler = ConversationHandler(
    entry_points=[start_handler],
    states={
        "menu": [MessageHandler(
            Filters.regex(
                f'^({online_timetable_btn}|{certificates_btn}|Рассылка спец. предложений)$')
            & (~Filters.command), menu)],
        "online_appointment": [
            MessageHandler(Filters.regex(f'^({settings_btn}|{check_appointments_btn}|{back_to_menu_btn})$')
                           & (~Filters.command), online_appointment),
            MessageHandler(Filters.regex(
                f'^({make_appointment_btn}|{appointment_info_btn}|{cancel_appointment_btn}|{back_to_menu_btn})$'),
                           online_appointment)],

        "certificates": [

            MessageHandler(Filters.regex(
                f'^(Добавление позиции|Изменение позиции|Удаление позиции|Просмотр позиций|{back_to_menu_btn})$')
                           & (~Filters.command), certificates_admin)],
        "yes_no_handler": [
            MessageHandler(Filters.text & (~Filters.command), yes_no_handler)
        ],

        # below the handlers, that make an appointment:
        "month_choosing": [MessageHandler(Filters.text & (~Filters.command), month_choosing)],
        "day_choosing": [MessageHandler(Filters.text & (~Filters.command), day_choosing)],
        "time_choosing": [MessageHandler(Filters.text & (~Filters.command), time_choosing)],

        # below the online_appointment_settings handlers:
        "online_appointment_settings": [MessageHandler(Filters.text & (~Filters.command),
                                                       online_appointment_settings)],
        "work_begin_hours_choosing": [
            MessageHandler(Filters.text & (~Filters.command), work_begin_hours_choosing)],
        "work_end_hours_choosing": [
            MessageHandler(Filters.text & (~Filters.command), work_end_hours_choosing)
        ]

    },
    fallbacks=[start_handler]
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
