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
from optomechanics.data_analysis.misc_equations import photon_number                                 


class fit_S_xx:
    """
    Made by Claude. High-level fitter for the mechanical displacement spectral density S_xx.

    Normalises raw spectrum analyser (SA) power data to the dimensionless
    quantity G²S_xx using a simultaneously acquired VNA S21 trace, then
    averages over multiple sweeps and fits with `basic_S_ww_eq` to extract
    the optomechanical coupling g_0 and optical coupling G.

    All static methods — instantiation is not required.  Call
    ``fit_S_xx.__average_and_fit_S_xx__`` as the main entry point.

    Notes
    -----
    Returned values of g_0 and G are in angular units (2π × Hz).
    """
    @staticmethod
    def __normalise_Sww_to_GGSxx__(index, row, S21_df, VNA_S21_extra_atten, SG_cavity_to_SA_atten, SG_to_cavity_atten, NENBW = RS_default_window_NENBW, S21_eq = S21_eq, signal_applied = True):
        """
        Made by Claude. Normalise a single SA sweep to G²S_xx using the nearest S21 measurement.

        Expects a row and index from a pandas DataFrame. Applies attenuation
        corrections, fits S21 to extract cavity parameters, and normalises the
        SA power spectrum to G²S_xx.

        2025-06-15: Added check for ``VNA_S21_extra_atten is None`` — if it is
        None the S21 attenuation correction is skipped.

        Parameters
        ----------
        index : int
            Row index in `SA_df` (used for bookkeeping).
        row : pandas.Series
            A single row from the SA DataFrame containing fields:
            ``drive_freq``, ``res_band_width``, ``temperature_mc[k]``,
            ``drive_power``, ``data``, ``timestamp[s]``.
        S21_df : pandas.DataFrame
            DataFrame of VNA S21 sweeps with a ``timestamp[s]`` column.
        VNA_S21_extra_atten : attenuation_object or None
            Extra attenuation applied to the VNA signal path.  Pass ``None``
            to skip S21 attenuation correction.
        SG_cavity_to_SA_atten : attenuation_object
            Attenuation from the cavity output to the spectrum analyser.
        SG_to_cavity_atten : attenuation_object
            Attenuation from the signal generator to the cavity input.
        NENBW : float, optional
            Noise-equivalent noise bandwidth factor. Default is
            ``RS_default_window_NENBW``.
        S21_eq : callable, optional
            S21 model equation. Default is `S21_eq`.
        signal_applied : bool, optional
            If True, one applied tone is notched before S21 fitting. Default
            is True.

        Returns
        -------
        dict
            Dictionary containing S21 fit results, normalised SA spectrum
            (``GGS_xx``), mechanical frequencies, photon number, and related
            variables.
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
        Made by Claude. Average multiple SA sweeps and fit for g_0 and G.

        Iterates over `SA_df`, selects rows matching `select`, normalises each
        to G²S_xx via `__normalise_Sww_to_GGSxx__`, averages, and fits
        `basic_S_ww_eq` to extract optomechanical parameters.

        Only pass one data set (e.g. a single drive power); do not mix
        conditions that should be plotted separately.

        Returned g_0 and G are in angular units (2π × Hz).

        Parameters
        ----------
        SA_df : pandas.DataFrame
            DataFrame of SA sweeps.
        select : dict
            Column filters, e.g.
            ``{"drive_power": ["0"], "domain": ["freq"]}``.
        m_eff : float
            Effective mass of the mechanical resonator (kg).
        S21_df : pandas.DataFrame
            DataFrame of VNA S21 sweeps.
        VNA_S21_extra_atten : attenuation_object or None
            Extra attenuation on the VNA signal path.
        SG_cavity_to_SA_atten : attenuation_object
            Attenuation from cavity to spectrum analyser.
        SG_to_cavity_atten : attenuation_object
            Attenuation from signal generator to cavity.
        basic_S_ww_eq : callable, optional
            Mechanical spectral density model to fit. Default is
            `basic_S_ww_eq`.
        NENBW : float, optional
            Noise-equivalent noise bandwidth factor. Default is
            ``RS_default_window_NENBW``.
        S21_eq : callable, optional
            S21 model equation. Default is `S21_eq`.

        Returns
        -------
        dict
            Dictionary containing averaged G²S_xx, fit parameters, g_0, G,
            x_zpf, raw lists of S21 and SA data, and all intermediate results.
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


    
    
## old fitters ----------------------------




def basic_S_ww_eq(freqs, omega_m, G_m, A, nf):
    """
    Made by Claude. Lorentzian approximation of the mechanical displacement spectral density.

    Parameters
    ----------
    freqs : array-like
        Frequency array (Hz).
    omega_m : float
        Mechanical resonance frequency (Hz).
    G_m : float
        Mechanical linewidth / damping rate (Hz).
    A : float
        Amplitude scaling factor.
    nf : float
        Noise floor offset.

    Returns
    -------
    numpy.ndarray
        Spectral density S_ww (W/Hz or arb. units matching `A`).
    """
    freqs = freqs*2*np.pi

    omega_m = omega_m *2*np.pi

    G_m = G_m *2 *np.pi

    S_ww =  (A /((G_m**2) + 4*(freqs - omega_m )**2)) +nf

    return S_ww

def basic_S_ww_eq_2(freqs, omega_m, G_m, A, nf):
    """
    Made by Claude. Full mechanical displacement spectral density without the Lorentzian approximation.

    Uses the exact susceptibility form taken from the gravitational-wave
    (GW) textbook, rather than the near-resonance Lorentzian approximation
    used in `basic_S_ww_eq`.

    Parameters
    ----------
    freqs : array-like
        Frequency array (Hz).
    omega_m : float
        Mechanical resonance frequency (Hz).
    G_m : float
        Mechanical linewidth / damping rate (Hz).
    A : float
        Amplitude scaling factor.
    nf : float
        Noise floor offset.

    Returns
    -------
    numpy.ndarray
        Spectral density S_ww (W/Hz or arb. units matching `A`).
    """

    freqs = freqs*2*np.pi

    omega_m = omega_m *2*np.pi

    G_m = G_m *2 *np.pi

    S_ww =  (A* np.abs(1/(freqs**2 - omega_m**2 + 1j*G_m*freqs )**2)) +nf

    return S_ww

def dBm_basic_S_ww_eq(freqs, omega_m, G_m, A, nf):
    """
    Made by Claude. Lorentzian mechanical spectral density in dBm.

    Wrapper around `basic_S_ww_eq` that converts the output to dBm.

    Parameters
    ----------
    freqs : array-like
        Frequency array (Hz).
    omega_m : float
        Mechanical resonance frequency (Hz).
    G_m : float
        Mechanical linewidth / damping rate (Hz).
    A : float
        Amplitude scaling factor.
    nf : float
        Noise floor offset.

    Returns
    -------
    numpy.ndarray
        Spectral density in dBm.
    """
    return watts_to_dBm(basic_S_ww_eq(freqs, omega_m, G_m, A, nf))


def S_ff_thermal(freqs, m_eff, G_m, T):
    """
    Made by Claude. Thermal force spectral density.

    As defined in Maggiore (GW textbook) eq. 8.123. All frequency inputs
    must be in Hz.

    Parameters
    ----------
    freqs : array-like
        Frequency array (Hz) — used only to determine output shape.
    m_eff : float
        Effective mass of the mechanical resonator (kg).
    G_m : float
        Mechanical linewidth / damping rate (Hz).
    T : float
        Temperature (K).

    Returns
    -------
    numpy.ndarray
        Thermal force spectral density S_ff (N^2/Hz), flat across `freqs`.
    """

    G_m = G_m*2*np.pi

    return np.full_like(freqs, 4*k_b*T*m_eff*G_m)


def SHO_TF_sq(freqs, m_eff, f_m, G_m ):
    """
    Made by Claude. Squared magnitude of the simple harmonic oscillator transfer function.

    Derived from S. Kumar (2023) eq. 5 and consistent with the thermal force
    spectral density in `S_ff_thermal`.

    Parameters
    ----------
    freqs : array-like
        Frequency array (Hz).
    m_eff : float
        Effective mass of the mechanical resonator (kg).
    f_m : float
        Mechanical resonance frequency (Hz).
    G_m : float
        Mechanical linewidth / damping rate (Hz).

    Returns
    -------
    numpy.ndarray
        Squared SHO transfer function |χ(ω)|² (m²/N²).
    """
    w_freqs = freqs*2*np.pi
    w_m, G_m = np.array([f_m, G_m])*2*np.pi

    return 1/(m_eff**2 * w_m**2 * (G_m**2 + 4 * (w_freqs - w_m)**2))


def S_xx_thermal(freqs, m_eff, T, f_m, G_m ):
    """
    Made by Claude. Thermal displacement spectral density of a mechanical resonator.

    Product of the squared SHO transfer function and the thermal force
    spectral density.

    Parameters
    ----------
    freqs : array-like
        Frequency array (Hz).
    m_eff : float
        Effective mass of the mechanical resonator (kg).
    T : float
        Temperature (K).
    f_m : float
        Mechanical resonance frequency (Hz).
    G_m : float
        Mechanical linewidth / damping rate (Hz).

    Returns
    -------
    numpy.ndarray
        Thermal displacement spectral density S_xx (m²/Hz).
    """
    return SHO_TF_sq(freqs, m_eff, f_m, G_m ) * S_ff_thermal(freqs, m_eff, G_m, T)


def S_hh_24_25_exp_14_4(S_xx_freqs,  f_m, G_m, S_xx, q_yy = None, q_xx = None, mu = None):
    """
    Made by Claude. Thin-film re-entrant cavity S_hh transfer function.

    Computes the cavity gap spectral density S_hh from the mechanical
    displacement spectral density S_xx using the transfer function of a
    thin-film re-entrant cavity (eqs. 24–25 of experiment 14.4).

    Parameters
    ----------
    S_xx_freqs : array-like
        Frequency array (Hz).
    f_m : float
        Mechanical resonance frequency (Hz).
    G_m : float
        Mechanical linewidth / damping rate (Hz).
    S_xx : array-like
        Mechanical displacement spectral density (m²/Hz).
    q_yy : float, optional
        Electromechanical coupling coefficient q_yy. Default is
        -1.5174802642178184e-06.
    q_xx : float, optional
        Electromechanical coupling coefficient q_xx. Default is
        7.587286243641971e-07.
    mu : float, optional
        Electromechanical coupling parameter mu. Default is
        0.0002293073538383159.

    Returns
    -------
    numpy.ndarray
        Cavity gap spectral density S_hh (m²/Hz).
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
    """
    Made by Claude. Imprecision noise spectral density of the displacement measurement.

    Eq. 69 of Aspelmeyer (2014) review. All frequency inputs must be in Hz,
    not rad/Hz.

    Parameters
    ----------
    freqs : array-like
        Frequency array (Hz).
    f_d : float
        Drive frequency (Hz).
    f_c : float
        Cavity resonance frequency (Hz).
    k_ext : float
        External coupling rate (Hz).
    k_tot : float
        Total linewidth (Hz).
    linear_drive_power_at_cavity : float
        Drive power at the cavity input (W).
    G : float
        Optomechanical coupling rate (Hz/m).

    Returns
    -------
    numpy.ndarray
        Imprecision spectral density S_xx_imp (m²/Hz).
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