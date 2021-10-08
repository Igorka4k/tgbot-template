from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import TOKEN
from keyboards import MONTH_CHOOSING_KEYBOARD
from tools import *
from exceptions import *
from db import queries
import datetime as dt

import functools

updater = Updater(token=TOKEN, use_context=True)


def start(update, ctx):
    """greeting"""
    # user_data init:
    ctx.user_data["date_of_appointment"] = []
    ctx.user_data["is_authorized"] = True
    ctx.user_data["date_of_appointment"] = []
    ctx.user_data["username"] = update.message.from_user["username"]

    ctx.bot.send_message(chat_id=update.effective_chat.id, text="hello")
    keyboard = ReplyKeyboardMarkup(keyboard=[["/timetable"]], resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Bot functional testing", reply_markup=keyboard)


def timetable_script_begin(update, ctx):
    keyboard = ReplyKeyboardMarkup(keyboard=[["/timetable"]], resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Bot functional testing", reply_markup=keyboard)
    return "timetable_script"


def stop(update, ctx):
    """stop"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Действие отменено.",
                         reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def timetable_script(update, ctx):
    keyboard = ReplyKeyboardMarkup(MONTH_CHOOSING_KEYBOARD, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Выберите месяц", reply_markup=keyboard)
    return "month_choosing"


@functools.partial(only_table_values, collection=MONTH_CHOOSING_KEYBOARD, keyboard_type="month")
def month_choosing(update, ctx):
    msg = update.message.text
    if msg == "_назад_":
        return timetable_script_begin(update, ctx)
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
    # date_of_appointment formatting:
    date = ctx.user_data["date_of_appointment"]
    if int(date[1]) < 10:
        date[1] = f"0{date[1]}"
    if int(date[2]) < 10:
        date[2] = f"0{date[2]}"
    formatting_date = f"{date[0]}-{date[1]}-{date[2]}, {date[3]}"

    # db appointment adding
    connection = db_connect()
    full_name = update.message.from_user["first_name"] + " " + update.message.from_user["last_name"]
    date = f"{date[2]}-{date[1]}-{date[0]}"
    time = date[3]
    tg_account = update.message.from_user["username"]
    queries.make_an_appointment(connection, full_name, date, time, tg_account)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы записаны на {formatting_date}.")
    return ConversationHandler.END


# handlers

start_handler = CommandHandler("start", start)
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("timetable", timetable_script)],
    states={
        "timetable_script": [CommandHandler("timetable", timetable_script)],
        "month_choosing": [MessageHandler(Filters.text & (~Filters.command), month_choosing)],
        "day_choosing": [MessageHandler(Filters.text & (~Filters.command), day_choosing)],
        "time_choosing": [MessageHandler(Filters.text & (~Filters.command), time_choosing)]
    },
    fallbacks=[CommandHandler("stop", stop)]
)

# dispatcher

dispatcher = updater.dispatcher

dispatcher.add_handler(start_handler)

dispatcher.add_handler(conv_handler)  # сущик вместо михендивского payment connect засунул весь процесс в conversation.

updater.start_polling()
