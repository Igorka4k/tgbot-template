from os import environ, path
from dotenv import load_dotenv
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters, Updater, CallbackQueryHandler
from telegram import *

from functions.payments.example import keyboard_callback_handler, show_carousel
from functions.timetable.tools import db_connect
from functions.timetable.db import queries

from base_template.keyboards import INVOICE_EDITOR_KEYBOARD, MAIN_MENU_KEYBOARD__admin, MAIN_MENU_KEYBOARD__user

if path.exists('../.env'):  # Переменные окружения хранятся в основной директории проекта
    load_dotenv('../.env')
else:
    raise ImportError("Can't import environment variables")

ADMIN_CHAT = list(map(int, environ.get('ADMIN_CHAT').split(',')))


def start(update, ctx):
    ctx.user_data["is_authorized"] = True
    ctx.user_data["username"] = update.message.from_user["username"]
    ctx.user_data["is_admin"] = True if update.effective_chat.id in ADMIN_CHAT else False
    if update.message.from_user["full_name"] is None:
        ctx.user_data["full_name"] = "Аноним"
    else:
        ctx.user_data["full_name"] = update.message.from_user["full_name"]

    connection = db_connect()

    text = ""

    if not queries.is_authorized(connection, update.message.from_user["username"]):
        queries.new_user_adding(connection, ctx.user_data["full_name"], ctx.user_data["username"])
        text += "Добро пожаловать к нам в бота!!!\n"
    else:
        text += "Вы уже авторизованы, я вас запомнил.\n"
    text += "Вы находитесь в главном меню."

    if ctx.user_data["is_admin"]:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(
            MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(
            MAIN_MENU_KEYBOARD__user, resize_keyboard=True))

    return 'menu'


def menu(update, ctx):
    msg = update.message.text

    if msg == "Онлайн-запись":
        if ctx.user_data["is_admin"]:
            pass
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Онлайн-запись (answer)",
                             reply_markup=ReplyKeyboardMarkup([["Заглушка", "Заглушка"],
                                                               ["<< Назад в меню"]], resize_keyboard=True))
        return 'online_appointment'

    if msg == "Сертификаты":
        if ctx.user_data["is_admin"]:
            ctx.bot.send_message(chat_id=update.message.chat_id,
                                 text="Добро пожаловать в редактор витрины Вашего магазина!\n\n"
                                      "Выберите один из вариантов ниже.",
                                 reply_markup=ReplyKeyboardMarkup(INVOICE_EDITOR_KEYBOARD,
                                                                  resize_keyboard=True))
            return 'certificates'
        else:
            ctx.bot.send_message(chat_id=update.message.chat_id,
                                 text="Добро пожаловать в наш магазин сертификатов!\n\nНаши товары:",
                                 reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__user, resize_keyboard=True))

            show_carousel(update, ctx)
            return 'menu'

    if msg == "Рассылка спец. предложений":
        if ctx.user_data["is_admin"]:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Pass")
            return 'menu'
    return 'menu'


def online_appointment(update, ctx):
    msg = update.message.text
    if msg == "<< Назад в меню":

        if ctx.user_data["is_admin"]:
            keyboard = MAIN_MENU_KEYBOARD__admin
        else:
            keyboard = MAIN_MENU_KEYBOARD__user

        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в главное меню.",
                             reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return 'menu'

    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Это заглушка, еблан.")

    return 'online_appointment'


def certificates_admin(update, ctx):
    msg = update.message.text
    if msg == "<< Назад в меню":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Вы вернулись в главное меню.",
                             reply_markup=ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD__admin, resize_keyboard=True))
        return 'menu'
    else:
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="Сюда функционал ещё не завезли")
    return 'certificates'


def stop(update, ctx):
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Stopped", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def unknown(update, ctx):
    """unknown command chat-exception"""
    # ctx.bot.send_message(chat_id=update.effective_chat.id, text="Неизвестная команда, нажмите сюда ==> /help")
    """Ignoring"""
    pass


start_handler = CommandHandler("start", start)
stop_handler = CommandHandler("stop", stop)
unknown_handler = MessageHandler(Filters.command, unknown)

main_menu_conv_handler = ConversationHandler(
    entry_points=[start_handler],
    states={
        "menu": [MessageHandler(
            Filters.regex('^(Онлайн-запись|Сертификаты|Рассылка спец. предложений)$') & (~Filters.command), menu)],
        "online_appointment": [
            MessageHandler(Filters.regex('^(Заглушка|<< Назад в меню)$') & (~Filters.command), online_appointment)],
        "certificates": [

            MessageHandler(Filters.regex(
                '^(Добавление позиции|Изменение позиции|Удаление позиции|Просмотр позиций|<< Назад в меню)$')
                           & (~Filters.command), certificates_admin)

        ]
    },
    fallbacks=[stop_handler]
)

updater = Updater(token=environ.get('BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(main_menu_conv_handler)

dispatcher.add_handler(CallbackQueryHandler(callback=keyboard_callback_handler, pass_chat_data=True))

dispatcher.add_handler(unknown_handler)

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
