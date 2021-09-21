from config import *
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, ConversationHandler

updater = Updater(token=TOKEN, use_context=True)  # bot create.



def start(update, ctx):
    """greeting"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Salamaleykum")


def command_list(update, ctx):
    """help command list"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Тут будет список команд.")


def first_question(update, ctx):
    """dialog function"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Can we talk? (yes/no)")
    return 1


def second_question(update, ctx):
    """dialog function"""
    response = update.message.text
    ctx.user_data["response1"] = response  # important data saving
    if response.lower() == "yes":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="How are you? (yes/no)")
        return 2
    elif response.lower() == "no":
        ctx.bot.send_message(chat_id=update.effective_chat.id, text="bruh, bye")
        return ConversationHandler.END
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="send yes/no next time")
    return ConversationHandler.END


def dialog_ending(update, ctx):
    """last bot message in the dialog"""
    response = update.message.text
    ctx.user_data["response2"] = response
    ctx.bot.send_message(chat_id=update.effective_chat.id, text=f"I`m {ctx.user_data['response2']} too.")
    return ConversationHandler.END


def stop(update, ctx):
    """dialog breaking"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Диалог прерван.")
    return ConversationHandler.END


def unknown(update, ctx):
    """unknown command chat-exception"""
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Неизвестная команда, пропишите /command_list")


dispatcher = updater.dispatcher  # dispatcher object, which manages all the handlers and something..

# Handlers
start_handler = CommandHandler("start", start)
command_list_handler = CommandHandler("command_list", command_list)
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("send_hi", start)],
    states={
        1: [MessageHandler(Filters.text, first_question)],
        2: [MessageHandler(Filters.text, second_question)]
    },
    fallbacks=[CommandHandler("stop", stop)]
)

unknown_handler = MessageHandler(Filters.command, unknown)

# Dispatcher adding
dispatcher.add_handler(start_handler)
dispatcher.add_handler(command_list_handler)
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(unknown_handler)
dispatcher.add_handler(CommandHandler("stop", stop))

updater.start_polling()
