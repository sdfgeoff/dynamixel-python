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
            "select_servo":self.select_servo,
            "select_register":self.select_register,
        })

        window = self.builder.get_object("main_window")
        window.show_all()

        self._registers = []
        self._scan_id = 0
        self.bus = None
        self._current_servo = None
        self._servo_list = Gtk.ListStore(int, str)
        
        self._setup_servo_list()
        self._insert_bauds()
        self.rescan_ports()
        



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
        self.clear_servo_registers()
        port = self.builder.get_object('port_lister').get_active_text()
        baud = int(self.builder.get_object('baud_lister').get_active_text())

        LOGGER.debug("Creating bus with port=%s and baud=%d", port, baud)
        if port and baud:
            try:
                uart = serial.Serial(port, baud, timeout=UART_TIMEOUT)
            except:
                self.bus = None
            else:
                self.bus = dynamixel.protocol2.Protocol2Bus(uart)
        else:
            self.bus = None

    def start_scan(self, *_args):
        """Starts the scan for servos. The actual scanning is handled by the
        _continue_scan function"""
        if self.bus is None:
            self.create_bus()
        self._scan_id = 0
        self.builder.get_object('connect_button').set_sensitive(False)
        self.builder.get_object('scan_progress').set_fraction(0.0)
        GLib.idle_add(self._continue_scan)

    def _continue_scan(self):
        """Incrementally scans the bus for servos. This runs on a GTK idle_add
        timer so that it doesn't block the UI"""
        self._scan_id += 1
        if self.bus is None or self._scan_id > 253:
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
        
    def clear_servo_registers(self):
        for item in self._registers:
            item.destroy()
        self._registers = []
        
    def set_current_servo(self, servo):
        self._current_servo = servo
        listbox = self.builder.get_object('servo_parameter')
        self.clear_servo_registers()
        if servo is None:
            return
            
        self.items = []
        
        register_data = self._current_servo.get_register_data()
        if register_data is None:
            logging.warn("No register data for %s", self._current_servo)
            return
        for register in register_data:
            row = RegisterEntry(register)
            self._registers.append(row)
            listbox.add(row)
        listbox.show_all()
        
    def select_register(self, *args):
        row_item = self.builder.get_object('servo_parameter').get_selected_row()
        register_data = row_item.register_data
        if self._current_servo is None:
            return
            
        register_name = dynamixel.servo.format_register_name(register_data['name'])
        print(self._current_servo.__dict__[register_name]())
            
        
    def select_servo(self, *_args):
        """Selects which servo the user wihes to edit"""
        path, _column = self.builder.get_object('found_servos').get_cursor()
        self.clear_servo_registers()
        if path is not None:
            servo_id = self._servo_list.get_iter(path)
            servo_address = self._servo_list.get_value(servo_id, 0)
            LOGGER.debug("Clicked on servo at address %d", servo_address)
            if self.bus is None:
                LOGGER.warning("How do we have a servo listing and no bus?")
                return

            servo_model = self.bus.ping(servo_address)
            servo_data = dynamixel.servodata.get_servo(servo_model)
            self.set_current_servo(dynamixel.servo.Servo(
                self.bus, servo_address, servo_data
            ))


    def close_window(self, *args):
        """Quits the program"""
        Gtk.main_quit(*args)



class RegisterEntry(Gtk.ListBoxRow):
    def __init__(self, register_data):
        super().__init__()
        self.register_data = register_data
        
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        self.add(self.hbox)
        label = Gtk.Label(register_data['name'], xalign=0)
        self.hbox.pack_start(label, True, True, 0)



def main():
    """Runs the GUI"""
    _panel = Configurator()
    Gtk.main()
