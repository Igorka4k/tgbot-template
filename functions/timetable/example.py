from telegram.ext import Updater, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardRemove
from base_template.keyboards import *
from functions.timetable.tools import *
from base_template.decorators import *
from base_template.db import queries
import datetime as dt
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from os import environ
import functools
from functions.timetable.new_calendar.example import calendar_build
from functions.timetable import notifies
from base_template.constants import *


def timetable_script_begin(update, ctx):
    """Подготовка к онлайн-записи"""

    # keyboard version: (НЕ УДАЛЯТЬ)
    # keyboard = ReplyKeyboardMarkup(MONTH_CHOOSING_KEYBOARD, resize_keyboard=True)
    # ctx.bot.send_message(chat_id=update.effective_chat.id, text="Выберите месяц", reply_markup=keyboard)
    # return "month_choosing"

    # calendar version:
    # return calendar_script(update, ctx)

    # author`s calendar version:

    # ==== timetable_settings:
    ctx.user_data["timetable_settings"] = {
        "timetable_range": queries.get_timetable_range(db_connect()),
        "working_hours": queries.get_working_hours(db_connect()),
        "days_off": queries.get_days_off(db_connect()),
        "holidays": queries.get_holidays(db_connect()),
        "notifies": queries.get_notifies(db_connect())
    }
    # print(ctx.user_data["timetable_settings"]['timetable_range'],
    #       ctx.user_data["timetable_settings"]['working_hours'],
    #       ctx.user_data['timetable_settings']['days_off'],
    #       ctx.user_data['timetable_settings']['holidays'],
    #       ctx.user_data['timetable_settings']['notifies'])
    ctx.user_data["make_an_appointment"] = True
    return calendar_build(update, ctx, do_timetable_settings=True)


def stop(update, ctx):
    """stop"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=conv_handler_stop_msg,
                         reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def calendar_script(update, ctx):
    calendar, step = DetailedTelegramCalendar().build()
    ctx.bot.send_message(update.effective_chat.id,
                         text=f"Выберите {LSTEP[step + '_ru']}:",
                         reply_markup=calendar)
    return "time_choosing"


def calendar_date_callback(update, ctx):  # пока не используется
    """calendar callback-handler function (not using)"""
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
        ctx.user_data["date_of_appointment"]['year'] = year  # (Порядок: год-месяц-день)
        ctx.user_data["date_of_appointment"]['month'] = month  # (Порядок: год-месяц-день)
        ctx.user_data["date_of_appointment"]['day'] = day  # (Порядок: год-месяц-день)

        # time_choosing redirect:
        keyboard = ReplyKeyboardMarkup(CalendarCog().get_hours_keyboard(
            begin=ctx.user_data["timetable_settings"]["working_hours"]["begin"],
            end=ctx.user_data["timetable_settings"]["working_hours"]["end"],
            between_range=queries.get_dates_between_range(db_connect()),
        ), resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=time_choosing_tip_msg, reply_markup=keyboard)
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
    ctx.user_data["date_of_appointment"]['year'] = year
    ctx.user_data["date_of_appointment"]['month'] = choice_month
    day_choosing_keyboard = CalendarCog().get_days_keyboard(year, choice_month)
    keyboard = ReplyKeyboardMarkup(day_choosing_keyboard, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=time_choosing_tip_msg, reply_markup=keyboard)
    return "day_choosing"


@functools.partial(only_table_values, keyboard_type="day")
def day_choosing(update, ctx):
    msg = update.message.text
    if msg == "<< Назад в меню":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в меню онлайн-записей.",
                             reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True))
        return 'online_appointment'
    ctx.user_data["date_of_appointment"].append(msg)
    keyboard = ReplyKeyboardMarkup(ctx.user_data["timetable_settings"]["timetable_hours"], resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Выберите теперь время.", reply_markup=keyboard)
    return "time_choosing"


def time_choosing2(update, ctx):
    if not ctx.user_data["is_date_choice"]:
        return "time_choosing"
    year = ctx.user_data['date_of_appointment']['year']
    month = ctx.user_data['date_of_appointment']['month']
    day = ctx.user_data['date_of_appointment']['day']
    all_times = [[':'.join(list(map(str, i.time)))] for i in
                 ctx.user_data['my_all_the_dates'][0].months[int(month) - 1].days[int(day) - 1].time]
    # TEST below:
    for i in range(len(all_times)):
        new_row = list(all_times[i][0])
        if len(all_times[i][0].split(":")[0]) != 2:
            new_row.insert(0, '0')
            all_times[i][0] = ''.join(new_row)
        if len(all_times[i][0].split(":")[1]) != 2:
            new_row.insert(-1, '0')
            all_times[i][0] = ''.join(new_row)
    time = msg = update.message.text.lower()
    # inline func decorator:
    if msg == back_to_menu_btn:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=main_menu_comeback_exc_msg)
        return "time_choosing2"
    if msg not in [i[0].lower() for i in all_times]:
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text=all_the_exc_msg)
        return "time_choosing2"

    ctx.user_data["date_of_appointment"]['time'] = time
    # test (busy time deleting):
    year = int(ctx.user_data['date_of_appointment']['year'])
    month = int(ctx.user_data['date_of_appointment']['month'])
    day = int(ctx.user_data['date_of_appointment']['day'])
    all_dates = ctx.user_data['my_all_the_dates']
    all_times = all_dates[0].months[month - 1].days[day - 1].time
    for t in all_times:
        if t.str_time == time:
            t.available = False
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Вы заняли время {time}, оно не будет доступно другим')
            break
    return timetable_script_finish(update, ctx)


# метод partial тут скрыт, это спецом
@functools.partial(only_table_values,
                   collection=online_timetable_hours(),
                   keyboard_type="time")
def time_choosing(update, ctx):
    time = msg = update.message.text
    # if [msg] not in ctx.user_data["only_table_val"]:
    #     keyboard = ReplyKeyboardMarkup(ctx.user_data["only_table_val"], resize_keyboard=True)
    #     ctx.bot.send_message(chat_id=update.effective_chat.id,
    #                          text=all_the_exc_msg,
    #                          reply_markup=keyboard)
    #     return "time_choosing"
    # if msg == back_btn:
    #     ctx.bot.send_message(chat_id=update.effective_chat.id, text=timetable_comeback_msg,
    #                          reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True))
    #     return 'online_appointment'
    if not ctx.user_data["is_date_choice"]:
        return "time_choosing"
    ctx.user_data["date_of_appointment"]['time'] = time
    return timetable_script_finish(update, ctx)


def timetable_script_finish(update, ctx):
    date = ctx.user_data["date_of_appointment"]
    date['month'] = "0" + str(date['month']) if len(str(date['month'])) == 1 else str(date['month'])  # month_formatted.
    date['day'] = "0" + str(date['day']) if len(str(date['day'])) == 1 else str(date['day'])  # day_formatted.
    formatting_date = f"{date['year']}-{date['month']}-{date['day']}, {date['time']}"
    # if ctx.user_data["make_an_appointment"]:
    connection = db_connect()
    try:
        name = update.message.from_user["first_name"]
        surname = update.message.from_user["last_name"]
        if name is None:
            name = anonymous_name
        if surname is None:
            surname = anonymous_surname
        full_name = name + " " + surname
    except Exception as ex:
        print(ex)
        full_name = anonymous_name + " " + anonymous_surname

    time = date['time']
    date = f"{date['day']}-{date['month']}-{date['year']}"

    tg_account = update.message.from_user["username"]
    queries.make_an_appointment(connection, full_name, date, time, tg_account)
    ctx.user_data["is_date_choice"] = False
    ctx.user_data["make_an_appointment"] = False
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы записаны на {formatting_date}\n" + promise_msg,
                         reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_user_menu, resize_keyboard=True))
    datetime_from_formatting = get_datetime_from_formatting(formatting_date)
    notifies.schedule_notify(update, ctx, datetime_from_formatting, time=time, date=date)
    return "online_appointment"


def timetable_connect(updater: Updater) -> None:
    """Adds required handlers"""
    dispatcher = updater.dispatcher
    # dispatcher.add_handler(callback_query_handler)
    dispatcher.add_handler(get_dates_handler)


# handlers


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
