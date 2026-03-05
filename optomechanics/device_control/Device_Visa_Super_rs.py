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
    Made by Claude. VISA device base class using the RsInstrument backend.

    Extends :class:`~optomechanics.device_control.Device_Visa_Super.Device`
    by replacing the PyVISA resource manager with the Rohde & Schwarz
    ``RsInstrument`` library for connection and resource listing.
    All SCPI commands inherited from the parent class remain available.

    SCPI reference: https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments

    ZNA manual:
    https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/pdm/cl_manuals/user_manual/1178_6462_01/ZNA_UserManual_en_34.pdf

    Parameters
    ----------
    address : str
        VISA resource address string (e.g. ``'TCPIP::192.168.x.x::INSTR'``).
    baud_rate : int, optional
        Serial baud rate.  Default is ``9600``.
    query_delay : float, optional
        Delay between write and read in a query (s).  Default is ``0``.
    timeout : float, optional
        VISA communication timeout (ms).  Default is ``10000``.
    """
    
    def __init__(self, address, baud_rate = 9600, query_delay = 0, timeout = 10000  ):
        """
        Made by Claude. Initialise the RsInstrument-backed device.

        Delegates to the parent
        :meth:`~optomechanics.device_control.Device_Visa_Super.Device.__init__`
        with a fixed timeout of ``25000`` ms, ignoring the ``timeout``
        parameter passed to this constructor.

        Parameters
        ----------
        address : str
            VISA resource address string.
        baud_rate : int, optional
            Serial baud rate.  Default is ``9600``.
        query_delay : float, optional
            Delay between write and read in a query (s).  Default is ``0``.
        timeout : float, optional
            Intended VISA timeout (ms).  Currently ignored — parent is always
            called with ``25000`` ms.  Default is ``10000``.
        """
        Device.__init__(self, address, baud_rate, timeout = 25000)

    def open(self):
        """
        Made by Claude. Open the instrument connection using the RsInstrument backend.

        Creates an :class:`RsInstrument` connection to ``self.address`` with
        ID query and reset both enabled (``True, True``).  Stores the
        instrument handle in ``self._device``.

        Returns
        -------
        Device
            Returns ``self`` to support the context-manager protocol.
        """
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
        Made by Claude. List all VISA resources visible to the RsInstrument backend.

        Returns
        -------
        list of str
            VISA resource address strings for all currently connected
            instruments, as reported by :meth:`RsInstrument.list_resources`.
        """
        instr_list = RsInstrument.list_resources("?*")
        return instr_list