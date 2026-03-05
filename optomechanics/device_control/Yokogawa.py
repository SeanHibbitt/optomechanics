from .Device_Visa_Super import Device
import pyvisa


class GS200(Device):
    """
    Manual: https://web-material3.yokogawa.com/IMGS210-01EN.pdf
    For Yokogawa GS200 DC Voltage Current Source
    
    To use this as a source, set to voltage or current source
    via using the source_function command.
    Then set the voltage/current level via
    the source_level_auto command
    """

    def __init__(self, address, baud_rate = 9600):
        Device.__init__(self, address, baud_rate)
        
        
        
    def source_function(self, function):
        """
        See page 13-11
        sets the source as voltage or current
        options:
            VOLT
            CURR
        """
        self.write(f":SOURce:FUNCtion {function}")
        
    def source_level_auto(self, level):
        """
        Sets the source voltage level
        See pg 5-3
        set level is in non-prefix units, i.e A or V  
        not mV or mA
        """
        self.write(f":SOURce:LEVel:AUTO {level}")
        
    def output_state(self,state):
        """
        Sets the output state, see page 5-5
        options:
            ON
            OFF
            1
            0
        """
        self.write(f":OUTPut:STATe {state}")
        
    def source_level_query(self,):
        """
        querys source level
        """
        self.query(":SOUrce:LEVel:AUTO?")
        
        
    #helper functions:
        
        
    def _set_source_level(self, function, level):
        """
        helper function, will set some voltage
        """
        #reset device
        self.RST()
        self.source_function(function)
        self.source_level_auto(level)
        self.output_state(1)
        
    def set_voltage(self, voltage):
        self._set_source_level("VOLT", voltage)
        
    def set_current(self, current):
        self._set_source_level("CURR", current)
        


if __name__ == "__main__":
    print("starting:")

    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    print("hey")
    
    source = GS200("USB0::0x0B21::0x0039::90Y936894::INSTR")
    print(source.IDN_query())
    
    source.set_current(1e-3)
    print(source.source_level_query())
    