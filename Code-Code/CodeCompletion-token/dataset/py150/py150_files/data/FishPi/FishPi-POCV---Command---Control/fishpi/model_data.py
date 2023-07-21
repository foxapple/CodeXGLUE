
#
# FishPi - An autonomous drop in the ocean
#
# POCVModelData
#  - Internal model containing FishPi POCV state


class POCVModelData:
    """ Internal model containing FishPi POCV state. """

    def __init__(self):
        # GPS
        self.has_GPS = False
        self.fix = 0
        self.lat = 0.0
        self.lon = 0.0
        self.gps_heading = 0.0
        self.speed = 0.0
        self.altitude = 0.0
        self.num_sat = 0

        # time
        self.has_time = False
        self.timestamp = ''
        self.datestamp = ''

        # compass
        self.has_compass = False
        self.compass_heading = 0.0
        self.compass_pitch = 0.0
        self.compass_roll = 0.0

        # magnetometer
        self.has_magnetometer = False
        self.magnet_x = 0.0
        self.magnet_y = 0.0
        self.magnet_z = 0.0

        # gyro
        self.has_gyro = False

        # accelerometer
        self.has_accelerometer = False
        self.accelerometer_x = 0.0
        self.accelerometer_y = 0.0
        self.accelerometer_z = 0.0

        # temperature
        self.has_temperature = False
        self.temperature = 0.0
