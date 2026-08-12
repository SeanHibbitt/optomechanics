from optomechanics.device_control.Lakeshore_372_AC_Res_Temp_Controller import Temp_Controller

import time
import datetime
import os
import traceback
import numpy as np

# Configuration
address = 'GPIB0::12::INSTR'
channel_1k = 3      # Channel for 1K pot thermometer
channel_mc = 4      # Channel for Mixing Chamber thermometer
sample_interval = 1.0  # Time between readings in seconds

def save_data_3(data, file_name, file_location = "D:\Python\Optomechanics\Optomechanics\GUI\test_data", headers = None, meta_data = {}, delimiter = "\t"):
    data = np.array(data)
    data_shape = np.shape(data)
    print(f"datashape:{data_shape}")
    with open(file_location+file_name, "w") as file1:
        for key, value in meta_data.items():
            file1.write(f"#\t{key}\t{value}\n")
        if headers != None:
            file1.write(headers+"\n")
        
        try:
            for  i in range(data_shape[1]):
                for l in range(data_shape[0]):
                    file1.write(f"{data[l,i]}\t")
                file1.write("\n")
        except IndexError as e:
            print(f"index error:\n{e}\ndata:\n{data}")
            for  i in range(data_shape[0]):
                file1.write(f"{data[i]}\t")
                file1.write("\n")


def create_filename():
    """Creates a filename with current date and time and full path"""
    
    # Define the directory path
    base_path = r"D:\Python\Optomechanics\Optomechanics\GUI\test_data"
    
    # Create the directory if it doesn't exist
    os.makedirs(base_path, exist_ok=True)
    
    # Create filename with timestamp
    now = datetime.datetime.now()
    filename = f"lakeshore_data_{now.strftime('%Y-%m-%d_%H-%M-%S')}.tsv"
    
    # Combine path and filename
    full_path = os.path.join(base_path, filename)
    
    return full_path

def write_header(file):
    """Writes column headers to the file"""
    header = (
        "# Timestamp | T_1k[K] | R_1k[Ohm] | Excitation_1k[W] | T_mc[K] | R_mc[Ohm] | Excitation_mc[W]\n"
    )
    file.write(header)

def main():
    """Main data logging loop"""
    
    # Create file with timestamp
    filename = create_filename()
    print(f"Starting data logging to: {filename}")
    print(f"Press Ctrl+C to stop\n")
    
    with open(filename, 'w') as datafile:
        # Write header
        write_header(datafile)
        
        # Connect to Lakeshore
        with Temp_Controller(address) as lakeshore:
            
            # Data logging loop
            try:
                print("Starting data collection loop...")
                loop_count = 0
                
                while True:
                    loop_count += 1
                    print(f"\n--- Loop iteration {loop_count} ---")
                    
                    # Get current time
                    timestamp = time.time()
                    print(f"Timestamp: {timestamp}")
                    
                    # Read 1K pot data
                    try:
                        print("Reading channel 1K (channel 3)...")
                        t_1k = float(lakeshore.ReadTemperature(channel_1k))
                        print(f"  T_1k = {t_1k}")
                        
                        r_1k = float(lakeshore.ReadResistance(channel_1k))
                        print(f"  R_1k = {r_1k}")
                        
                        excitation_1k = float(lakeshore.ReadExcitationPower(channel_1k))
                        print(f"  Excitation_1k = {excitation_1k}")
                        
                    except Exception as e:
                        print(f"ERROR reading 1K pot: {e}")
                        traceback.print_exc()
                        continue
                    
                    # Read Mixing Chamber data
                    try:
                        print("Reading Mixing Chamber (channel 4)...")
                        t_mc = float(lakeshore.ReadMCTemperature())
                        print(f"  T_mc = {t_mc}")
                        
                        r_mc = float(lakeshore.ReadResistance(channel_mc))
                        print(f"  R_mc = {r_mc}")
                        
                        excitation_mc = float(lakeshore.ReadExcitationPower(channel_mc))
                        print(f"  Excitation_mc = {excitation_mc}")
                        
                    except Exception as e:
                        print(f"ERROR reading Mixing Chamber: {e}")
                        traceback.print_exc()
                        continue
                    
                    # Format data line
                    data_line = (
                        f"{timestamp:.3f}\t"
                        f"{t_1k:.6f}\t{r_1k:.3f}\t{excitation_1k:.3e}\t"
                        f"{t_mc:.6f}\t{r_mc:.3f}\t{excitation_mc:.3e}\n"
                    )
                    
                    # Write to file
                    print("Writing to file...")
                    datafile.write(data_line)
                    datafile.flush()  # Ensure data is written immediately
                    print("Data written successfully")
                    
                    # Print to console
                    print(f"\nCurrent readings: T_1k: {t_1k:.6f} K | T_mc: {t_mc:.6f} K")
                    
                    # Wait for next sample
                    print(f"Waiting {sample_interval} seconds...\n")
                    time.sleep(sample_interval)
                    
            except KeyboardInterrupt:
                print("\n\nData logging stopped by user")
                print(f"Data saved to: {filename}")
                
            except Exception as e:
                print(f"\n\nUNEXPECTED ERROR: {e}")
                traceback.print_exc()
                print(f"Data saved to: {filename}")

if __name__ == "__main__":
    main()

