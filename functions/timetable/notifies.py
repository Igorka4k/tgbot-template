import datetime
from functions.timetable.tools import *
from base_template.context import *


def schedule_notify(update, ctx, when):
    from base_template.bot import updater
    chat_id = str(update.effective_chat.id)
    all_the_timer = get_timedelta(when)
    print(all_the_timer, "notifies_time")
    print(when, "when")
    day_before_timer = all_the_timer - datetime.timedelta(days=1)
    two_hours_before_timer = all_the_timer - datetime.timedelta(hours=2)
    updater.job_queue.run_once(callback=day_before_notify, when=day_before_timer, context=chat_id)
    updater.job_queue.run_once(callback=two_hours_before_notify,
                               when=two_hours_before_timer,
                               context=chat_id)
    updater.job_queue.start()


def day_before_notify(ctx):
    ctx.bot.send_message(chat_id=ctx.job.context,
                         text=day_before_notify_msg)


def two_hours_before_notify(ctx):
    ctx.bot.send_message(chat_id=ctx.job.context,
                         text=two_hours_before_notify_msg)
