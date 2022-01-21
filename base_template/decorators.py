# Тут необходимо будет прописать декораторы, которые будут обрабатывать непродуманные сценарии,
# например прерывать диалог, когда пользователь уходит из него коммандой /start к примеру.
from telegram import ReplyKeyboardMarkup
from base_template.context import *

from base_template.keyboards import ONLINE_TIMETABLE_admin_menu, ONLINE_TIMETABLE_user_menu


def only_admin(func):
    def something(update, ctx):
        if ctx.user_data["is_admin"]:
            func(update, ctx)
        else:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="У вас нет прав на использование этой команды.")
    return something


def only_table_values(func, collection=None, keyboard_type=None):
    def day_type(update, ctx):
        from functions.timetable.tools import CalendarCog
        import datetime
        collection = CalendarCog().get_days_keyboard(ctx.user_data["date_of_appointment"][0],
                                                     ctx.user_data["date_of_appointment"][1])
        msg = update.message.text
        try:
            # проверка на то чтобы запись была доступна только с завтра:
            if int(msg) <= datetime.date.today().day and \
                    ctx.user_data["date_of_appointment"][0] == datetime.date.today().year:
                ctx.user_data["date_of_appointment"][0] += 1

            # проверка уже на табличное значение:
            if msg not in [i[0] for i in collection]:
                raise Exception
        except Exception as ex:
            print(ex)
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=all_the_exc_msg)
            return "day_choosing"
        return func(update, ctx)

    def time_type(update, ctx):
        msg = update.message.text.lower()
        if msg == back_to_menu_btn:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text=main_menu_comeback_exc_msg)
            return
        if msg not in [i[0].lower() for i in collection]:
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=all_the_exc_msg)
            return ctx.user_data["state"]
        return func(update, ctx)

    def month_type(update, ctx):
        msg = update.message.text.lower()
        if msg not in [i[0].lower() for i in collection]:
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=all_the_exc_msg)
            return "month_choosing"
        return func(update, ctx)

    def timetable_range_type(update, ctx):
        msg = update.message.text.lower()
        if msg not in [i[0].lower() for i in collection]:
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=all_the_exc_msg)
            return "timetable_range_choosing"
        return func(update, ctx)

    def weekends_type(update, ctx):
        msg = update.message.text.lower()
        if msg not in [i.lower() for i in collection]:
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=all_the_exc_msg)
            return "weekends_choosing"
        return func(update, ctx)

    # type checking
    if keyboard_type == "day":
        return day_type
    elif keyboard_type == "time":
        return time_type
    elif keyboard_type == "month":
        return month_type
    elif keyboard_type == "timetable_range":
        return timetable_range_type
    elif keyboard_type == "weekends":
        return weekends_type
