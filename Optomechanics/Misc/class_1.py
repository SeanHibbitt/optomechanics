import visa
import pyvisa
import numpy as np
import time

def numtostr(mystr):
    return '%12.8e' % mystr

class SMA100B:
    def __init__(self ,device):
        rm = pyvisa.ResourceManager()
        self.SMA100B = rm.open_resource(device)
        print(self.SMA100B.query('*IDN?'))

    def set_mw_frequency(self,mw_freq):
        self.SMA100B.write('FREQ:FIX'+' '+str(mw_freq))
        
    def read_mw_frequency(self):
        return self.SMA100B.ask('FREQ:FIX?')
    
    def set_mw_power(self,mw_power):
        self.SMA100B.write('POW:LEV'+' '+str(mw_power))

    def read_mw_power(self):
        return self.SMA100B.ask('POW:LEV?')
    
    def turn_mw(self,OnOff):
        self.SMA100B.write('OUTP:STAT'+' '+str(OnOff))
        
# =============================================================================
#     def turn_mw_mod(self,OnOff):
#         self.SMA100B.write('OUTP:MOD:STAT'+' '+str(OnOff))
# =============================================================================

class SMP22:
    def __init__(self ,device):
        rm = pyvisa.ResourceManager()
        self.SMP22 = rm.open_resource(device)
        print(self.SMP22.query('*IDN?'))

    def set_mw_frequency(self,mw_freq):
        self.SMP22.write('FREQ:FIX'+' '+str(mw_freq))
        
    def read_mw_frequency(self):
        return self.SMP22.ask('FREQ:FIX?')
    
    def set_mw_power(self,mw_power):
        self.SMP22.write('POW:LEV'+' '+str(mw_power))

    def read_mw_power(self):
        return self.SMP22.ask('POW:LEV?')
    
    def turn_mw(self,OnOff):
        self.SMP22.write('OUTP:STAT'+' '+str(OnOff))
        
    def turn_mw_mod(self,OnOff):
        self.SMP22.write('OUTP:MOD:STAT'+' '+str(OnOff))
        
class SMF:
    def __init__(self ,device):
        rm = pyvisa.ResourceManager()
        self.SMF = rm.open_resource(device)
        print(self.SMF.query('*IDN?'))

    def set_mw_frequency(self,mw_freq):
        self.SMF.write('FREQ:FIX'+' '+str(mw_freq))
        
    def read_mw_frequency(self):
        return self.SMF.ask('FREQ:FIX?')
    
    def set_mw_power(self,mw_power):
        self.SMF.write('POW:LEV'+' '+str(mw_power))

    def read_mw_power(self):
        return self.SMF.ask('POW:LEV?')
    
    def turn_mw(self,OnOff):
        self.SMF.write('OUTP:STAT'+' '+str(OnOff))
        
    def turn_mw_mod(self,OnOff):
        self.SMF.write('OUTP:MOD:STAT'+' '+str(OnOff))
        
        
class FSW:
    #
    def __init__(self ,device):
        rm = pyvisa.ResourceManager()
        self.FSW = rm.open_resource(device)
        print(self.FSW.query('*IDN?')) 
   
    def set_cent_freq(self,cent_freq):
        self.FSW.write('FREQ:CENT'+' '+str(cent_freq))
        
    def read_cent_freq(self):
        return self.FSW.query('FREQ:CENT?')
    
    def set_span(self,span):
        self.FSW.write('FREQ:SPAN'+' '+str(span))
        
    def read_span(self):
        return self.FSW.query('FREQ:SPAN?')
    
    def set_bw(self,bw):
        self.FSW.write('BAND'+' '+str(bw))

    def read_bw(self):
        return self.FSW.query('BAND?')
    
    def set_sweep_points(self,points):
        self.FSW.write('SWE:POIN'+' '+str(points))
        
    def set_sweep_time(self,duration):
        self.FSW.write('SWE:TIME'+' '+str(duration))
        
    def get_sweep_time(self):
        return self.FSW.query('SWE:TIME?')
        
    def set_sweep_count(self,duration):
        self.FSW.write('SWE:COUNT'+' '+str(duration))
        
    def read_sweep_points(self):
        return self.FSW.query('SWE:POIN?')
    
    def average_state(self, onoff):
        self.FSW.write('AVER:STAT'+' '+str(onoff))
        
    def average_number(self, number):
        self.FSW.write('AVER:COUN'+' '+str(number))  
        
    def set_reference_level(self, level_dbm):
        """Set the reference level in dBm."""
        self.FSW.write(f'DISP:WIND:TRAC:Y:RLEV {level_dbm}')
             
    def single_trace(self,timeout=200000):
        self.FSW.write('INIT:CONT OFF')
        self.FSW.write('INIT:IMM')
        result = 0 
        cnt = 0
        while True:
            try:
                result = int(self.FSW.query("*OPC?"))
            except (pyvisa.VisaIOError):
                pass
            if result == 1 or cnt > timeout*10:
                break
            cnt+=1
        time.sleep(5)   
        datas = self.FSW.query('TRAC:DATA? TRACE1')
        self.FSW.write('INIT:CONT OFF')
        p=np.fromstring(datas,dtype=float,sep=',')
        return p


    def single_trace_VNA_mode(self,timeout=200000):
        self.FSW.write('INIT:CONT OFF')
        self.FSW.write('INIT:IMM')
        result = 0 
        cnt = 0
        while True:
            try:
                result = int(self.FSW.query("*OPC?"))
            except (pyvisa.VisaIOError):
                pass
            if result == 1 or cnt > timeout*10:
                break
            cnt+=1
        time.sleep(27)   
        datas = self.FSW.query('TRAC:DATA? TRACE1')
        self.FSW.write('INIT:CONT OFF')
        p=np.fromstring(datas,dtype=float,sep=',')
        power_avg=np.average(p)
        return power_avg

        


class ZNA:
    
    def __init__(self ,device):
        rm = pyvisa.ResourceManager()
        self.ZNA = rm.open_resource(device)
        print(self.ZNA.query('*IDN?')) 
        
    def Reset(self):
        self.ZNA.write('SYST:PRES *RST')
        
    def SetContinuous(self, onoff):
        self.ZNA.write('INIT:CONT'+' '+str(onoff))
        
    def SetStart(self, start_freq):
        self.ZNA.write('SENS:FREQ:STAR'+' '+str(start_freq))
        
    def SetStop(self, stop_freq):
        self.ZNA.write('SENS:FREQ:STOP'+' '+str(stop_freq))
        
    def SetCenter(self, center_freq):
        self.ZNA.write('SENS:FREQ:CENT'+' '+str(center_freq))
        
    def SetSpan(self, span):
        self.ZNA.write('SENS:FREQ:SPAN'+' '+str(span))
        
    def GetStart(self):
        self.ZNA.query('SENS:FREQ:STAR?')
        
    def GetStop(self):
        self.ZNA.query('SENS:FREQ:STOP?')
        
    def GetCenter(self):
        self.ZNA.query('SENS:FREQ:CENT?')
        
    def GetSpan(self):
        self.ZNA.query('SENS:FREQ:SPAN?')
        
    def SetPoints(self,sweep_points):
        self.ZNA.write('SENS:SWE:POIN'+' '+str(sweep_points))
        
    def SetIFBW(self, IFBW):
        self.ZNA.write('SENS:BWID'+' '+str(IFBW))
        
    def GetIFBW(self):
        self.ZNA.query('SENS:BWID?')
    
    def turn_mw_port_1(self,OnOff):
        self.ZNA.write('SOUR:POW1:STAT'+' '+str(OnOff))
        
        
    def set_mw_power_port_1(self,power):
        self.ZNA.write('SOUR:POW1'+' '+str(power))
        
    def average_state(self,OnOff):
        self.ZNA.write('SENS:AVER'+' '+str(OnOff))
    
    def average_numbers(self,avg_num):
        self.ZNA.write('SENS:AVER:COUN'+' '+str(avg_num))
        
    def single_trace_ZNA(self,timeout=200000):
        
        self.ZNA.write('INIT:CONT OFF')
        self.ZNA.write('INIT:IMM')
       
        result = 0 
        cnt = 0
        while True:
            try:
                result = int(self.ZNA.ask("*OPC?"))
            except (pyvisa.VisaIOError):
                pass
            if result == 1 or cnt > timeout*10:
                break
            cnt+=1 
# =============================================================================
#         time.sleep(sweep_time)
# =============================================================================
        data = self.ZNA.query('CALC:DATA? SDATA')
        self.ZNA.write('INIT:CONT OFF')
        
        data = np.asarray([float(xx) for xx in data.split(',')])
        data_re= data[::2]
        data_im= data[1::2]
        return data_re,data_im
        
    
        
    
        
       