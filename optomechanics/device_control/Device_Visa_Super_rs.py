# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 12:14:00 2024

@author: Sean Hibbitt
Email: Sean.hibbitt.2019@;ive.rhul.ac.uk
phone number: 07808665776

This is 
"""


import pyvisa  as visa
from RsInstrument import RsInstrument
from pyvisa import constants
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
from optomechanics.data_management import save_data_3 as save_data_3_temp
from optomechanics.device_control.Device_Visa_Super import Device as mainDevice


#%%Define Class
class Device(mainDevice):
    
    
    """
    super which edits Device_Visa_Super.Device with the RsInstruments version of PyVisa
    
    contains default scpi commands. 
    These were taken from the ZNA manual: https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/pdm/cl_manuals/user_manual/1178_6462_01/ZNA_UserManual_en_34.pdf

    SCPI wikipage: https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments
    """
    
    def __init__(self, address, baud_rate = 9600, query_delay = 0, timeout = 10000  ):
        Device.__init__(self, address, baud_rate, timeout = 25000)

    def open(self):
        """ Opens the device via visa"""
        self._device = RsInstrument(self.address, True, True)
        #setup device parameters
        #self._device.baud_rate = self.baud_rate
        #self._device.query_delay = self.query_delay
        #self._device.visa_timeout = self.timeout
        #self.CLS()
        #self.RST()
        return self

    @staticmethod 
    def connected_devices():
        """
        return a list of connected resources via RsInstrument
        """
        instr_list = RsInstrument.list_resources("?*")
        return instr_list