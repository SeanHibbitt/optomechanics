import numpy as np
from scipy.optimize import curve_fit
import traceback
import plotly.graph_objects as go
import pandas as pd
from optomechanics.data_management.data_management import attenuation_object
from optomechanics.data_analysis.unit_conversions import watts_ratio_to_dB, dB_to_watts_ratio, dB_to_linear_voltage,\
                                                     linear_voltage_to_dB, Vpp_to_Vrms, Vp_to_Vrms,\
                                                     Vrms_to_Vpp, Vrms_to_Vp, Vrms_to_watts,\
                                                     watts_to_dBw, RMS_to_dBw, RMS_to_dBm,\
                                                     dBw_to_watts, dBm_to_dBw, dBm_to_RMS,\
                                                     watts_to_dBm, dBm_to_watts, Vrms_squared_to_watts
                                                    



def find_closest_number(array, value):
    """
    Made by Claude. Find the index of the closest value in an array.

    Parameters
    ----------
    array : array-like
        Array to search.
    value : float
        Value to find the closest match to.

    Returns
    -------
    int
        Index of the element in `array` closest to `value`.
    """
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx




def convert_error_dB_to_linear(value, upper_error, lower_error,):
    """
    Made by Claude. Convert an asymmetric error from dB to linear voltage ratio scale.

    Errors must be magnitudes (both positive values). The value and errors are
    given in dB.

    Parameters
    ----------
    value : float
        Central value in dB.
    upper_error : float
        Upper error magnitude in dB (positive).
    lower_error : float
        Lower error magnitude in dB (positive).

    Returns
    -------
    value_linear : float
        Central value as a linear voltage ratio.
    upper_error_linear : float
        Upper error as a linear voltage ratio.
    lower_error_linear : float
        Lower error as a linear voltage ratio.
    """

    upper_value = value + upper_error
    lower_value = value - lower_error
    upper_value_linear = dB_to_linear_voltage(upper_value)
    lower_value_linear = dB_to_linear_voltage(lower_value)
    value_linear = dB_to_linear_voltage(value)
    upper_error_linear = upper_value_linear - value_linear
    lower_error_linear = lower_value_linear - value_linear

    return value_linear, upper_error_linear, lower_error_linear

def convert_error_linear_to_dB(value_linear, upper_error, lower_error,):
    """
    Made by Claude. Convert an asymmetric error from linear voltage ratio scale to dB.

    Errors must be magnitudes (not signed). The value and errors are given as
    linear voltage ratios.

    Parameters
    ----------
    value_linear : float
        Central value as a linear voltage ratio.
    upper_error : float
        Upper error magnitude as a linear voltage ratio (positive).
    lower_error : float
        Lower error magnitude as a linear voltage ratio (positive).

    Returns
    -------
    value_dB : float
        Central value in dB.
    upper_error_dB : float
        Upper error in dB.
    lower_error_dB : float
        Lower error in dB (absolute value).
    """

    upper_value_linear = value_linear + upper_error
    lower_value_linear = value_linear - lower_error
    if lower_value_linear < 0:
        lower_value_linear
    upper_value_dB = linear_voltage_to_dB(upper_value_linear)
    lower_value_dB = linear_voltage_to_dB(lower_value_linear)
    value_dB = linear_voltage_to_dB(value_linear)
    upper_error_dB = upper_value_dB - value_dB
    lower_error_dB = np.abs(lower_value_dB - value_dB)

    return value_dB, upper_error_dB, lower_error_dB

def convert_anti_sym_linear_mag_voltage_error_to_sym(value, upper_error, lower_error):
    """
    Made by Claude. Convert asymmetric linear magnitude voltage errors to a symmetric error.

    Computes a single symmetric error by averaging the absolute upper and lower
    error magnitudes. Raises a ValueError if any `value` is non-positive.

    Parameters
    ----------
    value : array-like
        Central values as linear voltage magnitudes (must all be positive).
    upper_error : array-like
        Upper error magnitudes (positive).
    lower_error : array-like
        Lower error magnitudes (positive).

    Returns
    -------
    numpy.ndarray
        Symmetric error array.

    Raises
    ------
    ValueError
        If any element of `value` is zero or negative.
    """
    if np.any(value <=0):
        raise ValueError("negative magnitude value")

    error = np.mean([np.abs(upper_error), np.abs(lower_error)], axis = 0)
    error = value[value - error <0]

    return error


def split_complex(complex_data):
    """
    Made by Claude. Split a complex array into a real concatenation of its real and imaginary parts.

    Parameters
    ----------
    complex_data : array-like of complex
        Input complex data.

    Returns
    -------
    numpy.ndarray
        1-D real array with the real part followed by the imaginary part.
    """
    complex_data = np.asarray(complex_data)
    return np.concatenate([complex_data.real, complex_data.imag])

def split_complex_wrapper(func):
    """
    Made by Claude. Wrap a complex-valued function to return real-concatenated output for scipy optimisation.

    Returns a new function that calls `func` and then concatenates the real
    and imaginary parts of the result into a single real array.  This makes
    complex-valued model functions compatible with ``scipy.optimize`` routines
    that require real-valued residuals.

    Parameters
    ----------
    func : callable
        A function that returns a complex array.

    Returns
    -------
    callable
        Wrapped function with the same signature as `func`, returning a real
        array of twice the length: ``[real_part, imag_part]``.
    """
    def wrapped(*args, **kwargs):
        c = func(*args, **kwargs)
        # Stack real and imaginary parts
        return np.concatenate([c.real, c.imag])
    return wrapped


def complex_to_mag_phase(c: complex):
    """
    changes complex to mag and phase
    
    :param complex: complex
    """

    phase = np.angle(c)
    mag = np.abs(c)
    return mag, phase


