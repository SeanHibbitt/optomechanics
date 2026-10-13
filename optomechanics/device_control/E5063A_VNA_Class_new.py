# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 12:14:00 2024

@author: Sean Hibbitt and Thomas Speake
Email: Sean.hibbitt.2019@live.rhul.ac.uk , Tom.speake2023@live.rhul.ac.uk
phone number: 07808665776


Plan:
    
    Check commands are similar to the ZNA ones: Done
    Add helper functions as required to replace anything missing


"""

import time
from datetime import datetime
import numpy as np
import pyvisa  as visa
from pyvisa import constants
from .Device_Visa_Super import Device
import matplotlib.pyplot as plt
import pandas




class VNA(Device):
    """
    Docstring by Claude. VISA driver for the Keysight E5063A vector network analyser.

    Extends :class:`~optomechanics.device_control.Device_Visa_Super.Device`
    with SCPI commands specific to the E5063A.  The command set is
    structurally similar to the Rohde & Schwarz ZNA; verify commands against
    the E5063A documentation before use.

    Parameters
    ----------
    address : str
        VISA resource address string (e.g. ``'TCPIP::134.219.128.53::INSTR'``).
    baud_rate : int, optional
        Serial baud rate.  Default is ``9600``.

    Attributes
    ----------
    freq_list : numpy.ndarray
        Frequency array populated by :meth:`sweep`.
    data_1 : numpy.ndarray
        Log-magnitude (dB) data populated by :meth:`sweep`.
    data_2 : numpy.ndarray
        Phase (degrees) data populated by :meth:`sweep`.
    freq_data : numpy.ndarray
        Stimulus frequency data populated by :meth:`sweep`.

    References
    ----------
    ZNA user manual:
    https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/pdm/cl_manuals/user_manual/1178_6462_01/ZNA_UserManual_en_34.pdf
    """
    
    def __init__(self, address, baud_rate = 9600):
        """
        Docstring by Claude. Initialise the E5063A VNA driver.

        Parameters
        ----------
        address : str
            VISA resource address string.
        baud_rate : int, optional
            Serial baud rate.  Default is ``9600``.
        """
        Device.__init__(self, address, baud_rate, timeout = 25000)
        
        
    
    def sense_freq_start(self, channel, FreqVal):
        """
        Docstring by Claude. Set the sweep start frequency (``SENSe<Ch>:FREQuency:STARt``).

        Parameters
        ----------
        channel : int
            Channel number.
        FreqVal : float
            Start frequency (Hz).  Resolution is 1 Hz.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """

        return self.write(f"SENSe{channel}:FREQuency:STARt {FreqVal}")
    
    
    def sense_freq_stop(self, channel, FreqVal):
        """
        Docstring by Claude. Set the sweep stop frequency (``SENSe<Ch>:FREQuency:STOP``).

        Parameters
        ----------
        channel : int
            Channel number.
        FreqVal : float
            Stop frequency (Hz).  Resolution is 1 Hz.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """

        return self.write(f"SENSe{channel}:FREQuency:STOP {FreqVal}")


    def sense_sweep_points(self, channel, SweepPoint):

        """
        Docstring by Claude. Set the number of measurement points per sweep (``SENSe<Ch>:SWEep:POINts``).

        Parameters
        ----------
        channel : int
            Channel number.
        SweepPoint : int
            Number of sweep points.  Valid range is 2–10001.

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

        try: SweepPoint in range(2, 10001) == True
        except: raise ValueError("Please use number of points from 2 to 10001")
        
        return self.write(f"SENSe{channel}:SWEep:POINts {SweepPoint}")

    def sense_sweep_type(self, channel, sense_sweep_type_format):
        """
        Docstring by Claude. Set the sweep type (``SENSe<Ch>:SWEep:TYPE``).

        Parameters
        ----------
        channel : int
            Channel number.
        sense_sweep_type_format : str
            Sweep type.  One of ``'LINear'``, ``'LOGarithmic'``, or
            ``'SEGment'``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe{channel}:SWEep:TYPE {sense_sweep_type_format}")

    def sense_average_state(self, channel, state):
        """
        Docstring by Claude. Enable or disable sweep averaging (``SENSe<Ch>:AVERage:STATe``).

        Parameters
        ----------
        channel : int
            Channel number.
        state : str
            ``'ON'`` to enable averaging; ``'OFF'`` to disable.  The number
            of averages is set by :meth:`sense_average_count`.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe{channel}:AVERage:STATe {state}")

    
    def sense_average_clear(self, channel):
        """
        Docstring by Claude. Start a new average cycle, discarding previous results (``SENSe:AVERage:CLEar``).

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
        Docstring by Claude. Set the number of sweeps to average (``SENSe<Ch>:AVERage:COUNt``).

        This sets the averaging factor for consecutive sweeps (not
        point-by-point averaging).  Verify behaviour before use.

        Parameters
        ----------
        channel : int
            Channel number.
        average_factor : int
            Number of sweeps to average.  Valid range is 1–999;
            default on the instrument is 16.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"SENSe{channel}:AVERage:COUNt {average_factor}")

        
    
    def sense_bandwidth_resolution(self, channel, band_width):
        """
        Docstring by Claude. Set the IF (resolution) bandwidth (``SENSe<Ch>:BANDwidth:RESolution``).

        Parameters
        ----------
        channel : int
            Channel number.
        band_width : float
            IF bandwidth (Hz).  Must be a power-of-ten multiple of one of
            ``[1, 1.5, 2, 3, 4, 5, 7]`` and no greater than ``300000`` Hz.
            Examples: 10, 15, 20, …, 100k, 150k, 200k, 300k.

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
        band_width_mods_truth = np.any(np.equal(np.array(band_width) % np.array([1,1.5,2,3,4,5,7]),[0,0,0,0,0,0,0]))\
            and band_width <= 300000
        try: band_width_mods_truth == True
        except: raise ValueError(f"band_width {band_width} not a valid amount, use power multiple of  : [1,1.5,2,3,5,7]; see user manual for more info")

        return self.write(f"SENSe{channel}:BANDwidth:RESolution {band_width}")
    

    
    def sense_sweep_time_auto(self, channel, boolean):
        """
        Docstring by Claude. Enable or disable automatic sweep time (``SENSe<Ch>:SWEep:TIME:AUTO``).

        Parameters
        ----------
        channel : int
            Channel number.
        boolean : str or int
            ``'ON'`` / ``1`` to enable auto sweep time; ``'OFF'`` / ``0``
            to disable.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """

        return self.write(f"SENSe{channel}:SWEep:TIME:AUTO {boolean}")
    
    def source_power_level(self, channel, IntSourcePow = -10):
        """
        Docstring by Claude. Set the internal source power level (``SOURce<Ch>:POWer:LEVel:IMMediate:AMPLitude``).

        Parameters
        ----------
        channel : int
            Channel number.
        IntSourcePow : float, optional
            Output power (dBm).  Must be in the range ``[-20, 0]``.
            Default is ``-10``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.

        Raises
        ------
        ValueError
            If ``IntSourcePow`` is outside ``[-20, 0]``.
        """
        if IntSourcePow <= 0 and IntSourcePow >=-20:
            pass
        else: raise ValueError("Incorrect power input")
        
        
        return self.write(f"SOURce{channel}:POWer:LEVel:IMMediate:AMPLitude {IntSourcePow}")
    
 
    def initiate_continuous(self, channel, boolean):
        """
        Docstring by Claude. Select single-sweep or continuous-sweep mode (``INITiate<Ch>:CONTinuous``).

        Parameters
        ----------
        channel : int
            Channel number.
        boolean : str or int
            ``'ON'`` / ``1`` for continuous sweep; ``'OFF'`` / ``0`` for
            single sweep.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"INITiate{channel}:CONTinuous {boolean}")
    
    def initiate_sweep(self,channel):
        """
        Docstring by Claude. Trigger a single sweep (``INITiate<Ch>:IMMediate``).

        Only available when the instrument is in single-sweep mode
        (``INITiate<Ch>:CONTinuous OFF``).

        Parameters
        ----------
        channel : int
            Channel number.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"INITiate{channel}")    
    

    
    
    def calculate_parameter_define(self, channel, TraceName, Result):
        """
        Docstring by Claude. Assign a measurement parameter to a trace (``CALCulate<Ch>:PARameter<Tr>:DEFine``).

        May need to be used alongside other commands to create the channel
        and trace first.

        Parameters
        ----------
        channel : int
            Channel number.
        TraceName : int or str
            Trace identifier.
        Result : str
            S-parameter to measure, e.g. ``'S11'``, ``'S12'``, ``'S21'``,
            or ``'S22'``.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"CALCulate{channel}:PARameter{TraceName}:DEFine {Result}")
          
    
    def output_state(self, state):
        """
        Docstring by Claude. Enable or disable the RF signal output (``OUTPut:STATe``).

        Parameters
        ----------
        state : str
            ``'ON'`` to enable the output; ``'OFF'`` to disable.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f"OUTPut:STATe {state}")
    
    def display_window_trace_y_scale_auto(self, channel, TraceName, boolean):

        """
        Docstring by Claude. Enable or disable Y-axis autoscale for a trace (``DISPlay:WINDow<Ch>:TRACe<Tr>:Y:SCALe:AUTO``).

        Parameters
        ----------
        channel : int
            Channel / window number.
        TraceName : int or str
            Trace identifier.
        boolean : bool or str
            ``True`` / ``'ON'`` to enable autoscale; ``False`` / ``'OFF'``
            to disable.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f":DISPlay:WINDow{channel}:TRACe{TraceName}:Y:SCALe:AUTO {boolean}")
    
    def calculate_data_format(self, channel, TraceName, data_format):
        """
        Docstring by Claude. Set the data format for a trace (``CALCulate<Ch>:TRACe<Tr>:FORMat``).

        See "Internal data arrays" in the instrument manual for details on
        how the format affects retrieved data.

        Parameters
        ----------
        channel : int
            Channel number.
        TraceName : int or str
            Trace identifier.
        data_format : str
            Data format string, e.g. ``'MLOGarithmic'`` (log magnitude),
            ``'PHASe'`` (phase in degrees), ``'REAL'``, ``'IMAGinary'``,
            etc.

        Returns
        -------
        tuple
            Return value of :meth:`~Device.write`.
        """
        return self.write(f':Calculate{channel}:TRACe{TraceName}:FORMat {data_format}')
                
    #####query commands:
        
    def sense_sweep_time_query(self, channel):
        """
        Docstring by Claude. Query the current sweep time (``SENSe<Ch>:SWEep:TIME?``).

        Parameters
        ----------
        channel : int
            Channel number.

        Returns
        -------
        str
            Sweep time in seconds as a string returned by the instrument.
        """
        return self.query(f"SENSe{channel}:SWEep:TIME?")
        

    
    def calculate_data_fdata_query(self, channel, TraceName):

        """
        Docstring by Claude. Retrieve formatted trace data (``CALCulate<Ch>:TRACe<Tr>:DATA:FDATa?``).

        Parameters
        ----------
        channel : int
            Channel number.
        TraceName : int or str
            Trace identifier.

        Returns
        -------
        str
            Comma-separated formatted data string.  The format is determined
            by the last call to :meth:`calculate_data_format`.
        """
        return self.query(f"CALCulate{channel}:TRACe{TraceName}:DATA:FDATa?")
    
    def calculate_data_sdata_query(self, channel, TraceName):

        """
        Docstring by Claude. Retrieve corrected (complex) trace data (``CALCulate<Ch>:TRACe<Tr>:DATA:SDATa?``).

        Parameters
        ----------
        channel : int
            Channel number.
        TraceName : int or str
            Trace identifier.

        Returns
        -------
        str
            Comma-separated corrected data string (real/imaginary pairs).
        """
        return self.query(f"CALCulate{channel}:TRACe{TraceName}:DATA:SDATa?")
    
    
    def sense_freq_data(self, channel):
        """
        Docstring by Claude. Query the frequency stimulus data array (``SENSe<Ch>:FREQuency:DATA?``).

        Parameters
        ----------
        channel : int
            Channel number.

        Returns
        -------
        str
            Comma-separated frequency values (Hz) as a string.
        """
        return self.query(f"SENSe{channel}:FREQuency:DATA?")
    

    def error(self,):
        """
        Docstring by Claude. Query the instrument error queue (``SYST:ERR?``).

        Returns
        -------
        str
            Error code and message string from the instrument error queue.
        """
        return self.query("SYST:ERR?")
        
    
    ####helper functions:
        
    
    def recieve_fdata(self, data_formats, channel, TraceName,):
        """
        Docstring by Claude. Retrieve formatted trace data for multiple data formats.

        Iterates over ``data_formats``, sets the trace format with
        :meth:`calculate_data_format`, and queries the data with
        :meth:`calculate_data_fdata_query` for each format.

        Parameters
        ----------
        data_formats : list of str
            Sequence of format strings to retrieve in turn (e.g.
            ``['MLOGarithmic', 'PHASe']``).
        channel : int
            Channel number.
        TraceName : int or str
            Trace identifier.

        Returns
        -------
        None
            Result is accumulated in ``data`` but not returned (incomplete
            implementation — function body does not return ``data``).
        """
        data = []
        for data_format in data_formats:
            self.calculate_data_format(self, channel, TraceName, data_format) 
            temp_data = self.caluculate_fdata_query(channel, TraceName)
            data.append(temp_data)
            
    
    ####Ease of Use Functions:
    
    def sweep(self, channel, Result, TraceName, freq_start, freq_stop,\
              number_of_points, probe_power, band_width, calibration = "ON",\
              load_state = "C:\\Users\\Instrument\\Documents\\User_States\\Cal_2026_10_13.sta", \
              sense_average_state = "OFF",\
              sense_average_count_factor = 1,\
              sense_average_point_count_factor = 1,\
              sense_sweep_type_format = "LINear",\
              reset = True,_file_name = "default", file_location = "", extra_meta = {}, dummy_sweep = False, ):
        """
        Docstring by Claude. Configure the VNA and perform a single S-parameter sweep.

        Resets the instrument (optionally), configures frequency range, sweep
        type, source power, IF bandwidth, and averaging, then triggers a
        single sweep.  Retrieves log-magnitude and phase data after the sweep
        completes and optionally saves the result to a tab-delimited file.

        Parameters
        ----------
        channel : int
            Channel number for the measurement.
        Result : str
            S-parameter to measure (e.g. ``'S11'``, ``'S21'``).
        TraceName : int or str
            Trace identifier within the channel.
        freq_start : float
            Sweep start frequency (Hz).
        freq_stop : float
            Sweep stop frequency (Hz).
        number_of_points : int
            Number of frequency points in the sweep.
        probe_power : float
            Source power level (dBm).  Must be in ``[-20, 0]``.
        band_width : float
            IF (resolution) bandwidth (Hz).
        calibration : str, optional
            ``'ON'`` to apply calibration correction; ``'OFF'`` to disable.
            Default is ``'ON'``.
        load_state : str, optional
            Path to the instrument state file to load on reset.
            Default is a pre-defined calibration file path.
        sense_average_state : str, optional
            ``'ON'`` to enable sweep averaging; ``'OFF'`` to disable.
            Default is ``'OFF'``.
        sense_average_count_factor : int, optional
            Number of sweeps to average (``SENSe:AVERage:COUNt``).
            Default is ``1``.
        sense_average_point_count_factor : int, optional
            Reserved for future use; currently unused.  Default is ``1``.
        sense_sweep_type_format : str, optional
            Sweep type: ``'LINear'`` or ``'LOGarithmic'``.
            Default is ``'LINear'``.
        reset : bool, optional
            If ``True``, calls :meth:`~Device.CLS`, :meth:`~Device.RST`, and
            loads the state file before configuring. Default is ``True``.
        _file_name : str, optional
            Base name for the output file (extension appended automatically).
            Default is ``'default'``.
        file_location : str or bool, optional
            Directory path for saving output.  Set to ``False`` to suppress
            saving.  Default is ``''``.
        extra_meta : dict, optional
            Additional key-value pairs to include in the file metadata.
            Default is ``{}``.
        dummy_sweep : bool, optional
            If ``True``, returns ``None`` immediately after triggering the
            sweep (no data retrieval).  Default is ``False``.

        Returns
        -------
        pandas.DataFrame
            Tabular data with columns ``freq[Hz]``,
            ``sweep_number_mag[dB]:1``, and ``sweep_number_phase[rad]:1``.
        dict
            Metadata dictionary including sweep parameters and timestamps.

        Raises
        ------
        Exception
            If ``sense_sweep_type_format`` is not ``'LINear'`` or
            ``'LOGarithmic'``.
        """
        print(f"error info pre-run check \n{self.error()}")
        
        
        
        if sense_sweep_type_format == "LINear":
            self.freq_list = np.linspace(freq_start, freq_stop, number_of_points)
        elif sense_sweep_type_format == "LOGarithmic":
            self.freq_list = np.logspace(freq_start, freq_stop, number_of_points)
        else: raise Exception("this isnt coded yet...")
            
        
        #reset the device to its default state
        if reset == True: 
            self.CLS()
            self.RST()
            self.write(f':MMEM:LOAD "{load_state}"')
            print(f"error info 310\n{self.error()}")
        #add correction:
        
        #create a trace, assigns it a measureable parameter and channel number
        self.calculate_parameter_define( channel, TraceName, Result)
        
        print(f"error info 321\n{self.error()}")
        #setup for the sweep as described on page 1807:
        self.initiate_continuous(channel, "OFF")
        self.sense_sweep_points(channel, 2)
        
        #Define sweep type (linear or logarithmic)
        self.sense_sweep_type(channel, sense_sweep_type_format)
        print(f"error info 328\n{self.error()}")
        
        #setup desired parameters:
        self.sense_freq_start(channel, freq_start)
        self.sense_freq_stop(channel, freq_stop)
        self.source_power_level(channel, probe_power)      
        self.sense_bandwidth_resolution(channel, band_width)
        self.sense_average_state(channel, sense_average_state)
        if sense_average_state == "ON" or sense_average_count_factor !=1:
            self.sense_average_state(channel, "ON")
            self.sense_average_count(channel, sense_average_count_factor)

        print(f"error info 342\n{self.error()}")
        
        #set sweep points to desired value
        self.sense_sweep_points(channel, number_of_points)
        print(f"error info 345\n{self.error()}")


        print("turning power on")
        self.output_state("ON")
        
        self.sense_sweep_time_auto(channel, "ON")

        self.write(f":SENSe:CORRection:STATe {calibration}")
        device_cal = self.query(":SENSe:CORRection:STATe?")

        print(f"sweep time: {self.query(':SENSe1:SWEep:TIME:AUTO?')}")
        sweep_time = self.sense_sweep_time_query(channel)
        print(f"expected time: {sweep_time}")
        #time.sleep(1)

        
    
        print(f"error info 357\n{self.error()}")
        #initialise sweep
        time_stamp_init = datetime.now()
        self.initiate_sweep(channel)
        print("sweep running, dont turn off")

        if dummy_sweep == True: return None

        self.WAI()
        plt.pause(float(sweep_time)*2*1.1+2)
        # print(f"error info 361\n{self.error()}")
        # self.OPC_query()
        
        # self._device.timeout = None
        # while True:
        #     #print("errors2:\n",self._device.query("SYST:ERR:ALL?"))
        #     plt.pause(float(sweep_time)*1.1+1)
        #     read = self._device.read_bytes(3)
            

        #     print(f"read: {read}")
        #     if b"1" in read:
        #         break
            
        #     print("waiting: 5")
        #     #time.sleep(5)
        delta_T =  datetime.now() - time_stamp_init
        delta_T = delta_T.total_seconds()
        args = locals()

        self._device.timeout = None
        print("Sweep finished, saving")

        #format data/Record
        print(f"error info 379: {channel}, {TraceName}\n {self.error()}")
        self.calculate_data_format(channel, TraceName, "MLOGarithmic")
        self.data_1 = np.fromstring(self.calculate_data_fdata_query(channel, TraceName), sep = "," )[0::2]
        self.calculate_data_format(channel, TraceName, "PHASe")
        self.data_2 = np.fromstring(self.calculate_data_fdata_query(channel, TraceName), sep = ",")[0::2]
        self.freq_data = np.fromstring(self.sense_freq_data(channel,), sep = ",")
        
        print(f"""
              data1shape = {np.shape(self.data_1)}
              
              data1shape = {np.shape(self.data_1)}
              
              data_freq = {np.shape(self.freq_data)}
              """
              
              
              )

        #turn rf power off
        self.output_state("OFF")
        print(f"error info 407 (final) \n{self.error()}")
        
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
        

        data_dict = {"freq[Hz]":self.freq_data}        
        data_dict[f"sweep_number_mag[dB]:1"] =  self.data_1
        data_dict[f"sweep_number_phase[rad]:1"] = self.data_2
        
        #print(data_dict)
        data_pandas = pandas.DataFrame.from_dict(data_dict)
        file_loc = file_location + file_name
        csv_data = data_pandas.to_csv(sep = "\t", index=False)
        with open(file_loc,  "w") as file:
            for key, value in meta_data_dict.items():
                file.write(f"#\t{key}\t{value}\n")
            file.write(csv_data)
                

        return data_pandas, meta_data_dict
        
        

if __name__ == "__main__":
    #example:
    address = 'TCPIP::134.219.128.53::INSTR'
    vna = VNA(address,)
    print(vna.IDN_query())
    
    
    rm = visa.ResourceManager()  
    rm.list_resources()
    vna =  rm.open_resource('TCPIP::134.219.128.53::INSTR')
    print(vna.query("*IDN?"))