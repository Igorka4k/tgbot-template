from telegram.ext import Updater
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from functions.timetable.tools import *
import datetime as dt
from os import environ
from .constants import *
import calendar


def calendar_build(update, ctx, entry_state="month", do_timetable_settings=False):
    # user_data init:
    ctx.user_data["date_of_appointment"] = []
    ctx.user_data["is_date_choice"] = False

    if entry_state == "month":
        ctx.user_data["state"] = "month_choosing"
        month_keys = get_month_keys(do_timetable_settings, timetable_settings=ctx.user_data["timetable_settings"])
        keyboard = InlineKeyboardMarkup(month_keys)
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text="Выберите месяц:",
                             reply_markup=keyboard)
    elif entry_state == "day":
        month = dt.datetime.now().month
        year = CalendarCog().get_year(int(month))
        ctx.user_data["date_of_appointment"].extend([year, month])
        ctx.user_data["state"] = "day_choosing"
        days_keys = get_days_keys(year, month,
                                  do_timetable_settings=ctx.user_data["make_an_appointment"],
                                  timetable_settings=ctx.user_data["timetable_settings"])
        keyboard = InlineKeyboardMarkup(days_keys)
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Выберите день (календарь на {month_name_ru[month - 1]}):",
                             reply_markup=keyboard)

    elif entry_state == "year":
        pass
    ctx.user_data["is_date_choice"] = True
    return "time_choosing"


def get_month_keys(do_timetable_settings, timetable_settings=None):
    """ getting month keys (winter, spring, summer, autumn) """
    if do_timetable_settings:
        month_range = list(
            map(lambda x: x.month, ExceptionCog().get_timetable_range(timetable_settings["timetable_range"])))

        start = month_range[0]
        end = month_range[1]
        correctly_month_values = set()
        correctly_month_values.add(end)
        if start == end:
            start += 1
        while start != end:
            if start > 12:
                start = 1
            correctly_month_values.add(start)
            start += 1
        month_range = correctly_month_values
        # holidays_range = list(map(lambda x: x.month, ExceptionCog().get_holidays_range(timetable_settings["holidays"])))
    rows = []
    row = []
    for i in range(1, 12 + 1):
        shifting = i - 1
        if shifting == 0:
            shifting = 12
        if do_timetable_settings and shifting in month_range:
            row.append(month_abbr_ru[shifting])
        elif not do_timetable_settings:
            row.append(month_abbr_ru[shifting])
        if i % 3 == 0:
            rows.append([InlineKeyboardButton(x, callback_data=month_ru.index(x) + 1) for x in row])
            row.clear()
    return rows


def get_slider_keys(month=None, year=None):
    if month:
        return ["<<", month_abbr_ru[month], ">>"]
    elif year:
        return


def get_days_keys(year, months_num, do_timetable_settings=False, timetable_settings=None):
    """ getting weekdays keys """
    first_weekday, month_range = calendar.monthrange(year, months_num)
    if do_timetable_settings:
        timetable_range = ExceptionCog().get_timetable_range(timetable_settings["timetable_range"])
        days_off = ExceptionCog().get_days_off_indexes(timetable_settings["days_off"])
        holidays_range = ExceptionCog().get_holidays_range(timetable_settings["holidays"])

    rows = list()
    rows.append([InlineKeyboardButton(i, callback_data="pass") for i in weekdays_header_ru])  # header adding..
    row = []
    num = 1
    btn_num = 0
    while num <= month_range:
        for i in range(7):
            btn_num += 1
            if btn_num <= first_weekday or num > month_range:
                row.append(InlineKeyboardButton(" ", callback_data="pass"))
                continue
            if do_timetable_settings:
                iter_date = datetime.date(year=year, month=months_num, day=num)
                if timetable_range[0] <= iter_date <= timetable_range[-1] and \
                        i not in days_off and \
                        (holidays_range is None or not holidays_range[0] <= iter_date <= holidays_range[-1]):
                    row.append(InlineKeyboardButton(str(num), callback_data=num))
                else:
                    row.append(InlineKeyboardButton(" ", callback_data="pass"))
            else:
                row.append(InlineKeyboardButton(str(num), callback_data=num))
            num += 1
        rows.append(row[:])
        row.clear()
    return rows


def main() -> None:
    updater = Updater(token=environ.get("BOT_TOKEN"), use_context=True)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
