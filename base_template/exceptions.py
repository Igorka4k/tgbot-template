# Тут необходимо будет прописать декораторы, которые будут обрабатывать непродуманные сценарии,
# например прерывать диалог, когда пользователь уходит из него коммандой /start к примеру.


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
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка, выберите предложенный вариант.")
            return "day_choosing"
        return func(update, ctx)

    def time_type(update, ctx):
        msg = update.message.text.lower()
        if msg not in [i[0].lower() for i in collection]:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка, выберите предложенный вариант.")
            return "time_choosing"
        return func(update, ctx)

    def month_type(update, ctx):
        msg = update.message.text.lower()
        if msg not in [i[0].lower() for i in collection]:
            ctx.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка, выберите предложенный вариант.")
            return "month_choosing"
        return func(update, ctx)

    # type checking
    if keyboard_type == "day":
        return day_type
    if keyboard_type == "time":
        return time_type
    if keyboard_type == "month":
        return month_type
