
import numpy as np
from scipy.optimize import curve_fit
import traceback
import plotly.graph_objects as go
import pandas as pd
from Optomechanics.Utilities.data_management import attenuation_object
from Optomechanics.Utilities.unit_conversions import watts_ratio_to_dB, dB_to_watts_ratio, dB_to_linear_voltage,\
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

def lighten_color(color, amount=0.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.
    From stack exchange

    Examples:
    >> lighten_color('g', 0.3)
    >> lighten_color('#F034A3', 0.6)
    >> lighten_color((.3,.55,.1), 0.5)
    """
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])

def update_plotly_layout(fig, xaxis_title, yaxis_title, xaxis_range=None, yaxis_range=None, title_name=None, tick_format = ('n', '.2f'),):
    """
    Update the layout of a Plotly figure with custom x-axis and y-axis settings.
    
    Parameters:
    - fig: Plotly figure object to update.
    - xaxis_title: Title for the x-axis.
    - yaxis_title: Title for the y-axis.
    - xaxis_range: Optional, range for the x-axis as [min, max]. Default is None.
    - yaxis_range: Optional, range for the y-axis as [min, max]. Default is None.
    """
    fig.update_layout(
        yaxis_title=yaxis_title,
        xaxis_title=xaxis_title,
        template='plotly_white',
        title=title_name,
        xaxis=dict(
            tickformat=tick_format[1],  # Format numbers to 2 decimal places
            ticksuffix='',     # Remove suffix like 'B' for billions
            showgrid=True,     # Show grid lines for better visibility
            tickfont=dict(
                family='Arial',  # Font family
                size=14,         # Font size
                color='black'    # Font color
            ),
            range=xaxis_range,   # Set the x-axis range if provided
            type = 'linear'
        ),
        yaxis=dict(
            tickformat=tick_format[0],  # Format numbers to 2 decimal places
            ticksuffix='',     # Remove suffix like 'B' for billions
            showgrid=True,     # Show grid lines for better visibility
            tickfont=dict(
                family='Arial',  # Font family
                size=14,         # Font size
                color='black'    # Font color
            ),
            range=yaxis_range,   # Set the y-axis range if provided
            type = 'linear'
        )
    )

#old conversion functions


# def dBm_to_watts(powers_dBm):
#     return (10**(powers_dBm/10))/1000



# def watts_to_dBm(watts):
#      return 10*np.log10(watts/(1e-3))


# def re_and_im_to_dB_and_phase(Re, Im):
#     dB = 20*np.log10(np.sqrt(Re**2 + Im**2))
#     z = Re + 1j*Im
#     phase = np.angle(z)
#     return dB, phase

# def RMS_to_dBm(V, Z_0 = 50):
#     return 10*np.log10((V**2)/(0.001*Z_0))

# def RMS_squared_to_dBm(V_square, Z_0 = 50):
#     return 10*np.log10((V_square)/(0.001*Z_0))

# def dBm_to_RMS(dBm, Z_0 = 50):
#     return np.sqrt((Z_0*0.001)*10**(dBm/10))


#https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000ow2XCAQ&l=en-GBs


def find_closest_number(array, value):    
    """find closes value in array
    find_closest_number(array, value)
    I made an edit
    """
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def S21_eq(freq,*p):
    """
    S21 equation for our cavities in linear voltage ratio
    
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
    S21 equation for our cavities in linear voltage ratio
    
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
    S21 equation for our cavities in linear voltage ratio
    
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

def convert_error_dB_to_linear(value, upper_error, lower_error,):
    """
    errors should be a magnitude, e.g both positive values
    magnitude etc should be given in dB
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
    errors should be magnitudes not signs
    magnitude etc should be given in linear voltage ratio
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

    if np.any(value <=0):
        raise ValueError("negative magnitude value")

    error = np.mean([np.abs(upper_error), np.abs(lower_error)], axis = 0)
    error = value[value - error <0]

    return error


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

def split_complex(complex_data):
    complex_data = np.asarray(complex_data)
    return np.concatenate([complex_data.real, complex_data.imag])

def split_complex_wrapper(func):
    """
    Wrapper to split complex function into real and imaginary parts
    for scipy optimization
    """
    def wrapped(*args, **kwargs):
        c = func(*args, **kwargs)
        # Stack real and imaginary parts
        return np.concatenate([c.real, c.imag])
    return wrapped



def fit_S21_peak_complex(complex_data, frequencies, guesses = False, signal_applied = False, equation = S21_eq_complex ):
    """
    not a wrapper, code needs re-factoring into smaller blocks. fits  for fit_S21_peak to fit complex
    Takes re and imag linear voltage ratio data and attempts to unwrap and normalise the phase offset
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





#-------------------------------------------------mechanics

def photon_number(f_d, f_c, k_extHz, k_totHz, P_in ):
    """
    From "A  Novel Architecture for room temperaturemicrowave optomechanical experiments" eq3. Should be
    redervived for new architecture

    expects variables in Hz not angular frequency
    """
    h_bar = 1.054571817e-34
    w_d, w_c, k_ext, k_tot = np.array([f_d, f_c, k_extHz, k_totHz,]) * 2*np.pi

    numerator = (2*k_ext * P_in)
    denominator = (h_bar *w_c) *( (k_tot**2) + 4*(w_d - w_c)**2 )

    return numerator/denominator


def basic_S_ww_eq(freqs, omega_m, G_m, A, nf):

    freqs = freqs*2*np.pi

    omega_m = omega_m *2*np.pi

    G_m = G_m *2 *np.pi

    S_ww =  (A /((G_m**2) + 4*(freqs - omega_m )**2)) +nf

    return S_ww

def basic_S_ww_eq_2(freqs, omega_m, G_m, A, nf):
    """
    Doesn't have lorentzian approx, taken from GW book
    """

    freqs = freqs*2*np.pi

    omega_m = omega_m *2*np.pi

    G_m = G_m *2 *np.pi

    S_ww =  (A* np.abs(1/(freqs**2 - omega_m**2 + 1j*G_m*freqs )**2)) +nf

    return S_ww

def dBm_basic_S_ww_eq(freqs, omega_m, G_m, A, nf):

    return watts_to_dBm(basic_S_ww_eq(freqs, omega_m, G_m, A, nf))


def S_ff_thermal(freqs, m_eff, G_m, T):
    """
    Thermal force spectral density as defined in 
    gw michele maggoire 8.123

    Give inputs in Hz
    """

    G_m = G_m*2*np.pi

    return np.full_like(freqs, 4*k_b*T*m_eff*G_m)


def SHO_TF_sq(freqs, m_eff, f_m, G_m ):
    """
    Transfer derived from function from S Kumar 2023 eq 5
    and thermal force power spectral density as in func S_ff_thermal
    """
    w_freqs = freqs*2*np.pi
    w_m, G_m = np.array([f_m, G_m])*2*np.pi

    return 1/(m_eff**2 * w_m**2 * (G_m**2 + 4 * (w_freqs - w_m)**2))


def S_xx_thermal(freqs, m_eff, T, f_m, G_m ):
    
    return SHO_TF_sq(freqs, m_eff, f_m, G_m ) * S_ff_thermal(freqs, m_eff, G_m, T)


def S_hh_24_25_exp_14_4(S_xx_freqs,  f_m, G_m, S_xx, q_yy = None, q_xx = None, mu = None):
    """
    thin-film re-entrant cavity S_hh transfer function 
    
    """
    #default values moved here so the def line doesn't get too long
    if q_yy is None:
        q_yy = -1.5174802642178184e-06
    if q_xx is None:
        q_xx =  7.587286243641971e-07
    if mu is None:
        mu = 0.0002293073538383159


    w_m = 2*np.pi*f_m
    w = 2*np.pi*S_xx_freqs
    G_m_rad = G_m*2*np.pi

    H = w*w*((q_xx - q_yy)/(4*mu))
    muChi = (1/((w**2)- (w_m**2) + 1j*G_m_rad*w)) 

    T_func_nn = H* muChi

    S_hh = S_xx/ np.abs(T_func_nn)**2


    return S_hh


def S_xx_impre(freqs, f_d, f_c, k_ext, k_tot, linear_drive_power_at_cavity, G):
    """eq 69 Aspelmeyer 2014 review
    All inputs should be in Hz, not radHz
    """
    n_cav = photon_number(f_d, f_c, k_ext, k_tot, linear_drive_power_at_cavity)
    G = G * 2*np.pi
    freqs_rad = freqs*2*np.pi
    k_tot_rad = k_tot * 2 * np.pi

    S_xx_imp = (k_tot/(16*n_cav * G **2)) * (1 + 4*(freqs_rad/k_tot_rad)**2)
    return S_xx_imp

def S_FF_back(freqs, f_d, G, f_c, k_ext, k_tot, linear_drive_power_at_cavity,):
    """
    Eq 70 Aspelmeyer 2014 review
    All freq inputs in Hz
    """
    n_cav = photon_number(f_d, f_c, k_ext, k_tot, linear_drive_power_at_cavity)
    G_rad = G * 2*np.pi
    k_tot_rad = k_tot*2*np.pi
    freqs_rad = freqs

    S_FF_bac = n_cav * (4*h_bar**2 * G_rad**2 / k_tot_rad) / (1 + 4 * (freqs_rad/k_tot_rad)**2)
    return S_FF_bac

def S_xx_back(freqs, m_eff, f_m, G_m, f_d, G, f_c, k_ext, k_tot, linear_drive_power_at_cavity,):

    S_FF_bac = S_FF_back(freqs, f_d, G, f_c, k_ext, k_tot, linear_drive_power_at_cavity,)
    TF_Sq = SHO_TF_sq(freqs, m_eff, f_m, G_m )
    
    return TF_Sq * S_FF_bac



def S_ww_constant_calculator(f_m, G_m, A, f_c, k_tot, k_ext, incident_pump_power, T, m_eff, drive_freq ):

    """equation from X rojas et al 28/11/2022, eq 3-> 5"""
    #constants
    h = 6.62607015e-34
    h_bar = h/(2*np.pi)
    k_b = 1.380649e-23

    w_m, G_m, w_c, k_tot, k_ext, w_drive = np.array([f_m, G_m, f_c, k_tot, k_ext, drive_freq]) * 2*np.pi

    detuning = w_drive - w_c

    n_d = 2*k_ext*incident_pump_power/(h_bar*w_c*(k_tot**2 + 4*detuning**2))
    x_zpf = np.sqrt( h_bar / (2 * m_eff * w_m))

    G = np.sqrt( A * ((k_tot**2) / (k_ext*n_d*h_bar*w_c) ) * (m_eff * (w_m**2) / (4 * k_b * T))   )

    g_0 = G * x_zpf /(2*np.pi)
    G = G /(2*np.pi)

    

    return g_0, G, n_d


def fit_basic_S_ww_eq_linear_power(freqs_minus_pump_freq:np.array, linear_power:np.array, guesses:list, sig = None):  
    """
    fits the basic S_ww equation

    freqs_minus_pump_freq: np.array containing frequencies relative to the pump frequency

    dBm_mag: np.array containing magnitudes in dBm

    list: list of guesses in order: [f_m, G_m, A, nf], shouldn't be reduced frequencies
    
    """

    return fit_basic_S_ww_eq(freqs_minus_pump_freq, watts_to_dBm(linear_power), guesses, sig)

def fit_basic_S_ww_eq(freqs_minus_pump_freq:np.array, dBm_mag:np.array, guesses:list, sig = None):  
    """
    fits the basic S_ww equation

    freqs_minus_pump_freq: np.array containing frequencies relative to the pump frequency

    dBm_mag: np.array containing magnitudes in dBm

    list: list of guesses in order: [f_m, G_m, A, nf], shouldn't be reduced frequencies
    
    """

    watts = dBm_to_watts(dBm_mag)
    if type(sig) != type(None):
        print(f"using given sig: {np.shape(sig)}")
    try:
        popt, pcov = curve_fit(basic_S_ww_eq, freqs_minus_pump_freq, watts, guesses, sigma = sig, maxfev = 50000)
    except RuntimeError:
        print(f"run-time error, returning guesses")
        popt = guesses
        pcov = np.full((len(guesses), len(guesses)), np.nan)

    return np.abs(popt), pcov


def FWHM_guesser(freqs, magnitude, resonance_guess):

    """
    wrapper to fit the basic S_ww equation 
    
    """
    
    max_iter = int(freqs.size/10)
    print(f"freq_size:{freqs.size}")
    print(f"max_iter:{max_iter}")
    dB_2 = -3.01
    

    resonance_pos = find_closest_number(freqs, resonance_guess)

    FWHM_mag = magnitude[resonance_pos]
    mag_at_res = FWHM_mag
    dif_magres_FWHMmag_dB_2 = np.inf

    for i in range(max_iter):
        pos = i + resonance_pos
        if pos >= max_iter:
            break
        minimise_variable = -1*((mag_at_res - FWHM_mag) + dB_2)
        if minimise_variable <= dif_magres_FWHMmag_dB_2:
            dif_magres_FWHMmag_dB_2 = minimise_variable
        else:
            break

    if i == max_iter:
        raise Exception("max iterations reached")
    
    FWHM_pos = pos
    print(f"final_FWHM pos:{pos}")
    FWHM_guess = np.abs(2*(np.abs(resonance_guess - freqs[FWHM_pos])))

    nf_guess = np.abs(dBm_to_watts((magnitude[0]+magnitude[-1])/2))


    A_guess = np.abs((dBm_to_watts(mag_at_res) - nf_guess)*(FWHM_guess*2*np.pi)**2)


    guesses = [resonance_guess, FWHM_guess, A_guess, nf_guess]

    popt, pcov = fit_basic_S_ww_eq(freqs, magnitude, guesses= guesses)
    return popt, pcov, guesses


# def fit_basic_S_ww_eq_auto_guesses(freqs_minus_pump_freq, dBm_mag, omega_m_guess = None, G_m_guess = None, A_guess = None, nf_guess = None):

#     watts = dBm_to_watts(dBm_mag)

#     if omega_m_guess == None:
#         omega_m_guess = freqs_minus_pump_freq(np.argmax(dBm_mag))
#     if G_m_guess == None:
#         G_m_guess = freqs_minus_pump_freq()

#     return popt, pcov

def OMIT_equation(f, f_m, g_m, A, floor, kk_tot):

    """
    OMIT fitting equation, A is defined as:
    A = (k_ext * 4 * omega_m * g_0**2 * n_d)  /  (sqrt(k**4 + 4*(w_p - w_c)) ))
    floor = sqrt(k_ext**2 / (sqrt(k**4 + 4*(w_p - w_c))  )

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
    guesses should be [f_m, g_m, A]
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
    guesses should be [f_m, g_m, A]
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




class fit_S_xx:
    @staticmethod
    def __normalise_Sww_to_GGSxx__(index, row, S21_df, VNA_S21_extra_atten, SG_cavity_to_SA_atten, SG_to_cavity_atten, NENBW = RS_default_window_NENBW, S21_eq = S21_eq, signal_applied = True):
        """
        Expects to have row and index from a pandas df.
        
        2025_06_15:
            Added check for if VNA_S21_extra_atten is None, if it is then it it doesn't apply
            attenuation to S21 power.
        
        """
        ##get relevant meta variables and process
        f_d = float(row["drive_freq"])
        RBW = float(row["res_band_width"])
        T = float(row["temperature_mc[k]"])
        drive_power = float(row["drive_power"])
        print(f"{drive_power=}")
        ##----------------------------------------------------


        ##get SA data
        SA_data_temp = row["data"]
        SA_freqs = np.array(row["data"]["freq[Hz]"])
        SA_powers = np.array(row["data"]["powers[dBm]"])
        
        #convert from ps to psd:
        ENBW = NENBW*RBW

        # print(f"rbw:{RBW}")
        # print(f"NENBW:{NENBW}")
        # print(f"ENBW:{ENBW}")
        SA_powers = watts_to_dBm(dBm_to_watts(SA_powers)/(ENBW) )

        
        ##----------------------------------------------------

        ##get related S21 data
        closest_less_time_index = find_closest_number(S21_df["timestamp[s]"], row["timestamp[s]"])
        if S21_df["timestamp[s]"][closest_less_time_index] > row["timestamp[s]"]:
            closest_less_time_index = closest_less_time_index-1
        S21_data_temp = S21_df.loc[closest_less_time_index]
        S21_freqs = np.array(S21_data_temp["data"]["freq[Hz]"])
        S21_powers = np.array(S21_data_temp["data"]["sweep_number_mag[dB]:1"])
        
        ##----------------------------------------------------

        ##Attenuate Data:
        #data has been attenuated, want to remove attenuation so we get S21 at the cavity
        if VNA_S21_extra_atten is None:
            pass
        else:
            S21_powers = (attenuation_object(S21_powers, S21_freqs) - VNA_S21_extra_atten).magnitude
            

        SA_powers  = (attenuation_object(SA_powers, SA_freqs)   - SG_cavity_to_SA_atten).magnitude
        #data isn't attenuated, we need the attenuated version so added attenuation.
        drive_power_at_cavity = (attenuation_object(float(row["drive_power"]), f_d) + SG_to_cavity_atten).magnitude
        linear_drive_power_at_cavity = dBm_to_watts(drive_power_at_cavity)
        ##----------------------------------------------------

        ##fit S21_data
        #assumes signal is applied
        if signal_applied == True:
            signal_applied = [float(S21_data_temp["band_width"]), 1]
        popt_S21, pcov_S21, guesses, S21_linear_voltage_fitted, S21_freq_fitted, errors = fit_S21_peak(S21_powers, S21_freqs, guesses = False, signal_applied = signal_applied)
        f_c, k_tot, k_ext, mx, c = popt_S21
        f_c_sig, k_tot_sig, k_ext_sig, mx_sig, c_sig = np.sqrt(np.diag(pcov_S21))
        
        ##----------------------------------------------------

        ##Normalise to G^2S_xx + nf/constants -> see A Novel Architecture for room temperaturemicrowave optomechanical experiments
        ##Be made ready for averaging
        
        n_d = photon_number(f_d, f_c, k_ext, k_tot, linear_drive_power_at_cavity)
        n_d_sig = n_d * np.sqrt((f_c_sig/f_c)**2 + (k_ext_sig/k_ext)**2)
        normalisation = (k_ext*n_d/(k_tot**2)) * h_bar* (f_c*2*np.pi)
        GGS_xx = dBm_to_watts(SA_powers)/normalisation #make sure dBm to watts
        
        ##----------------------------------------------------

        ##Convert to mechanical frequencies
        S_xx_freqs_temp = SA_freqs - f_d


        Output_dict = {
            "S21_power_attenuated":S21_powers,
            "S21_freqs":S21_freqs,
            "S21_linear_voltage_fitted":S21_linear_voltage_fitted,
            "S21_freq_fitted":S21_freq_fitted,
            "popt_S21":popt_S21,
            "pcov_S21":pcov_S21,
            "S21_eq":S21_eq,
            "n_d":n_d,
            "n_d_sig":n_d_sig,
            "SA_powers_attenuated":SA_powers,
            "GGS_xx":GGS_xx,
            "S_xx_freqs_temp":S_xx_freqs_temp,
            "NENBW":NENBW,
            "SG_drive_power":drive_power,
            "P_in_dBm":drive_power_at_cavity,
            "P_in_W":linear_drive_power_at_cavity,
            "T":T,
        }

        return Output_dict
    

    @staticmethod
    def __average_and_fit_S_xx__(SA_df, select, m_eff, S21_df, VNA_S21_extra_atten, SG_cavity_to_SA_atten, SG_to_cavity_atten, basic_S_ww_eq = basic_S_ww_eq, NENBW = RS_default_window_NENBW, S21_eq = S21_eq, ):

        """
        SA_df:
            Expects to have a pandas data frame

        selects:
            Expects a dictionary which selects data based on the wanted meta_data
            Selects example:
                select = {
                        "drive_power": ["0"],
                        "domain":["freq"]
                    }
                This selects only drive powers of "0", and domains of "freq"

        Only give this one data set, e.g not multiple powers that you want plotted seperately

        returned g_0 and G are in angular units (2pi*Hz)
        """
        S_ww_raw_list = []
        S_ww_raw_freqs_list = []
        S_ww_index_order = []

        GG_S_norm_list = []
        GG_S_norm_freqs_list = []

        S21_powers_list = []
        S21_freqs_list = []
        S21_index_order = []

        S21_powers_fitted_list = []
        S21_freqs_fitted_list = []

        variables_list = []

        for index, row in SA_df.iterrows():


            ##select data
            break_loop = False
            for key in select.keys():
                #print(f"{row[key]=}, {select[key]=}")
                if not row[key] in select[key]: 
                    break_loop = True
                    continue
            if break_loop: continue
            
            print(f"selected: {index=},{key=},{select[key]}")
            ##----------------------------------------------------

            

            GGSxx_dict = fit_S_xx.__normalise_Sww_to_GGSxx__(index, row, S21_df, VNA_S21_extra_atten, SG_cavity_to_SA_atten, SG_to_cavity_atten)
            """
                "S21_power_attenuated":S21_powers,
                "S21_freqs":S21_freqs,
                "S21_linear_voltage_fitted":S21_linear_voltage_fitted,
                "S21_freq_fitted":S21_freq_fitted,
                "popt_S21":popt_S21,
                "pcov_S21":pcov_S21,
                "S21_eq":S21_eq,
                "n_d":n_d,
                "SA_powers_attenuated":SA_powers_attenuated,
                "GGS_xx":GGS_xx,
                "S_xx_freqs_temp":S_xx_freqs_temp,
                "NENBW":NENBW,
                "SG_drive_power":drive_power,
                "P_in_dBm":drive_power_at_cavity,
                "P_in_W":linear_drive_power_at_cavity,
                "T":T,
            """
            popt_S21 = GGSxx_dict["popt_S21"]
            S21_power_attenuated = GGSxx_dict["S21_power_attenuated"]
            S21_freqs = GGSxx_dict["S21_freqs"]
            S21_linear_voltage_fitted = GGSxx_dict["S21_linear_voltage_fitted"]
            S21_freq_fitted = GGSxx_dict["S21_freq_fitted"]
            popt_S21 = GGSxx_dict["popt_S21"]
            pcov_S21 = GGSxx_dict["pcov_S21"]
            S21_eq = GGSxx_dict["S21_eq"]
            n_d = GGSxx_dict["n_d"]
            SA_powers_attenuated = GGSxx_dict["SA_powers_attenuated"]
            GGS_xx_temp = GGSxx_dict["GGS_xx"]
            NENBW = GGSxx_dict["NENBW"]
            SG_drive_power = ["drive_power"]
            P_in_dBm = GGSxx_dict["P_in_dBm"]
            P_in_W = GGSxx_dict["P_in_W"]
            T = GGSxx_dict["T"]
            S_xx_freqs_temp = GGSxx_dict["S_xx_freqs_temp"]
            

            f_c, k_tot, k_ext, mx_S21, c_S21 = popt_S21

            ##Store for averaging/passing for plotting
            S_ww_raw_list.append(SA_powers_attenuated)
            S_ww_raw_freqs_list.append(S_xx_freqs_temp)
            S_ww_index_order.append(index)

            GG_S_norm_list.append(GGS_xx_temp)
            GG_S_norm_freqs_list.append(S_xx_freqs_temp)
            
            S21_powers_list.append(S21_power_attenuated)
            S21_freqs_list.append(S21_freqs)

            S21_powers_fitted_list.append(linear_voltage_to_dB(S21_linear_voltage_fitted))
            S21_freqs_fitted_list.append(S21_freq_fitted)


            variables_list.append(
                {
                    "f_c":f_c,
                    "k_tot":k_tot,
                    "k_ext":k_ext,
                    "mx_S21":mx_S21,
                    "c_S21":c_S21,
                    "n_d":n_d,
                    "P_in":P_in_W,
                    "Temperature[k]":T,
                }
            )

            ##----------------------------------------------------

        ##Calculate Averages
        GG_S_norm_avg = np.mean(GG_S_norm_list, axis = 0)
        GG_S_norm_sig = np.std(GG_S_norm_list, axis = 0)
        variables_S21_df = pd.json_normalize(variables_list)
        variables_S21_df_mean = variables_S21_df.mean("index")
        print(f"{variables_S21_df_mean=}")
        S_xx_freqs = S_xx_freqs_temp

        ##fit with basic equation
        print(f"rel_freqs_shape:{np.shape(S_xx_freqs)}")
        resonance_freq_guess = S_xx_freqs[np.argmax(GG_S_norm_avg)]
        nf_guess = (GG_S_norm_avg[0] + GG_S_norm_avg[-1])/2
        guesses_mech = [resonance_freq_guess, 5e-2, 307, nf_guess ]
        #guesses_mech = [resonance_freq_guess, 0,0,0]

        #popt, pcov, guesses = FWHM_guesser(rel_freqs[int(rel_freqs.size*0.10):int(rel_freqs.size*0.90)], trace_power_averaged[int(rel_freqs.size*0.10):int(rel_freqs.size*0.90)], resonance_freq_guess )
        popt_S_xx, pcov_S_xx = curve_fit(basic_S_ww_eq, S_xx_freqs, GG_S_norm_avg, guesses_mech, )
        f_m, G_m, A, c = popt_S_xx

        GG_S_norm_fit = basic_S_ww_eq(S_xx_freqs, *popt_S_xx)
        ##----------------------------------------------------

        ##g_0 Calculation
        #def of A:
        # A = G^2 * (4 * k_b * T * G_m ) / ( m_eff * f_m^2 )
        G_m_2_pi = G_m * 2 * np.pi
        w_m = f_m * 2*np.pi

        
        #m_eff given  #for 14KHz mode
        G = np.sqrt( A * ( m_eff * w_m**2   ) / (4 * k_b * T * (G_m_2_pi)) )
        x_zpf = np.sqrt( h_bar / (2 * m_eff * (w_m)))
        g_0 = G * x_zpf

        print(f"g_0:{g_0:.3e}")
        ##---------------------------------------------------
        S_xx = (GG_S_norm_avg - c)/(G*G)
        S_xx_fit = (GG_S_norm_fit-c)/(G*G)

        output_dict =GGSxx_dict | {
            "S_ww_raw_list":S_ww_raw_list,
            "S_ww_raw_freqs_list":S_ww_raw_freqs_list,
            "S_ww_index_order":S_ww_index_order,
            "variables_list":variables_list,
            "S_xx":S_xx, 
            "S_xx_freqs":S_xx_freqs, 
            "popt_S_xx":popt_S_xx, 
            "pcov_S_xx":pcov_S_xx, 
            "S_xx_fit":S_xx_fit, 
            "GG_S_norm_fit":GG_S_norm_fit, 
            "variables_df_mean":variables_S21_df_mean, 
            "GGSxx_dict":GGSxx_dict, 
            "GG_S_norm_list":GG_S_norm_list,
            "GG_S_norm_avg":GG_S_norm_avg, 
            "GG_S_norm_sig":GG_S_norm_sig,
            "g_0":g_0,
            "G":G,
            "x_zpf":x_zpf,
            "S21_powers_list":S21_powers_list,
            "S21_freqs_list":S21_freqs_list,
            "S21_powers_fitted_list":S21_powers_fitted_list,
            "S21_freqs_fitted_list": S21_freqs_fitted_list,
        }


        return output_dict


    
    
