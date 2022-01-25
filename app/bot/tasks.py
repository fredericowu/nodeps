from celery import shared_task
#from celery.decorators import periodic_task
#from celery.task import periodic_task
from bot.connector.telegrambot import TelegramBot
from addon.models import XboxFriends
import anki_vector
import requests
from datetime import timedelta
import os
import time
from anki_vector.connection import ControlPriorityLevel
from anki_vector.util import distance_mm, speed_mmps, degrees, Angle, Pose

bot = TelegramBot()


#
#def add(celery):
#@periodic_task(run_every=timedelta(minutes=1))

def send_alarm():
    payload = {
        "robot_actions": [
            {
                "execute": "LuluIsPlaying"
            }
        ]
    }
    headers = {
        "Content-Type": "application/json"
    }
    requests.post("http://192.168.1.144:5000/api/robot/do", headers=headers, json=payload)

    """
    for _ in range(3):
        try:


            with anki_vector.Robot(behavior_activation_timeout=30,
                                   behavior_control_level=ControlPriorityLevel.OVERRIDE_BEHAVIORS_PRIORITY) as robot:
                robot.behavior.drive_off_charger()
                robot.behavior.say_text("Lulu is playing")
                robot.anim.play_animation_trigger('GreetAfterLongTime')
                robot.world.connect_cube()
                robot.behavior.drive_straight(distance_mm(200), speed_mmps(100))
                robot.behavior.say_text("he is playing")
                robot.behavior.turn_in_place(degrees(70))
                robot.behavior.say_text("Lulu is playing")
                robot.behavior.turn_in_place(degrees(220))
                robot.anim.play_animation_trigger('GreetAfterLongTime')
                robot.behavior.drive_on_charger()
        except anki_vector.exceptions.VectorTimeoutException:
            time.sleep(20)
            continue
        else:
            break
    """

@shared_task
def check_status():
    fred_id = 1223642032
    notify_friends = ["Broriz4927", ]
    #alert_cmd = '/home/ubuntu/workspace/vector-go-sdk/custom/speak.sh "Lulu is playing, he is playing, he is playing" &'
    status = XboxFriends.check_status()
    for friend in status:
        if status[friend]["changed"] and status[friend]["gamertag"] in notify_friends:
            msg = "{} is {} playing {}".format(status[friend]["gamertag"], status[friend]["state"], status[friend]["title"])
            bot.connection.send_message(fred_id, msg)

            if status[friend]["state"].lower() == "online":
                send_alarm()



"""
from celery.task.schedules import crontab
from celery.decorators import periodic_task

@periodic_task(run_every=crontab(hour=7, minute=30, day_of_week=1))
def a():
    ...
"""
