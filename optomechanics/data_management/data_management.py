"""
Made by Claude. Data I/O and attenuation management for optomechanics experiments.

Provides file reading/writing utilities, the attenuation_object class for
managing microwave attenuation chains, and save_data_3 for structured data export.
"""
import numpy as np
import pandas
from optomechanics.data_analysis.unit_conversions import *

def read_file(file_loc, sep = r"\s+" ):
    """
    Made by Claude. Read a delimited data file into a DataFrame and parse its metadata.

    Wraps ``pandas.read_csv``, skipping lines starting with ``#``, and also
    returns the metadata parsed from those comment lines via `read_meta_data`.
    A specific separator (e.g. ``sep=r"\\t"``) is faster than the default
    whitespace regexp.

    Parameters
    ----------
    file_loc : str or path-like
        Path to the data file (any format accepted by ``pandas.read_csv``).
    sep : str, optional
        Column separator regexp. Default is ``r"\\s+"`` (any whitespace).

    Returns
    -------
    data_pandas : pandas.DataFrame
        Data rows parsed from the file (comment lines excluded).
    meta_data : dict
        Key-value pairs read from comment lines (format ``#\\tkey\\tvalue``).
    """
    data_pandas = pandas.read_csv(file_loc, sep = sep, comment = "#", index_col = False)
    meta_data = read_meta_data(file_loc)

    return data_pandas, meta_data
    
def read_meta_data(file_loc):
    """
    Made by Claude. Parse key-value metadata from comment lines in a data file.

    Reads the file line by line until a non-comment, non-blank line is
    encountered.  Comment lines must have the format ``#\\tkey\\tvalue``.

    Parameters
    ----------
    file_loc : str or path-like
        Path to the data file.

    Returns
    -------
    dict
        Dictionary of ``{key: value}`` pairs extracted from comment lines.
    """
    meta_data = {}
    with open(file_loc, "r") as file:
        for line in file:
            if line == "\n": continue
            if '#' not in line: break
            line = line.split("\t")
            meta_data[line[1]] = line[2].replace("\n","")

    return meta_data 


# def save_data_3(data, file_name, file_location = "", headers = None, meta_data = {}, delimiter = "\t"):
#         data = np.array(data)
#         data_shape = np.shape(data)
#         #print(data_shape)
#         with open(file_location+file_name, "w") as file1:
#             for key, value in meta_data.items():
#                 file1.write(f"#\t{key}\t{value}\n")
#             if headers != None:
#                 file1.write(headers+"\n")
            
#             for  i in range(data_shape[1]):
#                 for l in range(data_shape[0]):
#                     file1.write(f"{data[l,i]}\t")
#                 file1.write("\n")


def save_data_3(data, file_name, file_location = "", headers = None, meta_data = {}, delimiter = "\t"):
    """
    Made by Claude. Save an array to a delimited text file with key-value metadata lines.

    Writes metadata as ``#\\tkey\\tvalue`` comment lines, then an optional
    header line, then the data.  For 2-D arrays the output is column-major;
    for 1-D arrays each element is written on its own line.

    Parameters
    ----------
    data : array-like
        Data to save (1-D or 2-D).  For 2-D arrays, shape should be
        ``(n_channels, n_points)``.
    file_name : str
        Output filename (including extension).
    file_location : str, optional
        Directory path for the output file. Default is ``""`` (current
        directory).
    headers : str or None, optional
        Column header line. Default is None.
    meta_data : dict, optional
        Dictionary of metadata key-value pairs written as comment lines.
        Default is ``{}``.
    delimiter : str, optional
        Field delimiter. Default is ``'\\t'`` (tab).
    """
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



class attenuation_object:
    """
    Made by Claude. Frequency-dependent attenuation with optional asymmetric errors.

    Stores a magnitude array (in dB) and a corresponding frequency array.
    Arithmetic operations (``+`` and ``-``) interpolate the second operand
    onto the frequencies of the first, then combine magnitudes and propagate
    errors in quadrature.

    .. warning::
        Addition and subtraction are **not** commutative: the first operand
        determines the output frequency grid.

    Parameters
    ----------
    magnitude : array-like
        Attenuation magnitudes (dB).
    frequencies : array-like
        Frequency values corresponding to each element of `magnitude` (Hz).
    upper_error : array-like or None, optional
        Upper error magnitudes (dB). Default is None (zeros used).
    lower_error : array-like or None, optional
        Lower error magnitudes (dB). Default is None (zeros used).

    Attributes
    ----------
    magnitude : numpy.ndarray
        Attenuation magnitudes (dB).
    frequencies : numpy.ndarray
        Frequency array (Hz).
    upper_error : numpy.ndarray
        Upper error magnitudes (dB).
    lower_error : numpy.ndarray
        Lower error magnitudes (dB).
    has_error : bool
        ``True`` if error arrays were provided; ``False`` otherwise.
    freq_len : float
        Frequency span (|last − first|) in Hz, or 1 if a single frequency.
    """

    def __init__(self, magnitude, frequencies, upper_error = None, lower_error = None ):
        """
        Made by Claude. Initialise the attenuation object and validate error arrays.

        Prints a warning if no errors are provided or if any error values are NaN.
        """
        self.magnitude = np.array(magnitude)
        self.frequencies = np.array(frequencies)

        if type(upper_error) is type(None):
            print("warning no errors")
            self.upper_error = np.zeros_like(self.magnitude)
            self.lower_error = self.upper_error
            self.has_error = False
        else:
            self.has_error = True
            self.upper_error = np.array(upper_error)
            self.lower_error = np.array(lower_error)    
        
        if np.any([self.upper_error, self.lower_error] == np.nan):
            print("warning np.nan in errors")


        if self.frequencies.size != 1: 
            self.freq_len = np.abs(self.frequencies[-1] - self.frequencies[0])
        else: self.freq_len = 1

    def load_from_tsv( file_location):
        """
        Made by Claude. Load an attenuation_object from a TSV file.

        The file must have the following tab-separated columns (with optional
        ``#``-prefixed metadata lines): ``Frequency[Hz]``, ``attenuation[dB]``,
        ``atten_upper_std[dB]``, ``atten_lower_std[dB]``.

        Parameters
        ----------
        file_location : str or path-like
            Path to the TSV file.

        Returns
        -------
        attenuation_object
            New instance loaded from the file.
        """

        data_pandas_temp, meta_data_temp = read_file(file_location)
        return attenuation_object(data_pandas_temp["attenuation[dB]"],data_pandas_temp["Frequency[Hz]"], data_pandas_temp["atten_upper_std[dB]"], data_pandas_temp["atten_lower_std[dB]"])

    def save_to_tsv():
        """
        Made by Claude. Save the attenuation_object to a TSV file.

        Raises
        ------
        Exception
            Always raised — method is not yet implemented.
        """
        raise Exception("not finished")
        pass

    def __add__(self, second_atten):
        """
        Made by Claude. Add two attenuation objects, propagating errors in quadrature.

        Interpolates `second_atten` onto ``self.frequencies``, adds the
        magnitudes, and propagates errors in quadrature.  Addition is **not**
        commutative: ``self`` determines the output frequency grid.

        Parameters
        ----------
        second_atten : attenuation_object
            Attenuation to add.

        Returns
        -------
        attenuation_object
            New instance with the combined magnitude and propagated errors.
        """
        interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
        result_mag = self.magnitude + interpolated_mag
        result_freqs = self.frequencies


        #error handling:
        if (self.has_error == False) and (second_atten.has_error == False):
            return attenuation_object(result_mag, result_freqs, None, None)

        if self.has_error == False:
            upper_error = np.zeros_like(interpolated_mag)
            lower_error = np.zeros_like(interpolated_mag)
        else:
            upper_error = self.upper_error
            lower_error = self.lower_error

        if second_atten.has_error == False:
            their_upper_error = np.zeros_like(interpolated_mag)
            their_lower_error = np.zeros_like(interpolated_mag)
        else:
            their_upper_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude + second_atten.upper_error) - interpolated_mag
            their_lower_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude - second_atten.lower_error) - interpolated_mag

        result_upper_error = np.sqrt(upper_error**2 + their_upper_error**2)
        result_lower_error = np.sqrt(lower_error**2 + their_lower_error**2)

        return attenuation_object(result_mag, result_freqs, result_upper_error, result_lower_error)
    
    def __sub__(self, second_atten):
        """
        Made by Claude. Subtract an attenuation object, propagating errors in quadrature.

        Interpolates `second_atten` onto ``self.frequencies``, subtracts the
        magnitudes, and propagates errors in quadrature.  Subtraction is **not**
        commutative: ``self`` determines the output frequency grid.

        Parameters
        ----------
        second_atten : attenuation_object
            Attenuation to subtract.

        Returns
        -------
        attenuation_object
            New instance with the result magnitude and propagated errors.
        """
        interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
        result_mag = self.magnitude - interpolated_mag
        result_freqs = self.frequencies


        #error handling:
        if (self.has_error == False) and (second_atten.has_error == False):
            return attenuation_object(result_mag, result_freqs, None, None)

        if self.has_error == False:
            upper_error = np.zeros_like(interpolated_mag)
            lower_error = np.zeros_like(interpolated_mag)
        else:
            upper_error = self.upper_error
            lower_error = self.lower_error

        if second_atten.has_error == False:
            their_upper_error = np.zeros_like(interpolated_mag)
            their_lower_error = np.zeros_like(interpolated_mag)
        else:
            their_upper_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude + second_atten.upper_error) - interpolated_mag
            their_lower_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude - second_atten.lower_error) - interpolated_mag

        result_upper_error = np.sqrt(upper_error**2 + their_upper_error**2)
        result_lower_error = np.sqrt(lower_error**2 + their_lower_error**2)

        return attenuation_object(result_mag, result_freqs, result_upper_error, result_lower_error)


    # def __add__(self, second_atten):

    #     interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
    #     result_mag = self.magnitude + interpolated_mag
    #     result_freqs = self.frequencies
    #     result_mag_linear = dB_to_linear_voltage(result_mag)

    #     #error handling:
    #     if self.has_error == False:
    #         self.upper_error_linear = np.zeros_like(interpolated_mag)
    #         self.lower_error_linear = np.zeros_like(interpolated_mag)
    #         self.mag_linear = dB_to_linear_voltage(self.magnitude)

    #     else:
    #         this_upper_error_dB = self.upper_error
    #         this_lower_error_dB = self.lower_error
    #         self.mag_linear, self.upper_error_linear, self.lower_error_linear = convert_error_dB_to_linear(self.magnitude, this_upper_error_dB, this_lower_error_dB)

    #     if second_atten.has_error == False:
    #         second_atten.upper_error_linear = np.zeros_like(interpolated_mag)
    #         second_atten.lower_error_linear = np.zeros_like(interpolated_mag)
    #         second_atten.mag_linear = dB_to_linear_voltage(second_atten.magnitude)
            
    #     else:
    #         their_upper_error_dB = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude + second_atten.upper_error) - second_atten.magnitude
    #         their_lower_error_dB = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude - second_atten.lower_error) - second_atten.magnitude
    #         second_atten.mag_linear, second_atten.upper_error_linear, second_atten.lower_error_linear = convert_error_dB_to_linear(second_atten.magnitude, their_upper_error_dB, their_lower_error_dB)

    #     linear_total_error_upper = result_mag_linear * np.sqrt( (self.upper_error_linear/self.mag_linear)**2 + (second_atten.upper_error_linear/second_atten.mag_linear)**2 )
    #     linear_total_error_lower = result_mag_linear * np.sqrt( (self.lower_error_linear/self.mag_linear)**2 + (second_atten.lower_error_linear/second_atten.mag_linear)**2 )
        
        

    #     result_mag_2, upper_error_dB, lower_error_dB = convert_error_linear_to_dB(result_mag_linear, linear_total_error_upper, linear_total_error_lower)
        
    #     if np.any(np.isnan(upper_error_dB)) or np.any(np.isnan(lower_error_dB)):
    #         print(f"nans found in error\n{linear_total_error_upper.tolist()=}\n----\n{linear_total_error_lower.tolist()=}\n-----\n {upper_error_dB.tolist()=} \n-----\n{lower_error_dB.tolist()=}\n=======\n\n ")

    #     if np.all(result_mag_2 != result_mag):
    #         raise Exception("convert_error_linear_to_dB gave different answer to expected answer")


    #     return attenuation_object(result_mag, result_freqs, upper_error_dB, lower_error_dB)
    
    # def __sub__(self, second_atten):

    #     second_atten.magnitude = -1*second_atten.magnitude

    #     return self.__add__( second_atten)

    
        

    # def __add__(self, second_atten):
    #     if self.freq_len < second_atten.freq_len:
    #         interpolated_mag = np.interp(second_atten.frequencies, self.frequencies, self.magnitude)
    #         result_mag = interpolated_mag + second_atten.magnitude
    #         result_freqs = second_atten.frequencies

    #         interpolated_upper_error = np.interp(second_atten.frequencies, self.frequencies, self.upper_error)
    #         interpolated_lower_error = np.interp(second_atten.frequencies, self.frequencies, self.lower_error)

    #         result_upper_error = interpolated_upper_error + second_atten.upper_error
    #         result_lower_error = interpolated_lower_error + second_atten.lower_error

    #     else: 
    #         interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
    #         result_mag = interpolated_mag + self.magnitude
    #         result_freqs = self.frequencies

    #         interpolated_upper_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.upper_error)
    #         interpolated_lower_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.lower_error)

    #         result_upper_error = interpolated_upper_error + self.upper_error
    #         result_lower_error = interpolated_lower_error + self.lower_error

    #     return attenuation_object(result_mag, result_freqs, result_upper_error, result_lower_error)
    
    # def __sub__(self, second_atten):
    #     if self.freq_len < second_atten.freq_len:
    #         interpolated_mag = np.interp(second_atten.frequencies, self.frequencies, self.magnitude)
    #         result_mag = interpolated_mag - second_atten.magnitude
    #         result_freqs = second_atten.frequencies

    #         interpolated_upper_error = np.interp(second_atten.frequencies, self.frequencies, self.upper_error)
    #         interpolated_lower_error = np.interp(second_atten.frequencies, self.frequencies, self.lower_error)

    #         result_upper_error = interpolated_upper_error + second_atten.upper_error
    #         result_lower_error = interpolated_lower_error + second_atten.lower_error

    #     else: 
    #         interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
    #         result_mag = - interpolated_mag + self.magnitude
    #         result_freqs = self.frequencies

    #         interpolated_upper_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.upper_error)
    #         interpolated_lower_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.lower_error)

    #         result_upper_error = interpolated_upper_error + self.upper_error
    #         result_lower_error = interpolated_lower_error + self.lower_error

    #     return attenuation_object(result_mag, result_freqs, result_upper_error, result_lower_error)

    
    def __call__(self, *args, **kwds):
        """
        Made by Claude. Return the magnitude and frequency arrays.

        Returns
        -------
        magnitude : numpy.ndarray
            Attenuation magnitudes (dB).
        frequencies : numpy.ndarray
            Frequency array (Hz).
        """
        return self.magnitude, self.frequencies

# class attenuation_object:

#     """
#     warning, built in addition and subtraction is not commutable.
#     The first object is primary and everything else is interpolated to those frequencies 
#     """

#     def __init__(self, magnitude, frequencies, upper_error = None, lower_error = None ):
#         self.magnitude = np.array(magnitude)
#         self.frequencies = np.array(frequencies)

#         if type(upper_error) is type(None):
#             print("warning no errors")
#             self.upper_error = np.zeros_like(self.magnitude)
#             self.lower_error = self.upper_error
#             self.has_error = False
#         else:
#             self.has_error = True
#             self.upper_error = np.array(upper_error)
#             self.lower_error = np.array(lower_error)    
        
#         if np.any([self.upper_error, self.lower_error] == np.nan):
#             print("warning np.nan in errors")


#         if self.frequencies.size != 1: 
#             self.freq_len = np.abs(self.frequencies[-1] - self.frequencies[0])
#         else: self.freq_len = 1

#     def load_from_tsv( file_location):
#         """Frequency[Hz]\tattenuation[dB]\tatten_upper_std[dB]\tatten_lower_std[dB]"""

#         data_pandas_temp, meta_data_temp = read_file(file_location)
#         return attenuation_object(data_pandas_temp["attenuation[dB]"],data_pandas_temp["Frequency[Hz]"], data_pandas_temp["atten_upper_std[dB]"], data_pandas_temp["atten_lower_std[dB]"])

#     def save_to_tsv():
#         raise Exception("not finished")
#         pass

#     def __add__(self, second_atten):

#         interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
#         result_mag = self.magnitude + interpolated_mag
#         result_freqs = self.frequencies


#         #error handling:
#         if (self.has_error == False) and (second_atten.has_error == False):
#             return attenuation_object(result_mag, result_freqs, None, None)

#         if self.has_error == False:
#             upper_error = np.zeros_like(interpolated_mag)
#             lower_error = np.zeros_like(interpolated_mag)
#         else:
#             upper_error = self.upper_error
#             lower_error = self.lower_error

#         if second_atten.has_error == False:
#             their_upper_error = np.zeros_like(interpolated_mag)
#             their_lower_error = np.zeros_like(interpolated_mag)
#         else:
#             their_upper_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude + second_atten.upper_error) - interpolated_mag
#             their_lower_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude - second_atten.lower_error) - interpolated_mag

#         result_upper_error = np.sqrt(upper_error**2 + their_upper_error**2)
#         result_lower_error = np.sqrt(lower_error**2 + their_lower_error**2)

#         return attenuation_object(result_mag, result_freqs, result_upper_error, result_lower_error)
    
#     def __sub__(self, second_atten):

#         interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
#         result_mag = self.magnitude - interpolated_mag
#         result_freqs = self.frequencies


#         #error handling:
#         if (self.has_error == False) and (second_atten.has_error == False):
#             return attenuation_object(result_mag, result_freqs, None, None)

#         if self.has_error == False:
#             upper_error = np.zeros_like(interpolated_mag)
#             lower_error = np.zeros_like(interpolated_mag)
#         else:
#             upper_error = self.upper_error
#             lower_error = self.lower_error

#         if second_atten.has_error == False:
#             their_upper_error = np.zeros_like(interpolated_mag)
#             their_lower_error = np.zeros_like(interpolated_mag)
#         else:
#             their_upper_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude + second_atten.upper_error) - interpolated_mag
#             their_lower_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude - second_atten.lower_error) - interpolated_mag

#         result_upper_error = np.sqrt(upper_error**2 + their_upper_error**2)
#         result_lower_error = np.sqrt(lower_error**2 + their_lower_error**2)

#         return attenuation_object(result_mag, result_freqs, result_upper_error, result_lower_error)


#     # def __add__(self, second_atten):

#     #     interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
#     #     result_mag = self.magnitude + interpolated_mag
#     #     result_freqs = self.frequencies
#     #     result_mag_linear = dB_to_linear_voltage(result_mag)

#     #     #error handling:
#     #     if self.has_error == False:
#     #         self.upper_error_linear = np.zeros_like(interpolated_mag)
#     #         self.lower_error_linear = np.zeros_like(interpolated_mag)
#     #         self.mag_linear = dB_to_linear_voltage(self.magnitude)

#     #     else:
#     #         this_upper_error_dB = self.upper_error
#     #         this_lower_error_dB = self.lower_error
#     #         self.mag_linear, self.upper_error_linear, self.lower_error_linear = convert_error_dB_to_linear(self.magnitude, this_upper_error_dB, this_lower_error_dB)

#     #     if second_atten.has_error == False:
#     #         second_atten.upper_error_linear = np.zeros_like(interpolated_mag)
#     #         second_atten.lower_error_linear = np.zeros_like(interpolated_mag)
#     #         second_atten.mag_linear = dB_to_linear_voltage(second_atten.magnitude)
            
#     #     else:
#     #         their_upper_error_dB = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude + second_atten.upper_error) - second_atten.magnitude
#     #         their_lower_error_dB = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude - second_atten.lower_error) - second_atten.magnitude
#     #         second_atten.mag_linear, second_atten.upper_error_linear, second_atten.lower_error_linear = convert_error_dB_to_linear(second_atten.magnitude, their_upper_error_dB, their_lower_error_dB)

#     #     linear_total_error_upper = result_mag_linear * np.sqrt( (self.upper_error_linear/self.mag_linear)**2 + (second_atten.upper_error_linear/second_atten.mag_linear)**2 )
#     #     linear_total_error_lower = result_mag_linear * np.sqrt( (self.lower_error_linear/self.mag_linear)**2 + (second_atten.lower_error_linear/second_atten.mag_linear)**2 )
        
        

#     #     result_mag_2, upper_error_dB, lower_error_dB = convert_error_linear_to_dB(result_mag_linear, linear_total_error_upper, linear_total_error_lower)
        
#     #     if np.any(np.isnan(upper_error_dB)) or np.any(np.isnan(lower_error_dB)):
#     #         print(f"nans found in error\n{linear_total_error_upper.tolist()=}\n----\n{linear_total_error_lower.tolist()=}\n-----\n {upper_error_dB.tolist()=} \n-----\n{lower_error_dB.tolist()=}\n=======\n\n ")

#     #     if np.all(result_mag_2 != result_mag):
#     #         raise Exception("convert_error_linear_to_dB gave different answer to expected answer")


#     #     return attenuation_object(result_mag, result_freqs, upper_error_dB, lower_error_dB)
    
#     # def __sub__(self, second_atten):

#     #     second_atten.magnitude = -1*second_atten.magnitude

#     #     return self.__add__( second_atten)

    
        

#     # def __add__(self, second_atten):
#     #     if self.freq_len < second_atten.freq_len:
#     #         interpolated_mag = np.interp(second_atten.frequencies, self.frequencies, self.magnitude)
#     #         result_mag = interpolated_mag + second_atten.magnitude
#     #         result_freqs = second_atten.frequencies

#     #         interpolated_upper_error = np.interp(second_atten.frequencies, self.frequencies, self.upper_error)
#     #         interpolated_lower_error = np.interp(second_atten.frequencies, self.frequencies, self.lower_error)

#     #         result_upper_error = interpolated_upper_error + second_atten.upper_error
#     #         result_lower_error = interpolated_lower_error + second_atten.lower_error

#     #     else: 
#     #         interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
#     #         result_mag = interpolated_mag + self.magnitude
#     #         result_freqs = self.frequencies

#     #         interpolated_upper_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.upper_error)
#     #         interpolated_lower_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.lower_error)

#     #         result_upper_error = interpolated_upper_error + self.upper_error
#     #         result_lower_error = interpolated_lower_error + self.lower_error

#     #     return attenuation_object(result_mag, result_freqs, result_upper_error, result_lower_error)
    
#     # def __sub__(self, second_atten):
#     #     if self.freq_len < second_atten.freq_len:
#     #         interpolated_mag = np.interp(second_atten.frequencies, self.frequencies, self.magnitude)
#     #         result_mag = interpolated_mag - second_atten.magnitude
#     #         result_freqs = second_atten.frequencies

#     #         interpolated_upper_error = np.interp(second_atten.frequencies, self.frequencies, self.upper_error)
#     #         interpolated_lower_error = np.interp(second_atten.frequencies, self.frequencies, self.lower_error)

#     #         result_upper_error = interpolated_upper_error + second_atten.upper_error
#     #         result_lower_error = interpolated_lower_error + second_atten.lower_error

#     #     else: 
#     #         interpolated_mag = np.interp(self.frequencies, second_atten.frequencies, second_atten.magnitude)
#     #         result_mag = - interpolated_mag + self.magnitude
#     #         result_freqs = self.frequencies

#     #         interpolated_upper_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.upper_error)
#     #         interpolated_lower_error = np.interp(self.frequencies, second_atten.frequencies, second_atten.lower_error)

#     #         result_upper_error = interpolated_upper_error + self.upper_error
#     #         result_lower_error = interpolated_lower_error + self.lower_error

#     #     return attenuation_object(result_mag, result_freqs, result_upper_error, result_lower_error)

    
#     def __call__(self, *args, **kwds):
#         return self.magnitude, self.frequencies
    