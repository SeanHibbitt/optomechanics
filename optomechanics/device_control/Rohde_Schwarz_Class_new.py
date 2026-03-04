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
        [SENSe:]AVERage[:STATe] Enable or disable the sweep average. Suffix: .
        Channel number Parameters: ON | OFF - enables
        or disables the automatic calculation of the sweep average over the specified number
        of sweeps ([SENSe:]AVERage:COUNt).
        *RST: OFF Example: See [SENSe:]AVERage:CLEar Manual operation: See "Factor / On / Reset" on page 554
        """
        return self.write(f"SENSe{channel}:AVERage:STATe {state}")

    
    def sense_average_clear(self, channel):
        """
        [SENSe:]AVERage:CLEar Starts a new average cycle, clearing all previous results and thus eliminating their
        effect on the new cycle. Suffix: . Channel number Example: SENS1:AVER:COUN 15; :AVER ON Set the average
        factor for channel 1 to 15 (the mnemonic SENS1 can be omitted) and enable the sweep average. AVER:COUN 5;
        CLE Reduce the average factor and restart the average. Usage: Event Manual operation:
        See "Factor / On / Reset" on page 554
        """
        return self.write(f"SENSe:{channel}AVERage:CLEar")
        
    
    def sense_average_count(self, channel, average_factor):
        """
        Defines the number of consecutive sweeps to be combined for the sweep average ("Factor").
        Suffix: . Channel number Parameters: Sweep average factor Range: 1 to 1000 
        *RST: 10 Example: See [SENSe:]AVERage:CLEar Manual operation: See "Factor / On / Reset" on page 554
        """
        return self.write(f"SENSe{channel}:AVERage:COUNt {average_factor}")
     
    
    def sense_average_point_count(self, channel, factor):
        """
        Defines the number of consecutive pulses to be point averaged ([SENSe: ]AVERage:POINt[:STATe] ON) Suffix: .
        Channel number Parameters: Point average factor Range: 1 to 100000 *RST: 10 Options: R&S ZNA-K7
        Manual operation: See "Point Average/Factor" on page 725
        """
        return self.write(f"SENSe{channel}:AVERage:POINt:COUNt {factor}")
        
    
    def sense_bandwidth_resolution(self, channel, band_width):
        """
        [SENSe<Ch>:]BANDwidth[:RESolution] <ResBandw>
        [SENSe<Ch>:]BWIDth[:RESolution] <IF Bandwidth>
        Defines the IF bandwidth of the analyzer (measurement bandwidth). Values between
        1 Hz and 1.5 MHz can be set. Option R&S ZNA-K17 enables bandwidths up to 30 MHz
        (see Chapter 4.7.8, "Increased IF bandwidth 30 MHz", on page 297).
        Suffix:
        <Ch>
        .
        Channel number
        Parameters:
        <IF Bandwidth> Bandwidths can be set in 1 – 1.5 – 2 – 3 – 5 – 7 steps. The analyzer rounds up any entered value between these steps and
        rounds down values exceeding the maximum bandwidth.
        Range: See above
        *RST: 10 kH
        """
        band_width_mods_truth = np.any(np.equal(np.array(band_width) % np.array([1,1.5,2,3,5,7]),[0,0,0,0,0,0]))
        try: band_width_mods_truth == True
        except: raise ValueError(f"band_width {band_width} not a valid amount, use power multiple of  : [1,1.5,2,3,5,7]; see user manual for more info")

        return self.write(f"SENSe{channel}:BANDwidth:RESolution {band_width}")
    
    def source_power_level(self, channel, IntSourcePow = -10):
        """
        SOURce<Ch>:POWer<PhyPt>[:LEVel][:IMMediate][:AMPLitude] <IntSourcePow>
        
        Defines the power of the internal signal source (channel base power). The setting is
        valid for all sweep types, except power sweep.
        Tip: Use SOURce<Ch>:POWer<PhyPt>:STARt and SOURce<Ch>:POWer<PhyPt>:
        STOP to define the sweep range for a power sweep.
        Suffix:
        <Ch>
        Channel number
        <PhyPt> Test port number of the analyzer. This suffix is ignored because
        the selected channel base power applies to all source ports
        used in the active channel.
        It is possible though to define a port-specific slope factor for the
        source power (SOURce<Ch>:POWer<PhyPt>[:LEVel][:
        IMMediate]:SLOPe) and a port-specific power offset
        (SOURce<Ch>:POWer<PhyPt>[:LEVel][:IMMediate]:
        OFFSet).
        Parameters:
        <IntSourcePow> Internal source power
        Range: The usable power range is frequency-dependent;
        refer to the data sheet.
        *RST: -10 dBm
        Default unit: dBm
        Example: FUNC "XFR:POW:RAT B1, A2"
        Activate a frequency sweep and select the ratio B1/A2 as measured parameter for channel and trace no. 1.
        SOUR:POW -6
        Set the internal source power for channel 1 to -6 dBm.
        Manual operation: See "Power" on page 542 
        
        """
        
        return self.write(f"SOURce{channel}:POWer:LEVel:IMMediate:AMPLitude {IntSourcePow}")
    
    def Trace_copy(self, MemTraceName, DataTraceName):
        
        """
        TRACe:COPY <MemTraceName>, <DataTraceName>
        Copies a data trace to a memory trace. The trace to be copied can be specified by two
        alternative methods:
        ● As the active data trace of channels 1 to 4 (CH1DATA, CH2DATA, CH3DATA,
        CH4DATA). If a mathematical trace is active, the associated data trace is copied.
        SCPI command reference
        R&S Command reference ®ZNA
        User Manual 1178.6462.02 ─ 34 1734
        ● As a trace with a name (string variable).
        The created memory trace can be specified as follows:
        ● As the memory trace named Mem<n>[Trc<m>], where n = 1, ... 8 and Trc<m> is
        the name of the copied data trace (MDATA1, MDATA2, MDATA3, MDATA4,
        MDATA5, MDATA6, MDATA7, MDATA8).
        ● As a memory trace with an arbitrary name (string variable).
        An existing memory trace with the same name is overwritten.
        Note: The copied trace is the data trace which is not modified by any mathematical
        operations. To copy a mathematical trace to a memory trace, use TRACe:COPY:MATH.
        To copy the active trace to the memory using an automatic memory trace name, use
        CALCulate<Chn>:MATH:MEMorize.
        Setting parameters:
        <MemTraceName> Name of the memory trace (see also Table 7-17).
        Range: <memory_trace> is either a string variable
        (enclosed in single or double quotes) or one of the
        following reserved names (no string variables):MDATA1 | MDATA2 | MDATA3 | MDATA4 |
        MDATA5 | MDATA6 | MDATA7 | MDATA8 (only for
        memory traces Mem<n>[Trc<m>], where n = 1, ...
        8).
        <DataTraceName> Name of the data trace (see also Table 7-17).
        Range: <data_trace> is either a string variable (enclosed in
        single or double quotes) or one of the following
        reserved names (no string variables):CH1DATA |
        CH2DATA | CH3DATA | CH4DATA (only for the
        active data trace in channels Ch1, Ch2, Ch3, Ch4).
        Example: *RST; :SWE:POIN 20
        Create a trace with 20 sweep points, making the created trace
        the active trace of channel 1 (omitted optional mnemonic
        SENSe1).
        TRAC:COPY "Mem_Pt20",CH1DATA
        Copy the current state of the created trace to a memory trace
        named "Mem_Pt20". The memory trace is not displayed.
        DISP:WIND:TRAC2:FEED "MEM_PT20"
        Display the created memory trace in the active diagram area
        (diagram area no. 1).
        Usage: Setting only
        Manual operation: See "Data to <Destination>" on page 455 """
        
        return self.write(f"TRACe:COPY {MemTraceName}, {DataTraceName}")
 
    def initiate_continuous(self, channel, boolean):
        """
        INITiate<Ch>:CONTinuous <Boolean>
        Qualifies whether the analyzer measures in single sweep or in continuous sweep
        mode.
        Suffix:
        <Ch>
        .
        Channel number.
        This suffix is ignored in the "ZVR" and "ZVABT" compatibility
        modes (SYSTem:LANGuage 'ZVR' | 'ZVABT').
        Parameters:
        <Boolean> ON - the analyzer measures continuously, repeating the current
        sweep.
        OFF - the measurement is stopped after the number of sweeps
        defined via [SENSe<Ch>:]SWEep:COUNt. INITiate<Ch>[:
        IMMediate][:DUMMy] initiates a new measurement cycle.
        *RST: ON
        see page 1323 on the manual for more infomation
        """
        return self.write(f"INITiate{channel}:CONTinuous {boolean}")
    
    def initiate_immediate_dummy(self,channel):
        """
        INITiate<Ch>[:IMMediate][:DUMMy]
        Starts a new single sweep sequence. This command is available in single sweep mode
        only (INITiate<Ch>:CONTinuous OFF). The data of the last sweep (or previous
        sweeps, see Chapter 8.2.4.3, "Retrieving the results of previous sweeps",
        on page 1829) can be read using CALCulate<Chn>:DATA:NSWeep:FIRSt?
        SDATa, <count>.
        Note: In contrast to all other commands of the analyzer, the
        INITiate<Ch>[:IMMediate]... commands have been implemented for overlapped execution; see Chapter 6.4, "Command processing", on page 1001.
        Suffix:
        <Ch>
        .
        Channel number. If the channel number does not exist the analyzer returns an error message. If the "ZVR" or "ZVABT" compatibility mode is active and INITiate<Ch>[:IMMediate]:
        SCOPe ALL is selected, this suffix is ignored.
        Example: See INITiate<Ch>:CONTinuous
        Usage: Event
        Manual operation: See "Restart Sweep" on page 583
        See page 1325 of manual
        """
        return self.write(f"INITiate{channel}:IMMediate:DUMMy")    
    
    def sense_sweep_time_auto(self, channel):
        """
        [SENSe<Ch>:]SWEep:TIME:AUTO <Boolean>
        When enabled, the (minimum) sweep time is calculated internally using
        the other channel settings and zero delay ([SENSe<Ch>:]SWEep:DWELl).
        Note: The automatically calculated sweep duration is ignored for
        the sweep types
        "Time" and "CW Mode" ([SENSe<Ch>:]SWEep:TYPE).
        Suffix:
        <Ch>
        .
        Channel number
        Parameters:
        <Boolean> ON | OFF - turn the automatic calculation of the sweep time on
        or off.
        OFF is also set if the sweep duration or delay is set explicitly
        using [SENSe<Ch>:]SWEep:TIME or [SENSe<Ch>:]SWEep:
        DWELl.
        *RST: ON
        Example: SWE:TIME 1
        Set a total sweep time of 1 s.
        SWE:TIME:AUTO?
        A query returns the value 1.
        Manual operation: See "Sweep Time / Auto" on page 557 """

        return self.query(f"SENSe{channel}:SWEep:TIME:AUTO")
    
    
    def calculate_parameter_sdefine(self, channel, TraceName, Result):
        """
        CALCulate<Ch>:PARameter:SDEFine <TraceName>, <Result>
        Creates a trace and assigns a channel number, a name and a measurement parameter to it. The trace becomes the active trace in the channel but is not displayed.
        Note: To display the trace defined via CALCulate<Ch>:PARameter:SDEFine, create a diagram (DISPlay[:WINDow<Wnd>][:STATe] ON) and assign the trace to this
        diagram (DISPlay[:WINDow<Wnd>]:TRACe<WndTr>:FEED); see example below.
        CALCulate<Ch>:PARameter:MEASure changes the measurement result of an
        existing trace.
        To select an existing trace as the active trace, use CALCulate<Ch>:PARameter:
        SELect. You can open the trace manager to obtain an overview of all channels and
        traces, including the traces that are not displayed.
        SCPI command reference
        R&S Command reference ®ZNA
        User Manual 1178.6462.02 ─ 34 1164
        Tip: This command has no query form. Use CALCulate<Ch>:PARameter:MEASure
        <TraceName> to query the measurement result of the trace. CALCulate<Ch>:
        PARameter:CATalog? returns a list of all defined traces.
        Suffix:
        <Ch>
        .
        Channel number referencing a previously defined channel. If
        <Ch> does not exist, it is generated with default channel settings.
        Setting parameters:
        <TraceName> Trace name, string variable, e.g. 'Trc4'. See "Rules for trace
        names" in "Table Area" on page 452. Trace names must be
        unique across all channels and diagrams.
        If a trace with the selected trace name already exists, the analyzer behaves as follows: If the existing trace is assigned to the
        same channel as the new trace, it is deleted. The new trace is
        not automatically assigned to a diagram area; see note above.
        If the existing trace is assigned to a different channel, no new
        trace can be created. The analyzer returns an error message.
        <Result> Measurement result (string variable), see table below.
        Example: CALC4:PAR:SDEF 'Ch4Tr1', 'S11'
        Create channel 4 and a trace named Ch4Tr1 to measure the
        input reflection coefficient S11.
        DISP:WIND2:STAT ON
        Create diagram area no. 2.
        DISP:WIND2:TRAC:FEED 'CH4TR1'
        Display the generated trace in diagram area no. 2.
        Usage: Setting only
        Manual operation: See "S-Parameter (selector)" on page 356  
        see table on page 1164 for correct parameter definitions
        """
        return self.write(f"CALCulate{channel}:PARameter:SDEFine '{TraceName}', '{Result}'")
          
    
    def calculate_parameter_delete(self, channel, TraceName):
        """
        See page 998 table
        """
        return self.write(f"CALCulate{channel}:PARameter:DELete '{TraceName}'")
    
    def display_window_state(self, window, state):
        """
        see page 998
        state: ON, OFF
        """
        return self.write(f"DISPlay:WINDow{window}:STATe {state}")
    
    
    def display_window_trace_feed(self, window, window_trace, TraceName ):
        """
        See page 998
        
        Assigns an existing trace (CALCulate<Ch>:PARameter:SDEFine) to a diagram
        area, using the <WndTr> suffix, and displays the trace. Use DISPlay[:
        WINDow<Wnd>]:TRACe:EFEed to assign the trace to a diagram area without using a
        numeric suffix.
        Tip: A trace can be assigned to a diagram only once. If a attempt is made to assign the
        same trace a second time (e.g. by typing DISP:WIND2:TRAC8:FEED 'CH4TR1'
        after executing the program example below) an error message -114,"Header suffix out
        of range" is generated. You can open the "Trace Manager" dialog to obtain an overview
        of all channels and traces, including the traces that are not displayed.
        Suffix:
        <Wnd>
        .
        Number of an existing diagram area (defined by means of
        DISPlay[:WINDow<Wnd>][:STATe] ON).
        <WndTr> Trace number used to distinguish the traces of the same diagram area <Wnd>.
        Parameters:
        <TraceName> String parameter for the trace name, e.g. 'Trc4'.
        Example: CALC4:PAR:SDEF 'Ch4Tr1', 'S11'
        Create channel 4 and a trace named Ch4Tr1 to measure the
        input reflection coefficient S11.
        DISP:WIND2:STAT ON
        Create diagram area no. 2.
        DISP:WIND2:TRAC9:FEED 'CH4TR1'
        Display the generated trace in diagram area no. 2, assigning the
        trace number 9 to it.
        Manual operation: See "Diagram / Channel" on page 450

        see page 1307
        """
        
        return self.write(f"DISPlay:WINDow{window}:TRACe{window_trace}:FEED '{TraceName}'")
    

    def calculate_parameter_delete_all(self,):
        """
        CALCulate:PARameter:DELete:ALL
        Deletes all traces in all channels of the active recall set, including the default trace
        Trc1 in channel 1. The manual control screen shows "No Trace".
        Example: See CALCulate<Ch>:PARameter:DELete
        Usage: Event
        Manual operation: See "Delete Trace" on page 450
        see page 1161
        """
        return self.write("CALCulate:PARameter:DELete:ALL")
    
    def output_state(self, state):
        """
        see page number 1372
        state: ON/OFF
        """
        return self.write(f"OUTPut:STATe {state}")
            
    #####query commands:
        
    
    def sense_sweep_time_auto_query(self, channel):
        """
        [SENSe<Ch>:]SWEep:TIME:AUTO <Boolean>
        When enabled, the (minimum) sweep time is calculated internally using
        the other channel settings and zero delay ([SENSe<Ch>:]SWEep:DWELl).
        Note: The automatically calculated sweep duration is ignored for
        the sweep types
        "Time" and "CW Mode" ([SENSe<Ch>:]SWEep:TYPE).
        Suffix:
        <Ch>
        .
        Channel number
        Parameters:
        <Boolean> ON | OFF - turn the automatic calculation of the sweep time on
        or off.
        OFF is also set if the sweep duration or delay is set explicitly
        using [SENSe<Ch>:]SWEep:TIME or [SENSe<Ch>:]SWEep:
        DWELl.
        *RST: ON
        Example: SWE:TIME 1
        Set a total sweep time of 1 s.
        SWE:TIME:AUTO?
        A query returns the value 1.
        Manual operation: See "Sweep Time / Auto" on page 557 """

        return self.query(f"SENSe{channel}:SWEep:TIME:AUTO?")
    
    def calculate_data_nsweep_first_query(self, channel,\
            format_type = "SDATa", FwCount = "1", FwCountEnd = ""):
    
        """
        CALCulate<Chn>:DATA:NSWeep:FIRSt? <Format>, <FwCount>[, <FwCountEnd>]
        Reads the response values of a trace or a consecutive group of traces acquired in single sweep mode (INITiate<Ch>:CONTinuous OFF).
        Tip:
        This command can only be used for [SENSe<Ch>:]SWEep:COUNt > 1.
        Suffix:
        <Chn>
        .
        Channel number used to identify the active trace
        Query parameters:
        <Format> SDATa
        Read unformatted sweep data (fixed parameter): Returns the
        real and imaginary part of each measurement point (2 values
        per trace point irrespective of the selected trace format).
        <FwCount> Number of the first sweep to be read. 1 denotes the first sweep
        acquired, 2 denotes the second, and so forth. The sweep count
        in single sweep mode is defined via [SENSe<Ch>:]SWEep:
        COUNt.
        Range: 1 to sweep count
        <FwCountEnd> Number of the last sweep to be read. If this parameter is omitted, it is implicitly set to <FwCount> (a single sweep is read).
        Range: <FwCount> to sweep count
        Return values:
        <Data> Response values, either in ASCII or block data format, depending on the current FORMat[:DATA] setting.
        See page 1036
        Doesn't work for one sweep
        """
        return self.write(f"CALCulate{channel}:DATA:NSWeep:FIRSt? {format_type},\
                          {FwCount}, {FwCountEnd}")
                          
    def calculate_data_query(self, channel, format_type = "FDATA"):
        """
        
        CALCulate<Chn>:DATA? <Format>
        The query reads the response values of the selected channel's active trace or reads
        error terms of the selected channel.
        The "set command" either imports formatted or unformatted trace data to the selected
        channel's active trace (see Chapter 4.1.7, "Data flow", on page 126) or writes error
        terms of the selected channel.
        Note
        ● The data format is parameter-dependent; see tables below. The unit is the default
        unit of the measured parameter; see CALCulate<Ch>:PARameter:SDEFine.
        ● Unformatted trace data (SDATa) can only be imported to memory traces
        ● Formatted trace data (FDATa) can only be imported to "live" traces if the related
        channel is in single sweep mode (INITiate<Ch>:CONTinuous OFF).
        Before the import, the target trace must be prepared according to the settings used
        during export. Any request for new data from the hardware ("Restart Sweep" in single sweep mode or switching to continuous sweep mode) discards imported data
        and switches the display back to measured data.
        Suffix:
        <Chn>
        .
        Channel number used to identify the active trace
        Parameters:
        <Data> Trace data either in ASCII or block data
        pg 1030

        """
        return self.query(f"CALCulate{channel}:DATA? {format_type}")
    
    
    def use_ext_ref(self,):
        return self.write("ROSC EXT")
    
    def load_cal(self, channel, file):
        self.write(f"MMEM:LOAD:CORR {channel}, '{file}'")

    def sense_sweep_count(self, channel, count):
        self.write(f"sense{channel}:sweep:count {count}")

    def calculate_data_nsweep_first(self, channel, format, fwcount, fwcountend):
        """ 
        retrieve data from the specified channel, and the specified swepe
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