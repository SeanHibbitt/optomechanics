
import numpy as np
import os

#loading temperature data



def temp_reader(temp_day_paths):

    """
    accepts a list of paths to months to read data from
    """

    Temperature = []
    Time = []
    Set_voltage = []
    for temp_day_path in temp_day_paths:
        with os.scandir(temp_day_path) as day_paths:
            for day_path in day_paths:
                print(day_path)
                with os.scandir(day_path) as file_paths:
                    for path in file_paths:
                        print(path)
                        temp_data = np.genfromtxt(path, delimiter = ',', skip_header = 1 ).T[0:3].tolist()
                        Time = Time + temp_data[0]
                        Temperature = Temperature + temp_data[1]
                        Set_voltage = Set_voltage + temp_data[2]

    print(len(Temperature))
    print(len(Set_voltage))
    Temperature = np.array(Temperature)
    Time = np.array(Time)
    Set_voltage = np.array(Set_voltage)

    #sort temperature base on time
    indicies = np.argsort(Time)
    Time = Time[indicies]
    Temperature = Temperature[indicies]
    Set_voltage = Set_voltage[indicies]

    return Time, Temperature, Set_voltage

    #how to sort:
    #np.nanargsort()
    #this gives you the indicies which result in a sorted array, eg:
    #a = [0,4,3,6]
    #indicies = np.nanargsort(a) -> [0,2,1,3]
    #a[indicies] -> [0,3,4,6]
