"""
Docstring by Claude. Optomechanically Induced Transparency / Absorption (OMIT/OMIA) fitting functions.

Provides the OMIT/OMIA lineshape equation and fitting routines for extracting
mechanical parameters from cavity transmission under strong pump driving.
The same equation handles both OMIT (transparency peak, ``A > 0``) and
OMIA (absorption dip, ``A < 0``) via the sign of the amplitude parameter.
"""
import numpy as np
from scipy.optimize import curve_fit
import traceback
import plotly.graph_objects as go
import pandas as pd
from optomechanics.data_management import attenuation_object
from optomechanics.data_analysis.unit_conversions import watts_ratio_to_dB, dB_to_watts_ratio, dB_to_linear_voltage,\
                                                     linear_voltage_to_dB, Vpp_to_Vrms, Vp_to_Vrms,\
                                                     Vrms_to_Vpp, Vrms_to_Vp, Vrms_to_watts,\
                                                     watts_to_dBw, RMS_to_dBw, RMS_to_dBm,\
                                                     dBw_to_watts, dBm_to_dBw, dBm_to_RMS,\
                                                     watts_to_dBm, dBm_to_watts, Vrms_squared_to_watts

from optomechanics.data_analysis.fitting._fitting import h_bar, k_b, RS_default_window_NENBW
from optomechanics.data_analysis.utilities import split_complex_wrapper, split_complex, find_closest_number,\
                                                    convert_error_dB_to_linear, convert_anti_sym_linear_mag_voltage_error_to_sym
from optomechanics.data_analysis.fitting.S21 import S21_eq, fit_S21_peak    






def OMIT_equation(f, f_m, g_m, A, floor, kk_tot):

    """
    Docstring by Claude. OMIT/OMIA lineshape equation for optomechanically induced transparency or absorption.

    Computes the OMIT/OMIA transmission amplitude as a function of frequency.
    Positive ``A`` produces a transparency peak (OMIT); negative ``A`` produces
    an absorption dip (OMIA).
    The amplitude parameter ``A`` and background ``floor`` are defined as::

        A     = (k_ext * 4 * omega_m * g_0**2 * n_d)
                / sqrt(k**4 + 4*(w_p - w_c)**2)
        floor = sqrt(k_ext**2
                / sqrt(k**4 + 4*(w_p - w_c)**2))

    Parameters
    ----------
    f : array_like
        Frequency array (Hz).
    f_m : float
        Mechanical resonance frequency (Hz).
    g_m : float
        Mechanical linewidth / damping rate, $\\Gamma_m / 2\\pi$ (Hz).
    A : float
        OMIT/OMIA amplitude (linear voltage units). Positive for
        transparency peak (OMIT), negative for absorption dip (OMIA).
    floor : float
        Background transmission level (linear voltage units).
    kk_tot : float
        Total optical linewidth (Hz).

    Returns
    -------
    OMIT : numpy.ndarray
        OMIT transmission amplitude (linear voltage units) evaluated at each
        frequency in ``f``.
    """

    w = 2*np.pi* f
    w_m = 2*np.pi*f_m
    G_m = 2*np.pi*g_m
    k_tot = 2*np.pi*kk_tot

    denominator = (w_m**2 - (w)**2 - 1j*G_m*w) * (k_tot - 2j*w)

    OMIT =  floor*(1+A *np.abs( 1/ denominator))
    
    return OMIT

def fit_OMIT(rel_freqs, mags_dB, k_tot, floor, guesses = False):

    """
    Made by Claude. Fit the OMIT equation to a measured transmission spectrum.

    Converts the input dB magnitudes to linear voltage, then fits
    :func:`OMIT_equation` using ``scipy.optimize.curve_fit``.  The ``floor``
    parameter is a free fit parameter here (contrast with
    :func:`fit_OMIT_set_floor`).

    Parameters
    ----------
    rel_freqs : array_like
        Frequency array (Hz), typically relative to a carrier.
    mags_dB : array_like
        Measured transmission magnitudes (dB).
    k_tot : float
        Fixed total optical linewidth (Hz) passed to :func:`OMIT_equation`.
    floor : float
        Initial guess for the background transmission level (linear voltage).
    guesses : list or False, optional
        Initial parameter guesses ``[f_m, g_m, A, floor]``.  If ``False``,
        auto-guesses are generated from the data. Default is ``False``.

    Returns
    -------
    popt : numpy.ndarray
        Optimal fit parameters ``[f_m, g_m, A, floor]``.
    pcov : numpy.ndarray
        Covariance matrix of ``popt``.
    amplitude_linear_voltage : numpy.ndarray
        Input magnitudes converted to linear voltage (used for fitting).
    guesses : list
        The parameter guesses actually used by ``curve_fit``.
    """

    


    #organise variables
    amplitude_linear_voltage = dB_to_linear_voltage(mags_dB)

    f_m_guess, g_m_guess, A_guess, floor = guesses

    #guesses:
    if np.any(guesses) == False:
        amplitude_linear_voltage_guess = np.abs(amplitude_linear_voltage)
        max_value = np.max(amplitude_linear_voltage_guess)
        f_m_guess = rel_freqs[np.argmax(amplitude_linear_voltage_guess)]
        g_m_guess = np.abs((f_m_guess - rel_freqs[find_closest_number(amplitude_linear_voltage_guess, max_value/2)]))*2
        floor_guess   = amplitude_linear_voltage[0]
        
        A_guess = np.abs(max_value - floor_guess)
        if np.abs((floor_guess - np.max(amplitude_linear_voltage))) < np.abs((floor_guess - np.min(amplitude_linear_voltage))):
            A_guess = A_guess * -1            
        
        guesses_temp = f_m_guess, g_m_guess, A_guess, floor_guess

        guesses[guesses == False] = guesses_temp[guesses == False]

    guesses = [f_m_guess, g_m_guess, A_guess, floor]

    OMIT_equation_reduced = lambda f, f_m, g_m, A, floor,: OMIT_equation(f, f_m, g_m, A, floor, k_tot)

    popt, pcov = curve_fit(OMIT_equation_reduced, rel_freqs, amplitude_linear_voltage, guesses, maxfev = 10000)

    

    return popt, pcov, amplitude_linear_voltage, guesses

def fit_OMIT_set_floor(rel_freqs, mags_dB, k_tot, floor, guesses = False):

    """
    Made by Claude. Fit the OMIT equation with a fixed background floor.

    Identical to :func:`fit_OMIT` except that ``floor`` is held fixed at the
    supplied value rather than being a free fit parameter.  This reduces the
    parameter space to ``[f_m, g_m, A]``.

    Parameters
    ----------
    rel_freqs : array_like
        Frequency array (Hz), typically relative to a carrier.
    mags_dB : array_like
        Measured transmission magnitudes (dB).
    k_tot : float
        Fixed total optical linewidth (Hz) passed to :func:`OMIT_equation`.
    floor : float
        Fixed background transmission level (linear voltage).
    guesses : list or False, optional
        Initial parameter guesses ``[f_m, g_m, A]``.  If ``False``,
        auto-guesses are generated from the data. Default is ``False``.

    Returns
    -------
    popt : numpy.ndarray
        Optimal fit parameters ``[f_m, g_m, A]``.
    pcov : numpy.ndarray
        Covariance matrix of ``popt``.
    amplitude_linear_voltage : numpy.ndarray
        Input magnitudes converted to linear voltage (used for fitting).
    guesses : list
        The parameter guesses actually used by ``curve_fit``.
    """

    #organise variables
    amplitude_linear_voltage = dB_to_linear_voltage(mags_dB)

    f_m_guess, g_m_guess, A_guess = guesses

    #guesses:
    if np.any(guesses) == False:
        amplitude_linear_voltage_guess = np.abs(amplitude_linear_voltage)
        max_value = np.max(amplitude_linear_voltage_guess)
        f_m_guess = rel_freqs[np.argmax(amplitude_linear_voltage_guess)]
        g_m_guess = np.abs((f_m_guess - rel_freqs[find_closest_number(amplitude_linear_voltage_guess, max_value/2)]))*2
        floor_guess   = amplitude_linear_voltage[0]
        
        A_guess = np.abs(max_value - floor_guess)
        if np.abs((floor_guess - np.max(amplitude_linear_voltage))) < np.abs((floor_guess - np.min(amplitude_linear_voltage))):
            A_guess = A_guess * -1            
        
        guesses_temp = f_m_guess, g_m_guess, A_guess, floor_guess

        guesses[guesses == False] = guesses_temp[guesses == False]

    guesses = [f_m_guess, g_m_guess, A_guess]

    OMIT_equation_reduced = lambda f, f_m, g_m, A: OMIT_equation(f, f_m, g_m, A, floor, k_tot)

    popt, pcov = curve_fit(OMIT_equation_reduced, rel_freqs, amplitude_linear_voltage, guesses, maxfev = 10000)

    

    return popt, pcov, amplitude_linear_voltage, guesses
