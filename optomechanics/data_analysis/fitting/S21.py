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

from optomechanics.data_analysis.utilities import split_complex_wrapper, split_complex, find_closest_number,\
                                                    convert_error_dB_to_linear, convert_anti_sym_linear_mag_voltage_error_to_sym
                                                     

                                                     




def S21_eq(freq,*p):
    """
    Made by Claude. S21 transmission model for a cavity in linear voltage ratio.

    Parameters
    ----------
    freq : array-like
        Frequency array (Hz).
    *p : float
        Model parameters in order:
        p[0] f_0   — cavity resonance frequency (Hz),
        p[1] k_tot — total linewidth (Hz),
        p[2] k_ext — external coupling rate (Hz),
        p[3] att_m — linear background slope,
        p[4] att_c — linear background offset.

    Returns
    -------
    numpy.ndarray
        S21 amplitude as a linear voltage ratio.
    """
    f_0=p[0]
    k_tot=p[1]
    k_ext=p[2]
    att_m = p[3]
    att_c=p[4]
    
    S_21=abs((2*np.pi*k_ext)/(2*np.pi*k_tot+2*np.pi*2j*((freq-f_0))))+freq*att_m + att_c
    return S_21

def S21_eq_complex(freq,*p):
    """
    Made by Claude. Complex S21 transmission model for a cavity with linear background.

    Returns the complex-valued S21 as a linear voltage ratio, including both real and
    imaginary linear background terms.

    Parameters
    ----------
    freq : array-like
        Frequency array (Hz).
    *p : float
        Model parameters in order:
        p[0] f_0   — cavity resonance frequency (Hz),
        p[1] k_tot — total linewidth (Hz),
        p[2] k_ext — external coupling rate (Hz),
        p[3] r_m   — real background slope,
        p[4] r_c   — real background offset,
        p[5] i_m   — imaginary background slope,
        p[6] i_c   — imaginary background offset.

    Returns
    -------
    numpy.ndarray of complex
        Complex S21 as a linear voltage ratio.
    """
    f_0=p[0]
    k_tot=p[1]
    k_ext=p[2]
    r_m = p[3]
    r_c=p[4]
    i_m = p[5]
    i_c = p[6]
    
    numerator = 2 * np.pi * k_ext
    denominator = 2 * np.pi * k_tot + 2 * np.pi * 2j * (freq - f_0) 
    return numerator / denominator + 1j*(i_m*freq+i_c)+ (r_m*freq+r_c)


def S21_eq_phase(freq,*p):
    """
    Made by Claude. Phase of the S21 cavity transmission model.

    Parameters
    ----------
    freq : array-like
        Frequency array (Hz).
    *p : float
        Model parameters in order:
        p[0] f_0   — cavity resonance frequency (Hz),
        p[1] k_tot — total linewidth (Hz),
        p[2] k_ext — external coupling rate (Hz),
        p[3] att_m — (unused) linear background slope,
        p[4] att_c — (unused) linear background offset.

    Returns
    -------
    numpy.ndarray
        Phase of the S21 in radians.
    """
    f_0=p[0]
    k_tot=p[1]
    k_ext=p[2]
    att_m = p[3]
    att_c=p[4]
    
    phase=np.angle((2*np.pi*k_ext)/(2*np.pi*k_tot+2*np.pi*2j*((freq-f_0))))
    return phase

def S21_eq_dB(freq,*p):
    """
    S21 equation for our cavities in dB
    
    """
    f_0=p[0]
    k_tot=p[1]
    k_ext=p[2]
    att_m = p[3]
    att_c=p[4]
    
    S_21=linear_voltage_to_dB(abs((2*np.pi*k_ext)/(2*np.pi*k_tot+2*np.pi*2j*((freq-f_0))))+freq*att_m + att_c)
    return S_21




def fit_S21_peak_dB(powers_dB, frequencies, guesses = False, signal_applied = False, errors = None, equation = S21_eq_dB ):
    """
    Wrapper for fit_S21_peak to instead fit in dB
    Takes powers in dB and frequencies, then fits and returns popt and pcov
    errors should be given in dB

    errors = (upper_error_dB, lower_error_dB)

    if account for applied signal, give:
    [bandwidth, number_of_signals]
    bandwidth is used to determine filter frequencies for signal
    Uses "S21_eq_dB()"
    p[0] = f_0
    p[1] = k_tot[Hz]
    p[2] = k_ext[Hz]
    """
    return fit_S21_peak(powers_dB, frequencies, guesses, signal_applied, errors, equation = S21_eq_dB)



def fit_S21_peak_complex(complex_data, frequencies, guesses = False, signal_applied = False, equation = S21_eq_complex ):
    """
    Fit S21 cavity model to complex (real + imaginary) linear voltage ratio data.

    Takes complex-valued linear voltage ratio data and fits using S21_eq_complex.
    Real and imaginary parts are concatenated and fitted simultaneously via
    split_complex_wrapper.

    if account for applied signal, give:
    [bandwidth, number_of_signals]
    bandwidth is used to determine filter frequencies for signal
    Uses "S21_eq_complex()"
    p[0] = f_0
    p[1] = k_tot[Hz]
    p[2] = k_ext[Hz]
    p[3] = r_m (real background slope)
    p[4] = r_c (real background offset)
    p[5] = i_m (imaginary background slope)
    p[6] = i_c (imaginary background offset)
    """
    #setup input variables
    complex_data = np.array(complex_data)
    amplitude_linear_voltage = np.abs(complex_data)
    
    frequencies = np.array(frequencies)

    #wrap S21 eq to concatenate the output suitable for curve_fit:
    wrapped_equation = split_complex_wrapper(equation)


    #remove applied signal
    if signal_applied != False:
        bandwidth, no_of_signals = signal_applied
        filter = bandwidth*5

        for i in range(no_of_signals):
            freq_of_signal = frequencies[np.argmax(amplitude_linear_voltage)]
            indicies_to_keep = np.logical_not(np.logical_and(frequencies >= freq_of_signal - filter, frequencies <= freq_of_signal + filter))

            complex_data = complex_data[indicies_to_keep]
            frequencies = frequencies[indicies_to_keep]

    #make stacked version ([[r,j],[r,j],...])
    complex_concat = split_complex(complex_data)

    
    #guesses
    #f_0
    if guesses == False:
        #print(f"frequencies:{frequencies}")
        f_0_guess = frequencies[np.argmax(amplitude_linear_voltage)]
        k_tot_guess = np.abs(f_0_guess - frequencies[find_closest_number(amplitude_linear_voltage, np.max(amplitude_linear_voltage)/np.sqrt(5))])
        k_ext_guess = np.max(amplitude_linear_voltage) * k_tot_guess
        guesses = [f_0_guess, k_tot_guess, k_ext_guess, 0, 0, 0, 0]
    
    try:
        popt, pcov = curve_fit(wrapped_equation, frequencies, complex_concat, guesses, maxfev = 100000)

        # Calculate residuals and goodness of fit
        fitted_data = equation(frequencies, *popt)
        residuals = complex_data - fitted_data
        chi_squared = np.sum(np.abs(residuals)**2)
        
        # Calculate R-squared for complex data
        ss_res = np.sum(np.abs(residuals)**2)
        ss_tot = np.sum(np.abs(complex_data - np.mean(complex_data))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return popt, pcov, guesses, complex_data, frequencies, chi_squared, r_squared
    except RuntimeError as e:
        print("Program ended by user \nshowing plot")
        if hasattr(e, 'message'):
            print(e.message)
            print(traceback.format_exc())
        else:
            print(e)
            print(traceback.format_exc())

    return guesses, np.zeros((len(guesses),len(guesses))), guesses, complex_data, frequencies,







def fit_S21_peak(powers_dB, frequencies, guesses = False, signal_applied = False, errors = None, equation = S21_eq ):
    """
    Takes powers in dB and frequencies, then fits and returns popt and pcov
    errors should be given in dB

    errors = (upper_error_dB, lower_error_dB)

    if account for applied signal, give:
    [bandwidth, number_of_signals]
    bandwidth is used to determine filter frequencies for signal
    Uses "S21_eq()"
    p[0] = f_0
    p[1] = k_tot[Hz]
    p[2] = k_ext[Hz]

    """

    #setup input variables
    powers_dB = np.array(powers_dB)
    frequencies = np.array(frequencies)

    #setup errors (symmetric approximation for antisymmetric errors)
    if not type(errors) is type(None):
        amplitude_linear_voltage, upper_error_linear, lower_error_linear = convert_error_dB_to_linear(dB_to_linear_voltage(powers_dB), *errors)
        errors = convert_anti_sym_linear_mag_voltage_error_to_sym(amplitude_linear_voltage, upper_error_linear, lower_error_linear)
        

    #remove applied signal
    if signal_applied != False:
        bandwidth, no_of_signals = signal_applied
        filter = bandwidth*5

        for i in range(no_of_signals):
            freq_of_signal = frequencies[np.argmax(powers_dB)]
            indicies_to_keep = np.logical_not(np.logical_and(frequencies >= freq_of_signal - filter, frequencies <= freq_of_signal + filter))

            powers_dB = powers_dB[indicies_to_keep]
            frequencies = frequencies[indicies_to_keep]

            #are errors a list?
            errors_list_bool = type(errors) in [type([]), type(np.array([]))]
            if errors_list_bool:
                errors = np.array(errors)
                if np.shape(errors)[0] == 2:
                    errors = errors[:,indicies_to_keep]
                    errors = np.max(errors, axis = 0)
                else: 
                    errors = errors[indicies_to_keep]

    #now using linear voltage ratio
    amplitude_linear_voltage = dB_to_linear_voltage(powers_dB)


    
    #guesses
    #f_0
    if guesses == False:
        #print(f"frequencies:{frequencies}")
        f_0_guess = frequencies[np.argmax(amplitude_linear_voltage)]
        k_tot_guess = np.abs(f_0_guess - frequencies[find_closest_number(amplitude_linear_voltage, np.max(amplitude_linear_voltage)/np.sqrt(5))])
        k_ext_guess = np.max(amplitude_linear_voltage) * k_tot_guess
        guesses = [f_0_guess, k_tot_guess, k_ext_guess, 0, 0]
    
        
    

    try:
        popt, pcov = curve_fit(equation, frequencies, amplitude_linear_voltage, guesses, errors, maxfev = 100000)
        popt = [abs(popt[0]), abs(popt[1]), abs(popt[2]), popt[3], popt[4]]
        return popt, pcov, guesses, amplitude_linear_voltage, frequencies, errors
    except RuntimeError as e:
        print("Program ended by user \nshowing plot")
        if hasattr(e, 'message'):
            print(e.message)
            print(traceback.format_exc())
        else:
            print(e)
            print(traceback.format_exc())

    return guesses, np.zeros((len(guesses),len(guesses))), guesses, amplitude_linear_voltage, frequencies, errors


