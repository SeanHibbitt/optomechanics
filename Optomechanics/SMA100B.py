# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 12:06:39 2024

@author: Sean Hibbitt
Created from sumits 'class 1.py' code
"""

from DeviceClasses import Device



class Signal_Generator(Device):
    """

    Class for controlling the SMA100B signal generator from rhode and schwarz
    manual: https://www.rohde-schwarz.com/uk/manual/r-s-sma100b-user-manual-manuals_78701-434880.html
    """
    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs, )
        
        
    def close(self,):
        #self.turn_mw("Off")
        Device.close(self)
        return self 
        
    def set_mw_frequency(self,mw_freq):
        self.write('FREQ:FIX'+' '+str(mw_freq))
        
    def read_mw_frequency(self):
        return self.query('FREQ:FIX?')
    
    def set_mw_power(self,mw_power):
        self.write('POW:LEV'+' '+str(mw_power))

    def read_mw_power(self):
        return self.query('POW:LEV?')
    
    def turn_mw(self,OnOff):
        self.write('OUTP:STAT'+' '+str(OnOff))