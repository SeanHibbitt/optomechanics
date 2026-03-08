"""
Made by Claude. General fitting utilities for optomechanics data.

Provides ring-down, linear fitting functions, and physical constants
used across the fitting subpackage (hbar, k_B, NENBW).
"""
import numpy as np
from scipy.optimize import curve_fit
import traceback
import plotly.graph_objects as go
import pandas as pd
from optomechanics.data_management.data_management import attenuation_object
from optomechanics.data_analysis.utilities import find_closest_number
from optomechanics.data_analysis.unit_conversions import watts_ratio_to_dB, dB_to_watts_ratio, dB_to_linear_voltage,\
                                                     linear_voltage_to_dB, Vpp_to_Vrms, Vp_to_Vrms,\
                                                     Vrms_to_Vpp, Vrms_to_Vp, Vrms_to_watts,\
                                                     watts_to_dBw, RMS_to_dBw, RMS_to_dBm,\
                                                     dBw_to_watts, dBm_to_dBw, dBm_to_RMS,\
                                                     watts_to_dBm, dBm_to_watts, Vrms_squared_to_watts
                                                     

                                                     

##define constants:

h_bar = 1.054571817e-34
k_b = 1.380649e-23
RS_default_window_NENBW = 4.082911856792962
##---------------------------


#https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000ow2XCAQ&l=en-GBs






def ring_down_eq(t, A_0, tau, V_0 ):
    """
    Made by Claude. Exponential ring-down decay equation.

    Models the time-domain envelope of a freely decaying mechanical oscillator
    as a decaying exponential plus a constant offset.  Following DeLorenzo
    (2016 thesis), the decay time constant is ``tau = 2Q / omega_m``.

    Parameters
    ----------
    t : array_like
        Time array (s).
    A_0 : float
        Initial amplitude at ``t = 0`` (same units as the signal).
    tau : float
        Decay time constant (s), equal to ``2Q / omega_m``.
    V_0 : float
        Constant background offset (same units as the signal).

    Returns
    -------
    numpy.ndarray
        Ring-down signal ``A_0 * exp(-t / tau) + V_0`` evaluated at each
        point in ``t``.
    """

    return A_0 * np.exp(-t/tau) + V_0

def tau_to_Q(tau, f_m):
    """
    Made by Claude. Convert ring-down time constant to mechanical quality factor.

    Uses the relation from DeLorenzo (2016 thesis): ``tau = 2Q / omega_m``,
    which rearranges to ``Q = tau * omega_m / 2 = tau * f_m * pi``.

    Parameters
    ----------
    tau : float
        Ring-down decay time constant (s).
    f_m : float
        Mechanical resonance frequency (Hz).

    Returns
    -------
    float
        Mechanical quality factor ``Q``.
    """
    return tau*f_m*np.pi


def fit_ring_down(t, A):
    """
    Made by Claude. Fit an exponential ring-down decay to time-domain data.

    Auto-generates initial parameter guesses and fits :func:`ring_down_eq`
    using ``scipy.optimize.curve_fit``.

    Parameters
    ----------
    t : array_like
        Time array (s).
    A : array_like
        Measured amplitude array (same units as the signal).

    Returns
    -------
    popt : numpy.ndarray
        Optimal fit parameters ``[A_0, tau, V_0]``.
    pcov : numpy.ndarray
        Covariance matrix of ``popt``.
    guesses : list
        Initial guesses ``[tau_guess, A_0_guess, V_0_guess]`` used by
        ``curve_fit``.
    """

    tau_guess = t[find_closest_number(A, A/np.exp(1))]
    A_0_guess = np.max(A)
    V_0_guess = A[-1]

    guesses = [tau_guess, A_0_guess, V_0_guess]

    popt, pcov = curve_fit(ring_down_eq, t, A, guesses, maxfev = 10000)

    return popt, pcov, guesses


def line_eq(x, m, c):
    """
    Made by Claude. Straight-line equation ``y = m*x + c``.

    Parameters
    ----------
    x : array_like
        Independent variable.
    m : float
        Gradient (slope).
    c : float
        y-intercept.

    Returns
    -------
    numpy.ndarray
        ``m * x + c`` evaluated at each point in ``x``.
    """

    return m*x+c

def fit_linear(x, y, errors = 1, ):
    """
    Made by Claude. Fit a straight line to data using ``scipy.optimize.curve_fit``.

    Parameters
    ----------
    x : array_like
        Independent variable data.
    y : array_like
        Dependent variable data.
    errors : array_like or float, optional
        Measurement uncertainties on ``y``, passed as ``sigma`` to
        ``curve_fit``.  Default is ``1`` (unweighted fit).

    Returns
    -------
    popt : numpy.ndarray
        Optimal fit parameters ``[m, c]`` for the line ``y = m*x + c``.
    pcov : numpy.ndarray
        Covariance matrix of ``popt``.
    """

    popt, pcov = curve_fit(line_eq, x, y, sigma = errors )

    return popt, pcov



