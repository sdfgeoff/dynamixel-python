"""The viewer is the base-station of the robot, used to display the video
feed and telemetry. The video feed is routed into the camera as a normal
webcam using a module such as the Eachine ROTG02
This application prioritizes low latency on that video stream.
"""


import os
import logging

import serial
import serial.tools.list_ports
import gi
gi.require_version('Gtk', '3.0')  # noqa
from gi.repository import Gtk, GLib

import dynamixel.protocol2
import dynamixel.servo
import dynamixel.servodata


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
logging.getLogger('dynamixel.protocol2').setLevel(logging.CRITICAL)

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
UART_TIMEOUT = 5/254


class Configurator:
    """The main viewer window"""
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(BASE_PATH, "layout.glade"))

        self.builder.connect_signals({
            "close_window":self.close_window,
            "rescan_ports":self.rescan_ports,
            "connect":self.create_bus,
            "scan":self.start_scan,
            "select_servo":self.select_servo
        })

        window = self.builder.get_object("main_window")
        window.show_all()

        self._servo_list = Gtk.ListStore(int, str)
        self._setup_servo_list()
        self._insert_bauds()
        self.rescan_ports()

        self._scan_id = 0
        self.bus = None
        self._current_servo = None


    def rescan_ports(self, *_args):
        """Checks for what ports are available"""
        LOGGER.info("Rescanning Ports")
        port_list = self.builder.get_object('port_lister')
        port_list.remove_all()
        for port in serial.tools.list_ports.comports():
            port_list.append_text(port.device)
        port_list.set_active(0)

    def _insert_bauds(self):
        """Inserts the baud rate options into the combo box"""
        bauds = [9600, 115200, 1000000]
        baud_list = self.builder.get_object('baud_lister')
        for baud in bauds:
            baud_list.append_text(str(baud))
        baud_list.set_active(0)

    def _setup_servo_list(self):
        """Creates the columns in the servo list panel"""
        list_view = self.builder.get_object('found_servos')
        list_view.set_model(self._servo_list)

        for i, column in enumerate(["Address", "Model"]):
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(column, cell, text=i)
            list_view.append_column(col)

    def create_bus(self, *_args):
        """Creates the bus used for talking to the servos. When it does this
        it clears out the list of known servos"""
        self.bus = None
        self._current_servo = None
        self._servo_list.clear()
        port = self.builder.get_object('port_lister').get_active_text()
        baud = int(self.builder.get_object('baud_lister').get_active_text())

        LOGGER.debug("Creating bus with port=%s and baud=%d", port, baud)
        if port and baud:
            self.bus = dynamixel.protocol2.Protocol2Bus(
                serial.Serial(port, baud, timeout=UART_TIMEOUT)
            )
        else:
            self.bus = None

    def start_scan(self, *_args):
        """Starts the scan for servos. The actual scanning is handled by the
        _continue_scan function"""
        if self.bus is None:
            self.create_bus()
        self._scan_id = 1
        self.builder.get_object('connect_button').set_sensitive(False)
        self.builder.get_object('scan_progress').set_fraction(0.0)
        GLib.idle_add(self._continue_scan)

    def _continue_scan(self):
        """Incrementally scans the bus for servos. This runs on a GTK idle_add
        timer so that it doesn't block the UI"""
        self._scan_id += 1
        if self.bus is None or self._scan_id > 254:
            LOGGER.info("Found %d servos", len(self._servo_list))
            self.builder.get_object('connect_button').set_sensitive(True)
            self.builder.get_object('scan_progress').set_fraction(1.0)
            return False

        self.builder.get_object('scan_progress').set_fraction(self._scan_id/253)
        servo_model = self.bus.ping(self._scan_id)
        if servo_model is not None:
            LOGGER.info("Found Servo at %d", self._scan_id)
            servo_data = dynamixel.servodata.get_servo(servo_model)
            if servo_data is None:
                servo_name = '??'
            else:
                servo_name = servo_data['name']
            self._servo_list.append([self._scan_id, servo_name])

        return True

    def select_servo(self, *_args):
        """Selects which servo the user wihes to edit"""
        path, _column = self.builder.get_object('found_servos').get_cursor()
        if path is not None:
            servo_id = self._servo_list.get_iter(path)
            servo_address = self._servo_list.get_value(servo_id, 0)
            LOGGER.debug("Clicked on servo at address %d", servo_address)
            if self.bus is None:
                LOGGER.warning("How do we have a servo listing and no bus?")
                return

            servo_model = self.bus.ping(servo_address)
            servo_data = dynamixel.servodata.get_servo(servo_model)
            self._current_servo = dynamixel.servo.Servo(
                self.bus, servo_address, servo_data
            )


    def close_window(self, *args):
        """Quits the program"""
        Gtk.main_quit(*args)



def main():
    """Runs the GUI"""
    _panel = Configurator()
    Gtk.main()
