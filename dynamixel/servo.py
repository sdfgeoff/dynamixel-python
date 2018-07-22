"""Contains the servo object, as well as the functions for converting from
an array of bytes to a more human readable format"""

import functools
import logging
import math

LOGGER = logging.getLogger(__name__)

class Servo:
    """Constructs a dynamixel servo from a python dict of registers, an
    address and a UART bus. This class handles the conversion from registers
    to nice function names. If you run dir(servo), you will get a list of
    set_<register> and get_<register> functions that correspond to the
    functionality of the servo. These are configured through the descriptor.
    Most descriptors should come from servodata.get_servo(model_number).

    This class also contains a list "on_hardware_error" which can contain
    callbacks to run when the servo reports a hardware error over it's status
    packet from a normal read/write.
    """
    def __init__(self, bus, address, descriptor=None):
        self.bus = bus
        self.address = address
        self.data = descriptor

        self.on_hardware_error = list()

        for register in self.data['register_map']:
            name = register['name'].lower().replace(' ', '_')
            if 'R' in register['access'].upper():
                self.__dict__['get_' + name] = functools.partial(
                    self.get_register,
                    register['address'],
                    register['size'],
                    register['display']
                )
            if 'W' in register['access'].upper():
                self.__dict__['set_' + name] = functools.partial(
                    self.set_register,
                    register['address'],
                    register['size'],
                    register['display']
                )

    def get_register(self, register, length, display_info):
        """Returns the value of a register, as parsed by the display_info"""
        got_data = self.bus.read(self.address, register, length)
        if got_data is None:
            LOGGER.error("Failed to read register {} of servo {}".format(register, self.address))
            return None

        self._check_hardware_error(got_data[0])
        return format_data(got_data[1:], display_info)

    def _check_hardware_error(self, byte):
        """Checks to see if the supplied byte indicates a hardware error on
        the servo. If it does, it runs any functions in the on_hardware_error
        list"""
        if byte != 0:
            LOGGER.warn("Hardware error on servo {}".format(self.address))
            for funct in self.on_hardware_error:
                funct(self)


    def set_register(self, register, length, display_info, value):
        """Returns True if succeeded, None if failed"""
        data_to_write = [0x01] * length
        for pos, data in enumerate(format_data_inverse(value, display_info)):
            data_to_write[-pos] = data

        result = self.bus.write(self.address, register, data_to_write)
        if result == None:
            LOGGER.error("Failed to set register {} of servo {}".format(register, self.address))
            return None

        self._check_hardware_error(result[0])
        return True

    def ping(self):
        """Returns True if the ping succeeds, otherwise it returns False"""
        return self.bus.ping(self.address) != None

    def __repr__(self):
        return "Servo {} ({})".format(self.address, self.data['name'])


def format_data(data, display_info):
    """Makes data display nicely. Used to convert from the bytes read
    on the register of the servo into something usable by the rest of the
    software"""
    if display_info['type'] == "bytes":
        return data

    combined = 0
    for pos, byte in enumerate(data):
        combined += byte << (8*pos)

    if "offset" in display_info:
        combined -= display_info['offset']

    if "scale" in display_info:
        combined *= display_info['scale']

    if display_info['type'] == 'int':
        return int(combined)

    if display_info['type'] == 'float':
        return float(combined)

    if display_info['type'] == "hex":
        return format(combined, 'x')

    if display_info['type'] == "bool":
        return bool(combined)

    return data


def format_data_inverse(data, display_info):
    """Does the opposide of format_data"""
    if display_info['type'] == "bytes":
        return data

    value = 0

    if display_info['type'] == "hex":
        value = int(data, 16)

    if display_info['type'] == 'int':
        value = int(data)

    if display_info['type'] == 'float':
        value = float(data)

    if display_info['type'] == 'bool':
        value = int(data)

    # Restrict range and correct
    if 'scale' in display_info:
        value = value / display_info['scale']
    if "offset" in display_info:
        value += display_info['offset']

    if 'min' in display_info:
        value = max(display_info['min'], value)
    if 'max' in display_info:
        value = min(display_info['max'], value)

    value = int(value)

    return list(value.to_bytes(math.floor((value.bit_length() + 7) / 8), 'little'))
