# main menu
from functions.timetable.tools import CalendarCog
# from db.queries import *
from context import *

MAIN_MENU_KEYBOARD__user = [[online_timetable_btn],
                            [price_btn],
                            [certificates_btn]]

MAIN_MENU_KEYBOARD__admin = [[online_timetable_btn],
                             [price_btn],
                             [certificates_btn],
                             [offers_sending_btn]]
# [all_the_text_editor_btn]]

INVOICE_EDITOR_KEYBOARD = [["Добавление позиции", "Изменение позиции", "Удаление позиции"],
                           ["Просмотр позиций", back_to_menu_btn]]

# online-appointments
MONTH_CHOOSING_KEYBOARD = [["(текущий месяц)"], ["январь"], ["февраль"], ["март"], ["апрель"],
                           ["май"], ["июнь"], ["июль"], ["август"],
                           ["сентябрь"], ["октябрь"], ["ноябрь"], ["декабрь"], [back_to_menu_btn]]

ONLINE_TIMETABLE_admin_menu = [[check_appointments_btn], [settings_btn], [back_to_menu_btn]]

ONLINE_TIMETABLE_user_menu = [[make_appointment_btn], [appointment_info_btn, cancel_appointment_btn],
                              [back_to_menu_btn]]

ONLINE_TIMETABLE_SETTINGS = [[timetable_range_btn, working_hours_btn, weekends_btn, holidays_btn],
                             [back_btn]]

# working_hours = queries.get_working_hours(db_connect())
# print(working_hours)
ONLINE_TIMETABLE_HOURS = CalendarCog().get_hours_keyboard(
    "00:00", "23:59"
)
print("-")
print(ONLINE_TIMETABLE_HOURS)
print("0")

TIMETABLE_DURATION = [[week_range_btn], [one_month_range_btn], [three_month_range_btn], [year_range_btn], [back_btn]]

HOLIDAYS_MENU = [[holidays_menu_set_btn], [holidays_menu_info_btn, holidays_menu_cancel_btn], [back_btn]]

ALL_THE_TEXT_EDITOR_MENU = [[default_text_modes_menu_btn,
                             get_texts_list_btn],
                            [back_btn]]

# Служебные клавы
PASS_KEYBOARD = [[pass_btn, pass_btn], [back_to_menu_btn]]
CANCEL_KEYBOARD = [[back_to_menu_btn]]
FINISH_KEYBOARD = [[finish_btn]]
YES_NO_KEYBOARD = [[agreement_btn, disagreement_btn]]
