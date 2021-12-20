from os import path

from dotenv import load_dotenv
from telegram import ParseMode, InputMediaPhoto
from telegram.ext import CallbackQueryHandler, MessageHandler, Filters

from functions.payments.example import keyboard_callback_handler, show_carousel
from base_template.db.queries import get_user_last_date, delete_appointment, get_days_off
from functions.timetable.example import *
from functions.timetable.admin_example import *
from functions.timetable.new_calendar.example import *
from base_template.some_tools import *

from base_template.keyboards import *
from base_template.constants import *

if path.exists('../.env'):  # Переменные окружения хранятся в основной директории проекта
    load_dotenv('../.env')
else:
    raise ImportError("Can't import environment variables")

ADMIN_CHAT = list(map(int, environ.get('ADMIN_CHAT').split(',')))


def start(update, ctx):
    ctx.user_data["is_authorized"] = True
    ctx.user_data["state"] = 'main_menu'
    ctx.user_data["make_an_appointment"] = False
    ctx.user_data["choose_holidays"] = {1: False, 2: False}
    ctx.user_data["tg_account"] = update.message.from_user["username"]
    ctx.user_data["is_admin"] = True if update.effective_chat.id in ADMIN_CHAT else False

    # ==== timetable_settings:
    ctx.user_data["timetable_settings"] = {
        "timetable_range": queries.get_timetable_range(db_connect()),
        "working_hours": queries.get_working_hours(db_connect()),
        "days_off": queries.get_days_off(db_connect()),
        "holidays": queries.get_holidays(db_connect())
    }
    if update.message.from_user["full_name"] is None:
        ctx.user_data["full_name"] = anonymous_name
    else:
        ctx.user_data["full_name"] = update.message.from_user["full_name"]

    connection = db_connect()

    text = ""

    if not queries.is_authorized(connection, update.message.from_user["tg_account"]):
        queries.new_user_adding(connection, ctx.user_data["full_name"], ctx.user_data["tg_account"])
        text += welcome_msg
    else:
        text += authorized_already_msg
    text += main_menu_nav_msg

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
            ctx.bot.send_message(chat_id=update.effective_chat.id, text=timetable_menu_nav_msg__admin,
                                 reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu,
                                                                  resize_keyboard=True))
        else:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text=timetable_menu_nav_msg__user,
                                 reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_user_menu, resize_keyboard=True))
        return 'online_appointment'

    elif msg == certificates_btn:
        ctx.user_data["state"] = "certificates"
        if ctx.user_data["is_admin"]:
            ctx.bot.send_message(chat_id=update.message.chat_id,
                                 text=shop_nav_msg__admin,
                                 reply_markup=ReplyKeyboardMarkup(INVOICE_EDITOR_KEYBOARD,
                                                                  resize_keyboard=True))
            return 'certificates'
        else:
            ctx.user_data["state"] = "menu"
            ctx.bot.send_message(chat_id=update.message.chat_id,
                                 text=shop_nav_msg__user,
                                 reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True))

            show_carousel(update, ctx)
            return 'menu'

    elif msg == offers_sending_btn:
        ctx.user_data["state"] = "menu"
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=pass_message)

    elif msg == price_btn:
        data = queries.get_service_from_price(db_connect())
        ctx.user_data["price_info"] = {i['title']: i for i in data}
        prices = [(i["title"], i["price"]) for i in data]
        # в callback_data попробовать передать ctx.user_data["state"] для реализации новой логики меню.
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(f"{i[0]} ({i[1]} руб)",
                                                               callback_data=i[0])] for i in prices])
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"{price_checklist_msg}",
                             reply_markup=keyboard)

    elif msg == all_the_text_editor_btn:
        keyboard = ReplyKeyboardMarkup(ALL_THE_TEXT_EDITOR_MENU, resize_keyboard=True)
        ctx.user_data["state"] = "text_editor_menu"
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text=all_the_text_editor_menu_msg,
                             reply_markup=keyboard)
        return 'text_editor_menu'
    return 'menu'


def online_appointment(update, ctx):
    msg = update.message.text
    if msg == back_to_menu_btn:
        ctx.user_data['state'] = "menu"
        if ctx.user_data["is_admin"]:
            keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True)
        else:
            keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True)

        ctx.bot.send_message(chat_id=update.effective_chat.id, text=main_menu_comeback_msg,
                             reply_markup=keyboard)
        return 'menu'

    elif ctx.user_data["is_admin"]:
        if msg == check_appointments_btn:
            get_dates(update, ctx)

        elif msg == settings_btn:
            ctx.user_data["states"] = 'online_appointment_settings'
            keyboard = ReplyKeyboardMarkup(ONLINE_TIMETABLE_SETTINGS, resize_keyboard=True)
            ctx.bot.send_message(chat_id=update.effective_chat.id, text=timetable_editor_nav_msg,
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
                msg_to_send = without_appointment_exc_msg__info
            else:
                msg_to_send = f"Вы записаны на {last_date['date']}, {last_date['time']}."
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=msg_to_send)

        elif msg == cancel_appointment_btn:
            last_date = get_user_last_date(db_connect(), ctx.user_data["tg_account"])
            if not last_date:
                msg_to_send = without_appointment_exc_msg__cancel
            else:
                delete_appointment(db_connect(), ctx.user_data["tg_account"])
                msg_to_send = f"Запись от {last_date['date']}, {last_date['time']} отменена."
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=msg_to_send)
    return 'online_appointment'


def text_editor_menu(update, ctx):
    msg = update.message.text
    if msg == back_btn:
        ctx.user_data["state"] = "main_menu"
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=main_menu_comeback_msg,
                             reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
        return 'menu'

    if msg == default_text_modes_menu_btn:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(str(i), callback_data="pass")] for i in range(3)])
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text="Темы кнопок и сообщений по-умолчанию:",
                             reply_markup=keyboard)
    elif msg == get_texts_list_btn:
        keyboard = ReplyKeyboardMarkup(CANCEL_KEYBOARD, resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text="Выберите текст для редактирования:\n"
                                  f"{get_texts_list(dispatcher, ctx, formatting_to_text=True)}",
                             reply_markup=keyboard)
        # return "finishing_handler"
        return "set_new_text_handler"


def online_appointment_settings(update, ctx):
    msg = update.message.text
    if msg == back_btn:
        ctx.user_data["state"] = "online_appointment"
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=timetable_editor_comeback_msg,
                             reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_admin_menu, resize_keyboard=True))
        return 'online_appointment'
    if msg == timetable_range_btn:
        keyboard = ReplyKeyboardMarkup(TIMETABLE_DURATION, resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=timetable_range_tip_msg,
                             reply_markup=keyboard)
        return "timetable_duration_choosing"
    elif msg == working_hours_btn:
        ctx.user_data["states"] = "work_begin_hours_choosing"
        keyboard = ReplyKeyboardMarkup(CalendarCog().get_hours_keyboard(), resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=time_choosing_tip_msg,
                             reply_markup=keyboard)
        return 'work_begin_hours_choosing'
    elif msg == weekends_btn:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data=i) for i in weekdays_header_ru],
                                         [InlineKeyboardButton(close_btn, callback_data=back_btn)]])
        days_off = get_days_off(db_connect())
        if not len(days_off):
            msg_to_send = f"Выберите нерабочие дни. На данный момент вы работаете без выходных."
        elif len(days_off) == 7:
            msg_to_send = f"Уберите нерабочии дни. На данный момент к вам нельзя записаться, т.к. " \
                          f"вы указали все дни недели нерабочими"
        else:
            msg_to_send = f"Выберите/Уберите нерабочие дни. ({', '.join(days_off)})"
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text=msg_to_send,
                             reply_markup=keyboard)
        ctx.user_data["state"] = "weekends_choosing"
    elif msg == holidays_btn:
        keyboard = ReplyKeyboardMarkup(HOLIDAYS_MENU, resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id,
                             text=holidays_menu_nav_msg,
                             reply_markup=keyboard)

        return "holidays_menu"


def certificates_admin(update, ctx):
    msg = update.message.text
    if msg == back_to_menu_btn:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=main_menu_comeback_msg,
                             reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
        return 'menu'
    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=pass_message)
    return 'certificates'


def all_the_callback(update, ctx):
    query = update.callback_query
    data = query.data
    if data == "pass":
        return
    elif ctx.user_data["state"] == "month_choosing":
        month = int(data)
        year = CalendarCog().get_year(month)
        days_keyboard = InlineKeyboardMarkup(get_days_keys(year, month,
                                                           do_timetable_settings=ctx.user_data["make_an_appointment"],
                                                           timetable_settings=ctx.user_data["timetable_settings"]))
        query.edit_message_text(text=f"Вы {month_abbr_ru[month]} выбрали.",
                                reply_markup=days_keyboard)
        ctx.user_data["date_of_appointment"].extend([year, month])
        ctx.user_data["state"] = "day_choosing"

    elif ctx.user_data["state"] == "day_choosing":
        day = int(data)
        ctx.user_data["date_of_appointment"].append(day)
        keyboard = ReplyKeyboardMarkup(CalendarCog().get_hours_keyboard(
            begin=ctx.user_data["timetable_settings"]["working_hours"]["begin"],
            end=ctx.user_data["timetable_settings"]["working_hours"]["end"]
        ), resize_keyboard=True)
        formatting_date = CalendarCog().chosen_date_formatting(ctx.user_data["date_of_appointment"])
        query.edit_message_text(text=f"Выбрана дата: {formatting_date}",
                                parse_mode=ParseMode.MARKDOWN)
        if ctx.user_data["make_an_appointment"]:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Выберите время",
                                 reply_markup=keyboard)
        elif ctx.user_data["choose_holidays"][1]:
            ctx.user_data["choose_holidays"][1] = False
            ctx.user_data["choose_holidays"][2] = True
            ctx.user_data["choose_holidays"]["first_date"] = '-'.join(
                [str(i) for i in ctx.user_data["date_of_appointment"]])
            calendar_build(update, ctx, entry_state="month")
        elif ctx.user_data["choose_holidays"][2]:
            ctx.user_data["choose_holidays"][2] = False
            ctx.user_data["choose_holidays"]["second_date"] = '-'.join(
                [str(i) for i in ctx.user_data["date_of_appointment"]])
            first_date = ctx.user_data["choose_holidays"]["first_date"]
            second_date = ctx.user_data["choose_holidays"]["second_date"]
            f_year, f_month, f_day = map(int, first_date.split("-"))
            s_year, s_month, s_day = map(int, second_date.split("-"))
            f_timedelta = datetime.date(year=f_year, month=f_month, day=f_day)
            s_timedelta = datetime.date(year=s_year, month=s_month, day=s_day)
            if f_timedelta > s_timedelta:
                ctx.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Вы выбрали некорректную дату отпуска (с {first_date} по {second_date})."
                                          f" Дата начала отпуска должна быть раньше даты конца отпуска.")
                return
            queries.set_holidays(db_connect(), first_date, second_date)
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Вы выбрали период нерабочих дней (с {first_date} по {second_date}) "
                                      f"в течении которых клиенты не смогут записаться к вам.")

    elif ctx.user_data["state"] == "weekends_choosing":
        if data == back_btn:
            query.delete_message()
            ctx.user_data["state"] = "online_appointment_settings"
            ctx.bot.send_message(chat_id=update.effective_chat.id,
                                 text=timetable_editor_comeback_msg,
                                 reply_markup=ReplyKeyboardMarkup(ONLINE_TIMETABLE_SETTINGS, resize_keyboard=True))
            return 'online_appointment_settings'
        values = queries.set_days_off(db_connect(), data)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data=i) for i in weekdays_header_ru],
                                         [InlineKeyboardButton(close_btn, callback_data=back_btn)]])
        days_off = [weekdays_header_ru[i] for i in range(len(weekdays_header_ru)) if values[i] == 1]

        if not len(days_off):
            msg_to_send = f"Выберите нерабочие дни. На данный момент вы работаете без выходных."
        elif len(days_off) == 7:
            msg_to_send = f"Уберите нерабочии дни. На данный момент к вам нельзя записаться, т.к. " \
                          f"вы указали все дни недели нерабочими"
        else:
            msg_to_send = f"Выберите/Уберите нерабочие дни. ({', '.join(days_off)})"
        query.edit_message_text(text=msg_to_send,
                                reply_markup=keyboard)

    if data == "укладка":
        price_info = ctx.user_data["price_info"]
        # print(f"{price_info[data]['img']}\n")  # картинка
        query.edit_message_text(text=f"Раздел: {price_info[data]['title']} Цена: {price_info[data]['price']}\n"
                                     f"{price_info[data]['description']}")
    elif data == "чистка":
        price_info = ctx.user_data["price_info"]
        query.edit_message_text(text=f"Раздел: {price_info[data]['title']} Цена: {price_info[data]['price']}\n"
                                     f"{price_info[data]['description']}")


def yes_no_handler(update, ctx):
    msg = update.message.text
    return "menu"


def finishing_handler(update, ctx):
    msg = update.message.text
    if ctx.user_data["state"] == "text_editor_menu":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=main_menu_comeback_msg,
                             reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
        return 'menu'
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=main_menu_comeback_msg,
                         reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
    return 'menu'


def stop(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=conv_handler_stop_msg,
                         reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def unknown(update, ctx):
    """unknown command chat-passing"""
    pass


start_handler = CommandHandler("start", start)
stop_handler = CommandHandler("stop", stop)
unknown_handler = MessageHandler(Filters.command, unknown)

all_the_callback_handler = CallbackQueryHandler(callback=all_the_callback)

main_menu_conv_handler = ConversationHandler(
    entry_points=[start_handler],
    states={
        "menu": [MessageHandler(
            Filters.regex(
                f'^({online_timetable_btn}|{certificates_btn}|'
                f'{offers_sending_btn}|{price_btn}|{all_the_text_editor_btn})$')
            & (~Filters.command), menu)],
        "online_appointment": [
            MessageHandler(Filters.regex(f'^({settings_btn}|{check_appointments_btn}|{back_to_menu_btn})$')
                           & (~Filters.command), online_appointment),
            MessageHandler(Filters.regex(
                f'^({make_appointment_btn}|{appointment_info_btn}|{cancel_appointment_btn}|{back_to_menu_btn})$'),
                online_appointment)],
        "text_editor_menu": [
            MessageHandler(Filters.regex(
                f'^({default_text_modes_menu_btn}|{get_texts_list_btn}|{back_btn})$')
                           & (~Filters.command), text_editor_menu)],

        "certificates": [

            MessageHandler(Filters.regex(
                f'^(Добавление позиции|Изменение позиции|Удаление позиции|Просмотр позиций|{back_to_menu_btn})$')
                           & (~Filters.command), certificates_admin)],
        "yes_no_handler": [
            MessageHandler(Filters.text & (~Filters.command), yes_no_handler)
        ],
        "finishing_handler": [MessageHandler(Filters.text & (~Filters.command), finishing_handler)],

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
        ],
        "timetable_duration_choosing": [
            MessageHandler(Filters.text & (~Filters.command), timetable_duration_choosing)
        ],
        "holidays_menu": [
            MessageHandler(Filters.text & (~Filters.command), holidays_menu)
        ],
        "set_new_text_handler": [
            MessageHandler(Filters.command, set_new_text_handler)
        ],
        "set_replica_handler": [
            MessageHandler(Filters.text & (~Filters.command), set_new_replica_text)
        ]
    },
    fallbacks=[start_handler],
)

updater = Updater(token=environ.get('BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher

timetable_connect(updater)
# calendar_connect(updater)
dispatcher.add_handler(main_menu_conv_handler)

dispatcher.add_handler(all_the_callback_handler)
dispatcher.add_handler(CallbackQueryHandler(callback=keyboard_callback_handler, pass_chat_data=True))

dispatcher.add_handler(unknown_handler)

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
    # updater.job_queue.start()
