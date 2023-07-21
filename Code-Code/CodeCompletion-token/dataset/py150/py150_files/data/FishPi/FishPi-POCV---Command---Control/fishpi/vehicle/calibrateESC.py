#!/usr/bin/python

#
# FishPi - An autonomous drop in the ocean
#
# Calibrate ESC through PWM controller
#

import raspberrypi

from time import sleep
from drive_controller import DriveController
from drive_controller import AdafruitDriveController

if __name__ == "__main__":
    print "Calibrating ESC"
    drive = AdafruitDriveController(debug=True, i2c_bus=raspberrypi.i2c_bus())

    raw_input("Power on ESC and enter calibration mode... Then press <ENTER>...")

    print "run full ahead for 5 sec..."
    drive.set_throttle(1.0)
    sleep(5)
    
    print "returning to neutral for 5 sec"
    drive.set_throttle(0.0)
    sleep(5)

    print "run full reverse for 5 sec"
    drive.set_throttle(-1.0)
    sleep(5)
    
    print "returning to neutral"
    drive.set_throttle(0.0)
    sleep(5)

    print "calibration should be complete!"

