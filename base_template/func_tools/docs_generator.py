from base_template.bot import dispatcher
from telegram.ext import ConversationHandler, CommandHandler
import json

commands = []
JSON_PATH = "../data/command_list.json"


def cmd_confirm(cmd):
    if cmd in existing_commands:
        return True
    confirm = input(f"Добавить команду {cmd} в command_list? (y/n)\n")
    while confirm.lower() != "y" and confirm.lower() != "n":
        print(".!. please use (y/n) .!.")
        confirm = input(f"Добавить команду {cmd} в command_list? (y/n)\n")
    if confirm.lower() == "y":
        return True
    return False  # in case response = "n"


with open(JSON_PATH, "r", encoding="utf-8") as file:
    existing_commands = [i for i in json.load(file).keys()]
    # print(existing_commands)

for val in dispatcher.handlers.values():
    for handler in val:
        if isinstance(handler, ConversationHandler):
            for entry_point in handler.entry_points:
                if isinstance(entry_point, CommandHandler):
                    cmd = entry_point.command[0]
                    if cmd_confirm(cmd):
                        commands.append(cmd)
            continue
        elif isinstance(handler, CommandHandler):
            cmd = handler.command[0]
            if cmd_confirm(cmd):
                commands.append(cmd)
            continue

dictionary = {key: "command_description_here" for key in commands}  # dictionary formatting

with open(JSON_PATH, "w", encoding="utf-8") as file:
    json.dump(dictionary, file, indent=4, ensure_ascii=False)
