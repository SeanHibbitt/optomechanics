"""Unit tests for data_analysis/fitting/Sww.py equation functions."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_analysis.fitting.Sww import basic_S_ww_eq

# basic_S_ww_eq(freqs, omega_m, G_m, A, nf)
# S_ww = A / (G_m_ang^2 + 4*(freqs_ang - omega_m_ang)^2) + nf

def test_basic_Sww_on_resonance():
    omega_m = 1e6; G_m = 1e3; A = 1.0; nf = 0.0
    G_ang = G_m * 2 * np.pi
    expected = A / G_ang**2
    result = basic_S_ww_eq(np.array([omega_m]), omega_m, G_m, A, nf)
    assert_allclose(result[0], expected, rtol=1e-10)

def test_basic_Sww_noise_floor():
    # Far off resonance the Lorentzian contribution vanishes, result -> nf
    omega_m = 1e6; G_m = 1e3; A = 1.0; nf = 0.5
    result = basic_S_ww_eq(np.array([omega_m + 1e9]), omega_m, G_m, A, nf)
    assert_allclose(result[0], nf, atol=1e-6)

def test_basic_Sww_peak_at_resonance():
    omega_m = 1e6; G_m = 1e3; A = 1.0; nf = 0.0
    freqs = np.array([omega_m - 1e4, omega_m, omega_m + 1e4])
    result = basic_S_ww_eq(freqs, omega_m, G_m, A, nf)
    assert result[1] > result[0] and result[1] > result[2]

def test_basic_Sww_scales_with_amplitude():
    omega_m = 1e6; G_m = 1e3; nf = 0.0
    r1 = basic_S_ww_eq(np.array([omega_m]), omega_m, G_m, 1.0, nf)[0]
    r2 = basic_S_ww_eq(np.array([omega_m]), omega_m, G_m, 2.0, nf)[0]
    assert_allclose(r2 / r1, 2.0, rtol=1e-12)

def test_basic_Sww_symmetric_about_resonance():
    omega_m = 1e6; G_m = 1e3; A = 1.0; nf = 0.0
    df = 5e3
    r_low = basic_S_ww_eq(np.array([omega_m - df]), omega_m, G_m, A, nf)[0]
    r_high = basic_S_ww_eq(np.array([omega_m + df]), omega_m, G_m, A, nf)[0]
    assert_allclose(r_low, r_high, rtol=1e-12)

def test_basic_Sww_nf_additive():
    omega_m = 1e6; G_m = 1e3; A = 1.0
    r0 = basic_S_ww_eq(np.array([omega_m]), omega_m, G_m, A, 0.0)[0]
    r1 = basic_S_ww_eq(np.array([omega_m]), omega_m, G_m, A, 1.0)[0]
    assert_allclose(r1 - r0, 1.0, rtol=1e-12)
