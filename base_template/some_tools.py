from telegram.ext import CommandHandler


def get_texts_list(dispatcher, ctx=None, formatting_to_text=False, just_adding_to_handler=False):
    """reads context.py file"""
    with open("context.py", "r", encoding="utf-8") as file:
        data = list(filter(lambda x: "#" not in x and len(x.strip()), file.readlines()))
        ans = []
        for elem in data:
            try:
                command = elem.split(' = ')[0]
                text = elem.split(' = ')[1]
                if just_adding_to_handler:
                    # dispatcher.add_handler(CommandHandler(command, handler))
                    pass
                    continue
                ans.append("/" + command + " - " + text)
            except Exception as ex:
                print(ex)
                ans.append(elem)
        if just_adding_to_handler:
            return
        ctx.user_data["texts_replicas"] = ans[:]
        if formatting_to_text:
            return "\n".join([f"{i[0]}. {i[1]}" for i in enumerate(ans, 1)])
        return enumerate(ans, 1)


def set_new_text_handler(update, ctx):
    msg = update.message.text[1:]
    texts_list = ctx.user_data["texts_replicas"]
    chosen_ind = [i.split(" - ")[0][1:] for i in texts_list].index(msg)
    chosen_msg = texts_list[chosen_ind].split(" - ")[0][1:]
    chosen_replica = texts_list[chosen_ind]
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Отправьте новый текст для выбранной реплики.")
    ctx.user_data["editing_replica"] = [chosen_msg, chosen_ind, chosen_replica]
    return "set_replica_handler"


def change_context(new_replica, ctx):
    chosen_msg, chosen_ind, chosen_replica = ctx.user_data["editing_replica"]
    with open("context.py", "r", encoding="utf-8") as file:
        file_rows = file.readlines()
        for i in range(len(file_rows)):
            elem = file_rows[i].strip()
            if elem == chosen_replica:
                # ctx.user_data["editing_replica"] = chosen_msg, i, chosen_replica
                command = chosen_replica.split(" = ")[0]
                file_rows[i] = command + " = " + f'"{chosen_msg}"'
                print("redacted:", command + " = " + f'"{chosen_msg}"')
                print("\n".join(file_rows))
                break

    with open("new_test_file.py", "w", encoding="utf-8") as file:
        file.write("\n".join(file_rows))
    pass


def set_new_replica_text(update, ctx):
    msg = update.message.text
    chosen = ctx.user_data["editing_replica"]
    change_context(msg, ctx)
    ctx.bot.send_message(chat_id=update.effective_chat.id, text="Новый текст для реплики установлен.\n"
                                                                "Нажмите ещё раз для повторного редактирования.")
    return "set_new_text_handler"




