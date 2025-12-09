# -*- coding: utf-8 -*-
"""
Created on Sunday 9th February 2025

@author: Sean Hibbitt
Email: Sean.hibbitt.2019@live.rhul.ac.uk
phone number: 07808665776

Aim:
    - convert basic commands from scipy to python to facilliate easier use

Notes:



"""

import time
from datetime import datetime
import numpy as np
import pyvisa  as visa
from pyvisa import constants
from .Device_Visa_Super import Device
import matplotlib.pyplot as plt
import pandas




class AFG1022(Device):
    """
    class for tektronix signal generator: AFG1022

    This is a basic signal generator that has a noise waveform function.
    While it doesn't specify the type of noise, on initial visual inspection it's white noise
    
    Tektronix manual: https://download.tek.com/manual/AFG1022-Quick-Start-User-Manual-EN.pdf
    tektronix programming manual: https://download.tek.com/manual/AFG1022-Programmer-Manual-EN.pdf
    
    
    """
    
    def __init__(self, address, baud_rate = 9600):
        Device.__init__(self, address, baud_rate, timeout = 25000)
    
    def set_output_state(self, state, source = 1):
        """
        turns on or off specific channels
        state in ["ON", "OFF", 1, 0, True, False]
        """
        self.write(f"OUTPut{source}:STATe {state}")

    def query_output_state(self, source):
        """
        
        """
        return self.query(f"OUTPut{source}:STATe?")

    def set_frequency(self, frequency,  source = 1 ):
        """
        set the output frequency of the source (Channel) in Hz
        """
        self.write(f"SOURce{source}:FREQuency:FIXed {frequency}Hz")

    def query_frequency(self, source = 1):
        """
        set the output frequency of the source (Channel) in Hz
        """
        return self.query(f"SOURce{source}:FREQuency:FIXed?")

    def set_output_waveform(self, waveform, source = 1):
        """
        set the output waveform for the specified channel/source
        See manual waveform types
        """
        self.write(f"SOURce{source}:FUNCtion:SHAPe {waveform}")

    def query_output_waveform(self, source = 1):
        """
        set the output waveform for the specified channel/source
        See manual waveform types
        """
        return self.query(f"SOURce{source}:FUNCtion:SHAPe?")

    def set_output_noise(self, source = 1):
        """
        helper function to set the waveform as noise
        """
        self.set_output_waveform("PRNoise", source)

    def set_voltage_offset(self, offset = 0, source = 1):
        """
        sets the voltage offset for a specified channel in milli-Voltz -> chosen 
        to help reduce chancel of overloading equipment.
        This should be set to 0 for most purposes, offset adds DC component.
        """
        self.write(f"SOURce{source}:VOLTage:LEVel:IMMediate:OFFSet {offset}mV")

    def query_voltage_offset(self, source = 1):
        """
        queries the voltage offset for a specified channel in milli-Voltz -> chosen 
        to help reduce chancel of overloading equipment.
        This should be set to 0 for most purposes, offset adds DC component.
        """
        return self.query(f"SOURce{source}:VOLTage:LEVel:IMMediate:OFFSet?")

    def set_output_amplitude(self, amplitude = 0, source = 1):
        """
        sets the amplitude for a specified channel in milli-Voltz (peak - peak).
        I'm assuming this means it's max noise amplitude is this

        The conversion to mV has been added by myself (sean) to reduce chance of
        overloading equipment as we should be working in mV most of the time.
        """

        #convert from mV to V:
        amplitude = amplitude/(1e3)

        self.write(f"SOURce{source}:VOLTage:LEVel:IMMediate:AMPLitude {amplitude}Vpp")

    def query_output_amplitude(self, source = 1):
        """
        Query the amplitude for a specified channel in Voltz (peak - peak).
        I'm assuming this means it's max noise amplitude is this

        """

        #convert from mV to V:
        amplitude = self.query(f"SOURce{source}:VOLTage:LEVel:IMMediate:AMPLitude?")
        #convert to mV
        #amplitude = float(amplitude)/1000
        return amplitude
    
    def next_error(self):
        return self.query("SYSTEM:ERROR:NEXT?")

    ## helper functions

    def set_noise(self, amplitude, source = 1, offset = 0):
        """
        helper function to set the noise output
        """
        self.set_output_noise(source)
        self.set_voltage_offset(offset, source)
        self.set_output_amplitude(amplitude, source)


    def query_state(self, source = 1):
        """
        helper function to set the noise output
        """
        escape = False
        while not escape:
            try:
                waveform = self.query_output_waveform(source).replace("\n","")
                voltage_offset = self.query_voltage_offset(source)
                amplitude = self.query_output_amplitude(source)
                frequency = self.query_frequency(source)
                state = self.query_output_state(source)
                
                dict_temp = {
                    "function": waveform,
                    "voltage_offset[V]":float(voltage_offset),
                    "amplitude[V]":float(amplitude),
                    "frequency[Hz]":float(frequency),
                    "state":state,
                }
                escape= True
            except ValueError as e:
                print(f"ValueError:{e}")

        return dict_temp


        

    