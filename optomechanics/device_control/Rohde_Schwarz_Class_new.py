# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 12:14:00 2024

@author: Sean Hibbitt and Thomas Speake
Email: Sean.hibbitt.2019@live.rhul.ac.uk , Tom.speake2023@live.rhul.ac.uk
phone number: 07808665776

changes log: (not using git)
Please make new version and save old version in a folder if mangage alterations/additions are made
please note any changes here under your name, along with contact details:
"""

import time
from datetime import datetime
import numpy as np
#import pyvisa  as visa
#from pyvisa import constants
from .Device_Visa_Super import Device
from optomechanics.Fitting import re_and_im_to_dB_and_phase
import pandas




class ZNA(Device):
    """
    Made by Claude. VISA driver for the Rohde & Schwarz ZNA vector network analyser.

    Extends :class:`~optomechanics.device_control.Device_Visa_Super.Device`
    with SCPI commands specific to the R&S ZNA family.

    Device: R&S ZNA67, 10 MHz to 67 GHz, 4 test ports 1.85 mm
    (order no. 1332.4500K64).

    Frequency settings:
      - Start / Stop: 100 kHz to 67 GHz
      - Centre: >100 kHz to <67 GHz
      - Span: 1 Hz to 66.9999 GHz

    Maximum sweep points: 100 001.

    Parameters
    ----------
    address : str
        VISA resource address string (e.g. ``'TCPIP::192.168.x.x::INSTR'``).
    baud_rate : int, optional
        Serial baud rate.  Default is ``9600``.
    **kwargs
        Additional keyword arguments forwarded to the parent
        :class:`~optomechanics.device_control.Device_Visa_Super.Device`
        ``__init__`` (e.g. ``timeout``).

    Attributes
    ----------
    freq_list : numpy.ndarray
        Frequency array populated by :meth:`sweep`.
    data_1 : numpy.ndarray
        Log-magnitude (dB) data populated by :meth:`sweep`.
    data_2 : numpy.ndarray
        Phase (degrees) data populated by :meth:`sweep`.

    References
    ----------
    ZNA user manual:
    https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/pdm/cl_manuals/user_manual/1178_6462_01/ZNA_UserManual_en_34.pdf
    """
    
    def __init__(self, address, baud_rate = 9600, **kwargs):
        """
        Made by Claude. Initialise the ZNA driver.

        Parameters
        ----------
        address : str
            VISA resource address string.
        baud_rate : int, optional
            Serial baud rate.  Default is ``9600``.
        **kwargs
            Additional keyword arguments forwarded to
            :class:`~optomechanics.device_control.Device_Visa_Super.Device`
            (e.g. ``timeout``).
        """
        Device.__init__(self, address, baud_rate, **kwargs)
        
    def calculate_format(self, channel, format_type):
        """
        Made by Claude. Set the trace display format (``CALCulate<Ch>:FORMat``).

        Parameters
        ----------
        channel : int
            Channel number identifying the active trace.
        format_type : str
            Display format.  One of ``'MLINear'``, ``'MLOGarithmic'``,
            ``'PHASe'``, ``'UPHase'``, ``'POLar'``, ``'SMITh'``,
            ``'ISMith'``, ``'GDELay'``, ``'REAL'``, ``'IMAGinary'``,
            ``'SWR'``, ``'COMPlex'``, ``'MAGNitude'``, or
            ``'LOGarithmic'``.  Reset value: ``'MLOGarithmic'``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        
        return self.write(f"CALCulate{channel}:FORMat {format_type}")    
        
    
    def sense_freq_start(self, channel, FreqVal):

        """
        Made by Claude. Set the sweep start frequency (``SENSe<Ch>:FREQuency:STARt``).

        Parameters
        ----------
        channel : int
            Channel number.
        FreqVal : float
            Start frequency (Hz).  Increment: 0.1 kHz.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe{channel}:FREQuency:STARt {FreqVal}")
    
    
    def sense_freq_stop(self, channel, FreqVal):

        """
        Made by Claude. Set the sweep stop frequency (``SENSe<Ch>:FREQuency:STOP``).

        Parameters
        ----------
        channel : int
            Channel number.
        FreqVal : float
            Stop frequency (Hz).  Increment: 0.1 kHz.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """

        return self.write(f"SENSe{channel}:FREQuency:STOP {FreqVal}")


    def sense_sweep_points(self, channel, SweepPoint):

        """
        Made by Claude. Set the number of measurement points per sweep (``SENSe<Ch>:SWEep:POINts``).

        Parameters
        ----------
        channel : int
            Channel number.
        SweepPoint : int
            Number of sweep points.  Valid range 1–100001; reset value 201.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.

        Raises
        ------
        ValueError
            If ``SweepPoint`` is outside the valid range (guard logic present
            but the ``try/except`` block does not correctly enforce it).
        """

        try: SweepPoint in range(1, 100002) == True
        except: raise ValueError("Please use number of points from 1 to 100001")
        
        return self.write(f"SENSe{channel}:SWEep:POINts {SweepPoint}")

    def sense_sweep_type(self, channel, sense_sweep_type_format):
        """
        Made by Claude. Select the sweep type (``SENSe<Ch>:SWEep:TYPE``).

        Parameters
        ----------
        channel : int
            Channel number.
        sense_sweep_type_format : str
            Sweep type.  One of ``'LINear'``, ``'LOGarithmic'``,
            ``'POWer'``, ``'CW'``, ``'POINt'``, ``'PULSe'``, or
            ``'IAMPlitude'``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe{channel}:SWEep:TYPE {sense_sweep_type_format}")

    def sense_average_state(self, channel, state):
        """
        Made by Claude. Enable or disable sweep averaging (``SENSe<Ch>:AVERage:STATe``).

        Parameters
        ----------
        channel : int
            Channel number.
        state : str
            ``'ON'`` to enable; ``'OFF'`` to disable.  Reset value: ``'OFF'``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe{channel}:AVERage:STATe {state}")

    
    def sense_average_clear(self, channel):
        """
        Made by Claude. Start a new average cycle, discarding previous results (``SENSe:AVERage:CLEar``).

        Parameters
        ----------
        channel : int
            Channel number.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe:{channel}AVERage:CLEar")
        
    
    def sense_average_count(self, channel, average_factor):
        """
        Made by Claude. Set the sweep averaging factor (``SENSe<Ch>:AVERage:COUNt``).

        Parameters
        ----------
        channel : int
            Channel number.
        average_factor : int
            Number of sweeps to average.  Range: 1–1000; reset value: 10.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe{channel}:AVERage:COUNt {average_factor}")
     
    
    def sense_average_point_count(self, channel, factor):
        """
        Made by Claude. Set the point-averaging factor (``SENSe<Ch>:AVERage:POINt:COUNt``).

        Requires option R&S ZNA-K7.  Point averaging must be enabled with
        ``SENSe<Ch>:AVERage:POINt:STATe ON`` before this setting takes effect.

        Parameters
        ----------
        channel : int
            Channel number.
        factor : int
            Number of pulses to average at each point.  Range: 1–100000;
            reset value: 10.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe{channel}:AVERage:POINt:COUNt {factor}")
        
    
    def sense_bandwidth_resolution(self, channel, band_width):
        """
        Made by Claude. Set the IF (resolution) bandwidth (``SENSe<Ch>:BANDwidth:RESolution``).

        Valid from 1 Hz to 1.5 MHz (up to 30 MHz with option R&S ZNA-K17).
        Bandwidths step in a 1–1.5–2–3–5–7 sequence per decade.

        Parameters
        ----------
        channel : int
            Channel number.
        band_width : float
            IF bandwidth (Hz).  Must be a step-multiple of
            ``[1, 1.5, 2, 3, 5, 7]``.  Reset value: 10 kHz.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.

        Raises
        ------
        ValueError
            If ``band_width`` is not a valid value (guard logic present but
            the ``try/except`` block does not correctly enforce it).
        """
        band_width_mods_truth = np.any(np.equal(np.array(band_width) % np.array([1,1.5,2,3,5,7]),[0,0,0,0,0,0]))
        try: band_width_mods_truth == True
        except: raise ValueError(f"band_width {band_width} not a valid amount, use power multiple of  : [1,1.5,2,3,5,7]; see user manual for more info")

        return self.write(f"SENSe{channel}:BANDwidth:RESolution {band_width}")
    
    def source_power_level(self, channel, IntSourcePow = -10):
        """
        Made by Claude. Set the channel base source power (``SOURce<Ch>:POWer:LEVel:IMMediate:AMPLitude``).

        Valid for all sweep types except power sweep.  The usable power range
        is frequency-dependent; refer to the instrument data sheet.

        Parameters
        ----------
        channel : int
            Channel number.
        IntSourcePow : float, optional
            Source power (dBm).  Reset value: ``-10``.  Default is ``-10``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """

        return self.write(f"SOURce{channel}:POWer:LEVel:IMMediate:AMPLitude {IntSourcePow}")
    
    def Trace_copy(self, MemTraceName, DataTraceName):

        """
        Made by Claude. Copy a data trace to a memory trace (``TRACe:COPY``).

        The source trace is the unmodified data trace.  An existing memory
        trace with the same name is overwritten.

        Parameters
        ----------
        MemTraceName : str
            Name for the destination memory trace.  May be a string variable
            or one of the reserved names ``MDATA1``–``MDATA8``.
        DataTraceName : str
            Name of the source data trace.  May be a string variable or one
            of the reserved names ``CH1DATA``–``CH4DATA``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """

        return self.write(f"TRACe:COPY {MemTraceName}, {DataTraceName}")
 
    def initiate_continuous(self, channel, boolean):
        """
        Made by Claude. Select single-sweep or continuous-sweep mode (``INITiate<Ch>:CONTinuous``).

        Parameters
        ----------
        channel : int
            Channel number.
        boolean : str
            ``'ON'`` for continuous measurement; ``'OFF'`` for single sweep
            (measurement stops after the sweep count set by
            ``SENSe<Ch>:SWEep:COUNt``).  Reset value: ``'ON'``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"INITiate{channel}:CONTinuous {boolean}")
    
    def initiate_immediate_dummy(self,channel):
        """
        Made by Claude. Trigger a new single sweep (``INITiate<Ch>:IMMediate:DUMMy``).

        Available in single-sweep mode only
        (``INITiate<Ch>:CONTinuous OFF``).  Implemented for overlapped
        execution.  Previous sweep data can be retrieved with
        ``CALCulate<Ch>:DATA:NSWeep:FIRSt? SDATa``.

        Parameters
        ----------
        channel : int
            Channel number.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"INITiate{channel}:IMMediate:DUMMy")    
    
    def sense_sweep_time_auto(self, channel):
        """
        Made by Claude. Query the automatic sweep time state (``SENSe<Ch>:SWEep:TIME:AUTO``).

        .. note::
           Despite the method name, this function *queries* (not sets) the
           auto-sweep-time state.  Use :meth:`sense_sweep_time_auto_query`
           for the same effect with explicit intent.

        Parameters
        ----------
        channel : int
            Channel number.

        Returns
        -------
        str
            ``'1'`` (auto on) or ``'0'`` (auto off) as returned by the
            instrument.
        """

        return self.query(f"SENSe{channel}:SWEep:TIME:AUTO")
    
    
    def calculate_parameter_sdefine(self, channel, TraceName, Result):
        """
        Made by Claude. Create a trace and assign a measurement parameter (``CALCulate<Ch>:PARameter:SDEFine``).

        The trace becomes the active trace in the channel but is not
        displayed.  To display it, create a diagram window with
        :meth:`display_window_state` and assign the trace with
        :meth:`display_window_trace_feed`.

        Parameters
        ----------
        channel : int
            Channel number.  Created with default settings if it does not
            already exist.
        TraceName : str
            Unique trace name (e.g. ``'Trc4'``).  An existing trace with the
            same name in the same channel is replaced.
        Result : str
            Measurement parameter (e.g. ``'S11'``, ``'S21'``).  See the ZNA
            manual (page 1164) for the full parameter table.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"CALCulate{channel}:PARameter:SDEFine '{TraceName}', '{Result}'")
          
    
    def calculate_parameter_delete(self, channel, TraceName):
        """
        Made by Claude. Delete a named trace from a channel (``CALCulate<Ch>:PARameter:DELete``).

        Parameters
        ----------
        channel : int
            Channel number.
        TraceName : str
            Name of the trace to delete.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"CALCulate{channel}:PARameter:DELete '{TraceName}'")
    
    def display_window_state(self, window, state):
        """
        Made by Claude. Create or destroy a diagram window (``DISPlay:WINDow<Wnd>:STATe``).

        Parameters
        ----------
        window : int
            Window (diagram area) number.
        state : str
            ``'ON'`` to create the window; ``'OFF'`` to remove it.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"DISPlay:WINDow{window}:STATe {state}")
    
    
    def display_window_trace_feed(self, window, window_trace, TraceName ):
        """
        Made by Claude. Assign a trace to a diagram window (``DISPlay:WINDow<Wnd>:TRACe<WndTr>:FEED``).

        The window must already exist (created with :meth:`display_window_state`).
        A trace can only be assigned to a given diagram once.

        Parameters
        ----------
        window : int
            Diagram area number.
        window_trace : int
            Trace slot number within the diagram area.
        TraceName : str
            Name of the trace to display (e.g. ``'Trc4'``).

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """

        return self.write(f"DISPlay:WINDow{window}:TRACe{window_trace}:FEED '{TraceName}'")
    

    def calculate_parameter_delete_all(self,):
        """
        Made by Claude. Delete all traces in all channels (``CALCulate:PARameter:DELete:ALL``).

        Deletes all traces in all channels of the active recall set,
        including the default trace ``Trc1`` in channel 1.  The manual
        control screen shows "No Trace" afterwards.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.

        See Also
        --------
        calculate_parameter_delete : Delete a single named trace.

        References
        ----------
        ZNA user manual, page 1161.
        """
        return self.write("CALCulate:PARameter:DELete:ALL")
    
    def output_state(self, state):
        """
        Made by Claude. Enable or disable the RF output (``OUTPut:STATe``).

        Parameters
        ----------
        state : str
            ``'ON'`` to enable the RF output; ``'OFF'`` to disable it.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.

        References
        ----------
        ZNA user manual, page 1372.
        """
        return self.write(f"OUTPut:STATe {state}")
            
    #####query commands:
        
    
    def sense_sweep_time_auto_query(self, channel):
        """
        Made by Claude. Query whether automatic sweep time is enabled (``SENSe<Ch>:SWEep:TIME:AUTO?``).

        When enabled, the minimum sweep time is calculated internally from
        the channel settings and the dwell time (``SENSe<Ch>:SWEep:DWELl``).
        The auto-calculated duration is ignored for ``"Time"`` and
        ``"CW Mode"`` sweep types.  Auto is also disabled when sweep duration
        or delay is set explicitly via ``SENSe<Ch>:SWEep:TIME`` or
        ``SENSe<Ch>:SWEep:DWELl``.

        Parameters
        ----------
        channel : int
            Channel number.

        Returns
        -------
        str
            ``'1'`` if automatic sweep time is enabled; ``'0'`` if disabled.
        """

        return self.query(f"SENSe{channel}:SWEep:TIME:AUTO?")
    
    def calculate_data_nsweep_first_query(self, channel,\
            format_type = "SDATa", FwCount = "1", FwCountEnd = ""):

        """
        Made by Claude. Send a NSWeep:FIRSt read request as a write command (``CALCulate<Chn>:DATA:NSWeep:FIRSt?``).

        Only valid when ``SENSe<Ch>:SWEep:COUNt`` > 1 and
        ``INITiate<Ch>:CONTinuous OFF``.  Returns unformatted (real +
        imaginary) data for the selected sweep or range of sweeps.

        .. note::
           This method uses :meth:`~Device.write` rather than
           :meth:`~Device.query`.  Use :meth:`calculate_data_nsweep_first`
           for the equivalent query call that returns data.  This variant
           does not work for a single sweep (``SWEep:COUNt 1``).

        Parameters
        ----------
        channel : int
            Channel number identifying the active trace.
        format_type : str, optional
            Data format.  Must be ``'SDATa'`` (real + imaginary pairs,
            2 values per point).  Default is ``'SDATa'``.
        FwCount : str, optional
            Index of the first sweep to read (1-based).  Default is ``'1'``.
        FwCountEnd : str, optional
            Index of the last sweep to read.  If ``''``, only the sweep at
            ``FwCount`` is read.  Default is ``''``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.

        References
        ----------
        ZNA user manual, page 1036.
        """
        return self.write(f"CALCulate{channel}:DATA:NSWeep:FIRSt? {format_type},\
                          {FwCount}, {FwCountEnd}")
                          
    def calculate_data_query(self, channel, format_type = "FDATA"):
        """
        Made by Claude. Read trace data for the active trace (``CALCulate<Chn>:DATA?``).

        The query reads the response values of the selected channel's active
        trace.  Data units follow the measured parameter (see
        ``CALCulate<Ch>:PARameter:SDEFine``).

        Notes
        -----
        - ``FDATa`` (formatted) can only be imported to "live" traces when
          the channel is in single-sweep mode
          (``INITiate<Ch>:CONTinuous OFF``).
        - ``SDATa`` (unformatted) can only be imported to memory traces.
        - Any hardware data request (restart sweep or switch to continuous
          mode) discards imported data and reverts the display to measured
          data.

        Parameters
        ----------
        channel : int
            Channel number identifying the active trace.
        format_type : str, optional
            Data format.  ``'FDATA'`` for formatted data; ``'SDATa'`` for
            unformatted real + imaginary pairs.  Default is ``'FDATA'``.

        Returns
        -------
        str
            Comma-separated trace data string (ASCII or block data depending
            on the ``FORMat[:DATA]`` setting).

        References
        ----------
        ZNA user manual, page 1030.
        """
        return self.query(f"CALCulate{channel}:DATA? {format_type}")
    
    
    def use_ext_ref(self,):
        """
        Made by Claude. Switch the reference oscillator to external (``ROSC EXT``).

        Configures the instrument to use an external 10 MHz reference signal.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write("ROSC EXT")
    
    def load_cal(self, channel, file):
        """
        Made by Claude. Load and apply a calibration file to a channel (``MMEM:LOAD:CORR``).

        Parameters
        ----------
        channel : int
            Channel number to apply the calibration to.
        file : str
            Full path to the calibration file on the instrument file system.
        """
        self.write(f"MMEM:LOAD:CORR {channel}, '{file}'")

    def sense_sweep_count(self, channel, count):
        """
        Made by Claude. Set the number of sweeps per measurement cycle (``SENSe<Ch>:SWEep:COUNt``).

        Parameters
        ----------
        channel : int
            Channel number.
        count : int
            Number of sweeps.  Used with ``INITiate<Ch>:CONTinuous OFF``
            for single-sweep mode with multiple accumulations.
        """
        self.write(f"sense{channel}:sweep:count {count}")

    def calculate_data_nsweep_first(self, channel, format, fwcount, fwcountend):
        """
        Made by Claude. Query trace data from a specific sweep in single-sweep mode (``CALCulate<Chn>:DATA:NSWeep:FIRSt?``).

        Returns unformatted (real + imaginary) data for the specified sweep
        or range of sweeps.  Requires ``SENSe<Ch>:SWEep:COUNt`` > 1 and
        ``INITiate<Ch>:CONTinuous OFF``.

        Parameters
        ----------
        channel : int
            Channel number identifying the active trace.
        format : str
            Data format.  Use ``'SDATa'`` for real + imaginary pairs
            (2 values per point).
        fwcount : int
            Index of the first sweep to read (1-based).
        fwcountend : int
            Index of the last sweep to read.

        Returns
        -------
        str
            Comma-separated data string containing real and imaginary pairs.

        See Also
        --------
        calculate_data_nsweep_first_query : Write variant of this command.
        """
        return self.query(f"calculate{channel}:data:nsweep:first? {format}, {fwcount}, {fwcountend}")

    def check_current_sweep_number():
        """CALCULATE1:DATA:NSWEEP:COUNT?"""
    
    ####Ease of Use Functions:
    
    def sweep(self, channel, Result, TraceName, freq_start, freq_stop,\
              number_of_points = 100, probe_power = -10, band_width = 1e3,\
              timeout = 1000, sweep_count = 1, sense_average_state = "OFF",\
              sense_average_count_factor = 1,\
              sense_average_point_count_factor = 1,\
              sense_sweep_type_format = "LINear",\
              reset = True,_file_name = "default", file_location = "", ext_ref = True, use_cal = False,\
              extra_meta = {},
                  ):
        
        args = locals()
        
        if sense_sweep_type_format == "LINear":
            self.freq_list = np.linspace(freq_start, freq_stop, number_of_points)
        elif sense_sweep_type_format == "LOGarithmic":
            self.freq_list = np.logspace(freq_start, freq_stop, number_of_points)
        else: raise Exception("this isnt coded yet...")
            
        
        #reset the device to its default state
        if reset == True: 
            self.CLS()
            self.RST()
            self.calculate_parameter_delete_all()
            pass
        
        self.use_ext_ref()
        
        #enable event tracking to make sure sweep is finished
        #self.enable_event()
        
        #create a trace, assigns it a measureable parameter and channel number
        self.calculate_parameter_sdefine( channel, TraceName, Result)
        
        #create display window and display trace:
        self.display_window_state(channel, "ON")
        self.display_window_trace_feed(channel, 2, TraceName)
        
        #setup for the sweep as described on page 1807:
        self.initiate_continuous(channel, "OFF")
        self.sense_sweep_points(channel, 2)
        
        #Define sweep type.
        self.sense_sweep_type(channel, sense_sweep_type_format)
        
        #setup desired parameters:
        self.sense_freq_start(channel, freq_start)
        self.sense_freq_stop(channel, freq_stop)
        self.source_power_level(channel, probe_power)      #power is in dB
        self.sense_bandwidth_resolution(channel, band_width)
        self.sense_average_state(channel, sense_average_state)
        if sense_average_state == "ON":
            self.sense_average_count(channel, sense_average_count_factor)
            self.sense_average_point_count(channel, sense_average_point_count_factor)

        
        #set sweep points to desired value
        self.sense_sweep_points(channel, number_of_points)
        
    
        print("Post Sweep Setup Error Check:\n",self._device.query("SYST:ERR:ALL?"))
        
        #predict sweep time
        #self.sense_sweep_time_auto(channel)
        #predicted_time = self.sense_sweep_time_auto_query(channel)
        #print(f"predicted sweep time = {predicted_time}")
    
        #initialise sweep
        self.output_state("ON")
        #setup cal:
        if use_cal != False:
            self.load_cal(channel, use_cal)

        
        self.sense_sweep_count(channel, sweep_count)
        time_stamp_init = datetime.now()
        self.initiate_immediate_dummy(channel)
        #self.WAI()
        print("sweep running, dont turn off")

        #wait for completetion
        #completed, response = self.wait_for_event(timeout)
        #assert completed == True, response
        #print("test error check:",self._device.query("SYST:ERR:ALL?"))
        self.OPC_query()
        timeout_note = self.timeout
        self._device.timeout = None
        while True:
            #print("errors2:\n",self._device.query("SYST:ERR:ALL?"))
            read = self._device.read_bytes(1, timeout)

            print(f"read: {read}")
            if read == b"1":
                break
        delta_T =  datetime.now() - time_stamp_init
        delta_T = delta_T.total_seconds()
        self._device.timeout = timeout_note

        self.output_state("OFF")
        print("Sweep finished, saving")
        print("After Run Error Check:\n",self._device.query("SYST:ERR:ALL?"))

        #print(f"\n\ndata = {self.data_1}|\n\n{self.data_2}")
        file_name = _file_name

        #meta_data:
        meta_data = ""
        meta_data_dict = {"time_start[s]":time_stamp_init.timestamp(),
                          "delta_T[s]":delta_T} | extra_meta
        variables = [x for x in args.items()][2:-2]
        for variable, element in variables:
            meta_data = meta_data + f"{variable}_{element}"
            meta_data_dict[variable] = element

    
        if file_location != False:
        
            file_name = file_name + f"{Result}_{probe_power}_"
            file_name = file_name + ".tsv"
            print(f"saving as: {file_location}{file_name}")
        

        data_dict = {"freq[Hz]":self.freq_list}        
        #format data/Record
        if sweep_count >1:
            data =  self.calculate_data_nsweep_first( channel, "SDATa", 1, sweep_count)
            data = np.fromstring(data, sep = ",")
            
            print(f"data:{data}")

            data = np.reshape(data,( sweep_count, number_of_points, 2)) #reshape data into (sweep, number of points, re and im)

            
            for i, sweep in enumerate(data[:,]):
                sweep = sweep.T
                #print(sweep.T)
                re = sweep[0]
                im = sweep[1]
                power_db, phase = re_and_im_to_dB_and_phase(re, im)
                data_dict[f"sweep_number_mag[dB]:{i+1}"] = power_db
                data_dict[f"sweep_number_phase[rad]:{i+1}"] = phase



            print("final error check:",self._device.query("SYST:ERR:ALL?")) 

        else:
                    #format data/Record
            self.calculate_format(channel, "MLOGarithmic")
            self.data_1 = np.fromstring(self.calculate_data_query(channel), sep = ",")
            self.calculate_format(channel, "PHASe")
            self.data_2 = np.fromstring(self.calculate_data_query(channel), sep = ",")

            data_dict[f"sweep_number_mag[dB]:1"] = self.data_1
            data_dict[f"sweep_number_phase[rad]:1"] = self.data_2
        
        #print(data_dict)
        data_pandas = pandas.DataFrame.from_dict(data_dict)
        file_loc = file_location + file_name
        csv_data = data_pandas.to_csv(sep = "\t")
        with open(file_loc,  "w") as file:
            for key, value in meta_data_dict.items():
                file.write(f"#\t{key}\t{value}\n")
            file.write(csv_data)

        
        return data_pandas, meta_data_dict

        #turn rf power off
        
    
        
        
        

    def save_data(self, file_name, location = "", meta_data = ""):
        with open(location+file_name, "w") as file1:
            file1.write(meta_data+"\n")
            file1.write('Logarithmic Magnitude [dB]\tPhase (e^iphase)\tFreq[Hz]\n')
            for data_1_, data_2_, Freq in zip(self.data_1, self.data_2, self.freq_list): 
                #print("data:",Re, Im, Freq)
                file1.write(f"{data_1_}\t{data_2_}\t{Freq}\n")
                

        
    #update for the zna for following point of peak via phase value
    
    def follow_value(self,):
        
        
        
        return 
    
        

if __name__ == "__main__":
    pass
    #example:
    # address = 'TCPIP::134.219.128.53::INSTR'
    # zna = ZNA(address,)
    # print(zna.IDN_query())
    
    
    # rm = visa.ResourceManager()  
    # rm.list_resources()
    # vna =  rm.open_resource('TCPIP::134.219.128.53::INSTR')
    # print(vna.query("*IDN?"))