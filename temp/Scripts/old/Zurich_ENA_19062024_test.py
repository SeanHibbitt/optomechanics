import zhinst.core
import matplotlib.pyplot as plt
import numpy as np
import time
from hgutilities.utils.paths import make_folder
from hgutilities.utils.printiterable import get_iterable_string
from hgutilities.utils import save_to_path, get_file_name
import os
from datetime import datetime
import pyvisa
import glob
def lorentzian_power(x, x0, kext,ktot):
    return kext**2 / (ktot**2 + (x - x0) **2)

# Convert dBm to linear power
def dBm_to_power(dBm):
    return 10 ** (dBm / 10)   

from scipy.optimize import curve_fit
from drawnow import drawnow


#%%
date = datetime.now().strftime("%Y_%m_%d")
description= 'S21_data_broad_sweep'
base_path = 'D:\\Documents\\Experiments Data\\Thin_film_exp_2\\2024_06_20\\'+str(date)+'_'+str(description)+'\\'
try:os.mkdir(base_path)
except: print("didn't make file")
Temps=[2.2]
for Temp in Temps:
    rm = pyvisa.ResourceManager()  
    rm.list_resources()
    MG1 = SMA100B('TCPIP::134.219.128.91::INSTR')
    MG1.turn_mw('OFF')
    temp_file='Z:\\Temp_set_point.txt'
    data=open(temp_file,'w')
    data.write('TEMP'+'\t'+'MXC'+'\t'+str(Temp)+'\t'+'1')
    data.close()
    time.sleep(2)
    
    
    ######### Finding the resonance frequency using ZNA ###########################
    
    from DeviceClasses.E5063A_VNA_Class import VNA
    address = 'TCPIP::134.219.128.53::INSTR'
    #This seems to make sure any preivous connections are removed.
    #zna = ZNA(address,)
    #zna.close()
    
    channels = [1]      # formatting: [1,2,3,4]
    measuring = ["S21"] # formatting: ["S12", "S21"..]
    traces = ["1"] # formatting: ["CH1TR1", "CH2TR1"]
    cent_freq=6.9648024e9
    span=5e6
    freq_start = cent_freq-span/2
    freq_stop = cent_freq+span/2
    number_of_point=10001
    band_width = 1e3
    power=0
    timestamp=time.time()
    file_name_prefix = 'Temp_'+str(Temp)+'_K_'
    with VNA(address,) as vna:
        
        print(vna.IDN_query())
        print("delay:", vna._device.query_delay)
    
        for channel, matrix, trace_name in zip(channels,\
                                               measuring,\
                                               traces):
            
            
            
            print("useful:",channel, matrix)
            data = vna.sweep(channel, matrix, trace_name, freq_start, freq_stop, number_of_point,\
                             power, band_width,\
                             _file_name=file_name_prefix, file_location= base_path, reset = True)
 
    
        vna.close()
    files=glob.glob(base_path + '/*.tsv')   
    for file in files:
        file_name=file.split('_')
        if float(file_name[12])==float(Temp):
    
    
            data = np.genfromtxt(file, delimiter='\t', skip_header=2)
        
            frequency = data[:, 2]
            amp1 = data[:, 0]
        
        
        
            max_index=np.where(amp1==max(amp1))
            peak_freq=frequency[max_index[0]][0]
            kext = 8e3   # Full-width at half-maximum
            ktot = 250e3
            s21_power = dBm_to_power(amp1)  # Convert to linear power
        
            # Fit the data using curve_fit in the power domain
            popt, pcov = curve_fit(lorentzian_power, frequency, s21_power, p0=[peak_freq, kext, ktot])
        
            # Plot the data and the fit
            plt.figure(figsize=(10, 6))
            plt.plot(frequency, s21_power, 'C0-', label='Data (S21 in Power)')
            plt.plot(frequency, lorentzian_power(frequency, *popt), 'k--', label='Fit in Power Domain')
            plt.title('Lorentzian Fit of S21 in Power Domain')
            plt.xlabel('Frequency (GHz)')
            plt.ylabel('S21 (linear scale)')
            plt.legend()
            plt.show()
            drive_freq=float(popt[0])    ###### Drive frequency is the fitted resonance peak from the S21 data
            print(drive_freq)
            # Output the fitted resonance frequency
            print(f"Estimated Resonance Frequency: {popt[0]} GHz")
            plt.pause(1)
            #plt.close()
            plt.pause(1)
            
            
            
            
            
            
            rm = pyvisa.ResourceManager()  
            rm.list_resources()
            MG1 = SMA100B('TCPIP::134.219.128.91::INSTR')
            date = datetime.now().strftime("%Y_%m_%d")
            drive_power=30
            
            # Connect to MFIA Instrument
            device_id = 'dev1374'
            apilevel = 6
            daq = zhinst.core.ziDAQServer('127.0.0.1', 8005, 1)


            description='Temp_'+str(Temp)+'_K_Frequency_sweep_broad_sweep'
            base_path_zurich = ("D:\\Documents\\Experiments Data\\Thin_film_exp_2\\"
                         f"2024_06_19\\{date}_{description}")
            demod_paths = [os.path.join(base_path_zurich, f"Demod {i+1}") for i in range(3)]
            make_folder(base_path_zurich)
            for demod_path in demod_paths:
                 make_folder(demod_path)
    
            tcs=[10e-3, 10e-3]
            sampling_rate=224.9
            amplitudes=[10] # Amplitude in V
            offset = 0 # Offset (bias voltage) in 
            output_range = 10.0  # Output range in V
            start_freqs = np.array([220])
            stop_freqs = np.array([280])
            sample_count=50001
            date = datetime.now().strftime("%Y_%m_%d")
            
            ####Microwave Generator setting parameters#########
            MG1.set_mw_frequency(drive_freq)
            MG1.set_mw_power(drive_power)
            MG1.turn_mw('ON')
            counters=1

            for start_freq,stop_freq in zip(start_freqs,stop_freqs):
                for tc in tcs:
                    for amplitude in amplitudes:
                        for count in range(counters):
                        # Setting the demods to be on the first oscillator
                            daq.setInt('/dev1374/demods/0/oscselect', 0)
                            daq.setInt('/dev1374/demods/1/oscselect', 0)
                            daq.setInt('/dev1374/demods/2/oscselect', 0)
                            daq.setInt('/dev1374/demods/3/oscselect', 0)
                            
                            # Setting the harmonics
                            daq.setInt('/dev1374/demods/0/harmonic', 1)
                            daq.setInt('/dev1374/demods/1/harmonic', 2)
                            daq.setInt('/dev1374/demods/2/harmonic', 3)
                            daq.setInt('/dev1374/demods/3/harmonic', 3)
                            
                            # Set the bandwidths/time constants
                            daq.setDouble('/dev1374/demods/0/timeconstant', tc)
                            daq.setDouble('/dev1374/demods/1/timeconstant', tc)
                            daq.setDouble('/dev1374/demods/2/timeconstant', tc)
                            daq.setDouble('/dev1374/demods/3/timeconstant', tc)
                            
                            # Set the demod sample rates
                            daq.setDouble('/dev1374/demods/0/rate', sampling_rate)
                            daq.setDouble('/dev1374/demods/1/rate', sampling_rate)
                            daq.setDouble('/dev1374/demods/2/rate', sampling_rate)
                            daq.setDouble('/dev1374/demods/3/rate', sampling_rate)
                            
                            daq.setInt('/dev1374/demods/0/enable', 1)
                            daq.setInt('/dev1374/demods/1/enable', 1)
                            daq.setInt('/dev1374/demods/2/enable', 1)
                            daq.setInt('/dev1374/demods/3/enable', 0)
                            
                            # Turning off sinc filters.
                            daq.setInt('/dev1374/demods/0/sinc', 0) # Demodulator 1
                            daq.setInt('/dev1374/demods/1/sinc', 0) # Demodulator 2
                            daq.setInt('/dev1374/demods/2/sinc', 0) # Demodulator 3
                            daq.setInt('/dev1374/demods/3/sinc', 0) # Demodulator 4
                            
                            # Setting the input signal for the demods
                            daq.setInt('/dev1374/demods/0/adcselect', 1) # Demodulator 1
                            daq.setInt('/dev1374/demods/1/adcselect', 1) # Demodulator 2
                            daq.setInt('/dev1374/demods/2/adcselect', 1) # Demodulator 3
                            daq.setInt('/dev1374/demods/3/adcselect', 1) # Demodulator 4
                            
                            daq.setInt('/dev1374/demods/0/order', 4)
                            daq.setInt('/dev1374/demods/1/order', 4)
                            daq.setInt('/dev1374/demods/2/order', 4)
                            daq.setInt('/dev1374/demods/3/order', 4)
                            
                            # Sigins
                            daq.setInt('/dev1374/sigins/0/ac', 1)
                            daq.setInt('/dev1374/sigins/0/imp50', 0)
                            daq.setInt('/dev1374/sigins/0/diff', 0)
                            
                            # Sigout
                            daq.setInt('/dev1374/sigouts/0/on', 1)
                            daq.setInt('/dev1374/sigouts/0/enables/6', 1)
                            daq.setDouble('/dev1374/sigouts/0/range', output_range)
                            daq.setDouble('/dev1374/sigouts/0/amplitudes/6', amplitude/10)
                            daq.setDouble('/dev1374/sigouts/0/offset', 0/10)
                            
                            
                            harmonics=['Demod 1','Demod 2','Demod 3']
                            units=['V','V','V']
                            plt.ion()
                            fig, axs = plt.subplots(3, 1, figsize=(10, 12))
                            lines = [ax.plot([], [],'.-')[0] for ax in axs]
                            fig.subplots_adjust(hspace=0.5)
                            for ax, harmonic,unit in zip(axs, harmonics,units):
                                ax.set_xlabel('Frequency (Hz)')
                                ax.set_ylabel(f'Amplitude ({unit})')
                                ax.set_title(f'dev1374 Sweeper Measurement -{harmonic}')
                                
                                
                            sweeper = daq.sweep()
                            sweeper.set('device', 'dev1374')
                            sweeper.set('xmapping', 0)
                            sweeper.set('historylength', 100)
                            sweeper.set('bandwidthcontrol', 0) # Bandwidth control is fixed now
                            sweeper.set('gridnode', '/dev1374/oscs/0/freq')
                            sweeper.set('save/directory', 'D:\\Documents\\Zurich Instruments\\LabOne\\WebServer')
                            sweeper.set('averaging/sample', 1)
                         
                            sweeper.set('start', start_freq)
                            sweeper.set('stop', stop_freq)
                         
                            sweeper.set('samplecount', sample_count)
                            sweeper_results = 0
                            sweeper.subscribe('/dev1374/demods/0/sample')
                            sweeper.subscribe('/dev1374/demods/1/sample')
                            sweeper.subscribe('/dev1374/demods/2/sample')
                            sweeper.execute()
                            while sweeper.progress() < 1.0 and not sweeper.finished():
                                time.sleep(5)
                                sweeper_results = sweeper.read()
                                print(f"Progress {float(sweeper.progress()) * 100:.2f} %\r")
                               
                                #if device in sweeper_results:
                                plotting_params=[
                                                 sweeper_results['dev1374']['demods']['0']['sample'][0][0]['r'],
                                                 sweeper_results['dev1374']['demods']['1']['sample'][0][0]['r'],
                                                 sweeper_results['dev1374']['demods']['2']['sample'][0][0]['r']]
                                plotting_freqs=[
                                                 sweeper_results['dev1374']['demods']['0']['sample'][0][0]['frequency'],
                                                 sweeper_results['dev1374']['demods']['1']['sample'][0][0]['frequency'],
                                                 sweeper_results['dev1374']['demods']['2']['sample'][0][0]['frequency']]
                                for index,(line,ax) in enumerate(zip(lines,axs)):
                                    amp = plotting_params[index]
                                    frequency = plotting_freqs[index]
                                    line.set_xdata(frequency)
                                    line.set_ydata(amp)
                                    ax.relim()
                                    ax.autoscale_view(True, True, True)
                                    plt.pause(0.05)
                                    fig.canvas.flush_events()
                            
                            sweeper.finish()
                            # Update the plot data
                            plotting_params=[
                                             sweeper_results['dev1374']['demods']['0']['sample'][0][0]['r'],
                                             sweeper_results['dev1374']['demods']['1']['sample'][0][0]['r'],
                                             sweeper_results['dev1374']['demods']['2']['sample'][0][0]['r']]
                            plotting_freqs=[
                                             sweeper_results['dev1374']['demods']['0']['sample'][0][0]['frequency'],
                                             sweeper_results['dev1374']['demods']['1']['sample'][0][0]['frequency'],
                                             sweeper_results['dev1374']['demods']['2']['sample'][0][0]['frequency']]
                            for index,(line,ax) in enumerate(zip(lines,axs)):
                                amp = plotting_params[index]
                                frequency = plotting_freqs[index]
                                line.set_xdata(frequency)
                                line.set_ydata(amp)
                                ax.relim()
                                ax.autoscale_view(True, True, True)
                                plt.pause(0.05)
                            plt.ioff()
                            plt.show()
                            sweeper.unsubscribe('*')
                            
                            
                            
                            
                            demod_parameters = ["frequency", "r", "phase", "x", "y",
                                                "rstddev", "phasestddev", "xstddev", "ystddev", "nexttimestamp"]
                            
                            def save_metadata_to_file(sweeper_results):
                                sweeper_results_string = get_iterable_string(sweeper_results)
                                file='Temp_'+str(Temp)+'_K_Metadata_V_app_'+str(amplitude)+'V_offset_'+str(offset)+'_V_start_freq_'+str(start_freq)+'_stop_freq_'+str(stop_freq)+'_sample_count_'+str(sample_count)+'_MW_drive_freq_'+str(drive_freq)+'_MW_drive_power_'+str(drive_power)+'_dBm_time_constant_'+str(tc)+'_s_.txt'
                                metadata_path = os.path.join(base_path_zurich,file )
                                with open(metadata_path, "w") as file:
                                    file.writelines(sweeper_results_string)
                            
                            
                            
                            def get_demod_results(sweeper_results):
                                demod_results = sweeper_results["dev1374"]["demods"]
                                demod_results = [demod_results[str(demod_number)]["sample"][0][0]
                                                 for demod_number in range(3)]
                                demod_results = [{key: demod_result[key] for key in demod_parameters}
                                                 for demod_result in demod_results]
                                return demod_results
                            
                            
                                        
                            def save_demods_results_to_file(sweeper_results):
                                get_demod_results(sweeper_results)
                                indexes=[0,1,2]
                                for demod_path,index in zip(demod_paths,indexes):
                                    file='Temp_'+str(Temp)+'_K_V_app_'+str(amplitude)+'_V_offset_'+str(offset)+'_V_start_freq_'+str(start_freq)+'_stop_freq_'+str(stop_freq)+'_sample_count_'+str(sample_count)+'_MW_drive_freq_'+str(drive_freq)+'_MW_drive_power_'+str(drive_power)+'_dBm__time_constant_'+str(tc)+'_s_.txt'
                                    file_path = os.path.join(demod_path,file )
                                    with open(file_path, "w") as file:
                                        for i in demod_parameters:
                                            file.write(str(i)+'\t')
                                        file.write('\n')
                                        for j in range(len(get_demod_results(sweeper_results)[0]['frequency'])):
                                            for i in demod_parameters:
                                                file.write(str(get_demod_results(sweeper_results)[index][i][j])+'\t')
                                            file.write('\n')
                            
                            
                            save_metadata_to_file(sweeper_results)
                            save_demods_results_to_file(sweeper_results)
                            plt.close()
                    daq.setInt('/dev1374/sigouts/0/on', 0)
                    daq.setInt('/dev1374/sigouts/0/enables/6', 0)
                