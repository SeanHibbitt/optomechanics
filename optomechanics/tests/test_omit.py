"""
Unit tests for optomechanics.data_analysis.fitting.omit.

Test parameters represent a physically plausible room-temperature microwave
optomechanical system:

- F_M = 1 MHz mechanical frequency (typical for SiN membrane)
- G_M = 10 Hz mechanical linewidth (Q ~ 1e5, room-temperature Q)
- KK_TOT = 1 MHz cavity linewidth (resolved-sideband regime: kk_tot ≈ f_m)
- A = 1e10 chosen to give a clearly visible peak above FLOOR = 1.0 at the
  given kk_tot. The OMIT denominator scales as ~omega_m^2 * kappa ~
  (2π × 1e6)^2 × (2π × 1e6) ~ 1e19 (rad/s)^3, so A ~ 1e10 produces a
  peak height of order 1 above the floor.
- FLOOR = 1.0 normalised background transmission (linear voltage).

Test data files (in tests/data/):
- omit_test_vector_peak.npz: OMIT peak (A > 0), 1001 points, 0.95–1.05 MHz
- omit_test_vector_dip.npz:  OMIA dip  (A < 0), same frequency range
See tests/data/README.md for file format and regeneration instructions.
"""
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose

from optomechanics.data_analysis.fitting.omit import (
    OMIT_equation,
    fit_OMIT,
    fit_OMIT_set_floor,
)
from optomechanics.data_analysis.unit_conversions import linear_voltage_to_dB

DATA_DIR = Path(__file__).parent / "data"


# Test parameters (physically plausible values)
F_M = 1e6       # 1 MHz mechanical frequency
G_M = 10.0      # 10 Hz mechanical linewidth
A = 1e10        # amplitude parameter
FLOOR = 1.0     # background floor (linear voltage)
KK_TOT = 1e6    # total optical linewidth 1 MHz


def test_OMIT_output_shape():
    """Output array shape should match input frequency array shape."""
    f = np.linspace(0.9e6, 1.1e6, 500)
    result = OMIT_equation(f, F_M, G_M, A, FLOOR, KK_TOT)
    assert result.shape == f.shape


def test_OMIT_all_positive():
    """OMIT transmission amplitude should be positive everywhere
    when floor > 0 and A > 0."""
    f = np.linspace(0.5e6, 1.5e6, 1000)
    result = OMIT_equation(f, F_M, G_M, A, FLOOR, KK_TOT)
    assert np.all(result > 0)


def test_OMIT_peak_near_resonance():
    """The maximum of the OMIT lineshape should be near f_m."""
    f = np.linspace(0.99e6, 1.01e6, 10000)
    result = OMIT_equation(f, F_M, G_M, A, FLOOR, KK_TOT)
    peak_freq = f[np.argmax(result)]
    # Peak should be within a few linewidths of f_m
    assert abs(peak_freq - F_M) < 10 * G_M


def test_OMIT_floor_scales_output():
    """Doubling the floor should double the output everywhere."""
    f = np.linspace(0.9e6, 1.1e6, 200)
    result1 = OMIT_equation(f, F_M, G_M, A, FLOOR, KK_TOT)
    result2 = OMIT_equation(f, F_M, G_M, A, 2.0 * FLOOR, KK_TOT)
    assert_allclose(result2, 2.0 * result1, rtol=1e-10)


def test_OMIT_far_off_resonance_approaches_floor():
    """Far from resonance the denominator is large, so OMIT -> floor."""
    f_far = np.array([1e9])  # 1 GHz, far from 1 MHz resonance
    result = OMIT_equation(f_far, F_M, G_M, A, FLOOR, KK_TOT)
    # The 1/denominator term should be negligible at this detuning
    assert_allclose(result[0], FLOOR, rtol=0.01)


def test_OMIT_zero_amplitude_gives_floor():
    """With A=0 the OMIT equation should return floor everywhere."""
    f = np.linspace(0.9e6, 1.1e6, 200)
    result = OMIT_equation(f, F_M, G_M, A=0.0, floor=FLOOR, kk_tot=KK_TOT)
    assert_allclose(result, FLOOR, rtol=1e-12)


def test_OMIT_larger_A_gives_taller_peak():
    """Increasing A should increase the peak height."""
    f = np.linspace(0.99e6, 1.01e6, 1000)
    peak1 = np.max(OMIT_equation(f, F_M, G_M, A=1e10, floor=FLOOR, kk_tot=KK_TOT))
    peak2 = np.max(OMIT_equation(f, F_M, G_M, A=2e10, floor=FLOOR, kk_tot=KK_TOT))
    assert peak2 > peak1


def test_OMIT_wider_linewidth_gives_broader_peak():
    """A larger mechanical linewidth g_m should produce a broader peak."""
    f = np.linspace(0.99e6, 1.01e6, 10000)
    result_narrow = OMIT_equation(f, F_M, g_m=10.0, A=A, floor=FLOOR, kk_tot=KK_TOT)
    result_wide = OMIT_equation(f, F_M, g_m=100.0, A=A, floor=FLOOR, kk_tot=KK_TOT)

    # FWHM proxy: count how many points are above half-max
    def fwhm_count(r):
        half_max = (np.max(r) + np.min(r)) / 2
        return np.sum(r > half_max)

    assert fwhm_count(result_wide) > fwhm_count(result_narrow)


# ---------------------------------------------------------------------------
# Exact-value regression tests (snapshot fixtures)
# ---------------------------------------------------------------------------

def test_OMIT_equation_exact_values_peak():
    """OMIT_equation must reproduce the pre-computed OMIT peak test vector.

    The .npz file is a frozen snapshot committed to git.  This test detects
    any future regression that changes OMIT_equation output.
    """
    data = np.load(DATA_DIR / "omit_test_vector_peak.npz")
    result = OMIT_equation(
        data["freqs"],
        float(data["f_m"]),
        float(data["g_m"]),
        float(data["A"]),
        float(data["floor"]),
        float(data["kk_tot"]),
    )
    assert_allclose(result, data["transmission"], rtol=1e-12,
                    err_msg="OMIT peak does not match pre-computed test vector")


def test_OMIT_equation_exact_values_dip():
    """OMIT_equation must reproduce the pre-computed OMIA dip test vector."""
    data = np.load(DATA_DIR / "omit_test_vector_dip.npz")
    result = OMIT_equation(
        data["freqs"],
        float(data["f_m"]),
        float(data["g_m"]),
        float(data["A"]),
        float(data["floor"]),
        float(data["kk_tot"]),
    )
    assert_allclose(result, data["transmission"], rtol=1e-12,
                    err_msg="OMIA dip does not match pre-computed test vector")


# ---------------------------------------------------------------------------
# Analytic property tests (non-circular — derived from the equation directly)
# ---------------------------------------------------------------------------

def test_OMIT_equation_analytic_floor_limit():
    """At A=0 the equation reduces exactly to floor (analytic identity).

    OMIT = floor * (1 + 0 * |1/denom|) = floor.  This is independent of
    frequency, linewidth, or kk_tot and does not rely on the .npz fixtures.
    """
    f = np.linspace(0.5e6, 1.5e6, 500)
    result = OMIT_equation(f, F_M, G_M, A=0.0, floor=FLOOR, kk_tot=KK_TOT)
    assert_allclose(result, FLOOR, rtol=1e-12)


def test_OMIT_negative_A_produces_dip():
    """Negative A should produce an absorption dip below floor (OMIA)."""
    f = np.linspace(0.99e6, 1.01e6, 1000)
    result = OMIT_equation(f, F_M, G_M, A=-1e10, floor=FLOOR, kk_tot=KK_TOT)
    assert np.min(result) < FLOOR, "OMIA dip should go below floor"
    dip_freq = f[np.argmin(result)]
    assert abs(dip_freq - F_M) < 10 * G_M, "OMIA dip should be near f_m"


def test_OMIT_negative_A_is_mirror_of_positive():
    """OMIA dip depth should equal OMIT peak height (relative to floor).

    This follows directly from the equation: substituting -A for +A negates
    the correction term, so the deviation from floor has the same magnitude.
    """
    f = np.linspace(0.99e6, 1.01e6, 1000)
    peak = OMIT_equation(f, F_M, G_M, A=1e10, floor=FLOOR, kk_tot=KK_TOT)
    dip = OMIT_equation(f, F_M, G_M, A=-1e10, floor=FLOOR, kk_tot=KK_TOT)
    peak_height = np.max(peak) - FLOOR
    dip_depth = FLOOR - np.min(dip)
    assert_allclose(peak_height, dip_depth, rtol=1e-9,
                    err_msg="OMIT peak and OMIA dip should be symmetric about floor")


# ---------------------------------------------------------------------------
# Fitting round-trip tests
# ---------------------------------------------------------------------------

def test_fit_OMIT_recovers_known_parameters():
    """Generate clean OMIT data, fit with explicit guesses, verify recovery."""
    freqs = np.linspace(0.95e6, 1.05e6, 1001)
    true_params = [1e6, 10.0, 1e10, 1.0]  # f_m, g_m, A, floor
    kk_tot = 1e6

    clean = OMIT_equation(freqs, *true_params, kk_tot)
    clean_dB = linear_voltage_to_dB(clean)

    popt, pcov, lin_data, guesses_out = fit_OMIT(
        freqs, clean_dB, kk_tot, floor=1.0,
        guesses=[1e6, 10.0, 1e10, 1.0],
    )

    assert_allclose(popt[0], true_params[0], rtol=0.01, err_msg="f_m not recovered")
    assert_allclose(popt[1], true_params[1], rtol=0.01, err_msg="g_m not recovered")
    assert_allclose(popt[2], true_params[2], rtol=0.01, err_msg="A not recovered")
    assert_allclose(popt[3], true_params[3], rtol=0.01, err_msg="floor not recovered")


def test_fit_OMIT_set_floor_recovers_known_parameters():
    """Generate clean OMIT data, fit with fixed floor, verify recovery."""
    freqs = np.linspace(0.95e6, 1.05e6, 1001)
    true_params = [1e6, 10.0, 1e10]  # f_m, g_m, A (floor fixed)
    kk_tot = 1e6
    floor = 1.0

    clean = OMIT_equation(freqs, *true_params, floor, kk_tot)
    clean_dB = linear_voltage_to_dB(clean)

    popt, pcov, lin_data, guesses_out = fit_OMIT_set_floor(
        freqs, clean_dB, kk_tot, floor=floor,
        guesses=[1e6, 10.0, 1e10],
    )

    assert_allclose(popt[0], true_params[0], rtol=0.01, err_msg="f_m not recovered")
    assert_allclose(popt[1], true_params[1], rtol=0.01, err_msg="g_m not recovered")
    assert_allclose(popt[2], true_params[2], rtol=0.01, err_msg="A not recovered")


def test_fit_OMIT_auto_guess():
    """fit_OMIT with default guesses=False should auto-detect parameters."""
    freqs = np.linspace(0.95e6, 1.05e6, 1001)
    true_params = [1e6, 10.0, 1e10, 1.0]
    kk_tot = 1e6

    clean = OMIT_equation(freqs, *true_params, kk_tot)
    clean_dB = linear_voltage_to_dB(clean)

    # guesses=False is the default — uses auto-guessing logic
    popt, pcov, lin_data, guesses_out = fit_OMIT(
        freqs, clean_dB, kk_tot, floor=1.0,
    )

    assert_allclose(popt[0], true_params[0], rtol=0.05,
                    err_msg="f_m not recovered via auto-guess")
