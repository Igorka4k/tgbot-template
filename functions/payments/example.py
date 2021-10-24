"""Basic example for a bot that can receive payment from user."""

from functions.payments.config import PAYMENT_TOKEN, TOKEN

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram import LabeledPrice

from telegram.ext import CommandHandler, PreCheckoutQueryHandler, CallbackQueryHandler
from telegram.ext import CallbackContext
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

BACK = '<<'
FORWARD = '>>'
MORE = 'Подробнее'


def get_data():
    """return data from somewhere"""
    return ['1/4', '2/4', '3/4', '4/4']


data = get_data()


def generate_keyboard():
    return [[InlineKeyboardButton(BACK, callback_data=BACK),
             InlineKeyboardButton(MORE, callback_data=MORE),
             InlineKeyboardButton(FORWARD, callback_data=FORWARD)]]


def start(update: Update, ctx: CallbackContext) -> None:
    update.message.reply_text("Купить сертификат /buy\n"
                              "Посмотреть все товары /carousel")


def show_carousel(update: Update, ctx: CallbackContext) -> None:
    """Показывает "карусель" с определённым индексом"""
    if "carousel_index" not in ctx.user_data:
        ctx.user_data["carousel_index"] = 0
    index = ctx.user_data["carousel_index"] % len(data)
    chat_id = update.message.chat_id
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


def create_invoice(update: Update, ctx: CallbackContext, chat_id=None) -> None:
    """Sends an invoice"""
    if chat_id is None:
        chat_id = update.message.chat_id
    title = "Покупка сертификата"
    description = "Это тестовый платёж (ВВОДИТЕ ТОЛЬКО ТЕСТОВЫЕ ДАННЫЕ)"
    payload = "Оплата через бота №XXX"
    provider_token = PAYMENT_TOKEN
    currency = "RUB"
    price = 100
    prices = [LabeledPrice("Сертификат", price * 499)]

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


def main() -> None:
    updater = Updater(TOKEN)
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
