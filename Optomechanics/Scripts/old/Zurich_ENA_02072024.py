
import matplotlib.pyplot as plt
import numpy as np
import time
import os
from datetime import datetime
import pyvisa
from DeviceClasses.E5063A_VNA_Class import VNA
# Convert dBm to linear power
def dBm_to_power(dBm):
    return 10 ** (dBm / 10)   



#%%
date = datetime.now().strftime("%Y_%m_%d")
description= 'Characterisation'
base_path = f'C:\\Users\\RoomTemp\\Documents\\Experiments\\Old RT redo\\Resonance Frequency vs Time\\{date}\\'
try:os.mkdir(base_path)
except: print("didn't make file")

address = 'TCPIP::169.254.216.160::INSTR'
channels = [1]      # formatting: [1,2,3,4]
measuring = ["S21",] # formatting: ["S12", "S21"..]
traces = ["1"] # formatting: ["CH1TR1", "CH2TR1"]
cent_freq=3.957153298e9
span=2e9
freq_start = cent_freq-span/2
freq_stop = cent_freq+span/2
number_of_point=200
band_width = 1e3
power=-5
timestamp=time.time()
with VNA(address,) as vna:
    print(vna.IDN_query())
    print("delay:", vna._device.query_delay)
    
    
    
    for channel in channels:
        for matrix in measuring:
            for trace_name in traces:
                print("useful:",channel, matrix)
                file_name_prefix = matrix
                data = vna.sweep(channel, matrix, trace_name, freq_start, freq_stop, number_of_point,\
                                 power, band_width,\
                                 _file_name=file_name_prefix, file_location= base_path, reset = True)
                fig, ax = plt.subplots()
                #ax.set_yscale("log")
                ax.plot(data[2], data[0])
                ax.set(title = f"{matrix}", ylabel = "Voltage [dBm]", xlabel = "frequency [Hz]")
                plt.show()
            
            
                

            