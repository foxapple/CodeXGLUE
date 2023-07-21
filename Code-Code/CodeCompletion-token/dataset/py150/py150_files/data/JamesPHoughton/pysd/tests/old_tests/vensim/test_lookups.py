from __future__ import division                                 
import numpy as np                                              
from pysd import functions                                      
from pysd import builder                                        
                                                                
class Components(builder.ComponentClass):                       
                                                                
    def lookup_function_call(self):
        """Type: Flow or Auxiliary
        """
        return self.lookup_function_table(self.accumulation()) 

    def rate(self):
        """Type: Flow or Auxiliary
        """
        return self.lookup_function_call() 

    def daccumulation_dt(self):                       
        return self.rate()                           

    def accumulation_init(self):                      
        return 0                           

    def accumulation(self):                            
        """ Stock: accumulation =                      
                 self.rate()                          
                                             
        Initial Value: 0                    
        Do not overwrite this function       
        """                                  
        return self.state["accumulation"]              
                                             
    def lookup_function_table(self, x):                                      
        return self.functions.lookup(x,                   
                                     self.lookup_function_table.xs,          
                                     self.lookup_function_table.ys)          
                                                          
    lookup_function_table.xs = [0.0, 0.25, 0.5, 0.75, 1.0]                                            
    lookup_function_table.ys = [0.1, 0.025, 0.0, -0.025, -0.1]                                            
                                                          
    def final_time(self):
        """Type: Flow or Auxiliary
        """
        return 100 

    def initial_time(self):
        """Type: Flow or Auxiliary
        """
        return 0 

    def saveper(self):
        """Type: Flow or Auxiliary
        """
        return self.time_step() 

    def time_step(self):
        """Type: Flow or Auxiliary
        """
        return 1 

