"""The servo databse contains the description of a servo as is necessary
for code to talk to it. The most important part of the servo description is
the register map, mapping from name to address and size, along with some
data about how to interpret the data"""
import json
import os

SERVO_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'servo-database'
)
SERVO_DATA = {}


def get_servo(model_number):
    """Returns the servo data for a specified model number. Returns None
    if the servo is unknown"""
    return SERVO_DATA.get(model_number)


def load_database(directory):
    """Loads servo data from json files in a specified directory"""
    for file_name in os.listdir(directory):
        if file_name.endswith('json'):
            raw_data = json.load(open(os.path.join(directory, file_name)))
            SERVO_DATA[raw_data['model_number']] = raw_data


load_database(SERVO_DIRECTORY)
