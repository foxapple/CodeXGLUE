#
# FishPi - An autonomous drop in the ocean
#
# TODO: -Enable for RaspberryPi as well. BBB-specific stuff from here should
#        go to the platform library

# how to make the fishpi directory available everywhere?
import hw_platform.hw_config as hw_config

if hw_config.platform == 'BBB':
    import Adafruit_BBIO.UART as UART

import gps
import os
import psutil
import serial
from subprocess import call
import logging


class GPSDError(Exception):
    """Exception indicating that an error occured while working with GPSD"""
    pass


class gpsdInterface():

    def __init__(self, interface="UART4", hw_interface="/dev/ttyO4",
            debug=False):
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        self.debug = debug
        self.uart = interface
        self.tty = hw_interface
        self.num_sat = 0

        # Default answer. Defined here to include num_sat
        self.default_return = (
            1,      # fix
            0.0,    # lat
            0.0,    # lon
            0.0,    # heading
            0.0,    # speed
            0.0,    # altitude
            self.num_sat,  # num_sat
            "",     # timestamp
            "")     # datestamp

        self.latest_return = self.default_return

        if hw_config.platform is None:
            logging.error("GPSD Interface:\tHardware platform is not " +
                "specified! Won't set up sensor.")
            return 1

        # Do setup for BeagleBone Black
        if hw_config.platform == 'BBB':
            if not self.setup_bbb():
                return 1

        # Do setup for RaspberryPi
        elif hw_config.platform == 'RPi':
            pass  # nothing to be done here

        # stop gpsd if it is running
        self.stop_gpsd()

        call(["gpsd", self.tty])
        self.session = gps.gps(mode=gps.WATCH_ENABLE)
        logging.info("GPSD:\tInitialization complete.")

    # This is untested!!
    def stop_gpsd(self):
        """ Searches for running instances of gpsd and kill them """
        for proc in psutil.process_iter():
            if proc.name == "gpsd":
                os.kill(proc.pid)

    def setup_bbb(self):
        num_failed_tries = 0
        while not self.setup_bbb_uart():
            if num_failed_tries < 10:
                logging.error("GPSD:\tCould not connect to " +
                    "serial interface. Trying again..")
                num_failed_tries += 1
            else:
                logging.error("GPSD:\tFailed to connect to " +
                    "serial interface. Aborting.")
                return False
        return True

    def setup_bbb_uart(self):
        # Is this necessary if I don't want to use it myself??
        UART.setup(self.uart)
        self.ser = serial.Serial(port=self.tty, baudrate=9600)
        self.ser.close()
        self.ser.open()
        if self.ser.isOpen():
            return True
        else:
            return False

    def tear_down(self):
        self.session.close()
        call(["killall", "gpsd"])
        if hw_config.platform == 'BBB':
            self.ser.close()
        # UART.cleanup(uart)    # not functional right now according to Adafruit
        logging.info("GPSD:\tTear-down complete.")
        return 0

    def read_raw_gpsd_data(self):
        """Read the newest data from gpsd and return it"""
        try:
            if self.session.waiting():
                report = self.session.next()
                return report
            else:
                return None
        except StopIteration:
            raise GPSDError()

    def read_sensor(self):
        """Read the newest data from gpsd and return a formatted version.
            Not active right now."""
        data = self.read_raw_gpsd_data()
        if data is None:
            return self.latest_return

        if data['class'] == 'TPV':
            if data.get('mode') == 1:  # really a number, not a string?
                return self.default_return
            else:
                self.latest_return = (
                    data.get('mode'),
                    data.get('lat'),
                    data.get('lon'),
                    data.get('track'),
                    data.get('speed'),
                    self.num_sat,
                    data['time'].split('T')[1],
                    data['time'].split('T')[2])
                return self.latest_return
        elif data['class'] == 'SKY':
            if 'satellites' in data.keys():
                self.num_sat = len(data['satellites'])
            else:
                self.num_sat = 0
        else:
            return self.latest_return


if __name__ == "__main__":
    from time import sleep
    gps_handler = gpsdInterface(debug=True)
    print 'FishPi gpsd Interface Example'
    while True:
        print gps_handler.read_raw_gpsd_data()
        sleep(1)
