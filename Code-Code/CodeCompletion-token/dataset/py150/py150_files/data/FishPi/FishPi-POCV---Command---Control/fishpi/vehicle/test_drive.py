#!/usr/bin/python

#
# FishPi - An autonomous drop in the ocean
#
# Simple test of PWM motor and servo drive
#

import raspberrypi

from time import sleep
from drive_controller import AdafruitDriveController

if __name__ == "__main__":
    print "testing drive controller..."
    drive = AdafruitDriveController(debug=True, i2c_bus=raspberrypi.i2c_bus())

    print "run full ahead for 5 sec..."
    drive.set_throttle(1.0)
    sleep(5)
    
    print "run 50% ahead for 5 sec..."
    drive.set_throttle(0.5)
    sleep(5)

    print "run 0% for 5 sec..."
    drive.set_throttle(0.0)
    sleep(5)

    print "run 50% reverse for 5 sec"
    drive.set_throttle(-0.5)
    sleep(5)
    
    print "run full reverse for 5 sec"
    drive.set_throttle(-1.0)
    sleep(5)
    
    print "and back to neutral..."
    drive.set_throttle(0.0)
    sleep(5)

    print "check out of bounds errors"
    try:
        drive.set_throttle(15.0)
    except ValueError:
        print "caught 15"
    
    try:
        drive.set_throttle(-10.0)
    except ValueError:
        print "caught -10"

    # test steering
    print "steer hard to port for 5 sec"
    drive.set_steering(-0.785398)
    sleep(5)

    print "steer to port for 5 sec"
    drive.set_steering(-0.3927)
    sleep(5)
    
    print "and back to neutral..."
    drive.set_steering(0.0)
    sleep(5)

    print "steer to starboard for 5 sec"
    drive.set_steering(0.3927)
    sleep(5)

    print "steer hard to starboard for 5 sec"
    drive.set_steering(0.785398)
    sleep(5)

    print "and back to neutral..."
    drive.set_steering(0.0)
    sleep(5)

