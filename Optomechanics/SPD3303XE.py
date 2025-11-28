from Optomechanics import Device
import pyvisa


class SPD(Device):
    """

    SPD3303x-e control
    manual:https://www.siglenteu.com/wp-content/uploads/dlm_uploads/2022/11/SPD3303X_QuickStart_E02A.pdf page 27
    """
    def __init__(self, address, baud_rate = 9600, **kwargs):
        Device.__init__(self, address, baud_rate, **kwargs)
        
    
    def measure_value(self, channel, function):
        """
        measure the output value
        channel options: CH1, CH2
        function: CURRent, VOLTage
        """
        return self.query(f"MEAS:{function}? {channel}")
    
    def set_value(self, channel, function, value):
        """
        set the output value
        channel options: CH1, CH2
        function: CURRent, VOLTage
        value: 
            volts: 0<->32
            amps: 0<->3.2
        """
        return self.write(f"{channel}:{function} {value}")
    
    def query_set_value(self, channel, function):
        """
        query the output value
        channel options: CH1, CH2
        function: CURRent, VOLTage
        """
        return self.query(f"{channel}:{function}?")
    


if __name__ == "__main__":
    print("starting:")

    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    print("hey")
    with SPD('USB0::0xF4EC::0x1430::SPD3XJFD7R7026::INSTR') as DMM:
        print(DMM.IDN_query())
        DMM.set_value("CH1", "VOLT", 10)

    print("end")
