"""
Unit conversions reference. This is so we know the unit conversions are right!
"""





import numpy as np

def watts_ratio_to_dB(watts_ratio: float):
    """
    Watts ratio to dB

    :watts_ratio: float
    """
    return 10*np.log10(watts_ratio)

def dB_to_watts_ratio(dB):
    """
    Docstring for dB_to_watts_ratio
    
    :param dB: float
    """
    return 10**(dB/10)

def dB_to_linear_voltage(powers_dB):
    return 10**(powers_dB/20)

def linear_voltage_to_dB(voltage_ratio):
    return 20*np.log10(voltage_ratio)

def Vpp_to_Vrms(V_pp):
    Vrms = V_pp/(2*np.sqrt(2))
    return Vrms

def Vp_to_Vrms(V_pp):
    Vrms = V_pp/(np.sqrt(2))
    return Vrms

def Vrms_to_Vpp(Vrms):
    V_pp = Vrms*(2*np.sqrt(2))
    return V_pp

def Vrms_to_Vp(Vrms):
    V_p = Vrms*(np.sqrt(2))
    return V_p

def Vrms_to_watts(Vrms, Z_0 = 50):
    return (Vrms**2)/Z_0

def watts_to_dBw(watts):
    return 10*np.log10(watts)

def RMS_to_dBw(Vrms, Z_0 = 50):
    watts = Vrms_to_watts(Vrms, Z_0)
    return watts_to_dBw(watts)

def RMS_to_dBm(Vrms, Z_0 = 50):
    return RMS_to_dBw(Vrms, Z_0) + 30

def dBw_to_watts(dBw):
    return 10**(dBw/10)

def dBm_to_dBw(dBm):
    return dBm - 30

def dBm_to_RMS(dBm, Z_0 = 50):
    dBw = dBm_to_dBw(dBm)
    watts = dBw_to_watts(dBw)
    Vrms = np.sqrt(watts * Z_0)
    return Vrms

def watts_to_dBm(watts):
    dBw = watts_to_dBw(watts)
    return dBw + 30

def dBm_to_watts(dBm):
    dBw = dBm_to_dBw(dBm)
    watts = dBw_to_watts(dBw)
    return watts

def Vrms_squared_to_watts(Vrms_squared,Z_0 = 50):
    watts = Vrms_squared/Z_0
    return watts
