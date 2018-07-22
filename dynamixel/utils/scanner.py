import argparse
import sys
import logging

import serial
from .. import protocol2, servodata, servo

logging.getLogger('dynamixel.protocol2').setLevel(logging.CRITICAL)

def do_scan(port, baud, timeout):
    uart = serial.Serial(port, baud, timeout=timeout)
    bus = protocol2.Protocol2Bus(uart)


    print("Scanning {} at baud {}".format(port, baud))
    for address in range(254):
        servo_model = bus.ping(address)
        print("{}/{}".format(address, 254), end="\r")
        if servo_model != None:
            servo_data = servodata.get_servo(servo_model)
            if servo_data == None:
                servo_name = "Unknown Servo Model"
            else:
                servo_name = servo_data['name']
            print("Found an {} at address {}".format(servo_name, address))

    print()
    print("Done")


def main(args):
    parser = argparse.ArgumentParser(description='Scan a TTY for dynamizel servos')
    parser.add_argument('--port', help='A TTY to serach (eg /dev/ttyUSB0)', default='/dev/ttyUSB0')
    parser.add_argument('--baud', help='Baud rate (eg 115200)', type=int, default=1000000)
    parser.add_argument('--timeout', help='How long to wait before deciding a servo is not present', type=float, default=(5/254))

    args = parser.parse_args()
    do_scan(args.port, args.baud, args.timeout)


if __name__ == "__main__":
    main(sys.argv[:1])
