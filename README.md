# dynamixel-python
Dynamixel servos speak half-duplex UART at a couple of standard baud rates. Since I've already 
written the protocol handling (originally to run it on micropython) I thought I'd whip it into
a halfway decent module. I don't expect anyone else to use this because dynamixel publishes a 
SDK. But if you're a python coder like me, or you want to inspect how the protocol works, feel 
free to take a look. 

There are a couple useful commands you can use:

* `python -m dynamixel.gui` Will open a GUI to allow you to configure servos

* `python -m dynamixel.utils.scanner` Will list the servos plugged in. This supports `--port` 
`--baud` and `--timeout` command line flags.

You can also import the module and work with servos in a somewhat sensible manner, such as:
```
from dynamixel import protocol2, servo, servodata

# Connect to the bus
uart = serial.Serial('/dev/ttyUSB0', 1000000, timeout=1.0)
bus = protocol2.Protocol2Bus(uart)

# Find the servo, identify it and formalize the connection
servo_model = bus.ping(ADDRESS)
if servo_model is None:
    print("Unable to find servo at address {}".format(ADDRESS))
servo_data = servodata.get_servo(servo_model)
if servo_data is None:
    print("Unknown servo type: {}".format(servo_model))
else:
    print("Found servo {} at {}".format(servo_data['name'], ADDRESS))
servo_2 = servo.Servo(bus, ADDRESS, servo_data)

servo_2.set_led(1)  # Color = Red
servo_2.set_position(90) # Degrees
```
To see what configuration a servo has, you can use dir(servo_object). The attributes are created
at runtime from the json file, so it's a pain to list them statically.

I may tidy up the servo creation API at some point in the near future.


# Supported Hardware

Currently it supports the XL-320 servo (the only ones I physically have), but adding new ones 
should just be a case of adding a json file with the register map into the servo-database folder.
