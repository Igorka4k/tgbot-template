# main menu
from functions.timetable.tools import CalendarCog
from base_template.db.queries import get_working_hours, get_dates_between_range
from functions.timetable.tools import db_connect
from base_template.context import *

MAIN_MENU_KEYBOARD__user = [[online_timetable_btn],
                            [price_btn]]

MAIN_MENU_KEYBOARD__admin = [[online_timetable_btn],
                             [price_btn],
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

ONLINE_TIMETABLE_SETTINGS = [[timetable_range_btn, weekends_btn, holidays_btn],
                             [working_hours_btn, dates_between_range_btn],
                             [back_btn]]


def online_timetable_hours():
    working_hours = get_working_hours(db_connect())
    between_range = get_dates_between_range(db_connect())
    ONLINE_TIMETABLE_HOURS = CalendarCog().get_hours_keyboard(  # пока не используется
        begin=working_hours['begin'],
        end=working_hours['end'],
        between_range=between_range)
    return ONLINE_TIMETABLE_HOURS


TIMETABLE_HOURS_ADMIN1 = CalendarCog().get_hours_keyboard(
    begin="00:00",
    end="23:59",
    between_range=30
)

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
