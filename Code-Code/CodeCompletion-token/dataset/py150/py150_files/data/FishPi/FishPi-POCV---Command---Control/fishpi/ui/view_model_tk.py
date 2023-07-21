#
# FishPi - An autonomous drop in the ocean
#
# Controller for View <-> onboard kernel
# View Model for POCV MainView
#

import logging
import math
import os

from PIL import Image
import Tkinter

class MainViewController:
    """ Coordinator between UI and main control layers. """
    
    def __init__(self, kernel, view_model):
        self._kernel = kernel
        self.model = view_model
    
    def update(self):
        """ Updates view model from kernel. """
        # GPS data
        self.model.GPS_latitude.set(self._kernel.data.lat)
        self.model.GPS_longitude.set(self._kernel.data.lon)
        
        self.model.GPS_heading.set(self._kernel.data.gps_heading)
        self.model.GPS_speed.set(self._kernel.data.speed)
        self.model.GPS_altitude.set(self._kernel.data.altitude)
        
        self.model.GPS_fix.set(self._kernel.data.fix)
        self.model.GPS_satellite_count.set(self._kernel.data.num_sat)
        
        # compass data
        self.model.compass_heading.set(self._kernel.data.compass_heading)
        
        # time data
        self.model.time.set(self._kernel.data.timestamp.isoformat())
        self.model.date.set(self._kernel.data.datestamp.isoformat())
        
        # other data
        self.model.temperature.set(self._kernel.data.temperature)
    
    @property
    def last_img(self):
        return self._kernel.last_img
    
    # Control modes (Manual, AutoPilot)
    def set_manual_mode(self):
        """ Stops navigation unit and current auto-pilot drive. """
        self._kernel.set_manual_mode()
    
    def set_auto_pilot_mode(self):
        """ Stops current manual drive and starts navigation unit. """
        self._kernel.set_auto_pilot_mode()
    
    def halt(self):
        """ Commands the NavigationUnit and Drive Control to Halt! """
        self._kernel.halt()
    
    @property
    def auto_mode_enabled(self):
        return self._kernel.auto_mode_enabled
    
    # Drive control
    # temporary direct access to DriveController to test hardware.
    
    def set_throttle(self, throttle_level):
        throttle_act = float(throttle_level)/100.0
        # adjustment for slider so min +/- .3 so if in .05 to .3 range, jump to .3
        if throttle_act > 0.05 and throttle_act < 0.3:
            throttle_act = 0.3
        elif throttle_act < -0.05 and throttle_act > -0.3:
            throttle_act = -0.3
        self._kernel.set_throttle(throttle_act)
    
    def set_steering(self, angle):
        angle_in_rad = (float(angle)/180.0)*math.pi
        # adjustment for slider in opposite direction - TODO - move to drive controller
        angle_in_rad = angle_in_rad * -1.0
        self._kernel.set_steering(angle_in_rad)
    
    # Route Planning and Navigation
    def set_speed(self, speed):
        """ Commands the NavigationUnit to set and hold a given speed. """
        self._kernel.set_speed(float(speed))
    
    def set_heading(self, heading):
        """ Commands the NavigationUnit to set and hold a given heading. """
        self._kernel.set_heading(float(heading))
    
    def navigate_to(self):
        """ Commands the NavigationUnit to commence navigation of a route. """
        #self._kernel.navigate_to(route)
        pass
    
    def get_current_map(self):
        return Image.open(os.path.join(self._kernel.config.resources_folder(), 'bournville.tif'))
    
    def load_gpx(self):
        # tk specific
        import tkFileDialog
        default_path = os.path.join(self._kernel.config.resources_folder(), 'sample_routes')
        filename = tkFileDialog.askopenfilename(initialdir=default_path, title="Select GPX file to load", filetypes=[("GPX", "*.GPX; *.gpx")])
        if os.path.exists(filename):
            logging.info("UI:\tloading %s" % filename)
            gpx = self._kernel.load_gpx(filename)
            # update list
            self.model.clear_waypoints()
            for route in gpx.routes:
                for point in route.points:
                    wp_str = '({0}:{1},{2})'.format(point.name, point.latitude, point.longitude)
                    logging.info(wp_str)
                    wp_str2 = '{0}  {1}, {2}    X'.format(point.name, point.latitude, point.longitude)
                    self.model.waypoints.append(wp_str2)
    
    def save_gpx(self):
        pass


class MainViewModel:
    """ UI Model containing bindable variables. """
    
    def __init__(self, root):
        # GPS data
        self.GPS_latitude = Tkinter.StringVar(master=root, value="##d ##.####' X")
        self.GPS_longitude = Tkinter.StringVar(master=root, value="##d ##.####' X")
        
        self.GPS_heading = Tkinter.DoubleVar(master=root, value=0.0)
        self.GPS_speed = Tkinter.DoubleVar(master=root, value=0.0)
        self.GPS_altitude = Tkinter.DoubleVar(master=root, value=0.0)
        
        self.GPS_fix = Tkinter.IntVar(master=root, value=0)
        self.GPS_satellite_count = Tkinter.IntVar(master=root, value=0)
        
        # compass data
        self.compass_heading = Tkinter.DoubleVar(master=root, value=0.0)
        
        # time data
        self.time = Tkinter.StringVar(master=root, value="hh:mm:ss")
        self.date = Tkinter.StringVar(master=root, value="dd:MM:yyyy")
        
        # other data
        self.temperature = Tkinter.DoubleVar(master=root, value=0.0)
        
        # other settings
        self.capture_img_enabled = Tkinter.IntVar(master=root, value=0)
        
        # route data
        self.waypoints = []
    
    def clear_waypoints(self):
        del self.waypoints[0:len(self.waypoints)]