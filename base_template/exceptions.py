# Тут необходимо будет прописать декораторы, которые будут обрабатывать непродуманные сценарии,
# например прерывать диалог, когда пользователь уходит из него коммандой /start к примеру.

def only_after_today(func):
    """тупое говно, которое надо заменить вдальнейшем проверкой на табличные значения представленные клавиатурой"""
    def checking(update, ctx):
        import datetime
        msg = update.message.text
        try:
            if int(msg) <= 0 or int(msg) >= 32:
                raise IndexError
            if int(msg) <= datetime.date.today().day:  # проверка на то чтобы запись была доступна только с завтра.
                ctx.user_data["date_of_appointment"][0] += 1
        except Exception as ex:
            print("Проверка на ввод конкретного дня:", ex)
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка ввода, повторите попытку.")
            return "day_choosing"
        func(update, ctx)
        return "time_choosing"

    return checking


def only_table_values(func, collection):

    def checking(update, ctx):
        msg = update.message.text
        if msg not in [i[0] for i in collection]:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка ввода, повторите попытку.")
            return "time_choosing"
        func(update, ctx)

    return checking
