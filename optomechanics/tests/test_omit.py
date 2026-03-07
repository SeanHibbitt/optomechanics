"""Unit tests for data_analysis/fitting/omit.py OMIT_equation function."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_analysis.fitting.omit import OMIT_equation


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
