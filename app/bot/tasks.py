from celery import shared_task
#from celery.decorators import periodic_task
#from celery.task import periodic_task
from bot.connector.telegrambot import TelegramBot
from addon.models import XboxFriends

from datetime import timedelta
import os
import time

bot = TelegramBot()


#
#def add(celery):
#@periodic_task(run_every=timedelta(minutes=1))
@shared_task
def check_status():
    fred_id = 1223642032
    notify_friends = ["Broriz4927", ]
    alert_cmd = '/home/ubuntu/workspace/vector-go-sdk/custom/speak.sh "Lulu is playing, he is playing, he is playing" &'
    status = XboxFriends.check_status()
    for friend in status:
        if status[friend]["changed"] and status[friend]["gamertag"] in notify_friends:
            msg = "{} is {} playing {}".format(status[friend]["gamertag"], status[friend]["state"], status[friend]["title"])
            bot.connection.send_message(fred_id, msg)

            if status[friend]["state"].lower() == "online":
                os.system(alert_cmd)
                time.sleep(60)
                os.system(alert_cmd)


"""
from celery.task.schedules import crontab
from celery.decorators import periodic_task

@periodic_task(run_every=crontab(hour=7, minute=30, day_of_week=1))
def a():
    ...
"""
