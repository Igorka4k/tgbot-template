# Функционал timetable со стороны админа.

from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from base_template.keyboards import *
from functions.timetable.tools import *
from base_template.decorators import *
from functions.timetable.db import queries
import datetime as dt
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from os import environ

import functools


@functools.partial(only_table_values, collection=CalendarCog().get_hours_keyboard(), keyboard_type="time")
def work_begin_hours_choosing(update, ctx):
    print("something")
    ctx.user_data["state"] = "work_end_hours_choosing"
    msg = update.message.text
    ctx.user_data['prev_msg'] = msg
    ctx.user_data["work_hours"] = {msg: ''}
    keyboard = ReplyKeyboardMarkup(ONLINE_TIMETABLE_HOURS, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Теперь введите время прекращения работы",
                         reply_markup=keyboard)
    return "work_end_hours_choosing"


# сделать проверку на то, чтобы время было не раньше начала (в декораторе)
@functools.partial(only_table_values, collection=CalendarCog().get_hours_keyboard(), keyboard_type="time")
def work_end_hours_choosing(update, ctx):
    msg = update.message.text
    ctx.user_data["work_hours"][ctx.user_data['prev_msg']] = msg

    keyboard = ReplyKeyboardMarkup(YES_NO_KEYBOARD, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Добавить часы работы? "
                                                                "(в случае если рабочий день не закончен)",
                         reply_markup=keyboard)

    beginning_time, ending_time = set_working_hours(update, ctx)
    keyboard = ReplyKeyboardMarkup(ONLINE_TIMETABLE_SETTINGS, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Готово! теперь к вам можно записаться только"
                                                                f" с {beginning_time} по {ending_time}.",
                         reply_markup=keyboard)
    return "online_appointment_settings"


def set_working_hours(update, ctx):
    chosen_time = min([dt.timedelta(hours=int(i.split(":")[0]),
                                    minutes=int(i.split(":")[1])) for i in ctx.user_data["work_hours"].keys()])
    total_seconds = int(chosen_time.total_seconds())
    hours, remainder = divmod(total_seconds, 60 * 60)
    minutes, seconds = divmod(remainder, 60)

    work_begin_time = dt.time(hour=hours, minute=minutes).strftime("%H:%M")
    work_end_time = ctx.user_data["work_hours"][work_begin_time]
    queries.working_time_adding(db_connect(), work_begin_time, work_end_time)
    return work_begin_time, work_end_time
