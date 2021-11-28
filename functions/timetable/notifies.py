import datetime
from functions.timetable.tools import *
from base_template.constants import *


def schedule_notify(update, ctx, when):
    from base_template.bot import updater
    days = get_timedelta(when).days - 1
    notifies_time = datetime.timedelta(days=days, hours=20)
    updater.job_queue.run_once(callback=day_before_notify, when=notifies_time, context={
        "chat_id": "904044654",
        "date_of_appointment": when,
        "notifies_time_first": notifies_time
    })
    print(notifies_time)
    updater.job_queue.start()


def day_before_notify(ctx):
    from base_template.bot import updater
    ctx.bot.send_message(chat_id=ctx.job.context["chat_id"],
                         text=day_before_notify_msg)
    minutes, seconds = ctx.job.context["date_of_appointment"].minutes, ctx.job.context["date_of_appointment"].seconds
    hours = (ctx.job.context["date_of_appointment"] - ctx.job.context["notifies_time_first"]).hours - 2
    print(hours, 'хуй2')
    updater.job_queue.run_once(callback=two_hours_before_notify, when=datetime.timedelta(hours=hours, minutes=minutes,
                                                                                         seconds=seconds),
                               context="904044654")
    updater.job_queue.start()


def two_hours_before_notify(ctx):
    ctx.bot.send_message(chat_id=ctx.job.context,
                         text=two_hours_before_notify_msg)
