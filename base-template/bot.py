from config import *
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

updater = Updater(token=TOKEN, use_context=True)  # bot create.


def start(update, ctx):
    """greeting"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Salamaleykum")


def start_dialog(update, ctx):
    """dialog beginning"""
    buttons = [[KeyboardButton(text="something.")]]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Alright, write me smth..", reply_markup=keyboard)
    return 1


def command_list(update, ctx):
    """help command list"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Тут будет список команд.")


def first_question(update, ctx):
    """dialog function"""
    buttons = [[KeyboardButton(text="yes"), KeyboardButton(text="no")]]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Can we talk? (yes/no)", reply_markup=keyboard)
    return 2


def second_question(update, ctx):
    """dialog function"""
    response = update.message.text
    ctx.user_data["response1"] = response  # important data saving
    if response.lower() == "yes":
        buttons = [[KeyboardButton(text="fine"), KeyboardButton(text="worse")]]
        keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="How are you? (fine/worse)", reply_markup=keyboard)
        return 3
    elif response.lower() == "no":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="bruh, bye",
                             reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return stop(update, ctx)


def dialog_ending(update, ctx):
    """last bot message in the dialog"""
    response = update.message.text
    if response not in ["fine", "worse"]:
        return stop(update, ctx)
    ctx.user_data["response2"] = response
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"I`m {ctx.user_data['response2']} too.",
                         reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def stop(update, ctx):
    """dialog breaking"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Диалог прерван.",
                         reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def unknown(update, ctx):
    """unknown command chat-exception"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Неизвестная команда, пропишите /command_list")


dispatcher = updater.dispatcher  # dispatcher object, which manages all the handlers and something..

# Handlers
start_handler = CommandHandler("start", start, pass_user_data=True)
command_list_handler = CommandHandler("command_list", command_list)
stop_handler = CommandHandler("stop", stop)
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("go", start_dialog)],
    states={
        1: [MessageHandler(Filters.text, first_question)],
        2: [MessageHandler(Filters.text, second_question)],
        3: [MessageHandler(Filters.text, dialog_ending)]
    },
    fallbacks=[stop_handler]
)

unknown_handler = MessageHandler(Filters.command, unknown)

# Dispatcher adding
dispatcher.add_handler(start_handler)
dispatcher.add_handler(command_list_handler)
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(stop_handler)

dispatcher.add_handler(unknown_handler)

updater.start_polling()
