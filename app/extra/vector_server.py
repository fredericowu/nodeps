#!/usr/bin/env python3

# Copyright (c) 2018 Anki, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Control Vector using a webpage on your computer.

This example lets you control Vector by Remote Control, using a webpage served by Flask.
"""
import datetime

import speech_recognition as sr
import asyncio
import time
from queue import Queue
import threading
import io
import os
import json
import sys
import inspect
import time
from enum import Enum
from lib import flask_helpers
import requests

import anki_vector
from anki_vector import util
from anki_vector import annotate
from anki_vector.user_intent import UserIntent
from anki_vector.util import distance_mm, speed_mmps, degrees, Angle, Pose
import datetime
import socket

import threading

try:
    from flask import Flask, request
except ImportError:
    sys.exit("Cannot import from flask: Do `pip3 install --user flask` to install")

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Cannot import from PIL: Do `pip3 install --user Pillow` to install")

class RobotAction:
    def __init__(self, robot):
        self.robot = robot

    def do(self, instructions):
        print("Received Instructions")
        print(instructions)
        robot_actions = instructions.get("robot_actions", [])
        for payload_item in robot_actions:
            if "say" in payload_item:
                self.robot.behavior.say_text(payload_item["say"])
            elif "execute" in payload_item:
                action_class = next(filter(lambda a: a[0] == payload_item["execute"] and \
                                                     issubclass(a[1], RobotAction),
                                           inspect.getmembers(sys.modules[__name__], inspect.isclass)),
                                    (None, None))[1]
                if action_class:
                    execute_kwargs = payload_item.get("execute_kwargs", {})
                    action_class(self.robot, **execute_kwargs)

        """
        
        print(payload)
        for item in payload:
            if "text" in item:
                #print("item text: "+ item["text"])
                try:
                    text_payload = json.loads(item["text"])
                except json.decoder.JSONDecodeError:
                    text_payload = item["text"]
                #print("text_payload", text_payload)
                #import pdb; pdb.set_trace()
                if type(text_payload) == str:
                    self.robot.behavior.say_text(text_payload)
                elif type(text_payload) == dict:
        """

class RobotContext:
    def __init__(self, robot):
        self.robot = robot
        self.want_to_go_to_face = 0


class ComeHere(RobotAction):
    def __init__(self, robot, arguments=None):
        robot.behavior.drive_off_charger()
        robot.anim.play_animation_trigger('GreetAfterLongTime')
        robot.behavior.drive_straight(distance_mm(200), speed_mmps(100))
        #faces = robot.behavior.find_faces()
        #print("FACES", faces)


class GoToHome(RobotAction):
    def __init__(self, robot, arguments=None):
        robot.anim.play_animation_trigger('anim_keepaway_getout_03')
        robot.anim.play_animation_trigger('anim_keepaway_getout_frustrated_01')
        robot.anim.play_animation_trigger('anim_keepaway_idleliftdown_01')
        robot.behavior.drive_on_charger()


class LuluIsPlaying(RobotAction):
    def __init__(self, robot, arguments=None):
        robot.behavior.drive_off_charger()
        robot.world.connect_cube()
        robot.behavior.say_text("Lulu is playing").result(10)
        robot.anim.play_animation_trigger('GreetAfterLongTime').result(10)
        robot.behavior.drive_straight(distance_mm(200), speed_mmps(100)).result(10)
        robot.behavior.say_text("he is playing").result(10)
        robot.behavior.turn_in_place(degrees(70)).result(10)
        robot.behavior.say_text("Lulu is playing").result(10)
        robot.behavior.turn_in_place(degrees(220)).result(10)
        robot.anim.play_animation_trigger('GreetAfterLongTime').result(10)
        robot.behavior.drive_on_charger()


class Nodeps(anki_vector.AsyncRobot):
    recognizer = sr.Recognizer()
    activation_word = ["buddy", ]
    deactivation_word = ["hey vector", "hey victor"]
    conversation_active = False
    conversation_active_time = 12
    last_talk = datetime.datetime.now() - datetime.timedelta(seconds=conversation_active_time+1)
    robot = None
    last_voice_heard = None
    #_has_control = False

    def process_text(self, text, time_took=None):
        self.last_voice_heard = datetime.datetime.now()

        # TODO: is_conversation_active( heard_activation / heard_deactivation)
        Nodeps.conversation_active = False
        need_processing = False
        if next(filter(lambda a: a.lower() in text.lower(), Nodeps.deactivation_word), None):
            print("Vector called!")
            Nodeps.conversation_active = False
            self.robot.conn.release_control()
        elif next(filter(lambda a: a.lower() in text.lower(), Nodeps.activation_word), None) or \
                (datetime.datetime.now() - Nodeps.last_talk).seconds <= Nodeps.conversation_active_time:
            Nodeps.conversation_active = True
            if self.robot.conn._behavior_control_level is None:
                self.robot.conn.request_control()
            Nodeps.last_talk = datetime.datetime.now()
            need_processing = True

        print("Decoded audio [" + str(Nodeps.conversation_active) + "] " + str(time_took) + ": " + text)
        if need_processing:
            payload = {
                "sender": "test_user",
                "text": text,
                "metadata": {}
            }
            r = requests.post('http://localhost:5005/webhooks/myio/webhook', json=payload)
            if r.status_code == 200:
                for item in r.json():
                    if "text" in item:
                        try:
                            text_payload = json.loads(item["text"])
                        except json.decoder.JSONDecodeError:
                            text_payload = {"robot_actions": [{"say": item["text"]}]}
                        self.robot.actions.do(text_payload)

    def __init__(self, *args, **kwargs):
        super(Nodeps, self).__init__(*args, **kwargs)
        Nodeps.recognizer.operation_timeout = 15
        #import pdb; pdb.set_trace()
        if not Nodeps.robot:
            Nodeps.robot = self
            self.actions = RobotAction(self)
            self.context = RobotContext(self)

        #import time; time.sleep(1)

        self.events.subscribe(Nodeps.on_control_granted, anki_vector.events.Events.control_granted)
        self.events.subscribe(Nodeps.on_control_lost, anki_vector.events.Events.control_lost)
        self.events.subscribe(Nodeps.on_user_intent, anki_vector.events.Events.user_intent)


    def connect(self, *args, **kwargs):
        super(Nodeps, self).connect(*args, **kwargs)
        """
        for i in range(10):
            try:
                asyncio.run(super(Nodeps, self).connect(*args, **kwargs))
            except: # (asyncio.exceptions.TimeoutError, anki_vector.connection.VectorAsyncException):
                print("Trying to connect to vector again")
                if i % 2 != 0:
                    os.system("ssh -i ~/.ssh/id_rsa_Vector-S3U5 root@192.168.1.118 reboot")
                time.sleep(60*3)
                continue

        print("ended")
        """
        Nodeps.on_control_granted(self, anki_vector.events.Events.control_granted, None)

    @staticmethod
    def on_control_lost(robot, event_type, event):
        print("[FRED] Control Lost")
        robot.behavior.set_eye_color(0.59, 1)
        #robot._has_control = False

    @staticmethod
    def on_control_granted(robot, event_type, event):
        print("[FRED] Control Granted")
        robot.behavior.set_eye_color(0.59, 1)
        #robot._has_control = True

        # user_intent = UserIntent(event)
        # print(f"Received {user_intent.intent_event}")
        # print(user_intent.intent_data)
        # done.set()

    @staticmethod
    def on_user_intent(robot, event_type, event):
        user_intent = UserIntent(event)
        print(f"Received {user_intent.intent_event} -> {event_type}")
        print(user_intent.intent_data)
        # done.set()


def create_default_image(image_width, image_height, do_gradient=False):
    """Create a place-holder PIL image to use until we have a live feed from Vector"""
    image_bytes = bytearray([0x70, 0x70, 0x70]) * image_width * image_height

    if do_gradient:
        i = 0
        for y in range(image_height):
            for x in range(image_width):
                image_bytes[i] = int(255.0 * (x / image_width))  # R
                image_bytes[i + 1] = int(255.0 * (y / image_height))  # G
                image_bytes[i + 2] = 0  # B
                i += 3

    image = Image.frombytes('RGB', (image_width, image_height), bytes(image_bytes))
    return image

def audio_worker(queue, robot):
    print("starting worker")
    while True:
        audio = queue.get()
        # print("Received audio")
        try:
            a = datetime.datetime.now()
            text = Nodeps.recognizer.recognize_google(audio)
            b = datetime.datetime.now()
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            continue
        except socket.timeout:
            continue
        except Exception as e:
            print("OTHER EXCEPTION " + str(e))
            print("Unexpected error:", sys.exc_info()[0])
            raise

            #import pdb; pdb.set_trace()
        if text:
            robot.process_text(text, time_took=(b - a).seconds)
        # queue.task_done()


def audio_listener(queue):

    PREFFERED_MIC = "WEB CAM"
    try:
        device_index = sr.Microphone.list_microphone_names().index(PREFFERED_MIC)
    except ValueError:
        device_index = None

    print("device_index = " + str(device_index))
    with sr.Microphone(device_index=device_index) as source:
    #with sr.Microphone() as source:
        print("Say something!")
        while True:
            try:
                a = datetime.datetime.now()
                audio = Nodeps.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                b = datetime.datetime.now()
                # audio = yield from queue.get()
                # message = yield from
            except sr.WaitTimeoutError:
                continue
            #print("New audio "+ str((b-a).seconds))
            queue.put(audio)
    queue.join()


def audio_main(robot):
    queue = Queue()
    threads = []
    for i in range(2):
        t = threading.Thread(target=audio_worker, args=(queue, robot,))
        threads.append(t)
        t.start()

    t = threading.Thread(target=audio_listener, args=(queue,))
    threads.append(t)
    t.start()


flask_app = Flask(__name__)
_default_camera_image = create_default_image(320, 240)
_is_mouse_look_enabled_by_default = False


def remap_to_range(x, x_min, x_max, out_min, out_max):
    """convert x (in x_min..x_max range) to out_min..out_max range"""
    if x < x_min:
        return out_min
    if x > x_max:
        return out_max
    ratio = (x - x_min) / (x_max - x_min)
    return out_min + ratio * (out_max - out_min)


class DebugAnnotations(Enum):
    DISABLED = 0
    ENABLED_VISION = 1
    ENABLED_ALL = 2


# Annotator for displaying RobotState (position, etc.) on top of the camera feed
class RobotStateDisplay(annotate.Annotator):
    def apply(self, image, scale):
        d = ImageDraw.Draw(image)

        bounds = [3, 0, image.width, image.height]

        def print_line(text_line):
            text = annotate.ImageText(text_line, position=annotate.AnnotationPosition.TOP_LEFT, outline_color='black',
                                      color='lightblue')
            text.render(d, bounds)
            TEXT_HEIGHT = 11
            bounds[1] += TEXT_HEIGHT

        robot = self.world.robot  # type: robot.Robot

        # Display the Pose info for the robot
        pose = robot.pose
        print_line('Pose: Pos = <%.1f, %.1f, %.1f>' % pose.position.x_y_z)
        print_line('Pose: Rot quat = <%.1f, %.1f, %.1f, %.1f>' % pose.rotation.q0_q1_q2_q3)
        print_line('Pose: angle_z = %.1f' % pose.rotation.angle_z.degrees)
        print_line('Pose: origin_id: %s' % pose.origin_id)

        # Display the Accelerometer and Gyro data for the robot
        print_line('Accelmtr: <%.1f, %.1f, %.1f>' % robot.accel.x_y_z)
        print_line('Gyro: <%.1f, %.1f, %.1f>' % robot.gyro.x_y_z)


class RemoteControlVector:

    def __init__(self, robot):
        self.vector = robot

        # don't send motor messages if it matches the last setting
        self.last_lift = None
        self.last_head = None
        self.last_wheels = None

        self.drive_forwards = 0
        self.drive_back = 0
        self.turn_left = 0
        self.turn_right = 0
        self.lift_up = 0
        self.lift_down = 0
        self.head_up = 0
        self.head_down = 0

        self.go_fast = 0
        self.go_slow = 0

        self.is_mouse_look_enabled = _is_mouse_look_enabled_by_default
        self.mouse_dir = 0

        all_anim_names = self.vector.anim.anim_list
        all_anim_names.sort()
        self.anim_names = []

        # Hide a few specific test animations that don't behave well
        bad_anim_names = [
            "ANIMATION_TEST",
            "soundTestAnim"]

        for anim_name in all_anim_names:
            if anim_name not in bad_anim_names:
                self.anim_names.append(anim_name)

        default_anims_for_keys = ["anim_turn_left_01",  # 0
                                  "anim_blackjack_victorwin_01",  # 1
                                  "anim_pounce_success_02",  # 2
                                  "anim_feedback_shutup_01",  # 3
                                  "anim_knowledgegraph_success_01",  # 4
                                  "anim_wakeword_groggyeyes_listenloop_01",  # 5
                                  "anim_fistbump_success_01",  # 6
                                  "anim_reacttoface_unidentified_01",  # 7
                                  "anim_rtpickup_loop_10",  # 8
                                  "anim_volume_stage_05"]  # 9

        self.anim_index_for_key = [0] * 10
        kI = 0
        for default_key in default_anims_for_keys:
            try:
                anim_idx = self.anim_names.index(default_key)
            except ValueError:
                print("Error: default_anim %s is not in the list of animations" % default_key)
                anim_idx = kI
            self.anim_index_for_key[kI] = anim_idx
            kI += 1

        all_anim_trigger_names = self.vector.anim.anim_trigger_list
        self.anim_trigger_names = []

        bad_anim_trigger_names = [
            "InvalidAnimTrigger",
            "UnitTestAnim"]

        for anim_trigger_name in all_anim_trigger_names:
            if anim_trigger_name not in bad_anim_trigger_names:
                self.anim_trigger_names.append(anim_trigger_name)

        self.selected_anim_trigger_name = self.anim_trigger_names[0]

        self.action_queue = []
        self.text_to_say = "Hi I'm Vector"

    def set_anim(self, key_index, anim_index):
        self.anim_index_for_key[key_index] = anim_index

    def handle_mouse(self, mouse_x, mouse_y):
        """Called whenever mouse moves
            mouse_x, mouse_y are in in 0..1 range (0,0 = top left, 1,1 = bottom right of window)
        """
        if self.is_mouse_look_enabled:
            mouse_sensitivity = 1.5  # higher = more twitchy
            self.mouse_dir = remap_to_range(mouse_x, 0.0, 1.0, -mouse_sensitivity, mouse_sensitivity)
            self.update_mouse_driving()

            desired_head_angle = remap_to_range(mouse_y, 0.0, 1.0, 45, -25)
            head_angle_delta = desired_head_angle - util.radians(self.vector.head_angle_rad).degrees
            head_vel = head_angle_delta * 0.03
            if self.last_head and head_vel == self.last_head:
                return
            self.last_head = head_vel
            self.vector.motors.set_head_motor(head_vel)

    def set_mouse_look_enabled(self, is_mouse_look_enabled):
        was_mouse_look_enabled = self.is_mouse_look_enabled
        self.is_mouse_look_enabled = is_mouse_look_enabled
        if not is_mouse_look_enabled:
            # cancel any current mouse-look turning
            self.mouse_dir = 0
            if was_mouse_look_enabled:
                self.update_mouse_driving()
                self.update_head()

    def update_drive_state(self, key_code, is_key_down, speed_changed):
        """Update state of driving intent from keyboard, and if anything changed then call update_driving"""
        update_driving = True
        if key_code == ord('W'):
            self.drive_forwards = is_key_down
        elif key_code == ord('S'):
            self.drive_back = is_key_down
        elif key_code == ord('A'):
            self.turn_left = is_key_down
        elif key_code == ord('D'):
            self.turn_right = is_key_down
        else:
            if not speed_changed:
                update_driving = False
        return update_driving

    def update_lift_state(self, key_code, is_key_down, speed_changed):
        """Update state of lift move intent from keyboard, and if anything changed then call update_lift"""
        update_lift = True
        if key_code == ord('R'):
            self.lift_up = is_key_down
        elif key_code == ord('F'):
            self.lift_down = is_key_down
        else:
            if not speed_changed:
                update_lift = False
        return update_lift

    def update_head_state(self, key_code, is_key_down, speed_changed):
        """Update state of head move intent from keyboard, and if anything changed then call update_head"""
        update_head = True
        if key_code == ord('T'):
            self.head_up = is_key_down
        elif key_code == ord('G'):
            self.head_down = is_key_down
        else:
            if not speed_changed:
                update_head = False
        return update_head

    def handle_key(self, key_code, is_shift_down, is_alt_down, is_key_down):
        """Called on any key press or release
           Holding a key down may result in repeated handle_key calls with is_key_down==True
        """

        # Update desired speed / fidelity of actions based on shift/alt being held
        was_go_fast = self.go_fast
        was_go_slow = self.go_slow

        self.go_fast = is_shift_down
        self.go_slow = is_alt_down

        speed_changed = (was_go_fast != self.go_fast) or (was_go_slow != self.go_slow)

        update_driving = self.update_drive_state(key_code, is_key_down, speed_changed)

        update_lift = self.update_lift_state(key_code, is_key_down, speed_changed)

        update_head = self.update_head_state(key_code, is_key_down, speed_changed)

        # Update driving, head and lift as appropriate
        if update_driving:
            self.update_mouse_driving()
        if update_head:
            self.update_head()
        if update_lift:
            self.update_lift()

        # Handle any keys being released (e.g. the end of a key-click)
        if not is_key_down:
            if ord('9') >= key_code >= ord('0'):
                anim_name = self.key_code_to_anim_name(key_code)
                self.queue_action((self.vector.anim.play_animation, anim_name))
            elif key_code == ord(' '):
                self.queue_action((self.vector.behavior.say_text, self.text_to_say))
            elif key_code == ord('X'):
                self.queue_action((self.vector.anim.play_animation_trigger, self.selected_anim_trigger_name))

    def key_code_to_anim_name(self, key_code):
        key_num = key_code - ord('0')
        anim_num = self.anim_index_for_key[key_num]
        anim_name = self.anim_names[anim_num]
        return anim_name

    def func_to_name(self, func):
        if func == self.vector.behavior.say_text:
            return "say_text"
        if func == self.vector.anim.play_animation:
            return "play_anim"
        return "UNKNOWN"

    def action_to_text(self, action):
        func, args = action
        return self.func_to_name(func) + "( " + str(args) + " )"

    def action_queue_to_text(self, action_queue):
        out_text = ""
        i = 0
        for action in action_queue:
            out_text += "[" + str(i) + "] " + self.action_to_text(action)
            i += 1
        return out_text

    def queue_action(self, new_action):
        if len(self.action_queue) > 10:
            self.action_queue.pop(0)
        self.action_queue.append(new_action)

    def update(self):
        """Try and execute the next queued action"""
        if self.action_queue:
            queued_action, action_args = self.action_queue[0]
            if queued_action(action_args):
                self.action_queue.pop(0)

    def pick_speed(self, fast_speed, mid_speed, slow_speed):
        if self.go_fast:
            if not self.go_slow:
                return fast_speed
        elif self.go_slow:
            return slow_speed
        return mid_speed

    def update_lift(self):
        lift_speed = self.pick_speed(8, 4, 2)
        lift_vel = (self.lift_up - self.lift_down) * lift_speed
        if self.last_lift and lift_vel == self.last_lift:
            return
        self.last_lift = lift_vel
        self.vector.motors.set_lift_motor(lift_vel)

    def update_head(self):
        if not self.is_mouse_look_enabled:
            head_speed = self.pick_speed(2, 1, 0.5)
            head_vel = (self.head_up - self.head_down) * head_speed
            if self.last_head and head_vel == self.last_head:
                return
            self.last_head = head_vel
            self.vector.motors.set_head_motor(head_vel)

    def update_mouse_driving(self):
        drive_dir = (self.drive_forwards - self.drive_back)

        turn_dir = (self.turn_right - self.turn_left) + self.mouse_dir
        if drive_dir < 0:
            # It feels more natural to turn the opposite way when reversing
            turn_dir = -turn_dir

        forward_speed = self.pick_speed(150, 75, 50)
        turn_speed = self.pick_speed(100, 50, 30)

        l_wheel_speed = (drive_dir * forward_speed) + (turn_speed * turn_dir)
        r_wheel_speed = (drive_dir * forward_speed) - (turn_speed * turn_dir)

        wheel_params = (l_wheel_speed, r_wheel_speed, l_wheel_speed * 4, r_wheel_speed * 4)
        if self.last_wheels and wheel_params == self.last_wheels:
            return
        self.last_wheels = wheel_params
        self.vector.motors.set_wheel_motors(*wheel_params)


def get_anim_sel_drop_down(selectorIndex):
    html_text = """<select onchange="handleDropDownSelect(this)" name="animSelector""" + str(selectorIndex) + """">"""
    i = 0
    for anim_name in flask_app.remote_control_vector.anim_names:
        is_selected_item = (i == flask_app.remote_control_vector.anim_index_for_key[selectorIndex])
        selected_text = ''' selected="selected"''' if is_selected_item else ""
        html_text += """<option value=""" + str(i) + selected_text + """>""" + anim_name + """</option>"""
        i += 1
    html_text += """</select>"""
    return html_text


def get_anim_sel_drop_downs():
    html_text = ""
    for i in range(10):
        # list keys 1..9,0 as that's the layout on the keyboard
        key = i + 1 if (i < 9) else 0
        html_text += str(key) + """: """ + get_anim_sel_drop_down(key) + """<br>"""
    return html_text


def get_anim_trigger_sel_drop_down():
    html_text = "x: "  # Add keyboard selector
    html_text += """<select onchange="handleAnimTriggerDropDownSelect(this)" name="animTriggerSelector">"""
    for anim_trigger_name in flask_app.remote_control_vector.anim_trigger_names:
        html_text += """<option value=""" + anim_trigger_name + """>""" + anim_trigger_name + """</option>"""
    html_text += """</select>"""
    return html_text


def to_js_bool_string(bool_value):
    return "true" if bool_value else "false"


@flask_app.route("/api/robot/do", methods=['POST',])
def api_robot_do():
    payload = request.json
    print(payload)
    try:
        Nodeps.robot.actions.do(payload)
        result = True
    except:
        result = False
    return json.dumps({"success": result})


@flask_app.route("/")
def handle_index_page():
    return """
    <html>
        <head>
            <title>remote_control_vector.py display</title>
        </head>
        <body>
            <h1>Remote Control Vector</h1>
            <table>
                <tr>
                    <td valign = top>
                        <div id="vectorImageMicrosoftWarning" style="display: none;color: #ff9900; text-align: center;">Video feed performance is better in Chrome or Firefox due to mjpeg limitations in this browser</div>
                        <img src="vectorImage" id="vectorImageId" width=640 height=480>
                        <div id="DebugInfoId"></div>
                    </td>
                    <td width=30></td>
                    <td valign=top>
                        <h2>Controls:</h2>

                        <h3>Driving:</h3>

                        <b>W A S D</b> : Drive Forwards / Left / Back / Right<br><br>
                        <b>Q</b> : Toggle Mouse Look: <button id="mouseLookId" onClick=onMouseLookButtonClicked(this) style="font-size: 14px">Default</button><br>
                        <b>Mouse</b> : Move in browser window to aim<br>
                        (steer and head angle)<br>
                        (similar to an FPS game)<br>

                        <h3>Head:</h3>
                        <b>T</b> : Move Head Up<br>
                        <b>G</b> : Move Head Down<br>

                        <h3>Lift:</h3>
                        <b>R</b> : Move Lift Up<br>
                        <b>F</b>: Move Lift Down<br>
                        <h3>General:</h3>
                        <b>Shift</b> : Hold to Move Faster (Driving, Head and Lift)<br>
                        <b>Alt</b> : Hold to Move Slower (Driving, Head and Lift)<br>
                        <b>P</b> : Toggle Free Play mode: <button id="freeplayId" onClick=onFreeplayButtonClicked(this) style="font-size: 14px">Default</button><br>
                        <b>O</b> : Toggle Debug Annotations: <button id="debugAnnotationsId" onClick=onDebugAnnotationsButtonClicked(this) style="font-size: 14px">Default</button><br>
                        <h3>Play Animations</h3>
                        <b>0 .. 9</b> : Play Animation mapped to that key<br>
                        <h3>Talk</h3>
                        <b>Space</b> : Say <input type="text" name="sayText" id="sayTextId" value=\"""" + flask_app.remote_control_vector.text_to_say + """\" onchange=handleTextInput(this)>
                        <h3>Eval</h3>
                        <b>[input]</b> : Eval <input type="text" name="evalText" id="evalTextId" value=\"""" + """\"><button onclick=handleEvalTextInput(this)>Eval</button>

                    </td>
                    <td width=30></td>
                    <td valign=top>
                    <h2>Animation key mappings:</h2>
                    """ + get_anim_sel_drop_downs() + """<br>
                    <h2>Animation Triggers:</h2>
                    """ + get_anim_trigger_sel_drop_down() + """<br><br>
                    </td>
                </tr>
            </table>

            <script type="text/javascript">
                var gLastClientX = -1
                var gLastClientY = -1
                var gIsMouseLookEnabled = """ + to_js_bool_string(_is_mouse_look_enabled_by_default) + """
                var gAreDebugAnnotationsEnabled = """ + str(flask_app.display_debug_annotations) + """
                var gIsFreeplayEnabled = false
                var gUserAgent = window.navigator.userAgent;
                var gIsMicrosoftBrowser = gUserAgent.indexOf('MSIE ') > 0 || gUserAgent.indexOf('Trident/') > 0 || gUserAgent.indexOf('Edge/') > 0;
                var gSkipFrame = false;

                if (gIsMicrosoftBrowser) {
                    document.getElementById("vectorImageMicrosoftWarning").style.display = "block";
                }

                function postHttpRequest(url, dataSet, responseHandler)
                {
                    var xhr = new XMLHttpRequest();
                    if (responseHandler) {
                      // alert(JSON.stringify( dataSet ));

                      xhr.onreadystatechange = function() {
                        if (xhr.readyState === 4) {
                          responseHandler(xhr.response);
                        }
                      }
                    }

                    xhr.open("POST", url, true);
                    xhr.send( JSON.stringify( dataSet ) );
                }

                function updateVector()
                {
                    console.log("Updating log")
                    if (gIsMicrosoftBrowser && !gSkipFrame) {
                        // IE doesn't support MJPEG, so we need to ping the server for more images.
                        // Though, if this happens too frequently, the controls will be unresponsive.
                        gSkipFrame = true;
                        document.getElementById("vectorImageId").src="vectorImage?" + (new Date()).getTime();
                    } else if (gSkipFrame) {
                        gSkipFrame = false;
                    }
                    var xhr = new XMLHttpRequest();
                    xhr.onreadystatechange = function() {
                        if (xhr.readyState == XMLHttpRequest.DONE) {
                            document.getElementById("DebugInfoId").innerHTML = xhr.responseText
                        }
                    }

                    xhr.open("POST", "updateVector", true);
                    xhr.send( null );
                }
                setInterval(updateVector , 60);

                function updateButtonEnabledText(button, isEnabled)
                {
                    button.firstChild.data = isEnabled ? "Enabled" : "Disabled";
                }

                function onMouseLookButtonClicked(button)
                {
                    gIsMouseLookEnabled = !gIsMouseLookEnabled;
                    updateButtonEnabledText(button, gIsMouseLookEnabled);
                    isMouseLookEnabled = gIsMouseLookEnabled
                    postHttpRequest("setMouseLookEnabled", {isMouseLookEnabled})
                }

                function updateDebugAnnotationButtonEnabledText(button, isEnabled)
                {
                    switch(gAreDebugAnnotationsEnabled)
                    {
                    case 0:
                        button.firstChild.data = "Disabled";
                        break;
                    case 1:
                        button.firstChild.data = "Enabled (vision)";
                        break;
                    case 2:
                        button.firstChild.data = "Enabled (all)";
                        break;
                    default:
                        button.firstChild.data = "ERROR";
                        break;
                    }
                }

                function onDebugAnnotationsButtonClicked(button)
                {
                    gAreDebugAnnotationsEnabled += 1;
                    if (gAreDebugAnnotationsEnabled > 2)
                    {
                        gAreDebugAnnotationsEnabled = 0
                    }
                    updateDebugAnnotationButtonEnabledText(button, gAreDebugAnnotationsEnabled)
                    areDebugAnnotationsEnabled = gAreDebugAnnotationsEnabled
                    postHttpRequest("setAreDebugAnnotationsEnabled", {areDebugAnnotationsEnabled})
                }

                function onFreeplayButtonClicked(button)
                {
                    gIsFreeplayEnabled = !gIsFreeplayEnabled;
                    updateButtonEnabledText(button, gIsFreeplayEnabled);
                    isFreeplayEnabled = gIsFreeplayEnabled
                    postHttpRequest("setFreeplayEnabled", {isFreeplayEnabled})
                }

                updateButtonEnabledText(document.getElementById("mouseLookId"), gIsMouseLookEnabled);
                updateButtonEnabledText(document.getElementById("freeplayId"), gIsFreeplayEnabled);
                updateDebugAnnotationButtonEnabledText(document.getElementById("debugAnnotationsId"), gAreDebugAnnotationsEnabled);

                function handleDropDownSelect(selectObject)
                {
                    selectedIndex = selectObject.selectedIndex
                    itemName = selectObject.name
                    postHttpRequest("dropDownSelect", {selectedIndex, itemName});
                }

                function handleAnimTriggerDropDownSelect(selectObject)
                {
                    animTriggerName = selectObject.value
                    postHttpRequest("animTriggerDropDownSelect", {animTriggerName});
                }

                function handleKeyActivity (e, actionType)
                {
                    var keyCode  = (e.keyCode ? e.keyCode : e.which);
                    var hasShift = (e.shiftKey ? 1 : 0)
                    var hasCtrl  = (e.ctrlKey  ? 1 : 0)
                    var hasAlt   = (e.altKey   ? 1 : 0)

                    if (actionType=="keyup")
                    {
                        if (keyCode == 79) // 'O'
                        {
                            // Simulate a click of the debug annotations button
                            onDebugAnnotationsButtonClicked(document.getElementById("debugAnnotationsId"))
                        }
                        else if (keyCode == 80) // 'P'
                        {
                            // Simulate a click of the freeplay button
                            onFreeplayButtonClicked(document.getElementById("freeplayId"))
                        }
                        else if (keyCode == 81) // 'Q'
                        {
                            // Simulate a click of the mouse look button
                            onMouseLookButtonClicked(document.getElementById("mouseLookId"))
                        }
                    }

                    postHttpRequest(actionType, {keyCode, hasShift, hasCtrl, hasAlt})
                }

                function handleMouseActivity (e, actionType)
                {
                    var clientX = e.clientX / document.body.clientWidth  // 0..1 (left..right)
                    var clientY = e.clientY / document.body.clientHeight // 0..1 (top..bottom)
                    var isButtonDown = e.which && (e.which != 0) ? 1 : 0
                    var deltaX = (gLastClientX >= 0) ? (clientX - gLastClientX) : 0.0
                    var deltaY = (gLastClientY >= 0) ? (clientY - gLastClientY) : 0.0
                    gLastClientX = clientX
                    gLastClientY = clientY

                    postHttpRequest(actionType, {clientX, clientY, isButtonDown, deltaX, deltaY})
                }

                function handleTextInput(textField)
                {
                    textEntered = textField.value
                    postHttpRequest("sayText", {textEntered})
                }

                function evalResponse(response) {
                    alert(response);
                }

                function handleEvalTextInput(textFiel)
                {
                    textEntered = document.getElementById("evalTextId").value;
                    postHttpRequest("eval", {textEntered}, evalResponse);
                    // alert(textEntered)
                }

                document.addEventListener("keydown", function(e) { handleKeyActivity(e, "keydown") } );
                document.addEventListener("keyup",   function(e) { handleKeyActivity(e, "keyup") } );

                document.addEventListener("mousemove",   function(e) { handleMouseActivity(e, "mousemove") } );

                function stopEventPropagation(event)
                {
                    if (event.stopPropagation)
                    {
                        event.stopPropagation();
                    }
                    else
                    {
                        event.cancelBubble = true
                    }
                }

                document.getElementById("sayTextId").addEventListener("keydown", function(event) {
                    stopEventPropagation(event);
                } );
                document.getElementById("sayTextId").addEventListener("keyup", function(event) {
                    stopEventPropagation(event);
                } );
            </script>

        </body>
    </html>
    """


def get_annotated_image():
    image = flask_app.remote_control_vector.vector.camera.latest_image
    if flask_app.display_debug_annotations != DebugAnnotations.DISABLED.value:
        return image.annotate_image()
    return image.raw_image


def streaming_video():
    """Video streaming generator function"""
    while True:
        if flask_app.remote_control_vector:
            image = get_annotated_image()

            img_io = io.BytesIO()
            image.save(img_io, 'PNG')
            img_io.seek(0)
            yield (b'--frame\r\n'
                   b'Content-Type: image/png\r\n\r\n' + img_io.getvalue() + b'\r\n')
        else:
            time.sleep(.1)


def serve_single_image():
    if flask_app.remote_control_vector:
        image = get_annotated_image()
        if image:
            return flask_helpers.serve_pil_image(image)

    return flask_helpers.serve_pil_image(_default_camera_image)


def is_microsoft_browser(req):
    agent = req.user_agent.string
    return 'Edge/' in agent or 'MSIE ' in agent or 'Trident/' in agent


@flask_app.route("/vectorImage")
def handle_vectorImage():
    if is_microsoft_browser(request):
        return serve_single_image()
    return flask_helpers.stream_video(streaming_video)


def handle_key_event(key_request, is_key_down):
    message = json.loads(key_request.data.decode("utf-8"))
    if flask_app.remote_control_vector:
        flask_app.remote_control_vector.handle_key(key_code=(message['keyCode']), is_shift_down=message['hasShift'],
                                                   is_alt_down=message['hasAlt'], is_key_down=is_key_down)
    return ""


@flask_app.route('/mousemove', methods=['POST'])
def handle_mousemove():
    """Called from Javascript whenever mouse moves"""
    message = json.loads(request.data.decode("utf-8"))
    if flask_app.remote_control_vector:
        flask_app.remote_control_vector.handle_mouse(mouse_x=(message['clientX']), mouse_y=message['clientY'])
    return ""


@flask_app.route('/setMouseLookEnabled', methods=['POST'])
def handle_setMouseLookEnabled():
    """Called from Javascript whenever mouse-look mode is toggled"""
    message = json.loads(request.data.decode("utf-8"))
    if flask_app.remote_control_vector:
        flask_app.remote_control_vector.set_mouse_look_enabled(is_mouse_look_enabled=message['isMouseLookEnabled'])
    return ""


@flask_app.route('/setAreDebugAnnotationsEnabled', methods=['POST'])
def handle_setAreDebugAnnotationsEnabled():
    """Called from Javascript whenever debug-annotations mode is toggled"""
    message = json.loads(request.data.decode("utf-8"))
    flask_app.display_debug_annotations = message['areDebugAnnotationsEnabled']
    if flask_app.remote_control_vector:
        if flask_app.display_debug_annotations == DebugAnnotations.ENABLED_ALL.value:
            flask_app.remote_control_vector.vector.camera.image_annotator.enable_annotator('robotState')
        else:
            flask_app.remote_control_vector.vector.camera.image_annotator.disable_annotator('robotState')
    return ""


@flask_app.route('/setFreeplayEnabled', methods=['POST'])
def handle_setFreeplayEnabled():
    """Called from Javascript whenever freeplay mode is toggled on/off"""
    message = json.loads(request.data.decode("utf-8"))
    isFreeplayEnabled = message['isFreeplayEnabled']
    if flask_app.remote_control_vector:
        connection = flask_app.remote_control_vector.vector.conn
        if isFreeplayEnabled:
            connection.release_control()
        else:
            connection.request_control()
            # started_control(flask_app.remote_control_vector.vector)

    return ""


@flask_app.route('/keydown', methods=['POST'])
def handle_keydown():
    """Called from Javascript whenever a key is down (note: can generate repeat calls if held down)"""
    return handle_key_event(request, is_key_down=True)


@flask_app.route('/keyup', methods=['POST'])
def handle_keyup():
    """Called from Javascript whenever a key is released"""
    return handle_key_event(request, is_key_down=False)


@flask_app.route('/dropDownSelect', methods=['POST'])
def handle_dropDownSelect():
    """Called from Javascript whenever an animSelector dropdown menu is selected (i.e. modified)"""
    message = json.loads(request.data.decode("utf-8"))

    item_name_prefix = "animSelector"
    item_name = message['itemName']

    if flask_app.remote_control_vector and item_name.startswith(item_name_prefix):
        item_name_index = int(item_name[len(item_name_prefix):])
        flask_app.remote_control_vector.set_anim(item_name_index, message['selectedIndex'])

    return ""


@flask_app.route('/animTriggerDropDownSelect', methods=['POST'])
def handle_animTriggerDropDownSelect():
    """Called from Javascript whenever the animTriggerSelector dropdown menu is selected (i.e. modified)"""
    message = json.loads(request.data.decode("utf-8"))
    selected_anim_trigger_name = message['animTriggerName']
    flask_app.remote_control_vector.selected_anim_trigger_name = selected_anim_trigger_name
    return ""


@flask_app.route('/sayText', methods=['POST'])
def handle_sayText():
    """Called from Javascript whenever the saytext text field is modified"""
    message = json.loads(request.data.decode("utf-8"))
    if flask_app.remote_control_vector:
        flask_app.remote_control_vector.text_to_say = message['textEntered']
    return ""


@flask_app.route('/updateVector', methods=['POST'])
def handle_updateVector():
    if flask_app.remote_control_vector:
        flask_app.remote_control_vector.update()
        action_queue_text = ""
        i = 1
        for action in flask_app.remote_control_vector.action_queue:
            action_queue_text += str(i) + ": " + flask_app.remote_control_vector.action_to_text(action) + "<br>"
            i += 1

        return "Action Queue:<br>" + action_queue_text + "\n"
    return ""


@flask_app.route('/eval', methods=['POST'])
def handle_eval():
    message = json.loads(request.data.decode("utf-8"))
    status = False
    print("try to eval", message)
    robot = flask_app.remote_control_vector.vector

    # import pdb;
    # pdb.set_trace()

    try:
        result = eval(message["textEntered"])
        status = True
    except Exception as e:
        result = str(e)

    if status:
        try:
            result = json.dumps(result)
        except:
            result = "<not encodable>"
    return {"status": status, "result": result}


def run():
    # args = util.parse_command_args()

    done = threading.Event()
    robot = Nodeps(enable_face_detection=True, enable_custom_object_detection=True)
    robot.connect(timeout=30)

    flask_app.remote_control_vector = RemoteControlVector(robot)
    flask_app.display_debug_annotations = DebugAnnotations.ENABLED_ALL.value

    robot.camera.init_camera_feed()
    # robot.behavior.drive_off_charger()
    # started_control(robot)

    robot.camera.image_annotator.add_annotator('robotState', RobotStateDisplay)

    audio_main(robot)
    flask_helpers.run_flask(flask_app, enable_flask_logging=False, open_page=False)


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt as e:
        pass
    except anki_vector.exceptions.VectorConnectionException as e:
        sys.exit("A connection error occurred: %s" % e)
