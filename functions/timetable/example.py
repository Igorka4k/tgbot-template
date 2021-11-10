from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler,\
    CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from base_template.keyboards import *
from functions.timetable.tools import *
from base_template.decorators import *
from functions.timetable.db import queries
import datetime as dt
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from os import environ
import functools


def timetable_script_begin(update, ctx):
    """Подготовка к онлайн-записи"""

    # user_data init:
    ctx.user_data["date_of_appointment"] = []
    ctx.user_data["is_date_choice"] = False

    # keyboard version: (НЕ УДАЛЯТЬ)
    # keyboard = ReplyKeyboardMarkup(MONTH_CHOOSING_KEYBOARD, resize_keyboard=True)
    # ctx.bot.send_message(chat_id=update.effective_chat.id, text="Выберите месяц", reply_markup=keyboard)
    # return "month_choosing"

    # calendar version:
    # return calendar_script(update, ctx)

    # authors calendar version:
    return new_calendar_script(update, ctx)


def stop(update, ctx):
    """stop"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Действие отменено.",
                         reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def new_calendar_script(update, ctx):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("test btn", callback_data="its test")]
    ])
    ctx.bot.send_message(chat_id=update.effective_chat.id,
                         text="test",
                         reply_markup=keyboard)
    print("ok")


def new_calendar_callback(update, ctx):
    query = update.callback_query
    data = query.data
    query.edit_message_text(text="good", parse_mode=ParseMode.MARKDOWN)


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
        keyboard = ReplyKeyboardMarkup(CalendarCog().get_hours_keyboard(), resize_keyboard=True)
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
        keyboard = ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="На сколько будет доступна запись?",
                             reply_markup=keyboard)
        return "timetable_admin_menu_settings"


@only_admin
def get_dates(update, ctx):
    """ appointments getting from db """
    # надо обновить, отправлять не длинный список, а слайдер с кнопками редактируемый, который можно будет
    # менять. Кнопки: кол-во всех за всё время записей, ближайшая запись, все записи на какой-то промежуток времени
    # (сегодня, неделя, месяц...).
    connection = db_connect()
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"{queries.get_data(connection)}")


@functools.partial(only_table_values, collection=MONTH_CHOOSING_KEYBOARD, keyboard_type="month")
def month_choosing(update, ctx):
    msg = update.message.text
    if msg == "<< Назад в меню":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в меню онлайн-записей.",
                             reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True))
        return 'online_appointment'
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
    if msg == "<< Назад в меню":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в меню онлайн-записей.",
                             reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True))
        return 'online_appointment'
    ctx.user_data["date_of_appointment"].append(msg)
    keyboard = ReplyKeyboardMarkup(CalendarCog().get_hours_keyboard(), resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Выберите теперь время.", reply_markup=keyboard)
    return "time_choosing"


# метод partial позволяет передавать параметры в декоратор.
@functools.partial(only_table_values, collection=ONLINE_TIMETABLE_HOURS, keyboard_type="time")
def time_choosing(update, ctx):
    msg = update.message.text
    if msg == "<< Назад в меню":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в меню онлайн-записей.",
                             reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True))
        return 'online_appointment'
    if not ctx.user_data["is_date_choice"]:
        return "time_choosing"
    ctx.user_data["date_of_appointment"].append(msg)

    # ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Запись оформлена.",
    #                      reply_markup=ReplyKeyboardRemove())
    return timetable_script_finish(update, ctx)


def timetable_script_finish(update, ctx):
    date = ctx.user_data["date_of_appointment"]
    formatting_date = f"{date[0]}-{date[1]}-{date[2]}, {date[3]}"

    connection = db_connect()
    full_name = update.message.from_user["first_name"] + " " + update.message.from_user["last_name"]
    time = date[3]
    date = f"{date[2]}-{date[1]}-{date[0]}"

    tg_account = update.message.from_user["username"]
    queries.make_an_appointment(connection, full_name, date, time, tg_account)
    ctx.user_data["is_date_choice"] = False

    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы записаны на {formatting_date}.",
                         reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_user_menu, resize_keyboard=True))
    return "online_appointment"


def timetable_connect(updater: Updater) -> None:
    """Adds required handlers"""
    dispatcher = updater.dispatcher
    # dispatcher.add_handler(callback_query_handler)
    dispatcher.add_handler(get_dates_handler)
    dispatcher.add_handler(new_calendar_callback_query_handler)


# handlers


new_calendar_callback_query_handler = CallbackQueryHandler(callback=new_calendar_callback)
# callback_query_handler = CallbackQueryHandler(callback=calendar_date_callback)
get_dates_handler = CommandHandler("get_dates", get_dates)  # возможность узнать текущие записи через команду


def main() -> None:
    updater = Updater(token=environ.get("BOT_TOKEN"), use_context=True)
    updater.dispatcher.add_handler(get_dates_handler)
    timetable_connect(updater)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
