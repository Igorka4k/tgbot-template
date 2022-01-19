from base_template.bot import *

start_handler = CommandHandler("start", start)
stop_handler = CommandHandler("stop", stop)
unknown_handler = MessageHandler(Filters.command, unknown)

all_the_callback_handler = CallbackQueryHandler(callback=all_the_callback)

main_menu_conv_handler = ConversationHandler(
    entry_points=[start_handler],
    states={
        "menu": [MessageHandler(
            Filters.regex(
                f'^({online_timetable_btn}|{certificates_btn}|'
                f'{offers_sending_btn}|{price_btn}|{all_the_text_editor_btn})$')
            & (~Filters.command), menu)],
        "online_appointment": [
            MessageHandler(Filters.regex(f'^({settings_btn}|{check_appointments_btn}|{back_to_menu_btn})$')
                           & (~Filters.command), online_appointment),
            MessageHandler(Filters.regex(
                f'^({make_appointment_btn}|{appointment_info_btn}|{cancel_appointment_btn}|{back_to_menu_btn})$'),
                online_appointment)],
        "text_editor_menu": [
            MessageHandler(Filters.regex(
                f'^({default_text_modes_menu_btn}|{get_texts_list_btn}|{back_btn})$')
                           & (~Filters.command), text_editor_menu)],

        "certificates": [

            MessageHandler(Filters.regex(
                f'^(Добавление позиции|Изменение позиции|Удаление позиции|Просмотр позиций|{back_to_menu_btn})$')
                           & (~Filters.command), certificates_admin)],
        "yes_no_handler": [
            MessageHandler(Filters.text & (~Filters.command), yes_no_handler)
        ],
        "finishing_handler": [MessageHandler(Filters.text & (~Filters.command), finishing_handler)],

        # below the handlers, that make an appointment:
        "month_choosing": [MessageHandler(Filters.text & (~Filters.command), month_choosing)],
        "day_choosing": [MessageHandler(Filters.text & (~Filters.command), day_choosing)],
        "time_choosing": [MessageHandler(Filters.text & (~Filters.command), time_choosing)],

        # below the online_appointment_settings handlers:
        "online_appointment_settings": [MessageHandler(Filters.text & (~Filters.command),
                                                       online_appointment_settings)],
        "work_begin_hours_choosing": [
            MessageHandler(Filters.text & (~Filters.command), work_begin_hours_choosing)],
        "work_end_hours_choosing": [
            MessageHandler(Filters.text & (~Filters.command), work_end_hours_choosing)
        ],
        "timetable_duration_choosing": [
            MessageHandler(Filters.text & (~Filters.command), timetable_duration_choosing)
        ],
        "holidays_menu": [
            MessageHandler(Filters.text & (~Filters.command), holidays_menu)
        ],
        "dates_between_range": [
            MessageHandler(Filters.text & (~Filters.command), dates_between_range)
        ],
        "set_new_text_handler": [
            MessageHandler(Filters.command, set_new_text_handler)
        ],
        "set_replica_handler": [
            MessageHandler(Filters.text & (~Filters.command), set_new_replica_text)
        ],

        "check_price_list": [
            MessageHandler(Filters.text & (~Filters.command), check_price_list)
        ]
    },
    fallbacks=[start_handler],
)

updater = Updater(token=environ.get('BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher

timetable_connect(updater)
# calendar_connect(updater)
dispatcher.add_handler(main_menu_conv_handler)

dispatcher.add_handler(all_the_callback_handler)
dispatcher.add_handler(CallbackQueryHandler(callback=keyboard_callback_handler, pass_chat_data=True))

dispatcher.add_handler(unknown_handler)
if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
    # updater.job_queue.start()
