#
# FishPi - An autonomous drop in the ocean
#
# View Controller for RPC approach
# View Model for POCV MainView
#

import os
import logging
import math
import wx

from PIL import Image

class MainViewController:
    """ Coordinator between UI and main control layers. """
    
    def __init__(self, rpc_client, view_model, config):
        self._rpc_client = rpc_client
        self.model = view_model
        self.config = config
    
    # rpc related items
    def set_rpc_client(self, rpc_client):
        self._rpc_client = rpc_client
    
    def lost_rpc_client(self):
        self._rpc_client = None
    
    def close_connection(self):
        if self._rpc_client:
            self._rpc_client.close_connection()
    
    def update(self):
        """ Updates view model from rpc channel. """
        if self._rpc_client:
            # trigger update (async though so only pick up response on next update)
            self._rpc_client.update()
        
            # GPS data
            self.model.GPS_latitude = self._rpc_client.data.lat
            self.model.GPS_longitude = self._rpc_client.data.lon
        
            self.model.GPS_heading = self._rpc_client.data.gps_heading
            self.model.GPS_speed = self._rpc_client.data.gps_speed
            self.model.GPS_altitude = self._rpc_client.data.altitude
        
            self.model.GPS_fix = self._rpc_client.data.fix
            self.model.GPS_satellite_count = self._rpc_client.data.num_sat
        
            # compass data
            self.model.compass_heading = self._rpc_client.data.compass_heading
        
            # time data
            self.model.time = self._rpc_client.data.timestamp
            #strftime(self._rpc_client.data.timestamp).isoformat()
            self.model.date = self._rpc_client.data.datestamp
            #strftime(self._rpc_client.data.datestamp).isoformat()
        
            # other data
            self.model.temperature = self._rpc_client.data.temperature

            # some debugging:
            logging.debug("GPS:\tLat = %s" % str(self.model.GPS_latitude))
            logging.debug("GPS:\tLon = %s" % str(self.model.GPS_longitude))
            logging.debug("GPS:\tHead = %s" % str(self.model.GPS_heading))
            logging.debug("GPS:\tSpeed = %s" % str(self.model.GPS_speed))
            logging.debug("GPS:\tAlt = %s" % str(self.model.GPS_altitude))
            logging.debug("Compass:\tHead = %s" % str(self.model.compass_heading))
    
    # Control modes (Manual, AutoPilot)
    def set_manual_mode(self):
        """ Stops navigation unit and current auto-pilot drive. """
        self._rpc_client.set_manual_mode()
    
    def set_auto_pilot_mode(self):
        """ Stops current manual drive and starts navigation unit. """
        self._rpc_client.set_auto_mode()
    
    def halt(self):
        """ Commands the NavigationUnit and Drive Control to Halt! """
        self._rpc_client.halt()
    
    @property
    def auto_mode_enabled(self):
        return self._rpc_client.auto_mode_enabled
    
    # Drive control
    # temporary direct access to DriveController to test hardware.
    
    def set_drive(self, throttle_level, angle):
        # throttle
        throttle_act = float(throttle_level)/100.0
        #
        # speed limiter!!
        #
        #throttle_act *= 0.2
        
        # adjustment for slider so min +/- .3 so if in .05 to .3 range, jump to .3
        if throttle_act > 0.05 and throttle_act < 0.3:
            throttle_act = 0.3
        elif throttle_act < -0.05 and throttle_act > -0.3:
            throttle_act = -0.3
        
        # steering
        angle_in_rad = (float(angle)/180.0)*math.pi
        # adjustment for slider in opposite direction - TODO - move to drive controller
        #angle_in_rad = angle_in_rad * -1.0
    
        # call rpc
        self._rpc_client.set_drive(throttle_act, angle_in_rad)
    
    # Route Planning and Navigation
    def set_navigation(self, speed, heading):
        """ Commands the NavigationUnit to set and hold a given speed and heading. """
        self._rpc_client.set_navigation(float(speed), float(heading))
        
    def navigate_to(self):
        """ Commands the NavigationUnit to commence navigation of a route. """
        #self._rpc_client.navigate_to(route)
        pass
    
    def get_current_map(self):
        imageFile = os.path.join(self.config.resources_folder(), 'bournville.tif')
        #image = wx.BitmapFromImage(Image.open(imageFile))

        image = wx.BitmapFromImage(wx.Image(imageFile, wx.BITMAP_TYPE_TIF))
        return image
    
    def load_gpx(self):
        pass
    
    def save_gpx(self):
        pass

class MainViewModel:
    """ UI Model containing bindable variables. """
    
    def __init__(self):
        # GPS data
        self.GPS_latitude = "##d ##.####' X"
        self.GPS_longitude = "##d ##.####' X"
        
        self.GPS_heading = 0.0
        self.GPS_speed = 0.0
        self.GPS_altitude = 0.0
        
        self.GPS_fix = False
        self.GPS_satellite_count = 0
        
        # compass data
        self.compass_heading = 0.0
        
        # time data
        self.time = "hh:mm:ss"
        self.date = "dd:MM:yyyy"
        
        # other data
        self.temperature = 0.0
        
        # other settings
        self.capture_img_enabled = True
        
        # route data
        self.waypoints = []
    
    def clear_waypoints(self):
        del self.waypoints[0:len(self.waypoints)]