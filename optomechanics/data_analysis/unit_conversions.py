"""
Unit conversions reference. This is so we know the unit conversions are right!
"""




import numpy as np

def watts_ratio_to_dB(watts_ratio: float):
    """
    Made by Claude. Convert a linear power ratio to decibels.

    Parameters
    ----------
    watts_ratio : float
        Linear power ratio (output power / input power).

    Returns
    -------
    float
        Power ratio in dB (10 * log10(watts_ratio)).
    """
    return 10*np.log10(watts_ratio)

def dB_to_watts_ratio(dB):
    """
    Made by Claude. Convert a power value in decibels to a linear watts ratio.

    Parameters
    ----------
    dB : float
        Power value in dB.

    Returns
    -------
    float
        Linear power ratio (10 ** (dB / 10)).
    """
    return 10**(dB/10)

def dB_to_linear_voltage(powers_dB):
    """
    Made by Claude. Convert a value in decibels to a linear voltage ratio.

    Parameters
    ----------
    powers_dB : float
        Value in dB.

    Returns
    -------
    float
        Linear voltage ratio (10 ** (powers_dB / 20)).
    """
    return 10**(powers_dB/20)

def linear_voltage_to_dB(voltage_ratio):
    """
    Made by Claude. Convert a linear voltage ratio to decibels.

    Parameters
    ----------
    voltage_ratio : float
        Linear voltage ratio.

    Returns
    -------
    float
        Value in dB (20 * log10(voltage_ratio)).
    """
    return 20*np.log10(voltage_ratio)

def Vpp_to_Vrms(V_pp):
    """
    Made by Claude. Convert peak-to-peak voltage to RMS voltage.

    Parameters
    ----------
    V_pp : float
        Peak-to-peak voltage (V).

    Returns
    -------
    float
        RMS voltage (V_pp / (2 * sqrt(2))).
    """
    Vrms = V_pp/(2*np.sqrt(2))
    return Vrms

def Vp_to_Vrms(V_pp):
    """
    Made by Claude. Convert peak voltage to RMS voltage.

    Parameters
    ----------
    V_pp : float
        Peak voltage (V).

    Returns
    -------
    float
        RMS voltage (V_p / sqrt(2)).
    """
    Vrms = V_pp/(np.sqrt(2))
    return Vrms

def Vrms_to_Vpp(Vrms):
    """
    Made by Claude. Convert RMS voltage to peak-to-peak voltage.

    Parameters
    ----------
    Vrms : float
        RMS voltage (V).

    Returns
    -------
    float
        Peak-to-peak voltage (Vrms * 2 * sqrt(2)).
    """
    V_pp = Vrms*(2*np.sqrt(2))
    return V_pp

def Vrms_to_Vp(Vrms):
    """
    Made by Claude. Convert RMS voltage to peak voltage.

    Parameters
    ----------
    Vrms : float
        RMS voltage (V).

    Returns
    -------
    float
        Peak voltage (Vrms * sqrt(2)).
    """
    V_p = Vrms*(np.sqrt(2))
    return V_p

def Vrms_to_watts(Vrms, Z_0 = 50):
    """
    Made by Claude. Convert RMS voltage to power in watts.

    Parameters
    ----------
    Vrms : float
        RMS voltage (V).
    Z_0 : float, optional
        Impedance in ohms. Default is 50.

    Returns
    -------
    float
        Power in watts (Vrms ** 2 / Z_0).
    """
    return (Vrms**2)/Z_0

def watts_to_dBw(watts):
    """
    Made by Claude. Convert power in watts to dBW.

    Parameters
    ----------
    watts : float
        Power in watts.

    Returns
    -------
    float
        Power in dBW (10 * log10(watts)).
    """
    return 10*np.log10(watts)

def RMS_to_dBw(Vrms, Z_0 = 50):
    """
    Made by Claude. Convert RMS voltage to power in dBW.

    Parameters
    ----------
    Vrms : float
        RMS voltage (V).
    Z_0 : float, optional
        Impedance in ohms. Default is 50.

    Returns
    -------
    float
        Power in dBW.
    """
    watts = Vrms_to_watts(Vrms, Z_0)
    return watts_to_dBw(watts)

def RMS_to_dBm(Vrms, Z_0 = 50):
    """
    Made by Claude. Convert RMS voltage to power in dBm.

    Parameters
    ----------
    Vrms : float
        RMS voltage (V).
    Z_0 : float, optional
        Impedance in ohms. Default is 50.

    Returns
    -------
    float
        Power in dBm.
    """
    return RMS_to_dBw(Vrms, Z_0) + 30

def dBw_to_watts(dBw):
    """
    Made by Claude. Convert power in dBW to watts.

    Parameters
    ----------
    dBw : float
        Power in dBW.

    Returns
    -------
    float
        Power in watts (10 ** (dBw / 10)).
    """
    return 10**(dBw/10)

def dBm_to_dBw(dBm):
    """
    Made by Claude. Convert power in dBm to dBW.

    Parameters
    ----------
    dBm : float
        Power in dBm.

    Returns
    -------
    float
        Power in dBW (dBm - 30).
    """
    return dBm - 30

def dBm_to_RMS(dBm, Z_0 = 50):
    """
    Made by Claude. Convert power in dBm to RMS voltage.

    Parameters
    ----------
    dBm : float
        Power in dBm.
    Z_0 : float, optional
        Impedance in ohms. Default is 50.

    Returns
    -------
    float
        RMS voltage (V).
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
