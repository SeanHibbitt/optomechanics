"""Unit tests for data_management/data_management.py."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_management.data_management import attenuation_object

def make_flat(mag, freqs):
    return attenuation_object(np.full(len(freqs), mag), np.array(freqs, dtype=float))

def test_attenuation_object_init_stores_values():
    freqs = np.array([1e9, 2e9, 3e9])
    mag = np.array([1.0, 2.0, 3.0])
    a = attenuation_object(mag, freqs)
    assert_allclose(a.magnitude, mag)
    assert_allclose(a.frequencies, freqs)

def test_attenuation_object_no_errors_has_error_false():
    a = make_flat(5.0, [1e9, 2e9])
    assert a.has_error == False

def test_attenuation_object_with_errors_has_error_true():
    freqs = np.array([1e9, 2e9])
    mag = np.array([1.0, 2.0])
    a = attenuation_object(mag, freqs, np.array([0.1, 0.1]), np.array([0.1, 0.1]))
    assert a.has_error == True

def test_attenuation_object_call_returns_mag_and_freqs():
    freqs = np.array([1e9, 2e9, 3e9])
    mag = np.array([1.0, 2.0, 3.0])
    a = attenuation_object(mag, freqs)
    returned_mag, returned_freqs = a()
    assert_allclose(returned_mag, mag)
    assert_allclose(returned_freqs, freqs)

def test_attenuation_object_add_same_frequencies():
    freqs = np.array([1e9, 2e9, 3e9])
    a = make_flat(3.0, freqs)
    b = make_flat(2.0, freqs)
    c = a + b
    assert_allclose(c.magnitude, np.full(3, 5.0), rtol=1e-12)
    assert_allclose(c.frequencies, freqs)

def test_attenuation_object_add_scalar_interpolation():
    # b has single frequency, should be interpolated to a frequencies
    freqs_a = np.array([1e9, 2e9, 3e9])
    a = make_flat(10.0, freqs_a)
    b = attenuation_object(np.array([5.0]), np.array([1e9]))
    c = a + b
    assert_allclose(c.magnitude, np.full(3, 15.0), rtol=1e-12)

def test_attenuation_object_sub_same_frequencies():
    freqs = np.array([1e9, 2e9, 3e9])
    a = make_flat(10.0, freqs)
    b = make_flat(3.0, freqs)
    c = a - b
    assert_allclose(c.magnitude, np.full(3, 7.0), rtol=1e-12)

def test_attenuation_object_add_preserves_frequencies():
    freqs = np.array([1e9, 2e9, 3e9])
    a = make_flat(1.0, freqs)
    b = make_flat(1.0, freqs)
    c = a + b
    assert_allclose(c.frequencies, freqs)

def test_attenuation_object_add_error_propagation_quadrature():
    freqs = np.array([1e9, 2e9])
    mag = np.array([0.0, 0.0])
    err = np.array([3.0, 3.0])
    a = attenuation_object(mag, freqs, err, err)
    b = attenuation_object(mag, freqs, err, err)
    c = a + b
    # quadrature: sqrt(3^2+3^2)=3*sqrt(2)
    expected_err = 3.0 * np.sqrt(2)
    assert_allclose(c.upper_error, np.full(2, expected_err), rtol=1e-10)
    assert_allclose(c.lower_error, np.full(2, expected_err), rtol=1e-10)

def test_attenuation_object_freq_len_multi():
    freqs = np.array([1e9, 3e9])
    a = make_flat(0.0, freqs)
    assert_allclose(a.freq_len, 2e9, rtol=1e-12)

def test_attenuation_object_freq_len_single():
    a = attenuation_object(np.array([1.0]), np.array([5e9]))
    assert a.freq_len == 1
