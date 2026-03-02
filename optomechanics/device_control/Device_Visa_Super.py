# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 12:14:00 2024

@author: Sean Hibbitt
Email: Sean.hibbitt.2019@;ive.rhul.ac.uk
phone number: 07808665776

changes log: (not using git)
Please make new version and save old version in a folder if mangage alterations/additions are made
please note any changes here under your name, along with contact details:
"""


import pyvisa  as visa
from pyvisa import constants
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
from optomechanics.data_management.data_management import save_data_3 as save_data_3_temp


#%%Define Class
class Device():
    """
    Made by Claude. VISA super-class providing IEEE 488.2 / SCPI commands and device management.

    Wraps pyvisa to provide SCPI commands common to all Rohde & Schwarz (and
    compatible) instruments.  Subclass this to add instrument-specific methods.
    Supports use as a context manager (``with`` statement).

    SCPI command reference: ZNA User Manual
    https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/pdm/cl_manuals/user_manual/1178_6462_01/ZNA_UserManual_en_34.pdf

    SCPI standard: https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments

    Parameters
    ----------
    address : str
        VISA resource address string (e.g. ``'TCPIP::192.168.0.1::INSTR'``).
    baud_rate : int, optional
        Baud rate for serial connections. Default is 9600.
    query_delay : float, optional
        Delay in seconds between write and read in a query. Default is 0.
    timeout : int, optional
        Communication timeout in milliseconds. Default is 10000.

    Attributes
    ----------
    rm : pyvisa.ResourceManager
        The pyvisa resource manager instance.
    address : str
        VISA resource address string.
    baud_rate : int
        Baud rate.
    query_delay : float
        Query delay in seconds.
    timeout : int
        Communication timeout in milliseconds.
    _device : pyvisa.Resource
        The open pyvisa resource; available after calling `open`.
    """
    
    
    
    def __init__(self, address, baud_rate = 9600, query_delay = 0, timeout = 10000  ):
        """
        Made by Claude. Initialise the resource manager and store connection parameters.

        The connection is not opened here; call `open` (or use the ``with``
        statement) to establish communication with the instrument.
        """
        #setup visa
        self.rm = visa.ResourceManager()  

        #setup parameters
        self.address = address
        self.baud_rate = baud_rate
        self.query_delay = query_delay 
        self.timeout = timeout
        #sets default delay to be 0.1s
        #self._device = self.rm.open_resource(self.address)


    def open(self):
        """
        Made by Claude. Open the VISA resource and configure communication parameters.

        Returns
        -------
        Device
            Returns ``self`` to allow chaining and use in ``with`` blocks.
        """
        self._device = self.rm.open_resource(self.address)
        #setup device parameters
        self._device.baud_rate = self.baud_rate
        self._device.query_delay = self.query_delay
        self._device.timeout = self.timeout
        #self.CLS()
        #self.RST()
        return self


    def __enter__(self):
        """
        Made by Claude. Enter the context manager by opening the VISA resource.

        Calls `open` and returns ``self``, enabling use in ``with`` blocks::

            with Device('TCPIP::192.168.0.1::INSTR') as dev:
                dev.IDN_query()

        See also: https://realpython.com/python-with-statement/#coding-class-based-context-managers

        Returns
        -------
        Device
            The opened device instance.
        """
        return self.open()
        
    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Made by Claude. Exit the context manager by closing the VISA resource.

        Calls `close` on exit.  If an ``IndexError`` was raised inside the
        ``with`` block it is caught, printed, and suppressed.

        Parameters
        ----------
        exc_type : type or None
            Exception type, or ``None`` if no exception occurred.
        exc_value : Exception or None
            Exception instance, or ``None``.
        exc_tb : traceback or None
            Traceback object, or ``None``.

        Returns
        -------
        bool or None
            ``True`` if an ``IndexError`` was caught (suppressing propagation);
            ``None`` otherwise.
        """
        self.close()
        if isinstance(exc_value, IndexError):
            # Handle IndexError here...
            print(f"An exception occurred in your with block: {exc_type}")
            print(f"Exception message: {exc_value}")
            return True

    @staticmethod
    def connected_devices():
        """
        Made by Claude. List all VISA resources currently visible to the system.

        Creates a temporary resource manager, enumerates all resources, and
        returns the result.

        Returns
        -------
        tuple of str
            VISA resource address strings for all connected devices.
        """
        temp_rm = visa.ResourceManager()  
        temp_list = temp_rm.list_resources()
        del temp_rm
        return temp_list


        
    def query(self, cmd,):
        """
        Made by Claude. Send a SCPI query command and return the response string.

        Parameters
        ----------
        cmd : str
            SCPI command string to send (e.g. ``'*IDN?'``).

        Returns
        -------
        str
            Response string from the instrument.
        """
        return self._device.query(cmd)
    
    def write(self, cmd):
        """
        Made by Claude. Send a SCPI write command with no response expected.

        Parameters
        ----------
        cmd : str
            SCPI command string to send.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call
            (number of bytes written, status code).
        """
        return self._device.write(cmd)
        
    def read_bytes(self, bits):
        """
        Made by Claude. Read a fixed number of bytes from the instrument.

        Parameters
        ----------
        bits : int
            Number of bytes to read.

        Returns
        -------
        bytes
            Raw bytes read from the instrument.
        """
        return self._device.read_bytes(bits)
    
    def close(self,):
        """
        Made by Claude. Close the VISA resource manager and print a confirmation message.
        """
        self.rm.close()
        print("device closed")
    
    
    ####generic SCPI commands:
        
    ##### write commands:
    def CLS(self,):
        """
        Made by Claude. Send the ``*CLS`` (Clear Status) SCPI command.

        Clears the status byte (STB), the standard event register (ESR), and the
        EVENt part of the QUEStionable and OPERation registers to zero.  Does not
        alter mask or transition register parts.  Clears the output buffer.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write("*CLS")
    
    def OPC(self,):
        """
        Made by Claude. Send the ``*OPC`` (Operation Complete) SCPI command.

        Sets bit 0 in the event status register when all preceding commands have
        been executed.  This bit can be used to initiate a service request.
        See `ESE` and `ESR_query` for event-status register management.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write("*OPC")

    def PCB(self,Address):
        """
        Made by Claude. Send the ``*PCB`` (Pass Control Back) SCPI command.

        Indicates the controller address to which remote control is returned
        after termination of the triggered action.

        Parameters
        ----------
        Address : int
            Controller address in the range 0–30.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write(f"*PCB{Address}")
    
    def PRE(self, Value):
        """
        Made by Claude. Send the ``*PRE`` (Parallel Poll Register Enable) SCPI command.

        Sets the parallel poll enable register to the indicated value.

        Parameters
        ----------
        Value : int
            Value to write to the parallel poll enable register (0–255).

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write(f"*PRE{Value}")
    
    def PSC(self, Action):
        """
        Made by Claude. Send the ``*PSC`` (Power On Status Clear) SCPI command.

        Determines whether the contents of the ENABle registers are preserved or
        reset when the instrument is switched on.  A service request can be
        triggered on power-on if the ESE and SRE registers are suitably configured.

        Parameters
        ----------
        Action : int
            ``0`` — preserve the status register contents on power-on.
            ``1`` — reset the status registers on power-on.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        
        return self.write(f"*PSC{Action}")
    
    
    def RST(self, ):
        """
        Made by Claude. Send the ``*RST`` (Reset) SCPI command.

        Sets the instrument to its defined default state.  Equivalent to
        ``SYSTem:PRESet[:DUMMy]``.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write(f"*RST")
    
    def SRE(self, Contents):
        """
        Made by Claude. Send the ``*SRE`` (Service Request Enable) SCPI command.

        Sets the service request enable register to the specified value.
        Bit 6 (MSS mask bit) always remains 0.

        Parameters
        ----------
        Contents : int
            Contents of the service request enable register in decimal form
            (0–255); bit 6 is always 0.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write(f"*SRE{Contents}")
    
    def TRG(self,):
        """
        Made by Claude. Send the ``*TRG`` (Trigger) SCPI command.

        Triggers all actions waiting for a trigger event and generates a manual
        trigger signal.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write("*TRG")
    
    def WAI(self,):
        """
        Made by Claude. Send the ``*WAI`` (Wait to Continue) SCPI command.

        Prevents execution of subsequent commands until all preceding commands
        have been executed and all signals have settled.

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write("*WAI")
    
    def ESE(self, value):
        """
        Made by Claude. Send the ``*ESE`` (Event Status Enable) SCPI command.

        Sets the event status enable register to the specified value.

        Parameters
        ----------
        value : int
            Value for the event status enable register (0–255).

        Returns
        -------
        tuple
            Return value of the underlying pyvisa write call.
        """
        return self.write(f"*ESE {value}")
    
    #####query commands:
    
    def ESE_query(self):
        """
        Made by Claude. Query the event status enable register (``*ESE?``).

        Returns
        -------
        str
            Contents of the event status enable register in decimal form.
        """
        return self.query("*ESE?")

    
    def ESR_query(self):
        """
        Made by Claude. Query and clear the event status register (``*ESR?``).

        Returns the contents of the event status register in decimal form and
        then sets the register to zero.  Bit 0 (OPC bit) indicates whether
        all preceding operations have completed: ``1`` = ready, ``0`` = busy.

        Returns
        -------
        str
            Contents of the event status register in decimal form (0–255).
        """
        return self.query("*ESR?")
        
    def IDN_query(self,):
        """
        Made by Claude. Query the instrument identification string (``*IDN?``).

        Returns the manufacturer, instrument type, serial number, and software
        revision.

        Returns
        -------
        str
            Instrument identification string.
        """
        return self.query("*IDN?")
    
    
    def IST_query(self, ):
        """
        
        *IST?
        Individual status query
        Returns the contents of the IST flag in decimal form. The IST flag is the status bit
        which is sent during a parallel poll.
        Return values:
        <ISTflag> 0 | 1
        Usage: Query only

        """
        return self.query("*IST?")
    
    def OPT_query(self, ):
        """
        
        *OPT?
        Option identification query
        Returns a list of installed options. The response consists of arbitrary ASCII response
        data according to IEEE 488.2. The options are returned at fixed positions in a commaseparated string. A zero is returned for options that are not installed.
        For a list of all available options and their description, refer to the specifications document.
        The OPT information is editable; see "Define *IDN + *OPT..." on page 939.
        Usage: Query only
        Manual operation: See relevant device manual

        """
        return self.query("*OPT?")
    
    def STB_query(self, ):
        """
        
        *STB?
        Status byte query
        Reads the contents of the status byte in decimal form.
        Usage: Query only

        """
        return self.query("*STB?")
    
    def TST_query(self,):
        """
        
        *TST?
        Self-test query
        Performs a self test and returns its boolean result (0 = passed, 1 = failed)
        Return values:
        <ErrorCode> integer > 0 (in decimal format)
        An error occurred.
        0
        No errors occurred.
        Usage: Query only
        Manual operation: relevant device manual

        """
        
        return self.query(f"*TST?")
    
    def OPC_query(self,):
        
        
        return self.write("*OPC?")
    
    
    ####Extra Functions
    
    def check_OPC_event(self):
        OPC_bit = bin(int(self.ESR_query()))[0]
        return OPC_bit
    
    
    
    def wait_on_OPC(self, wait_time = 60, timeout = None, updates = True, function = None, **function_kwargs):
        self.ESE(1)
        print(f"ESE bits:{self.ESE_query()}")
        self.OPC()
        
        while True:
            if function != None:
                 function(**function_kwargs)

            completed = self.check_OPC_event()
            print(f"event status: {completed}")
            if completed == 1:
                print(f"finished task, completed = {completed}")
                break
            print(f"No update, waiting {wait_time} seconds.")
            plt.pause(wait_time)
        return True
    
   
    
    def save_data(self, datas, freqs, file_name, file_location = "", headers = None, meta_data = "", delimiter = "\t"):
        
        with open(file_location+file_name, "w") as file1:
            file1.write(meta_data+"\n")
            if headers != None:
                file1.write(headers+"\n")
            for data, freq in zip(datas, freqs): 
                file1.write(f"{data}{delimiter}{freq}\n")


    def save_data_2(self, data, file_name, file_location = "", headers = None, meta_data = "", delimiter = "\t"):
        data_shape = np.shape(data)
        #print(data_shape)
        with open(file_location+file_name, "w") as file1:
            file1.write(meta_data+"\n")
            if headers != None:
                file1.write(headers+"\n")
            
            for  i in range(data_shape[1]):
                for l in range(data_shape[0]):
                    file1.write(f"{data[l,i]}\t")
                file1.write("\n")

    def save_data_3(self, data, file_name, file_location = "", headers = None, meta_data = {}, delimiter = "\t"):
        
        data_shape = np.shape(data)
        print(f"datashape:{data_shape}")
        with open(file_location+file_name, "w") as file1:
            for key, value in meta_data.items():
                file1.write(f"#\t{key}\t{value}\n")
            if headers != None:
                file1.write(headers+"\n")
            
            try:
                for  i in range(data_shape[1]):
                    for l in range(data_shape[0]):
                        file1.write(f"{data[l,i]}\t")
                    file1.write("\n")
            except IndexError as e:
                print(f"index error:\n{e}\ndata:\n{data}")
                for  i in range(data_shape[0]):
                    file1.write(f"{data[i]}\t")
                    file1.write("\n")

   

    
    #not sure if this works:
    # def enable_event(self,):
    #     """
    #     Enables pyvisa to look for a specific event
    #     See: https://pyvisa.readthedocs.io/en/stable/introduction/event_handling.html#waiting-on-events-using-a-queue
    #     for more details
    #     """
    #     self.event_type = constants.EventType.service_request
    #     self.event_mech = constants.EventMechanism.queue
    #     self._device.enable_event(self.event_type, self.event_mech)
    #     return self.event_type, self.event_mech
    
    
    # def wait_for_event(self,timeout = 1000):
    #     """
    #     Waits for the event specified in enable_event,
    #     then checks its the right event, before disabling the event
    #     and return the response.
        
    #     useful documentation url:
    #         https://pyvisa.readthedocs.io/en/latest/api/resources.html#pyvisa.resources.MessageBasedResource.wait_on_event
        
    #     Returns:
    #         bool for if response timed out or not (True for timed out), WaitResponse object

    #     """
    #     self.OPC()
    #     self.response = self._device.wait_on_event(self.event_type, timeout, True)
    #     assert self.response.event.event_type == self.event_type, "seen wrong event type"
    #     self._device.disable_event(self.event_type, self.event_mech)
        
    #     return self.response.timed_out, self.response
        
        
        
        
    
    
if __name__ == "__main__":
    #ZNA = Device('TCPIP::134.219.128.53::INSTR')
    
    
    #ZNA.write('*IDN?')
    #while True:
    #    print(ZNA.read_bytes())
    
    #print(ZNA.query("*IDN?"))
    
    #the same as above but without the class, directly from pyvisa
    #rm = visa.ResourceManager()  
    #vna =  rm.open_resource('TCPIP::134.219.128.53::INSTR')
    #print(vna.query("*IDN?"))
    
    pass
        