# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 14:57:25 2024

@author: seanh
"""

from DeviceClasses import Device
import pyvisa
import numpy as np


class DMM6500(Device):
    """

    Keithley multimeter remote access code:
        
    manuals:
        https://download.tek.com/manual/EN-DMM6500-900-01_Users_Manual_DMM6500-900-01A.pdf
        https://download.tek.com/manual/DMM6500-901-01B_Sept_2019_Ref.pdf

    Aims:
    Perform a voltage/current/resitance measurement

    """
    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs, )
        
    def open(self,):
        Device.open(self)
        
        return self

    
    def update_timeout_wrt_aperture(self,func ):
        """
        updates the timeout wrt to the aperture of a given function
        """
        volt_aper = self.query_sense_function_aperture(func)
        self._device.timeout = volt_aper * 1.1

        return 

    def update_timeout_startup(self,):
        """
        checks aperatures of voltage, current, and resistance, before updating timeout
        """
        volt_aper = self.query_sense_function_aperture("volt")
        curr_aper = self.query_sense_function_aperture("curr")
        resi_aper = self.query_sense_function_aperture("res")

        max_aper = np.max([volt_aper,curr_aper, resi_aper])
        self._device.timeout = max_aper * 1.1
    
    def query_sense_function_aperture(self, function):
        """
        queries the current aperture, see measure for function 
        details
        """
        return float(self.query(f":{function}:APER?"))

    def measure(self, function,):
        """
        Implements the :MEASure? command as see in 
        page 13-7 of the reference manual
        function inputs are:
        VOLTage[:DC] RESistance TEMPerature VOLTage[:DC]:RATio
        VOLTage:AC FRESistance CONTinuity DIGitize:VOLTage
        CURRent[:DC] DIODe FREQuency[:VOLTage] DIGitize:CURRent
        CURRent:AC CAPacitance PERiod[:VOLTage
        """
        return self.query(f"meas:{function}?")
        
    def number_of_errors(self):
        """ pg 13-165"""
        return self.query("syst:err:count?")
    
    def oldest_error(self):
        """pg 13-164"""
        return self.query("SYST:ERR:NEXT? ")

    #%helper functions

    def current_errors(self):
        """
        returns a list of the number of errors present
        in the error bus.
        """
        error_list = []
        for i in self.number_of_errors():
            error_list.append(self.oldest_error())
        return error_list



        
if __name__ == "__main__":
    print("starting:")

    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    print("hey")
    with DMM6500('TCPIP0::169.254.117.116::inst0::INSTR') as DMM:
        print(DMM.IDN_query())
        print("")

    
    #DMM = DMM6500("TCPIP0::169.254.117.116::inst0::INSTR")  
    #print(DMM.IDN_query())
    #DMM._device.before_close()
    #DMM._device.close()


    