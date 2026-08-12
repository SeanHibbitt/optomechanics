"""Unit tests for data_analysis/misc_equations.py."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_analysis.misc_equations import photon_number

# photon_number(f_d, f_c, k_extHz, k_totHz, P_in)
# numerator = 2*k_ext*P_in  (angular)
# denominator = hbar*w_c * (k_tot^2 + 4*(w_d-w_c)^2)

def test_photon_number_on_resonance_known():
    # On resonance: f_d==f_c, so (w_d-w_c)=0
    # n = 2*k_ext*P_in / (hbar*w_c*k_tot^2) (angular units cancel 2pi)
    h_bar = 1.054571817e-34
    f_c = 1e9
    k_ext = 1e6
    k_tot = 2e6
    P_in = 1e-12
    w_c = f_c * 2 * np.pi
    k_ext_ang = k_ext * 2 * np.pi
    k_tot_ang = k_tot * 2 * np.pi
    expected = (2 * k_ext_ang * P_in) / (h_bar * w_c * k_tot_ang**2)
    result = photon_number(f_c, f_c, k_ext, k_tot, P_in)
    assert_allclose(result, expected, rtol=1e-10)

def test_photon_number_off_resonance_lower_than_on():
    f_c = 1e9
    k_ext = 1e6
    k_tot = 2e6
    P_in = 1e-12
    n_on = photon_number(f_c, f_c, k_ext, k_tot, P_in)
    n_off = photon_number(f_c + 10e6, f_c, k_ext, k_tot, P_in)
    assert n_off < n_on

def test_photon_number_scales_linearly_with_power():
    f_c = 1e9
    k_ext = 1e6
    k_tot = 2e6
    P1 = 1e-12
    P2 = 2e-12
    n1 = photon_number(f_c, f_c, k_ext, k_tot, P1)
    n2 = photon_number(f_c, f_c, k_ext, k_tot, P2)
    assert_allclose(n2 / n1, 2.0, rtol=1e-12)

def test_photon_number_positive():
    result = photon_number(1e9, 1e9, 1e6, 2e6, 1e-12)
    assert result > 0
