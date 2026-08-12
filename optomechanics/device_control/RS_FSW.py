from .Device_Visa_Super import Device
import pyvisa
import numpy as np
import time
import matplotlib.pyplot as plt
from optomechanics.data_analysis.unit_conversions import dBm_to_watts, watts_to_dBm

class FSW(Device):
    """

    RS Spectrum analyser control code
    manual:https://www.rohde-schwarz.com/uk/manual/fsw-user-manual-manuals_78701-29088.html
    Based off of original code by Dr Sumit Kumar.
    """
    def __init__(self, address, timeout = 100000, **kwargs):
        Device.__init__(self, address, timeout, **kwargs)
        
        
        
    def set_cent_freq(self,cent_freq):
        self.write('FREQ:CENT'+' '+str(cent_freq))
        
    def read_cent_freq(self):
        return self.query('FREQ:CENT?')
    
    def set_span(self,span):
        self.write('FREQ:SPAN'+' '+str(span))
        
    def read_span(self):
        return self.query('FREQ:SPAN?')
    
    def set_bw(self,bw):
        """
        minimum bandwidth of 1Hz
        """
        self.write('BAND'+' '+str(bw))

    def set_video_bw(self, vid_bw):
        """
        video bandwidth is an artificial bandwidth that I don't fully understand, it should be set low however
        """
        self.write(f"BAND:VID {vid_bw}")

    def read_bw(self):
        return self.query('BAND?')
    
    def set_sweep_points(self, points):
        """
        default is 1001
        max is 100001
        """
        self.write('SWE:POIN'+' '+str(points))
        
    def set_sweep_time(self, duration):
        self.write('SWE:TIME'+' '+str(duration))
        
    def get_sweep_time(self):
        """ warning, this may change other settings"""
        

        return self.query('SWE:TIME?')
        
    def set_sweep_count(self, count):
        """
        equivalent to average for single sweep mode,
        see 'Sweep/Average Count':https://www.rohde-schwarz.com/webhelp/FSW_HTML_UserManuals_en/Content/83c62bf2eec542d5.htm#d4450894e55595
        sweep count max: 200000
        """
        self.write(f'SWE:COUNT {count}')
        
    def read_sweep_points(self):
        return self.query('SWE:POIN?')
    
    def set_average_state(self, Bool):
        """ON|OFF|1|0 """
        self.write('AVER:STAT'+' '+str(Bool))
        
    def set_average_number(self, number):
        self.write('AVER:COUN'+' '+str(number))  
        
    def set_reference_level(self, level_dbm):
        """Set the reference level in dBm."""
        self.write(f'DISP:WIND:TRAC:Y:RLEV {level_dbm}')
        
    def sweep_duration_query(self):
        """Query total sweep duration, including data processing"""
        return self.query("sweep:duration?")
    
    def y_data_query(self, TraceNumber = "TRACE1"):
        return self.query(f"trace:data? {TraceNumber}")
    
    def x_data_query(self, TraceNumber = "TRACE1"):
        return self.query(f"trace:data:x? {TraceNumber}")
    
    
                
    def system_error_next(self,):
        return self.query("system:error?")
    

    def autoscale_axes(self):
        self.write("display:trace:y:auto once")

    def auto_level(self):
        "auto levels"
        self.write("ADJ:LEV")


    def set_ref_level(self, level):
        """set level in dBm"""
        self.write(f"DISP:TRAC:Y:RLEV {level}dBm")

    def set_ref(self, loc = "EXT"):
        """ sets the ref, ext or int
        EXT or INT
        doesn#t work
        """
        return self.write(f"ROSC:SOUR {loc}")
    
    def use_detector_type_average(self,):
        return self.write(":SENS:WIND1:DET1:FUNC AVER")

    def sweep(self, central_freq, span, band_width, sweep_points, video_band_width = 1,\
              average_number = 1, sweep_time = False, ref_level = "auto", use_average_sample = False, ref = "EXT", *args, save = True, file_location = "", file_name = "default", **kwargs):
        print(f"FSW:\nCurrent Errors:{self.query('system:error:list?')}")
        self.write("system:error:clear:remote")
        self.RST()
        self.set_ref(ref)

        
        self.write('INIT:CONT OFF')
        
        
         
        self.set_cent_freq(central_freq)
        self.set_span(span)
        self.set_bw(band_width)
        self.set_video_bw(video_band_width)
        self.set_sweep_points(sweep_points)
        #self.set_average_state("ON")
        #self.set_average_number(average_number)


        if sweep_time != False:
            self.set_sweep_time(sweep_time)

        if ref_level == "auto":
            self.auto_level()
        else: self.set_ref_level(ref_level)

        if use_average_sample == True:
            self.use_detector_type_average()

        self.data = [[]]
        self._device.timeout = None
        sweep_time = self.sweep_duration_query()
        expected_time = float(sweep_time)*1.1*average_number + 1
        print(f"FSW:expected sweep time:{expected_time}")
        
        for count in range(average_number):
            self._device.timeout = None
            print("FSW: sweeping")
            self.write('INIT:IMM')
            
            print(f"FSW:{self.system_error_next()}")
            self.autoscale_axes()
            
            
            
            #plt.pause(expected_time)
            self.autoscale_axes()
            #self.wait_on_OPC(wait_time = expected_time/4, function = self.autoscale_axes)
            self.WAI()
            data_p = self.y_data_query()
            
            self._device.timeout = self.timeout

            self.power=np.fromstring(data_p,dtype=float,sep=',')
            
            self.data.append(self.power)

        data_f = self.x_data_query()    
        self.freqs=np.fromstring(data_f,dtype=float,sep=',')    

        #print(len(self.power))
        #print(len(self.freqs))

        self.data[0] = self.freqs
        self.data = np.array(self.data)
        #print(self.data)
        print(self.data.shape)
        print("saving data")

        if save:
            meta_data = f"central_freq_{central_freq},span_{span},band_width_{band_width},sweep_points{sweep_points},average_number{average_number}"
            headers = "frequency[Hz]    powers[dBm]"
            self.save_data_2(self.data, *args, meta_data = meta_data, headers = headers, \
                           file_location = file_location, file_name = file_name )
        
        self.write('INIT:CONT OFF') 

        self.powers = watts_to_dBm(np.mean(dBm_to_watts(self.data[1:]), axis = 0, dtype = np.longdouble))

        return self.powers, self.freqs


    
    def VNA_mode(self, central_freq, span, band_width, sweep_points,\
              average_number = 1, sweep_time = False, *args, save = True, file_location = "", **kwargs):
        #print(f"FSW:\nCurrent Errors:{self.query('system:error:list?')}")
        self.write("system:error:clear:remote")
        
        self.write('INIT:CONT OFF')
        
        
        
        self.set_cent_freq(central_freq)
        self.set_span(span)
        self.set_bw(band_width)
        self.set_sweep_points(sweep_points)
        self.set_average_state("ON")
        self.set_average_number(average_number)

        if sweep_time != False:
            self.set_sweep_time(sweep_time)

        #print("FSW: sweeping")
        self.write('INIT:IMM;*WAI')
        
        
        # errors = self.system_error_next()
        # if errors != '0,"No error"':
        #     print(f"FSW:{errors}")

        #self.WAI()
        self.autoscale_axes()
        #self.wait_on_OPC(wait_time = expected_time/4, function = self.autoscale_axes)

        data_p = self.y_data_query()
        data_f = self.x_data_query()


            
        self.power=np.fromstring(data_p,dtype=float,sep=',')
        self.freqs=np.fromstring(data_f,dtype=float,sep=',')
        
        if save:
            meta_data = f"central_freq_{central_freq},span_{span},band_width_{band_width},sweep_points{sweep_points},average_number{average_number}"
            headers = "power[dBm],frequency[Hz]"
            self.save_data(self.power, self.freqs, *args, meta_data = meta_data, headers = headers, \
                           file_location = file_location, **kwargs)
        
        self.write('INIT:CONT OFF')
        
        
        return self.power, self.freqs
