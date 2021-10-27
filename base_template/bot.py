from os import environ, path
from dotenv import load_dotenv

from base_template.constants import *
from base_template.keyboards import *
from base_template.exceptions import *

from functions.timetable.tools import CalendarCog
from functions.timetable.db import queries
from functions.timetable import tools
from functions.payments.example import payment_connect
from functions.timetable.example import timetable_connect, timetable_script_begin
from base_template.exceptions import *
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

import json

if path.exists('../.env'):  # Переменные окружения хранятся в основной директории проекта
    load_dotenv('../.env')
else:
    raise ImportError("Can't import environment variables")

ADMIN_CHAT = list(map(int, environ.get('ADMIN_CHAT').split(',')))

updater = Updater(token=environ.get('BOT_TOKEN'), use_context=True)  # bot create.


def start(update, ctx):
    """greeting"""
    from functions.timetable.tools import db_connect
    # короче надо будет как то сохранить инфу о том кто подписан на бота и проявляет активность,
    # у сущика уже есть идеи, можно побазарить как-нибудь, но пока тока запись о том что пользователь когда-то писал
    # /start, в ctx.user_data:

    # ctx.user_data initialization:
    ctx.user_data["is_authorized"] = True
    ctx.user_data["username"] = update.message.from_user["username"]
    ctx.user_data["is_admin"] = True if update.effective_chat.id in ADMIN_CHAT else False
    if update.message.from_user["full_name"] is None:
        ctx.user_data["full_name"] = "Аноним"
    else:
        ctx.user_data["full_name"] = update.message.from_user["full_name"]

    # authorize check:
    connection = db_connect()
    if not queries.is_authorized(connection, update.message.from_user["username"]):
        queries.new_user_adding(connection, ctx.user_data["full_name"], ctx.user_data["username"])
    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы уже авторизованы.")

    # entry_points пидорас, так как не отлавливает команду start как точку вхождения, юзаем костыль,
    # но это не так критично:
    keyboard = ReplyKeyboardMarkup([["/menu"]], resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Нажмите кнопку ниже для перехода в меню",
                         reply_markup=keyboard)


def menu(update, ctx):
    """main menu"""
    if ctx.user_data["is_admin"]:
        keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True)
    else:
        keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы находитесь в главном меню бота.",
                         reply_markup=keyboard)
    return "service_choosing"


def service_choosing(update, ctx):
    msg = update.message.text

    if ctx.user_data["is_admin"]:
        if msg == "Онлайн-запись":
            keyboard = ReplyKeyboardMarkup([["/timetable"]], resize_keyboard=True)
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Нажмите на кнопку ниже",
                                 reply_markup=keyboard)
            return timetable_script_begin(update, ctx)  # меню админа по онлайн-записям.
        if msg == "Сертификаты (редактирование позиций)":
            return certificate_script(update, ctx)
        if msg == "Рассылка спец. предложений":
            return notifies_script(update, ctx)
        return "service_choosing"

    elif not ctx.user_data["is_admin"]:
        if msg == "Онлайн-запись":
            keyboard = ReplyKeyboardMarkup([["/timetable"]], resize_keyboard=True)
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Нажмите на кнопку ниже",
                                 reply_markup=keyboard)
            return timetable_script_begin(update, ctx)
        if msg == "Сертификаты":
            return certificate_script(update, ctx)


def notifies_script(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Тут можно будет отправить рассылку.")
    return menu(update, ctx)


def certificate_script(update, ctx):
    if ctx.user_data["is_admin"]:
        msg_to_send = "Тут можно будет продать сертификаты."
    else:
        msg_to_send = "Тут можно будет купить сертификаты."
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=msg_to_send)
    return menu(update, ctx)


def command_list(update, ctx):
    """help command list"""
    with open(CMD_LIST_PATH, "r", encoding="utf-8") as file:
        all_the_commands = json.load(file)
        formatting_commands = "\n\n".join([f"/{key} - {val.capitalize()}." for key, val in all_the_commands.items()])
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=formatting_commands)


def stop(update, ctx):
    """dialog breaking"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы принудительно вернулись в главное меню.")
    return ConversationHandler.END


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
        # Main menu:
        "service_choosing": [MessageHandler(Filters.text & (~Filters.command), service_choosing)],
        "certificate_script": [MessageHandler(Filters.text & (~Filters.command), certificate_script)],
        "notifies_script": [MessageHandler(Filters.text & (~Filters.command), notifies_script)],
    },
    fallbacks=[main_menu_handler])

unknown_handler = MessageHandler(Filters.command, unknown)

# Dispatcher adding
# !!!ПРЕВОСХОДСТВО СЛУШАТЕЛЯ ЗАВИСИТ ОТ МОМЕНТА ЕГО ДОБАВЛЕНИЯ В ДИСПЕТЧЕР!!!
# ---1 level---
dispatcher.add_handler(start_handler)
# ---2 level---
dispatcher.add_handler(main_menu_conv_handler)
dispatcher.add_handler(help_handler)

# external modules connection:
payment_connect(updater)
pay_carousel_connect(updater)
timetable_connect(updater)

# ---3 level---
dispatcher.add_handler(unknown_handler)

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
