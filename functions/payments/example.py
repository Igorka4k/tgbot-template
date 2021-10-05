"""Basic example for a bot that can receive payment from user."""

from functions.payments.config import PAYMENT_TOKEN, TOKEN

from telegram import LabeledPrice, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    PreCheckoutQueryHandler,
    CallbackContext, MessageHandler, Filters,
)


def start(update: Update, ctx: CallbackContext) -> None:
    update.message.reply_text("Чтобы купить сертификат нажмите тут --> /buy")


def create_invoice(update: Update, ctx: CallbackContext) -> None:
    """Sends an invoice"""
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


def main() -> None:
    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    payment_connect(updater)
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
