import argparse
import sys
import logging

import serial
import time
import fix_path
from dynamixel import protocol2, servodata, servo

#logging.getLogger('protocol2').setLevel(logging.DEBUG)
logging.getLogger('servo').setLevel(logging.CRITICAL)
ADDRESS = 2


uart = serial.Serial('/dev/ttyUSB0', 1000000, timeout=1.0)
bus = protocol2.Protocol2Bus(uart)

servo_model = bus.ping(ADDRESS)
if servo_model is None:
    print("Unable to find servo at address {}".format(ADDRESS))
servo_data = servodata.get_servo(servo_model)
if servo_data is None:
    print("Unknown servo type: {}".format(servo_model))
servo_2 = servo.Servo(bus, ADDRESS, servo_data)


servo_2.set_led(1)
time.sleep(1)
servo_2.set_led(2)
time.sleep(1)
servo_2.set_led(4)
time.sleep(1)

servo_2.set_goal_position(0)
time.sleep(1)
print(servo_2.get_present_position(), '=0?')
servo_2.set_goal_position(45)
time.sleep(1)
print(servo_2.get_present_position(), '=45?')
servo_2.set_goal_position(-45)
time.sleep(1)
print(servo_2.get_present_position(), '=-45?')

#for i in range(1000):
#    print(servo_2.get_present_position())
