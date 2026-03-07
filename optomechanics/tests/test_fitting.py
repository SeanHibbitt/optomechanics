"""Unit tests for data_analysis/fitting/_fitting.py functions."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_analysis.fitting._fitting import (
    ring_down_eq, tau_to_Q, line_eq, fit_ring_down, fit_linear,
)


# ---------------------------------------------------------------------------
# ring_down_eq
# ---------------------------------------------------------------------------

def test_ring_down_eq_at_t_zero():
    """At t=0 the exponential is 1, so result should be A_0 + V_0."""
    result = ring_down_eq(0.0, A_0=5.0, tau=1.0, V_0=2.0)
    assert_allclose(result, 7.0, rtol=1e-12)


def test_ring_down_eq_at_t_tau():
    """At t=tau the exponential is exp(-1), so result = A_0*exp(-1) + V_0."""
    tau = 2.0
    result = ring_down_eq(tau, A_0=5.0, tau=tau, V_0=2.0)
    expected = 5.0 * np.exp(-1) + 2.0
    assert_allclose(result, expected, rtol=1e-12)


def test_ring_down_eq_large_t():
    """For t >> tau the exponential decays to zero; result approaches V_0."""
    result = ring_down_eq(1e6, A_0=5.0, tau=1.0, V_0=3.0)
    assert_allclose(result, 3.0, atol=1e-10)


def test_ring_down_eq_array_input():
    """Verify the function works on numpy arrays and returns correct shape."""
    t = np.array([0.0, 1.0, 2.0, 3.0])
    result = ring_down_eq(t, A_0=1.0, tau=1.0, V_0=0.0)
    expected = np.exp(-t)
    assert result.shape == t.shape
    assert_allclose(result, expected, rtol=1e-12)


# ---------------------------------------------------------------------------
# tau_to_Q
# ---------------------------------------------------------------------------

def test_tau_to_Q_known_value():
    """Q = pi * f_m * tau. Check with simple values."""
    Q = tau_to_Q(tau=1.0, f_m=100.0)
    expected = np.pi * 100.0
    assert_allclose(Q, expected, rtol=1e-12)


def test_tau_to_Q_realistic():
    """Check with physically realistic values (f_m ~ MHz, Q ~ 1e6)."""
    f_m = 1e6  # 1 MHz
    tau = 1.0  # 1 second
    Q = tau_to_Q(tau, f_m)
    expected = np.pi * 1e6
    assert_allclose(Q, expected, rtol=1e-12)


# ---------------------------------------------------------------------------
# line_eq
# ---------------------------------------------------------------------------

def test_line_eq_slope_and_intercept():
    """y = 2*x + 3 at x=5 should give 13."""
    result = line_eq(5.0, m=2.0, c=3.0)
    assert_allclose(result, 13.0, rtol=1e-12)


def test_line_eq_zero_slope():
    """Flat line y = 0*x + 7 should give 7 everywhere."""
    x = np.array([0, 1, 100, -50])
    result = line_eq(x, m=0.0, c=7.0)
    assert_allclose(result, 7.0, rtol=1e-12)


def test_line_eq_array_input():
    """Verify array output matches m*x + c element-wise."""
    x = np.linspace(-10, 10, 50)
    result = line_eq(x, m=-3.0, c=1.5)
    expected = -3.0 * x + 1.5
    assert_allclose(result, expected, rtol=1e-12)


# ---------------------------------------------------------------------------
# fit_ring_down  (synthetic data recovery)
# ---------------------------------------------------------------------------

def test_fit_ring_down_recovers_parameters():
    """Generate clean ring-down data and verify fit recovers A_0, tau, V_0."""
    A_0_true, tau_true, V_0_true = 10.0, 0.5, 1.0
    t = np.linspace(0, 5 * tau_true, 500)
    y = ring_down_eq(t, A_0_true, tau_true, V_0_true)

    popt, pcov, guesses = fit_ring_down(t, y)
    assert_allclose(popt[0], A_0_true, rtol=1e-3)
    assert_allclose(popt[1], tau_true, rtol=1e-3)
    assert_allclose(popt[2], V_0_true, atol=1e-3)


def test_fit_ring_down_noisy_data():
    """Fit should still recover parameters within tolerance on noisy data."""
    rng = np.random.default_rng(42)
    A_0_true, tau_true, V_0_true = 8.0, 1.0, 0.5
    t = np.linspace(0, 5 * tau_true, 1000)
    y = ring_down_eq(t, A_0_true, tau_true, V_0_true)
    y_noisy = y + rng.normal(0, 0.05, size=y.shape)

    popt, pcov, guesses = fit_ring_down(t, y_noisy)
    assert_allclose(popt[0], A_0_true, rtol=0.1)
    assert_allclose(popt[1], tau_true, rtol=0.1)
    assert_allclose(popt[2], V_0_true, atol=0.2)


# ---------------------------------------------------------------------------
# fit_linear  (synthetic data recovery)
# ---------------------------------------------------------------------------

def test_fit_linear_recovers_parameters():
    """Generate clean linear data and verify fit recovers m and c."""
    m_true, c_true = 2.5, -1.0
    x = np.linspace(0, 10, 100)
    y = line_eq(x, m_true, c_true)

    popt, pcov = fit_linear(x, y)
    assert_allclose(popt[0], m_true, rtol=1e-6)
    assert_allclose(popt[1], c_true, atol=1e-6)


def test_fit_linear_noisy_data():
    """Fit should recover parameters within tolerance on noisy data."""
    rng = np.random.default_rng(123)
    m_true, c_true = -0.3, 5.0
    x = np.linspace(0, 20, 200)
    y = line_eq(x, m_true, c_true) + rng.normal(0, 0.1, size=x.shape)

    popt, pcov = fit_linear(x, y)
    assert_allclose(popt[0], m_true, atol=0.05)
    assert_allclose(popt[1], c_true, atol=0.2)


def test_fit_linear_with_errors():
    """Fit with explicit error bars should still converge."""
    m_true, c_true = 1.0, 0.0
    x = np.linspace(0, 10, 50)
    y = line_eq(x, m_true, c_true)
    errors = np.ones_like(x) * 0.5

    popt, pcov = fit_linear(x, y, errors=errors)
    assert_allclose(popt[0], m_true, rtol=1e-6)
    assert_allclose(popt[1], c_true, atol=1e-6)
