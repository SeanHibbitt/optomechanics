
from .Device_Visa_Super import Device

# trigger_command = 'KRDG?4'
# TMC_value=float(instrument.query(trigger_command))
# trigger_command1 = 'KRDG?3'
# T1K_value=float(instrument.query(trigger_command1))

class Temp_Controller(Device):
    """

    Class for controlling the SMA100B signal generator from rhode and schwarz
    manual: https://www.rohde-schwarz.com/uk/manual/r-s-sma100b-user-manual-manuals_78701-434880.html
    """
    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs, ) 
        
    def ReadTemperature(self,channel):
        return self.query(f"KRDG?{channel}")

    def ReadMCTemperature(self):
        """Channel 4"""
        return self.ReadTemperature("4")
    
    def ReadExcitationPower(self, channel):
        return self.query(f"RDGPWR?{channel}")
    
    def ReadResistance(self, channel):
        return self.query(f"RDGR?{channel}")
    
    def ReadInputSetup(self, channel):
        return self.query(f"INTYPE?{channel}")
    
    def ReadHeaterOutput(self, channel):
        return self.query(f"HTR?{channel}")
    
    def ReadManualHeaterOutput(self, channel):
        return self.query(f"MOUT?{channel}")
    
    def ReadHeaterRange(self, channel):
        return self.query(f"RANGE?{channel}")
    
    def ReadStillOutput(self, channel):
        return self.query(f"STILL?{channel}")
    
    def ReadPID(self, channel):
        return self.query(f"PID?{channel}")