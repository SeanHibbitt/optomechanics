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
                                                     

                                                     

##define constants:

h_bar = 1.054571817e-34
k_b = 1.380649e-23
RS_default_window_NENBW = 4.082911856792962
##---------------------------


#https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000ow2XCAQ&l=en-GBs






def ring_down_eq(t, A_0, tau, V_0 ):
    """
    Basic ring-down equation
    tau := 2Q/w_m, as in delorenzo laura 2016 thesis
    """

    return A_0 * np.exp(-t/tau) + V_0

def tau_to_Q(tau, f_m):
    """
    tau equation from delorenzo laura 2016 thesis
    tau := 2Q/w_m
    """
    return tau*f_m*np.pi


def fit_ring_down(t, A):

    tau_guess = t[find_closest_number(A, A/np.exp(1))]
    A_0_guess = np.max(A)
    V_0_guess = A[-1]

    guesses = [tau_guess, A_0_guess, V_0_guess]

    popt, pcov = curve_fit(ring_down_eq, t, A, guesses, maxfev = 10000)

    return popt, pcov, guesses


def line_eq(x, m, c):

    return m*x+c

def fit_linear(x, y, errors = 1, ):

    popt, pcov = curve_fit(line_eq, x, y, sigma = errors )

    return popt, pcov



