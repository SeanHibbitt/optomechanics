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
                                                     

                                                     





def photon_number(f_d, f_c, k_extHz, k_totHz, P_in ):
    """
    From "A  Novel Architecture for room temperaturemicrowave optomechanical experiments" eq3. Should be
    re-derived for new architecture

    expects variables in Hz not angular frequency
    """
    h_bar = 1.054571817e-34
    w_d, w_c, k_ext, k_tot = np.array([f_d, f_c, k_extHz, k_totHz,]) * 2*np.pi

    numerator = (2*k_ext * P_in)
    denominator = (h_bar *w_c) *( (k_tot**2) + 4*(w_d - w_c)**2 )

    return numerator/denominator
