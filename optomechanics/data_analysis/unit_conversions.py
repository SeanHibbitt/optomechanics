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
    """
    Convert dB to linear voltage ratio.

    :param powers_dB: value in dB
    :returns: linear voltage ratio (10 ** (powers_dB / 20))
    """
    return 10**(powers_dB/20)

def linear_voltage_to_dB(voltage_ratio):
    """
    Convert linear voltage ratio to dB.

    :param voltage_ratio: linear voltage ratio
    :returns: value in dB (20 * log10(voltage_ratio))
    """
    return 20*np.log10(voltage_ratio)

def Vpp_to_Vrms(V_pp):
    """
    Convert peak-to-peak voltage to RMS voltage.

    :param V_pp: peak-to-peak voltage
    :returns: RMS voltage (V_pp / (2 * sqrt(2)))
    """
    Vrms = V_pp/(2*np.sqrt(2))
    return Vrms

def Vp_to_Vrms(V_pp):
    """
    Convert peak voltage to RMS voltage.

    :param V_pp: peak voltage
    :returns: RMS voltage (V_p / sqrt(2))
    """
    Vrms = V_pp/(np.sqrt(2))
    return Vrms

def Vrms_to_Vpp(Vrms):
    """
    Convert RMS voltage to peak-to-peak voltage.

    :param Vrms: RMS voltage
    :returns: peak-to-peak voltage (Vrms * 2 * sqrt(2))
    """
    V_pp = Vrms*(2*np.sqrt(2))
    return V_pp

def Vrms_to_Vp(Vrms):
    """
    Convert RMS voltage to peak voltage.

    :param Vrms: RMS voltage
    :returns: peak voltage (Vrms * sqrt(2))
    """
    V_p = Vrms*(np.sqrt(2))
    return V_p

def Vrms_to_watts(Vrms, Z_0 = 50):
    """
    Convert RMS voltage to power in watts.

    :param Vrms: RMS voltage
    :param Z_0: impedance in ohms (default 50)
    :returns: power in watts (Vrms^2 / Z_0)
    """
    return (Vrms**2)/Z_0

def watts_to_dBw(watts):
    """
    Convert power in watts to dBW.

    :param watts: power in watts
    :returns: power in dBW (10 * log10(watts))
    """
    return 10*np.log10(watts)

def RMS_to_dBw(Vrms, Z_0 = 50):
    """
    Convert RMS voltage to power in dBW.

    :param Vrms: RMS voltage
    :param Z_0: impedance in ohms (default 50)
    :returns: power in dBW
    """
    watts = Vrms_to_watts(Vrms, Z_0)
    return watts_to_dBw(watts)

def RMS_to_dBm(Vrms, Z_0 = 50):
    """
    Convert RMS voltage to power in dBm.

    :param Vrms: RMS voltage
    :param Z_0: impedance in ohms (default 50)
    :returns: power in dBm
    """
    return RMS_to_dBw(Vrms, Z_0) + 30

def dBw_to_watts(dBw):
    """
    Convert power in dBW to watts.

    :param dBw: power in dBW
    :returns: power in watts (10 ** (dBw / 10))
    """
    return 10**(dBw/10)

def dBm_to_dBw(dBm):
    """
    Convert power in dBm to dBW.

    :param dBm: power in dBm
    :returns: power in dBW (dBm - 30)
    """
    return dBm - 30

def dBm_to_RMS(dBm, Z_0 = 50):
    """
    Convert power in dBm to RMS voltage.

    :param dBm: power in dBm
    :param Z_0: impedance in ohms (default 50)
    :returns: RMS voltage
    """
    dBw = dBm_to_dBw(dBm)
    watts = dBw_to_watts(dBw)
    Vrms = np.sqrt(watts * Z_0)
    return Vrms

def watts_to_dBm(watts):
    """
    Convert power in watts to dBm.

    :param watts: power in watts
    :returns: power in dBm
    """
    dBw = watts_to_dBw(watts)
    return dBw + 30

def dBm_to_watts(dBm):
    """
    Convert power in dBm to watts.

    :param dBm: power in dBm
    :returns: power in watts (10 ** ((dBm - 30) / 10))
    """
    dBw = dBm_to_dBw(dBm)
    watts = dBw_to_watts(dBw)
    return watts

def Vrms_squared_to_watts(Vrms_squared,Z_0 = 50):
    """
    Convert Vrms^2 to power in watts.

    :param Vrms_squared: RMS voltage squared (V^2)
    :param Z_0: impedance in ohms (default 50)
    :returns: power in watts (Vrms_squared / Z_0)
    """
    watts = Vrms_squared/Z_0
    return watts
