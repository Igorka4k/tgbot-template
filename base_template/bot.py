from base_template.data.config import *
from base_template.constants import *
from base_template.keyboards import *
from functions.timetable.tools import CalendarCog
from functions.timetable.db import queries
from functions.timetable import tools
from functions.payments.example import payment_connect
from base_template.exceptions import *

from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

import json
import functools

updater = Updater(token=TOKEN, use_context=True)  # bot create.


def start(update, ctx):
    """greeting"""
    from functions.timetable.tools import db_connect
    # короче надо будет как то сохранить инфу о том кто подписан на бота и проявляет активность,
    # у сущика уже есть идеи, можно побазарить как-нибудь, но пока тока запись о том что пользователь когда-то писал
    # /start, в ctx.user_data:
    # ctx.user_data initialization:
    # ПРИМЕЧАНИЕ: Пока что есть такой косяк, что user_data сбрасывается при перезапуске бота.
    ctx.user_data["is_authorized"] = True
    ctx.user_data["date_of_appointment"] = []
    ctx.user_data["username"] = update.message.from_user["username"]
    ctx.user_data["is_admin"] = True if update.effective_chat.id in admin_chat else False
    if update.message.from_user["full_name"] is None:
        ctx.user_data["full_name"] = "Аноним"
    else:
        ctx.user_data["full_name"] = update.message.from_user["full_name"]
    connection = db_connect()
    if not queries.is_authorized(connection, update.message.from_user["username"]):
        queries.new_user_adding(connection, ctx.user_data["full_name"], ctx.user_data["username"])
    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы уже авторизованы, я вас запомнил.")

    # /start не может быть entry_point`ом в диалоге, поэтому просим начать диалог через отдельную команду /menu:
    keyboard = ReplyKeyboardMarkup([["/menu"]], resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id,
                         text=f'Приветствую, {ctx.user_data["username"]},'
                              f' для использования бота нажмите на кнопку перехода в меню.',
                         reply_markup=keyboard)


def menu(update, ctx):
    """main menu"""
    if ctx.user_data["is_admin"]:
        keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True)
    else:
        keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text='Вы находитесь в главном меню бота.',
                         reply_markup=keyboard)
    return "service_choosing"


def service_choosing(update, ctx):
    msg = update.message.text

    if ctx.user_data["is_admin"]:

        if msg == "онлайн-записи":
            return get_appointments_script(update, ctx)
        if msg == "статистика доходов":
            return benefits_script(update, ctx)
        if msg == "Редактирование спец. предложений":
            return competitors_script(update, ctx)
        return "service_choosing"

    if not ctx.user_data["is_admin"]:
        if msg == "онлайн-запись":
            return timetable_script(update, ctx)
        if msg == "сертификаты":
            return online_buy_script(update, ctx)


def get_appointments_script(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Информация по текущим записям:\n\n"
                                                                + queries.get_data(connection=tools.db_connect()))
    return "service_choosing"


def online_buy_script(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Тут будут предложения разных позиций цифровых товаров,"
                                                                "таких как сертификаты и тд..")
    return "service_choosing"


def timetable_script(update, ctx):
    keyboard = ReplyKeyboardMarkup(MONTH_CHOOSING_KEYBOARD, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Выберите месяц", reply_markup=keyboard)
    return "month_choosing"


def competitors_script(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Тут будет список конкурентов.")
    return menu(update, ctx)


def benefits_script(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Тут будет список доходов.")
    return menu(update, ctx)


@functools.partial(only_table_values, collection=MONTH_CHOOSING_KEYBOARD, keyboard_type="month")
def month_choosing(update, ctx):
    import datetime as dt
    msg = update.message.text
    if msg == "_назад_":
        return menu(update, ctx)
    word_to_num = {
        "(текущий месяц)": dt.datetime.now().month,
        "январь": 1,
        "февраль": 2,
        "март": 3,
        "апрель": 4,
        "май": 5,
        "июнь": 6,
        "июль": 7,
        "август": 8,
        "сентябрь": 9,
        "октябрь": 10,
        "ноябрь": 11,
        "декабрь": 12,
    }
    choice_month = word_to_num[msg]
    year = CalendarCog().get_year(choice_month)
    ctx.user_data["date_of_appointment"].append(year)
    ctx.user_data["date_of_appointment"].append(choice_month)
    day_choosing_keyboard = CalendarCog().get_days_keyboard(year, choice_month)
    keyboard = ReplyKeyboardMarkup(day_choosing_keyboard, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Теперь выберите день.", reply_markup=keyboard)
    return "day_choosing"


@functools.partial(only_table_values, keyboard_type="day")
def day_choosing(update, ctx):
    msg = update.message.text
    ctx.user_data["date_of_appointment"].append(msg)
    keyboard = ReplyKeyboardMarkup(CalendarCog().get_hours(), resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Выберите теперь время.", reply_markup=keyboard)
    return "time_choosing"


# метод partial позволяет передавать параметры в декоратор.
@functools.partial(only_table_values, collection=CalendarCog().get_hours(), keyboard_type="time")
def time_choosing(update, ctx):
    msg = update.message.text
    ctx.user_data["date_of_appointment"].append(msg)

    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Запись оформлена.",
                         reply_markup=ReplyKeyboardRemove())
    return timetable_script_finish(update, ctx)


def timetable_script_finish(update, ctx):
    from functions import timetable  # модуль для записи в бд.
    # date_of_appointment formatting:
    date = ctx.user_data["date_of_appointment"]
    if int(date[1]) < 10:
        date[1] = f"0{date[1]}"
    if int(date[2]) < 10:
        date[2] = f"0{date[2]}"
    formatting_date = f"{date[0]}-{date[1]}-{date[2]}, {date[3]}"

    # db appointment adding
    connection = timetable.tools.db_connect()
    full_name = update.message.from_user["first_name"] + " " + update.message.from_user["last_name"]
    date = f"{date[2]}-{date[1]}-{date[0]}"
    time = date[3]
    tg_account = update.message.from_user["username"]
    queries.make_an_appointment(connection, full_name, date, time, tg_account)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы записаны на {formatting_date}.")
    return ConversationHandler.END


def command_list(update, ctx):
    """help command list"""
    with open(CMD_LIST_PATH, "r", encoding="utf-8") as file:
        all_the_commands = json.load(file)
        formatting_commands = "\n\n".join([f"{key} - {val.capitalize()}." for key, val in all_the_commands.items()])
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=formatting_commands)


def stop(update, ctx):
    """dialog breaking"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы принудительно вернулись в главное меню.")
    return menu(update, ctx)


@only_admin
def get_dates(update, ctx):
    """ appointments getting from db """
    from functions.timetable.tools import db_connect
    connection = db_connect()
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"{queries.get_data(connection)}")


def unknown(update, ctx):
    """unknown command chat-exception"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Неизвестная команда, нажмите сюда ==> /help")


dispatcher = updater.dispatcher  # dispatcher object, which manages all the handlers and something..

# Handlers
start_handler = CommandHandler("start", start)
main_menu_handler = CommandHandler("menu", menu)
help_handler = CommandHandler("help", command_list)
stop_handler = CommandHandler("stop", stop)
main_menu_conv_handler = ConversationHandler(
    entry_points=[main_menu_handler],
    states={
        "service_choosing": [MessageHandler(Filters.text & (~Filters.command), service_choosing)],
        "timetable_script": [MessageHandler(Filters.text & (~Filters.command), timetable_script)],
        "timetable_script_finish": [MessageHandler(Filters.text & (~Filters.command), timetable_script_finish)],
        "time_choosing": [MessageHandler(Filters.text & (~Filters.command), time_choosing)],
        "month_choosing": [MessageHandler(Filters.text & (~Filters.command), month_choosing)],
        "day_choosing": [MessageHandler(Filters.text & (~Filters.command), day_choosing)],
        "benefits_script": [MessageHandler(Filters.text & (~Filters.command), benefits_script)],
        "competitors_script": [MessageHandler(Filters.text & (~Filters.command), competitors_script)],
    },
    fallbacks=[stop_handler]
)
get_dates_handler = CommandHandler("get_dates", get_dates)

unknown_handler = MessageHandler(Filters.command, unknown)

# Dispatcher adding !!!ПРЕВОСХОДСТВО СЛУШАТЕЛЯ ЗАВИСИТ ОТ МОМЕНТА ЕГО ДОБАВЛЕНИЯ В ДИСПЕТЧЕР!!!
###
dispatcher.add_handler(start_handler)
###
dispatcher.add_handler(main_menu_conv_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(get_dates_handler)
payment_connect(updater)
###
dispatcher.add_handler(unknown_handler)

updater.start_polling()

updater.idle()
