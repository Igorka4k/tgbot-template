"""Basic example for a bot that can receive payment from user."""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import Update
from telegram import LabeledPrice

from telegram.ext import CommandHandler, PreCheckoutQueryHandler, CallbackQueryHandler
from telegram.ext import CallbackContext
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

from os import environ

from base_template.keyboards import INVOICE_EDITOR_KEYBOARD

BACK = '<<'
FORWARD = '>>'
MORE = 'Подробнее'

INVOICE_BACK = '<<<'
INVOICE_FORWARD = '>>>'
DELETE = 'Удалить'
EDIT = 'Изменить'


def get_data():
    """return data from somewhere"""
    # return ['1/4', '2/4', '3/4', '4/4']
    # return ['1/4']
    return []


data = get_data()


def generate_keyboard():
    return [[InlineKeyboardButton(BACK, callback_data=BACK),
             InlineKeyboardButton(MORE, callback_data=MORE),
             InlineKeyboardButton(FORWARD, callback_data=FORWARD)]]


def generate_invoice_keyboard():
    return [[InlineKeyboardButton(BACK, callback_data=INVOICE_BACK),
             InlineKeyboardButton(EDIT, callback_data=EDIT),
             InlineKeyboardButton(DELETE, callback_data=DELETE),
             InlineKeyboardButton(INVOICE_FORWARD, callback_data=INVOICE_FORWARD)]]


def start(update: Update, ctx: CallbackContext) -> None:
    update.message.reply_text("Купить сертификат /buy\n"
                              "Посмотреть все товары /carousel")


def show_carousel(update: Update, ctx: CallbackContext) -> None:
    """Показывает "карусель" с определённым индексом"""
    if "carousel_index" not in ctx.user_data:
        ctx.user_data["carousel_index"] = 0
    chat_id = update.message.chat_id

    if len(data) == 0:
        ctx.bot.send_message(chat_id=chat_id,
                             text="Товары в магазине закончились. Ждём новых поставок.\n"
                                  "Просим прощения за предоставленные неудобства.")
        return

    index = ctx.user_data["carousel_index"] % len(data)

    if len(data) == 1:
        ctx.bot.send_message(chat_id=chat_id, text=str(data[index]),
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(MORE, callback_data=MORE)]],
                                                               resize_keyboard=True))
    else:
        ctx.bot.send_message(chat_id=chat_id, text=str(data[index]),
                             reply_markup=InlineKeyboardMarkup(generate_keyboard(),
                                                               resize_keyboard=True))


def keyboard_callback_handler(update: Update, ctx: CallbackContext) -> None:
    """обработка коллбеков копок"""
    query = update.callback_query
    query_data = query.data

    if "carousel_index" not in ctx.user_data:
        ctx.user_data["carousel_index"] = 0

    if query_data == MORE:
        query.delete_message()
        create_invoice(update, ctx, query.message.chat_id)

    elif query_data == FORWARD:
        ctx.user_data["carousel_index"] += 1
        ctx.user_data["carousel_index"] %= len(data)
        query.edit_message_text(text=str(data[ctx.user_data["carousel_index"]]),
                                reply_markup=InlineKeyboardMarkup(generate_keyboard()))

    elif query_data == BACK:
        ctx.user_data["carousel_index"] -= 1
        ctx.user_data["carousel_index"] %= len(data)
        query.edit_message_text(text=str(data[ctx.user_data["carousel_index"]]),
                                reply_markup=InlineKeyboardMarkup(generate_keyboard()))

    elif query_data == INVOICE_FORWARD:
        ctx.user_data["carousel_index"] += 1
        ctx.user_data["carousel_index"] %= len(data)
        query.edit_message_text(text=str(data[ctx.user_data["carousel_index"]]),
                                reply_markup=InlineKeyboardMarkup(generate_invoice_keyboard()))

    elif query_data == INVOICE_BACK:
        ctx.user_data["carousel_index"] -= 1
        ctx.user_data["carousel_index"] %= len(data)
        query.edit_message_text(text=str(data[ctx.user_data["carousel_index"]]),
                                reply_markup=InlineKeyboardMarkup(generate_invoice_keyboard()))

    elif query_data == DELETE:
        query.delete_message()
        create_invoice(update, ctx, query.message.chat_id)

    elif query_data == EDIT:
        query.delete_message()
        create_invoice(update, ctx, query.message.chat_id)


def create_invoice(update: Update, ctx: CallbackContext, chat_id=None) -> None:
    """Sends an invoice"""
    if chat_id is None:
        chat_id = update.message.chat_id
    title = "Это тестовый платёж (ВВОДИТЕ ТОЛ"
    description = "Это тестовый платёж (ВВОДИТЕ ТОЛЬКО ТЕСТОВЫЕ ДАННЫЕ)" \
                  " 294860836708367846823864807086780208687020867280473067880" \
                  "36702360872807438067082687087234688236702846708247680246708827" \
                  "6807248028046702867 qeribnaobniaosrnbaiwrbnjrisnbirpsnbonnirrbihn" \
                  "RKBHHwourhboHRWBUO"
    print(description.__len__(), title.__len__())
    payload = "Оплата через бота №XXX"
    provider_token = environ.get('BOT_PAYMENT_TOKEN')
    currency = "RUB"
    price = 1000000
    prices = [LabeledPrice("Сертификат", price * 100)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    ctx.bot.send_invoice(
        chat_id,
        title,
        description,
        payload,
        provider_token,
        currency,
        prices,
        need_name=True,
        need_phone_number=True
    )


def precheckout_callback(update: Update, ctx: CallbackContext) -> None:
    query = update.pre_checkout_query
    if query.invoice_payload != "Оплата через бота №XXX":
        query.answer(ok=False, error_message="Кажется, что-то пошло не так...")
        update.message.reply_text("Возникла ошибка при выполнении платежа.\n"
                                  "Техническая поддержка: +79123456789")
    else:
        query.answer(ok=True)


def successful_payment_callback(update: Update, ctx: CallbackContext) -> None:
    update.message.reply_text("Благодарим за покупку!")


def payment_connect(updater: Updater) -> None:
    """Adds required handlers"""
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("buy", create_invoice))
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))


def pay_carousel_connect(updater: Updater) -> None:
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("carousel", show_carousel))
    dispatcher.add_handler(CallbackQueryHandler(callback=keyboard_callback_handler, pass_chat_data=True))


def carousel_editor_welcome(update: Update, ctx: CallbackContext):
    ctx.bot.send_message(chat_id=update.message.chat_id, text="Добро пожаловать в редактор витрины Вашего магазина!\n\n"
                                                              "Выберите один из вариантов ниже.",
                         reply_markup=ReplyKeyboardMarkup(INVOICE_EDITOR_KEYBOARD,
                                                          resize_keyboard=True))
    return 'test'


def invoice_editor_message_handler(update: Update, ctx: CallbackContext):
    msg = update.message.text
    chat_id = update.message.chat_id

    if ctx.user_data["is_admin"]:
        if msg == "Просмотр позиций (в режиме редактора)":
            ctx.bot.send_message(chat_id=chat_id, text="Просмотр позиций (в режиме редактора)")
            return 'test'
        if msg == "Добавление позиции":
            ctx.bot.send_message(chat_id=chat_id, text="Добавление позиции")
        if msg == "Изменение позиции":
            ctx.bot.send_message(chat_id=chat_id, text="Редактирование позиции")
        if msg == "Удаление позиции":
            ctx.bot.send_message(chat_id=chat_id, text="Удаление позиции")


def main() -> None:
    updater = Updater(environ.get('BOT_TOKEN'))
    updater.dispatcher.add_handler(CommandHandler("start", start))
    payment_connect(updater)
    pay_carousel_connect(updater)
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
