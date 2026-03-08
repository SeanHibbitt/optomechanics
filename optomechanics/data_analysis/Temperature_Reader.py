"""
Made by Claude. Temperature data loading and parsing for optomechanics experiments.

Reads temperature log files from cryogenic measurement setups and provides
utilities for aligning temperature data with mechanical PSD time series.
"""
import numpy as np
import os

#loading temperature data



def temp_reader(temp_day_paths):

    """
    Made by Claude. Read and concatenate temperature log files from a directory tree.

    Walks a two-level directory hierarchy (month → day → files) rooted at
    each path in ``temp_day_paths``, reads all CSV files using
    ``numpy.genfromtxt``, concatenates the time, temperature, and set-voltage
    columns, and returns them sorted by time.

    Parameters
    ----------
    temp_day_paths : list of str
        Paths to monthly directories.  Each directory is expected to contain
        day subdirectories, which in turn contain comma-delimited CSV files
        with a one-row header and columns ``[time, temperature, set_voltage, ...]``.

    Returns
    -------
    Time : numpy.ndarray
        Concatenated and time-sorted time stamps (first column of each CSV).
    Temperature : numpy.ndarray
        Concatenated and time-sorted temperature values (second column).
    Set_voltage : numpy.ndarray
        Concatenated and time-sorted set-voltage values (third column).
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
