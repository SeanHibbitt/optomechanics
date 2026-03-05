"""Unit tests for data_analysis/fitting/S21.py equation functions."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_analysis.fitting.S21 import S21_eq, S21_eq_dB, S21_eq_phase, S21_eq_complex

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
