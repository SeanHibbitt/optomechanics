from Optomechanics.Device_Visa_Super_rs import Device
import pyvisa
import numpy as np
import time
import matplotlib.pyplot as plt
from Optomechanics.Utilities.Fitting import dBm_to_watts, watts_to_dBm, RMS_to_dBm
import pandas

class FSW(Device):
    """

    RS Spectrum analyser control code
    manual:https://www.rohde-schwarz.com/uk/manual/fsw-user-manual-manuals_78701-29088.html
    Based off of original code by Dr Sumit Kumar.
    """
    def __init__(self, address, timeout = 100000,  baud_rate = 9600, **kwargs):
        Device.__init__(self, address, timeout =  timeout, baud_rate = baud_rate, **kwargs)
        
        
        
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
        video bandwidth, equivalent to an averaging window
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
    
    #### IQ analyser mode specific functions:


    def sweep(self, central_freq, span, band_width, sweep_points, video_band_width = 1,\
              average_number = 1, sweep_time = False, ref_level = "auto", use_average_sample = False, ref = "EXT", *args, save = True, file_location = "", file_name = "default", extra_meta = {}, reset = True, **kwargs):
       
        args = locals()
       
        print(f"FSW:\nCurrent Errors:{self.query('system:error:list?')}")
        self.write("system:error:clear:remote")
        if reset == True:
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
        print(f"FSW:expected sweep time:{expected_time/60} minutes")
        
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

        #print(self.data)
        print(self.freqs.shape)
        print(self.data[1].shape)

        self.data = np.array(self.data)
        
        print(f"saving data to:{file_location}\\{file_name}")

        if save:
            meta_data = {"central_freq":central_freq,
                         "span":span,
                         "band_width":band_width,
                         "sweep_points":sweep_points,
                         "average_number":average_number} | extra_meta
            
            variables = [x for x in args.items()][2:-2]
            for variable, element in variables:
                meta_data[variable] = element
            
            headers = "frequency[Hz]    powers[dBm]"
            self.save_data_3(self.data, meta_data = meta_data, headers = headers, \
                           file_location = file_location, file_name = file_name )
        
        self.write('INIT:CONT OFF')

        self.powers = watts_to_dBm(np.mean(dBm_to_watts(self.data[1:]), axis = 0, dtype = np.longdouble))

        return self.powers, self.freqs


    
    def VNA_mode(self, central_freq, span, band_width, sweep_points,\
              average_number = 1, sweep_time = False, *args, save = True, file_location = "", extra_meta = {}, **kwargs):
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
    
    # def IQ_time_data_sweep(self, central_freq, span,  res_bw,\
    #             average_number = 1, ref_level = "auto", ref = "EXT", *args, save = True, file_location = "", file_name = "default", extra_meta = {}, reset = True, **kwargs):
        
    #     sample_rate = span*1.25
    #     record_points = sample_rate/res_bw
        
        
        
    #     print(f"FSW:\nCurrent Errors:{self.query('system:error:list?')}")
    #     self.write("system:error:clear:remote")
    #     if reset == True:
    #         self.RST()
    #     self.set_ref(ref)

    #     #create measurement channel
    #     self.write("INST:CRE IQ,'IQANALYZER'")
    #     #swith to single sweep modee
    #     self.write('INIT:CONT OFF')
    #     #query filter bw (useable frequencies)
    #     filter_bandwidth = self.query("TRAC:IQ:BWID?")
            
    #     self.set_cent_freq(central_freq)
    #     self.set_span(span)

    #     if ref_level == "auto":
    #         self.auto_level()
    #     else: self.set_ref_level(ref_level)

    #     #switch to simple daq mode:
    #     self.write("TRACE:IQ ON")

    #     #setup IQ Data sweep:
    #     self.write(f"TRACE:IQ:SET NORM,0,{sample_rate},IMM,POS,0,{record_points}")

    #     #set data form:
    #     #self.format

    #     self._device.timeout = None
    #     sweep_time = 1/res_bw
    #     print(f"FSW:expected sweep time:{sweep_time+1}")
    #     args = locals()


    #     self.data = []
        
    #     for count in range(average_number):
    #         self._device.timeout = None
    #         print(f"FSW: sweeping {count+1}/{average_number}")
    #         self.write("INI")
    #         self.autoscale_axes()
    #         #self.wait_on_OPC(wait_time = sexpected_time/4, function = self.autoscale_axes)
    #         self.WAI()
    #         print(f"finished sweep")
    #         y_data = self.query("TRAC:DATA? TRACE1")
    #         x_data = self.query("TRAC:X? TRACE1")
            
    #         print(f"FSW:{self.system_error_next()}")


    #         self._device.timeout = self.timeout

    #         self.y_data =np.fromstring(y_data,dtype=float,sep=',')
    #         self.x_data =np.fromstring(x_data,dtype=float,sep=',')

    #         self.data.append(self.y_data)
    #         self.data.append(self.x_data)
        
    #     self.data = np.asarray(self.data)
    #     print(f"daq finished")
    #     print(self.data)
    #     print(self.data.shape)
        
    #     print(f"saving data to:{file_location}\\{file_name}")

    #     if save:
    #         meta_data = {"central_freq":central_freq,
    #                         "span":span,
    #                         "res_band_width": res_bw,
    #                         "sweep_points"  : record_points,
    #                         "sample_rate"   : sample_rate,
    #                         "average_number": average_number
    #                     } | extra_meta
            
    #         variables = [x for x in args.items()][2:-2]
    #         for variable, element in variables:
    #             meta_data[variable] = element
            
    #         headers = "powers[dBm]\ttimes[s]"
    #         self.save_data_3(self.data, meta_data = meta_data, headers = headers, \
    #                         file_location = file_location, file_name = file_name )
        
    #     self.write('INIT:CONT OFF')

    #     #self.powers = watts_to_dBm(np.mean(dBm_to_watts(self.data), axis = 0, dtype = np.longdouble))

    #     return self.data, meta_data

    def IQ_time_data_sweep(self, central_freq, span,  res_bw,\
                average_number = 1, ref_level = "auto", ref = "EXT", *args, save = True, file_location = "", file_name = "default", extra_meta = {}, reset = True, **kwargs):
        
        sample_rate = span*1.25
        record_points = sample_rate/res_bw
        print(f"sample rate:{sample_rate}")
        print(f"record_points:{record_points}")

        
        
        print(f"FSW (1):\nCurrent Errors:{self.query('system:error:list?')}")
        self.write("system:error:clear:remote")
        if reset == True:
            self.RST()
        self.set_ref(ref)

        print(f"FSW (2):\nCurrent Errors:{self.query('system:error:list?')}")

        self.write('INIT:CONT OFF')
            
        print(f"FSW (3):\nCurrent Errors:{self.query('system:error:list?')}")


        self.set_cent_freq(central_freq)
        self.set_span(span)

        if ref_level == "auto":
            self.auto_level()
        else: self.set_ref_level(ref_level)

        print(f"FSW (4):\nCurrent Errors:{self.query('system:error:list?')}")


        #switch to simple daq mode:
        self.write("TRACE:IQ ON")
        #set IQ format
        self.write("TRAC:IQ:DATA:FORM IQPair")
        #self.write("FORM REAL,64")

        print(f"FSW (5):\nCurrent Errors:{self.query('system:error:list?')}")


        #setup IQ Data sweep:
        self.write(f"TRACE:IQ:SET NORM,0,{sample_rate},IMM,POS,0,{record_points}")
        TRACEIQSET = self.query("TRACE:IQ:SET?")
        print(TRACEIQSET)
        filter_bandwidth = self.query("TRAC:IQ:BWID?")
        print(f"filter_bandwidth:{filter_bandwidth}")

        print(f"FSW (6):\nCurrent Errors:{self.query('system:error:list?')}")


        #set data form:
        #self.format

        self._device.timeout = None
        sweep_time = 1/res_bw
        print(f"FSW:expected sweep time:{sweep_time+1}")
        args = locals()


        self.data = []
        
        for count in range(average_number):
            self._device.timeout = None
            print(f"FSW: sweeping {count+1}/{average_number}")
            IQ_data_str = self.query('TRAC:IQ:DATA?; *WAI')
            print(f"FSW:sweep finished")
            print(f"FSW: (7){self.system_error_next()}")


            self._device.timeout = self.timeout

            self.IQ_data=np.fromstring(IQ_data_str,dtype=float,sep=',')
            #print(self.IQ_data)
            print(self.IQ_data.shape)
            self.Q_data = self.IQ_data[range(0, len(self.IQ_data), 2)]
            self.I_data = self.IQ_data[range(1, len(self.IQ_data), 2)]
            #print(self.Q_data,"\n" ,self.I_data)
            print(self.I_data.shape)
            voltage = np.sqrt(self.I_data**2 + self.Q_data**2)
            #dBm = RMS_to_dBm(voltage)
            
        
            self.data.append(voltage)
        
        self.data = np.asarray(self.data)
        print(f"daq finished")
        #print(self.data)
        print(self.data.shape)
        
        print(f"saving data to:{file_location}\\{file_name}")


        meta_data = {"central_freq":central_freq,
                        "span":span,
                        "res_band_width": res_bw,
                        "sweep_points"  : record_points,
                        "sample_rate"   : sample_rate,
                        "average_number": average_number,
                        "filter_bandwidth":filter_bandwidth
                    } | extra_meta
        
        variables = [x for x in args.items()][2:-2]
        for variable, element in variables:
            meta_data[variable] = element

        if save:
            headers = "powers[dBm]"
            self.save_data_3(self.data, meta_data = meta_data, headers = headers, \
                            file_location = file_location, file_name = file_name )
        
        self.write('INIT:CONT OFF')

        #self.powers = watts_to_dBm(np.mean(dBm_to_watts(self.data), axis = 0, dtype = np.longdouble))

        return self.data, meta_data, self.Q_data, self.I_data
    

    def IQ_trace_sweep(self, central_freq, span,  res_bw,\
                average_number = 1, ref_level = "auto", ref = "EXT", *args, save = True,\
                file_location = "", file_name = "default", extra_meta = {}, reset = True, **kwargs):
        
        maximum_record_points = 440e6

        sample_rate = span*1.25
        record_points = int(sample_rate/res_bw)
        print(f"sample rate:{sample_rate}")
        print(f"record_points:{record_points}")


        if record_points >maximum_record_points:
            print(f"maximum record points = {maximum_record_points} \nsetting to maximum")
            record_points = int(maximum_record_points)
            res_bw = sample_rate/record_points
            print(f"new res_bw:{res_bw}")

        
        
        print(f"FSW (1):\nCurrent Errors:{self.query('system:error:list?')}")
        self.write("system:error:clear:remote")
        if reset == True:
            self.RST()
        self.set_ref(ref)

        print(f"FSW (2):\nCurrent Errors:{self.query('system:error:list?')}")

        #create IQ analyser channel
        self.write("INST:CRE IQ,'IQANALYZER'")
        self.write('INIT:CONT OFF')
            
        print(f"FSW (3):\nCurrent Errors:{self.query('system:error:list?')}")

        self.set_cent_freq(central_freq)
        #self.set_span(span)

        if ref_level == "auto":
            self.auto_level()
        else: self.set_ref_level(ref_level)

        print(f"FSW (4):\nCurrent Errors:{self.query('system:error:list?')}")


        #switch to simple daq mode:
        #set IQ format
        self.write("TRAC:IQ:DATA:FORM IQBLock")
        IQ_format = self.query("TRAC:IQ:DATA:FORM?")
        print(f"data format:{IQ_format}")
        #self.write("FORM REAL,64")
        #trace write mode:
        self.write("DISP:TRAC1:MODE WRIT")
        #add spectrum
        self.query("LAY:ADD:WIND? '1',RIGH,FREQ")
    


        print(f"FSW (5):\nCurrent Errors:{self.query('system:error:list?')}")


        #setup IQ Data sweep:
        self.write(f"TRACE:IQ:SET NORM,0,{sample_rate},IMM,POS,0,{record_points}")
        TRACEIQSET = self.query("TRACE:IQ:SET?")
        print(TRACEIQSET)
        filter_bandwidth = self.query("TRAC:IQ:BWID?")
        print(f"filter_bandwidth:{filter_bandwidth}")
        #trace_time_points:

        time_trace_length = record_points#
        time_trace_length_max = 100001
        if time_trace_length > time_trace_length_max:
            time_trace_length = time_trace_length_max

        self.write(":SENS:SWE:WIND1:POIN 100001")
        time_trace_points = self.query(":SENS:SWE:WIND1:POIN?")
        #set mode to sampling:
        self.write(":SENS:WIND1:DET1:FUNC AVER")
        time_trace_func = self.query(":SENS:WIND1:DET1:FUNC?")


        #setup spectrum:
        self.write("IQ:BAND:MODE FFT")
        self.write("IQ:FFT:ALG AVER")
        fft_transform_method = self.query("IQ:FFT:ALG?")
        self.write(f"DISP:TRAC1:MODE WRIT")
        fft_trace_mode = self.query("DISP:TRAC1:MODE?")
        self.write(f":SENS:WIND2:DET1:FUNC AVER")
        fft_trace_func = self.query(":SENS:WIND2:DET1:FUNC?")
        #set fft length to max:
        fft_trace_length = record_points#
        fft_trace_length_max = 524288
        if fft_trace_length > fft_trace_length_max:
            fft_trace_length = fft_trace_length_max

        self.write(f":SENS:IQ:FFT:LENG {fft_trace_length}")
        self.write(f":SENS:IQ:FFT:WIND:LENG {fft_trace_length}")

        fft_trace_length = self.query(":SENS:IQ:FFT:LENG?")
        fft_window_length = self.query(":SENS:IQ:FFT:WIND:LENG?")



        print(f"FSW (6):\nCurrent Errors:{self.query('system:error:list?')}")


        #set data form:
        #self.format

        self._device.timeout = None
        sweep_time = 1/res_bw
        print(f"FSW:expected sweep time and data retrieval:{sweep_time*1.74257425743/60} minutes")
        args = locals()


        self.data_power = [[]]
        self.data_fft_power = [[]]
        self.data_IQ_voltage = [[]]

        self._device.data_chunk_size = 1e9
        
        for count in range(average_number):
            self._device.visa_timeout = 1e9
            print(f"FSW: sweeping {count+1}/{average_number}")
            self.write('INIT;*WAI')
            print(f"FSW:{self.system_error_next()}")
            print(f"retrieving time domain data")
            time_domain_power = np.fromstring(self.query("TRAC1:DATA? TRACE1"),dtype=float,sep=',')
            print(f"retrieving spectrum data")
            freq_domain_power = np.fromstring(self.query("TRAC2:DATA? TRACE1"),dtype=float,sep=',')
            print(f"retrieving raw data")
            I = []
            Q = []
    
            
            #max_split_number = 100
            max_chunk_size = 131072
            split_number = int(np.ceil(record_points/max_chunk_size))
            chunk_size = int(record_points/split_number)
            print(f"chunk_size:{chunk_size}")
            for i in range (split_number):
                i = i
                start_position = i * chunk_size
                print(f"start_position:{start_position},chunks_size:{chunk_size},loading: {(i+1)*chunk_size/record_points*100}%")
                data_temp = np.fromstring(self.query(f"TRAC1:IQ:DATA:MEMory? {start_position},{chunk_size}"), dtype = float, sep = "," )
                I_temp = data_temp[0:chunk_size].tolist()
                Q_temp = data_temp[chunk_size:].tolist()
                I = I + I_temp
                Q = Q + Q_temp

                print(f" % loaded:{(i+1)*chunk_size/record_points*100}%")
                print(f"FSW (7):\nCurrent Errors:{self.query('system:error:list?')}")

            print(f"raw data retrieved")
        

            print(f"FSW:sweep finished")


            self._device.visa_timeout = self.timeout

            self.data_power.append(time_domain_power)
            self.data_fft_power.append(freq_domain_power)
            self.data_IQ_voltage.append(I)
            self.data_IQ_voltage.append(Q)
            print(f"data_I:{len(I)}")
            print(f"data_IQ:{len(self.data_IQ_voltage[0])},{len(self.data_IQ_voltage[1])},{len(self.data_IQ_voltage[2])}")

        print(f"retrieving x data")
        self.data_power[0] = np.fromstring(self.query("TRAC1:X? TRACE1"),dtype=float,sep=',')
        self.data_fft_power[0] = np.fromstring(self.query("TRAC2:X? TRACE1"),dtype=float,sep=',')
        self.data_IQ_voltage[0] = np.linspace(0, 1/res_bw, len(I), endpoint= True)
        print(f"data_IQ:{len(self.data_IQ_voltage[0])},{len(self.data_IQ_voltage[1])},{len(self.data_IQ_voltage[2])}")

        #print(f"time_data:\n{self.data_power}")
        
        self.data_power = np.asarray(self.data_power)
        self.data_fft_power = np.asarray(self.data_fft_power)
        self.data_IQ_voltage = np.asarray(self.data_IQ_voltage)

        print(f"daq finished")
        #print(self.data)
        print(f"fft data shape:{self.data_fft_power.shape}")
        print(f"time data shape:{self.data_power.shape}")
        
        print(f"saving data to:{file_location}\\{file_name}")


        meta_data = {"central_freq":central_freq,
                        "span":span,
                        "res_band_width": res_bw,
                        "sweep_points"  : record_points,
                        "sample_rate"   : sample_rate,
                        "average_number": average_number,
                        "filter_bandwidth":filter_bandwidth
                    } | extra_meta
        
        variables = [x for x in args.items()][2:-2]
        for variable, element in variables:
            meta_data[variable] = element

        meta_data["domain"] = "time"

        #time:
        if save:
            headers = "time[s]\tpowers[dBm]"
            self.save_data_3(self.data_power, meta_data = meta_data, headers = headers, \
                            file_location = file_location, file_name = file_name+"_time_domain_.tsv" )

        meta_data["domain"] = "freq"
          
        if save:
            headers = "freq[Hz]\tpowers[dBm]"
            self.save_data_3(self.data_fft_power, meta_data = meta_data, headers = headers, \
                            file_location = file_location, file_name = file_name+"_freq_domain_.tsv" )
            
        meta_data["domain"] = "IQ_voltage_mag"
        if save:
            headers = "time[s]\tI_voltage_rms[V]\tQ_voltage_rms[V]"
            #in rms, found by trial and error when comparing to SA result
            self.save_data_3(self.data_IQ_voltage, meta_data = meta_data, headers = headers, \
                            file_location = file_location, file_name = file_name+"_IQRAW_domain_.tsv" )
        
        self.write('INIT:CONT OFF')

        #self.powers = watts_to_dBm(np.mean(dBm_to_watts(self.data), axis = 0, dtype = np.longdouble))

        return self.data_power, self.data_fft_power, self.data_IQ_voltage, meta_data
    

#     Displays the frequency spectrum of the captured I/Q samples.

# The specified "Analysis Bandwidth" is indicated by vertical blue lines.

# Remote command: 
# LAY:ADD:WIND? '1',RIGH,FREQ, see LAYout:ADD[:WINDow]?

# Results:

# TRACe<n>[:DATA]?

 