"""

A script to combine two arbitry devices capable of
signal generation and detection (Signal generator
and spectrum analyser) to emualate a VNA

By Sean Hibbitt 
"""
import numpy as np
from ..data_management import save_data_3
from .fitting._fitting import dBm_to_watts, watts_to_dBm, watts_ratio_to_dB

class Vector_Network_Analyser():
    
    
    def __init__(self, signal_generator, signal_analyser,):
        
        """
        returns an instance of the Vector_Network_Analyser class
        after being passed a signal_generator and signal_analyser
        function.
        
        The functions must fit:
            
        def SG(frequency, power, OnOff )
        
        def SA(freq, band_width):
            return amplitude[dBm], frequency
        
        
        span and sweep_points should be minimised in SA
        
        (to be updated with phase)
        
        Setup to only sweep one S parameter at a time as not
        a proper VNA
        
        """
        
        self.SG = signal_generator
        self.SA = signal_analyser

    def sweep(self, central_frequency, span, sweep_points, power, band_width, extra_meta = {}, save_location = None, file_name = ""):
        if central_frequency-span/2 <=0:
            raise ValueError("invalid span")
        
        power_watts = dBm_to_watts(power)
        
        args = locals()
        
        self.SG(central_frequency, power, "ON")   
        
        amplitudes = []
        amplitudes_sig = []
        self.data = []

        frequencies = np.linspace(central_frequency-span/2, central_frequency+span/2, sweep_points, endpoint  = True)
        self.data.append(frequencies)

        amplitudes = []
        amplitudes_sig = []
        
        i = 0
        for frequency in frequencies :
            self.SG(frequency, power, "ON")
            amplitudes_raw, frequencies_temp = np.array(self.SA(frequency, band_width))
            #print(f"amplitudes_raw:{amplitudes_raw}")
            amplitudes_watts_ratio = dBm_to_watts(amplitudes_raw)/power_watts
            #print(f"amplitudes_watts_ratio:{amplitudes_watts_ratio}")

            
            amplitudes.append(np.mean(amplitudes_watts_ratio))
            amplitudes_sig.append(np.std(amplitudes_watts_ratio))

            i = i+1
            print(f"vna_sweep:{100*(i/frequencies.size)}% finished")
        
            
        amplitudes = np.array(amplitudes)
        amplitudes_sig = np.array(amplitudes_sig)

        
            

        print(f"amplitudes = {amplitudes}")
        print(f"amplitudes = {np.array(amplitudes).shape}")

        amplitudes = watts_ratio_to_dB(amplitudes)
        amplitudes_sig = watts_ratio_to_dB(amplitudes_sig)

        self.data.append(amplitudes)
        self.data.append(amplitudes_sig)
        
        self.SG(frequency, power, "OFF")
        if save_location != None:
            print(f"saving data to:{save_location}, name:{file_name}")
            meta_data = {} | extra_meta
            
            variables = [x for x in args.items()][2:-2]
            for variable, element in variables:
                meta_data[variable] = element
            
            headers = "frequency[Hz]    S21[dB]    S21_sig[dB]"
            save_data_3(self.data, meta_data = meta_data, headers = headers, \
                           file_location = save_location, file_name = file_name )
            


        return frequencies, amplitudes, amplitudes_sig
        
