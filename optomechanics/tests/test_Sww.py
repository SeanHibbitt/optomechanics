"""Unit tests for data_analysis/fitting/Sww.py equation functions."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_analysis.fitting.Sww import (
    basic_S_ww_eq, basic_S_ww_eq_2, dBm_basic_S_ww_eq,
    S_ff_thermal, SHO_TF_sq, S_xx_thermal,
)
from optomechanics.data_analysis.fitting._fitting import k_b
from optomechanics.data_analysis.unit_conversions import watts_to_dBm

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


# ---------------------------------------------------------------------------
# basic_S_ww_eq_2 tests (full susceptibility form)
# ---------------------------------------------------------------------------

def test_basic_Sww2_peak_at_resonance():
    """basic_S_ww_eq_2 should peak at f_m."""
    f_m = 1e6; G_m = 1e3; A = 1.0; nf = 0.0
    freqs = np.array([f_m - 1e4, f_m, f_m + 1e4])
    result = basic_S_ww_eq_2(freqs, f_m, G_m, A, nf)
    assert result[1] > result[0] and result[1] > result[2]


def test_basic_Sww2_noise_floor():
    """Far from resonance basic_S_ww_eq_2 should approach nf."""
    f_m = 1e6; G_m = 1e3; A = 1.0; nf = 0.5
    result = basic_S_ww_eq_2(np.array([f_m + 1e9]), f_m, G_m, A, nf)
    assert_allclose(result[0], nf, atol=1e-6)


def test_basic_Sww2_on_resonance_value():
    """Check analytic on-resonance value of basic_S_ww_eq_2."""
    f_m = 1e6; G_m = 1e3; A = 1.0; nf = 0.0
    w_m = f_m * 2 * np.pi
    G_ang = G_m * 2 * np.pi
    # On resonance: |1/(f^2 - f_m^2 + j*G_m*f)|^2 at f=f_m
    # denominator = (0 + j*G_ang*w_m), so |...|^2 = 1/(G_ang*w_m)^2
    expected = A / (G_ang * w_m) ** 2
    result = basic_S_ww_eq_2(np.array([f_m]), f_m, G_m, A, nf)
    assert_allclose(result[0], expected, rtol=1e-10)


def test_basic_Sww2_symmetric_near_resonance():
    """basic_S_ww_eq_2 should be approximately symmetric near resonance for high Q."""
    f_m = 1e6; G_m = 10; A = 1.0; nf = 0.0
    df = 50  # small offset
    r_low = basic_S_ww_eq_2(np.array([f_m - df]), f_m, G_m, A, nf)[0]
    r_high = basic_S_ww_eq_2(np.array([f_m + df]), f_m, G_m, A, nf)[0]
    # Not exactly symmetric (unlike Lorentzian approx), but very close for high Q
    assert_allclose(r_low, r_high, rtol=0.01)


# ---------------------------------------------------------------------------
# dBm_basic_S_ww_eq tests
# ---------------------------------------------------------------------------

def test_dBm_basic_Sww_is_dBm_of_linear():
    """dBm_basic_S_ww_eq should equal watts_to_dBm(basic_S_ww_eq(...))."""
    f_m = 1e6; G_m = 1e3; A = 1e-10; nf = 1e-12
    freqs = np.linspace(f_m - 5e3, f_m + 5e3, 50)
    linear = basic_S_ww_eq(freqs, f_m, G_m, A, nf)
    dBm_result = dBm_basic_S_ww_eq(freqs, f_m, G_m, A, nf)
    expected_dBm = watts_to_dBm(linear)
    assert_allclose(dBm_result, expected_dBm, rtol=1e-10)


def test_dBm_basic_Sww_peak_at_resonance():
    """dBm output should also peak at resonance."""
    f_m = 1e6; G_m = 1e3; A = 1e-10; nf = 1e-12
    freqs = np.array([f_m - 1e4, f_m, f_m + 1e4])
    result = dBm_basic_S_ww_eq(freqs, f_m, G_m, A, nf)
    assert result[1] > result[0] and result[1] > result[2]


# ---------------------------------------------------------------------------
# S_ff_thermal tests
# ---------------------------------------------------------------------------

def test_S_ff_thermal_formula():
    """S_ff_thermal should return 4 * k_B * T * m_eff * gamma_m (in angular)."""
    T = 300.0; m_eff = 1e-12; G_m = 100.0
    G_m_ang = G_m * 2 * np.pi
    expected = 4 * k_b * T * m_eff * G_m_ang
    freqs = np.array([1e6, 2e6, 3e6])
    result = S_ff_thermal(freqs, m_eff, G_m, T)
    # Should be flat (same value at all frequencies)
    assert_allclose(result, expected, rtol=1e-12)


def test_S_ff_thermal_flat_spectrum():
    """S_ff_thermal should be frequency-independent."""
    T = 300.0; m_eff = 1e-12; G_m = 100.0
    freqs = np.linspace(1e3, 1e7, 100)
    result = S_ff_thermal(freqs, m_eff, G_m, T)
    assert_allclose(result, result[0], rtol=1e-15)


def test_S_ff_thermal_scales_with_temperature():
    """Doubling T should double S_ff."""
    m_eff = 1e-12; G_m = 100.0
    freqs = np.array([1e6])
    r1 = S_ff_thermal(freqs, m_eff, G_m, 300.0)[0]
    r2 = S_ff_thermal(freqs, m_eff, G_m, 600.0)[0]
    assert_allclose(r2 / r1, 2.0, rtol=1e-12)


def test_S_ff_thermal_zero_temperature():
    """At T=0, S_ff should be zero."""
    freqs = np.array([1e6])
    result = S_ff_thermal(freqs, 1e-12, 100.0, 0.0)
    assert_allclose(result[0], 0.0, atol=1e-50)


# ---------------------------------------------------------------------------
# SHO_TF_sq tests
# ---------------------------------------------------------------------------

def test_SHO_TF_sq_on_resonance():
    """On resonance, SHO_TF_sq should equal 1/(m^2 * w_m^2 * G_m_ang^2)."""
    f_m = 1e6; G_m = 100.0; m_eff = 1e-12
    w_m = f_m * 2 * np.pi
    G_ang = G_m * 2 * np.pi
    expected = 1.0 / (m_eff**2 * w_m**2 * G_ang**2)
    result = SHO_TF_sq(np.array([f_m]), m_eff, f_m, G_m)
    assert_allclose(result[0], expected, rtol=1e-10)


def test_SHO_TF_sq_decreases_off_resonance():
    """SHO_TF_sq should be maximal at resonance."""
    f_m = 1e6; G_m = 100.0; m_eff = 1e-12
    freqs = np.array([f_m - 1e4, f_m, f_m + 1e4])
    result = SHO_TF_sq(freqs, m_eff, f_m, G_m)
    assert result[1] > result[0] and result[1] > result[2]


def test_SHO_TF_sq_far_off_resonance():
    """Far from resonance, SHO_TF_sq should be very small."""
    f_m = 1e6; G_m = 100.0; m_eff = 1e-12
    on_res = SHO_TF_sq(np.array([f_m]), m_eff, f_m, G_m)[0]
    far_off = SHO_TF_sq(np.array([f_m + 1e8]), m_eff, f_m, G_m)[0]
    assert far_off < on_res * 1e-6


def test_SHO_TF_sq_scales_with_mass():
    """Doubling mass should reduce TF_sq by factor of 4 (m^2 in denominator)."""
    f_m = 1e6; G_m = 100.0
    r1 = SHO_TF_sq(np.array([f_m]), 1e-12, f_m, G_m)[0]
    r2 = SHO_TF_sq(np.array([f_m]), 2e-12, f_m, G_m)[0]
    assert_allclose(r1 / r2, 4.0, rtol=1e-10)


# ---------------------------------------------------------------------------
# S_xx_thermal tests
# ---------------------------------------------------------------------------

def test_S_xx_thermal_equals_product():
    """S_xx_thermal should equal SHO_TF_sq * S_ff_thermal."""
    f_m = 1e6; G_m = 100.0; m_eff = 1e-12; T = 300.0
    freqs = np.linspace(f_m - 5e3, f_m + 5e3, 100)
    result = S_xx_thermal(freqs, m_eff, T, f_m, G_m)
    expected = SHO_TF_sq(freqs, m_eff, f_m, G_m) * S_ff_thermal(freqs, m_eff, G_m, T)
    assert_allclose(result, expected, rtol=1e-12)


def test_S_xx_thermal_peaks_at_resonance():
    """S_xx_thermal should peak at f_m."""
    f_m = 1e6; G_m = 100.0; m_eff = 1e-12; T = 300.0
    freqs = np.array([f_m - 1e4, f_m, f_m + 1e4])
    result = S_xx_thermal(freqs, m_eff, T, f_m, G_m)
    assert result[1] > result[0] and result[1] > result[2]


def test_S_xx_thermal_on_resonance_value():
    """Check analytic on-resonance value of S_xx_thermal."""
    f_m = 1e6; G_m = 100.0; m_eff = 1e-12; T = 300.0
    w_m = f_m * 2 * np.pi
    G_ang = G_m * 2 * np.pi
    # S_xx(f_m) = [1/(m^2 * w_m^2 * G_ang^2)] * [4*k_b*T*m*G_ang]
    #           = 4*k_b*T / (m * w_m^2 * G_ang)
    expected = 4 * k_b * T / (m_eff * w_m**2 * G_ang)
    result = S_xx_thermal(np.array([f_m]), m_eff, T, f_m, G_m)
    assert_allclose(result[0], expected, rtol=1e-10)


def test_S_xx_thermal_zero_temperature():
    """At T=0, S_xx_thermal should be zero everywhere."""
    f_m = 1e6; G_m = 100.0; m_eff = 1e-12
    freqs = np.linspace(f_m - 5e3, f_m + 5e3, 50)
    result = S_xx_thermal(freqs, m_eff, 0.0, f_m, G_m)
    assert_allclose(result, 0.0, atol=1e-50)
