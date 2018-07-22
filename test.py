import servo
import protocol2
import servodata
import serial

uart = serial.Serial('/dev/ttyUSB0', 1000000, timeout=1.0)
bus = protocol2.Protocol2Bus(uart)

servo = servo.Servo(bus)
