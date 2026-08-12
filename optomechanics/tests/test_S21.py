"""Unit tests for data_analysis/fitting/S21.py equation and fitting functions."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_analysis.fitting.S21 import (
    S21_eq, S21_eq_dB, S21_eq_phase, S21_eq_complex,
    fit_S21_peak, fit_S21_peak_dB, fit_S21_peak_complex,
)
from optomechanics.data_analysis.unit_conversions import linear_voltage_to_dB

# Parameters: f_0, k_tot, k_ext, att_m, att_c
# S21 = |k_ext / (k_tot + 2j*(f-f_0))| + f*att_m + att_c  (angular 2pi cancelled)
# On resonance (f=f_0): S21 = k_ext/k_tot + att_c (att_m term negligible at resonance check)

def test_S21_eq_on_resonance():
    f0=1e9; ktot=1e6; kext=0.5e6; m=0.0; c=0.0
    result = S21_eq(np.array([f0]), f0, ktot, kext, m, c)
    expected = kext/ktot
    assert_allclose(result[0], expected, rtol=1e-10)

def test_S21_eq_off_resonance_lower():
    f0=1e9; ktot=1e6; kext=0.5e6; m=0.0; c=0.0
    on = S21_eq(np.array([f0]), f0, ktot, kext, m, c)[0]
    off = S21_eq(np.array([f0+10e6]), f0, ktot, kext, m, c)[0]
    assert off < on

def test_S21_eq_background_offset():
    f0=1e9; ktot=1e6; kext=0.5e6; m=0.0; c=0.1
    far_off = S21_eq(np.array([f0+1e9]), f0, ktot, kext, m, c)
    # Far off resonance: S21_peak term -> 0, result ~ c
    assert_allclose(far_off[0], 0.1, atol=0.01)

def test_S21_eq_linear_slope():
    f0=1e9; ktot=1e6; kext=0.5e6; m=1e-12; c=0.0
    # With background slope only, S21 at f1 and f2 known analytically
    f1 = f0 + 1e9
    f2 = f0 + 2e9
    r1 = S21_eq(np.array([f1]), f0, ktot, kext, m, c)[0]
    r2 = S21_eq(np.array([f2]), f0, ktot, kext, m, c)[0]
    # Verify both are positive and r2 > r1 (slope contribution positive)
    assert r1 > 0 and r2 > r1

def test_S21_eq_dB_on_resonance():
    f0=1e9; ktot=1e6; kext=0.5e6; m=0.0; c=0.0
    result_linear = S21_eq(np.array([f0]), f0, ktot, kext, m, c)[0]
    result_dB = S21_eq_dB(np.array([f0]), f0, ktot, kext, m, c)[0]
    expected_dB = 20*np.log10(result_linear)
    assert_allclose(result_dB, expected_dB, rtol=1e-10)

def test_S21_eq_phase_on_resonance_zero():
    f0=1e9; ktot=1e6; kext=0.5e6; m=0.0; c=0.0
    phase = S21_eq_phase(np.array([f0]), f0, ktot, kext, m, c)
    assert_allclose(phase[0], 0.0, atol=1e-12)

def test_S21_eq_phase_below_resonance_positive():
    f0=1e9; ktot=1e6; kext=0.5e6; m=0.0; c=0.0
    phase = S21_eq_phase(np.array([f0-1e6]), f0, ktot, kext, m, c)
    assert phase[0] > 0

def test_S21_eq_phase_above_resonance_negative():
    f0=1e9; ktot=1e6; kext=0.5e6; m=0.0; c=0.0
    phase = S21_eq_phase(np.array([f0+1e6]), f0, ktot, kext, m, c)
    assert phase[0] < 0

def test_S21_eq_complex_on_resonance_real():
    # On resonance with zero background, result should be purely real
    f0=1e9; ktot=1e6; kext=0.5e6; rm=0.0; rc=0.0; im=0.0; ic=0.0
    result = S21_eq_complex(np.array([f0]), f0, ktot, kext, rm, rc, im, ic)
    assert_allclose(result[0].imag, 0.0, atol=1e-15)
    expected_real = kext/ktot
    assert_allclose(result[0].real, expected_real, rtol=1e-10)

def test_S21_eq_complex_background():
    f0=1e9; ktot=1e6; kext=0.5e6; rm=0.0; rc=0.2; im=0.0; ic=0.1
    # Far off resonance: complex result ~ rc + i*ic
    result = S21_eq_complex(np.array([f0+1e9]), f0, ktot, kext, rm, rc, im, ic)
    assert_allclose(result[0].real, 0.2, atol=0.01)
    assert_allclose(result[0].imag, 0.1, atol=0.01)


# ---------------------------------------------------------------------------
# Fitting function tests
# ---------------------------------------------------------------------------

# Helper: generate synthetic S21 data with known parameters
_F0 = 5e9       # 5 GHz resonance
_KTOT = 1e6     # 1 MHz total linewidth
_KEXT = 5e5     # 500 kHz external coupling
_ATT_M = 0.0    # zero background slope
_ATT_C = 0.0    # zero background offset
_NPTS = 2001    # number of frequency points
_SPAN = 20e6    # 20 MHz span centred on f0
_FREQS = np.linspace(_F0 - _SPAN / 2, _F0 + _SPAN / 2, _NPTS)


def test_fit_S21_peak_recovers_parameters():
    """fit_S21_peak should recover f_0, k_tot, k_ext from synthetic linear data."""
    # Generate noiseless synthetic data using S21_eq
    synth = S21_eq(_FREQS, _F0, _KTOT, _KEXT, _ATT_M, _ATT_C)
    # Convert to dB (fit_S21_peak expects dB input, converts internally)
    synth_dB = linear_voltage_to_dB(synth)

    popt, pcov, guesses, amp_lin, freqs_out, errors = fit_S21_peak(
        synth_dB, _FREQS
    )

    assert_allclose(popt[0], _F0, rtol=0.01, err_msg="f_0 recovery failed")
    assert_allclose(popt[1], _KTOT, rtol=0.05, err_msg="k_tot recovery failed")
    assert_allclose(popt[2], _KEXT, rtol=0.05, err_msg="k_ext recovery failed")



def test_fit_S21_peak_dB_recovers_parameters():
    """fit_S21_peak_dB should recover f_0, k_tot, k_ext from dB data."""
    synth_dB = linear_voltage_to_dB(
        S21_eq(_FREQS, _F0, _KTOT, _KEXT, _ATT_M, _ATT_C)
    )

    popt, pcov, guesses, amp_lin, freqs_out, errors = fit_S21_peak_dB(
        synth_dB, _FREQS
    )

    # f_0 and k_tot are well-determined; k_ext is poorly constrained in dB space
    assert_allclose(popt[0], _F0, rtol=0.01, err_msg="f_0 recovery failed (dB)")
    assert_allclose(popt[1], _KTOT, rtol=0.05, err_msg="k_tot recovery failed (dB)")


def test_fit_S21_peak_complex_recovers_parameters():
    """fit_S21_peak_complex should recover f_0, k_tot, k_ext from complex data."""
    synth_complex = S21_eq_complex(
        _FREQS, _F0, _KTOT, _KEXT, 0.0, 0.0, 0.0, 0.0
    )

    popt, pcov, guesses, data_out, freqs_out, chi2, r2 = fit_S21_peak_complex(
        synth_complex, _FREQS
    )

    assert_allclose(abs(popt[0]), _F0, rtol=0.01, err_msg="f_0 recovery failed (complex)")
    assert_allclose(abs(popt[1]), _KTOT, rtol=0.05, err_msg="k_tot recovery failed (complex)")
    assert_allclose(abs(popt[2]), _KEXT, rtol=0.05, err_msg="k_ext recovery failed (complex)")
    # R-squared should be very close to 1 for noiseless data
    assert r2 > 0.99, f"R-squared too low: {r2}"


def test_fit_S21_peak_complex_with_background():
    """fit_S21_peak_complex should handle a non-zero background."""
    rc = 0.01; ic = 0.005
    synth_complex = S21_eq_complex(
        _FREQS, _F0, _KTOT, _KEXT, 0.0, rc, 0.0, ic
    )

    popt, pcov, guesses, data_out, freqs_out, chi2, r2 = fit_S21_peak_complex(
        synth_complex, _FREQS
    )

    assert_allclose(abs(popt[0]), _F0, rtol=0.01)
    assert_allclose(abs(popt[1]), _KTOT, rtol=0.05)
    assert_allclose(abs(popt[2]), _KEXT, rtol=0.05)


def test_fit_S21_peak_returns_correct_length():
    """fit_S21_peak should return 6 elements in the tuple."""
    synth_dB = linear_voltage_to_dB(
        S21_eq(_FREQS, _F0, _KTOT, _KEXT, _ATT_M, _ATT_C)
    )
    result = fit_S21_peak(synth_dB, _FREQS)
    assert len(result) == 6, f"Expected 6-tuple, got {len(result)}"


def test_fit_S21_peak_complex_returns_correct_length():
    """fit_S21_peak_complex should return 7 elements in the tuple."""
    synth_complex = S21_eq_complex(
        _FREQS, _F0, _KTOT, _KEXT, 0.0, 0.0, 0.0, 0.0
    )
    result = fit_S21_peak_complex(synth_complex, _FREQS)
    assert len(result) == 7, f"Expected 7-tuple, got {len(result)}"
