from .Device_Visa_Super import Device
import pyvisa
import numpy as np
import time
import matplotlib.pyplot as plt

class FSL(Device):
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
        minimum bandwidth of 300Hz
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
        max is 10001
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

    
                
    def system_error_next(self,):
        return self.query("system:error?")
    
    
 
           
    def sweep(self, central_freq, span, band_width, sweep_points,\
              video_band_width = 1, average_number = 1, sweep_time = False, *args, save = True, file_location = "", **kwargs):
        print(f"FSW:\nCurrent Errors:{self.query('system:error:list?')}")
        self.write("system:error:clear:all")
        
        self.write('INIT:CONT OFF')
        
        
        
        self.set_cent_freq(central_freq)
        self.set_span(span)
        self.set_bw(band_width)
        self.set_video_bw(video_band_width)
        self.set_sweep_points(sweep_points)
        self.set_average_state("ON")
        self.set_average_number(average_number)

        if sweep_time != False:
            self.set_sweep_time(sweep_time)
            print(f"setting sweep time to {sweep_time}")
        else:
            sweep_time = self.sweep_duration_query()


        print("FSW: sweeping")
        self.write('INIT:IMM')
        
        

        print(f"FSW:{self.system_error_next()}")
        expected_time = float(sweep_time)*1.1*average_number + 1


        print(f"FSW:expected sweep time:{expected_time}")
        self._device.timeout = None
        
        
        print(f"waiting: {expected_time*10}")
        #plt.pause(expected_time*10)

        print("WAI command")
        self.WAI()
        print("saving y data")
        data_p = self.y_data_query()

        self._device.timeout = self.timeout
        self.power=np.fromstring(data_p,dtype=float,sep=',')
        number_of_points = len(self.power)

        central_freq = float(central_freq)
        span = float(span)

        self.freqs = np.linspace(central_freq-span/2, central_freq+span/2, number_of_points)
        
        if save:
            meta_data = f"central_freq_{central_freq},span_{span},band_width_{band_width},sweep_points{sweep_points},average_number{average_number}"
            headers = "power[dBm],frequency[Hz]"
            self.save_data(self.power, self.freqs, *args, meta_data = meta_data, headers = headers, \
                           file_location = file_location, **kwargs)
        
        print("Stopping sweep")
        self.write('INIT:CONT OFF')
        
        
        return self.power, self.freqs


    
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
