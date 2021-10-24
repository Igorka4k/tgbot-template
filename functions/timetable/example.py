from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from functions.timetable.config import TOKEN, admin_chat
from functions.timetable.keyboards import MONTH_CHOOSING_KEYBOARD, ONLINE_APPOINTMENTS_KEYBOARD__admin
from functions.timetable.tools import *
from exceptions import *
from functions.timetable.db import queries
import datetime as dt
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

import functools


def start(update, ctx):
    """greeting"""
    # user_data init:
    ctx.user_data["date_of_appointment"] = []
    ctx.user_data["is_date_choice"] = False
    return timetable_script_begin(update, ctx)

    # if __name__ == "__main__":
    #     ctx.bot.send_message(chat_id=update.effective_chat.id, text="hello")
    #     keyboard = ReplyKeyboardMarkup(keyboard=[["/timetable"]], resize_keyboard=True)
    #     ctx.bot.send_message(chat_id=update.effective_chat.id, text="Bot functional testing", reply_markup=keyboard)


def timetable_script_begin(update, ctx):
    """Подготовка к онлайн-записи"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="/timetable - команда")
    return "timetable_script"


# def timetable_script_begin(update, ctx):
#     keyboard = ReplyKeyboardMarkup(keyboard=[["/timetable"]], resize_keyboard=True)
#     ctx.bot.send_message(chat_id=update.effective_chat.id, text="Bot functional testing", reply_markup=keyboard)
#     return "timetable_script"


def stop(update, ctx):
    """stop"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Действие отменено.",
                         reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def timetable_script(update, ctx):
    # keyboard version:
    # keyboard = ReplyKeyboardMarkup(MONTH_CHOOSING_KEYBOARD, resize_keyboard=True)
    # ctx.bot.send_message(chat_id=update.effective_chat.id, text="Выберите месяц", reply_markup=keyboard)
    # return "month_choosing"

    # calendar version:
    if ctx.user_data["is_admin"]:
        return timetable_admin_menu(update, ctx)
    return calendar_script(update, ctx)


def calendar_script(update, ctx):
    calendar, step = DetailedTelegramCalendar().build()
    ctx.bot.send_message(update.effective_chat.id,
                         text=f"Выберите {LSTEP[step + '_ru']}:",
                         reply_markup=calendar)
    return "time_choosing"


def calendar_date_callback(update, ctx):
    """calendar callback-handler function"""
    query = update.callback_query

    result, key, step = DetailedTelegramCalendar().process(query.data)
    if not result and key:
        ctx.bot.edit_message_text(f"Выберите {LSTEP[step + '_ru']}:",
                                  query.message.chat.id,
                                  query.message.message_id,
                                  reply_markup=key)
    elif result:
        ctx.bot.edit_message_text(f"Дата {result} выбрана.",
                                  query.message.chat.id,
                                  query.message.message_id)
        year, month, day = str(result).split("-")
        ctx.user_data["date_of_appointment"].extend([year, month, day])  # (Порядок: год-месяц-день)

        # time_choosing redirect:
        keyboard = ReplyKeyboardMarkup(CalendarCog().get_hours(), resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Выберите теперь время.", reply_markup=keyboard)
        ctx.user_data["is_date_choice"] = True
        return "time_choosing"


def timetable_admin_menu_choice(update, ctx):
    """ Обработка выбора в меню записей (у админа)"""
    msg = update.message.text
    if msg == "Список записей":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вот текущие записи:")
        return get_dates(update, ctx)
    if msg == "Настройки":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Тут будут настройки бота.")
        return "timetable_admin_menu"


@only_admin
def get_dates(update, ctx):
    """ appointments getting from db """
    # надо обновить, отправлять не длинный список, а сообщение с кнопками редактируемое, которое можно будет
    # менять. Кнопки: кол-во всех за всё время записей, ближайшая запись, все записи на какой-то промежуток времени
    # (сегодня, неделя, месяц...); возможно скриншот бд со всеми записями.
    from functions.timetable.tools import db_connect
    connection = db_connect()
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"{queries.get_data(connection)}")


def timetable_admin_menu(update, ctx):
    keyboard = ReplyKeyboardMarkup(ONLINE_APPOINTMENTS_KEYBOARD__admin, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Тут будет запись на приём.", reply_markup=keyboard)
    return "timetable_admin_menu"


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
    if not ctx.user_data["is_date_choice"]:
        return "time_choosing"
    msg = update.message.text
    ctx.user_data["date_of_appointment"].append(msg)

    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Запись оформлена.",
                         reply_markup=ReplyKeyboardRemove())
    return timetable_script_finish(update, ctx)


def timetable_script_finish(update, ctx):
    # date_of_appointment formatting:
    date = ctx.user_data["date_of_appointment"]
    formatting_date = f"{date[0]}-{date[1]}-{date[2]}, {date[3]}"

    # db appointment adding
    connection = db_connect()
    full_name = update.message.from_user["first_name"] + " " + update.message.from_user["last_name"]
    date = f"{date[2]}-{date[1]}-{date[0]}"
    time = date[3]
    tg_account = update.message.from_user["username"]
    queries.make_an_appointment(connection, full_name, date, time, tg_account)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы записаны на {formatting_date}.")

    # flags clearing:
    ctx.user_data["is_date_choice"] = False
    return ConversationHandler.END


def timetable_connect(updater: Updater) -> None:
    """Adds required handlers"""
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(callback_query_handler)


# handlers

start_handler = CommandHandler("start", start)
callback_query_handler = CallbackQueryHandler(callback=calendar_date_callback)
get_dates_handler = CommandHandler("get_dates", get_dates)
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("timetable", timetable_script)],
    states={
        "timetable_script": [CommandHandler("timetable", timetable_script)],
        "timetable_admin_menu": [MessageHandler(Filters.text & (~Filters.command), timetable_admin_menu_choice)],
        "month_choosing": [MessageHandler(Filters.text & (~Filters.command), month_choosing)],
        "day_choosing": [MessageHandler(Filters.text & (~Filters.command), day_choosing)],
        "time_choosing": [MessageHandler(Filters.text & (~Filters.command), time_choosing)]
    },
    fallbacks=[CommandHandler("stop", stop)]
)


def main() -> None:
    updater = Updater(token=TOKEN, use_context=True)
    # Commands:
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(get_dates_handler)
    # =========
    timetable_connect(updater)
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
