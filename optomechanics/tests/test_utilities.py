"""Unit tests for data_analysis/utilities.py."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from optomechanics.data_analysis.utilities import find_closest_number, convert_error_dB_to_linear, convert_error_linear_to_dB, split_complex, split_complex_wrapper, complex_to_mag_phase

def test_find_closest_exact():
    arr = [1.0, 2.0, 3.0, 4.0]
    assert find_closest_number(arr, 3.0) == 2

def test_find_closest_between_values():
    arr = [0.0, 1.0, 3.0, 10.0]
    assert find_closest_number(arr, 2.0) == 1

def test_find_closest_single_element():
    assert find_closest_number([42.0], 0.0) == 0

def test_find_closest_negative():
    arr = [-5.0, -1.0, 0.0, 2.0]
    assert find_closest_number(arr, -0.4) == 2

def test_convert_error_dB_to_linear_zero_error():
    val_linear, upper, lower = convert_error_dB_to_linear(0.0, 0.0, 0.0)
    assert_allclose(val_linear, 1.0, rtol=1e-12)
    assert_allclose(upper, 0.0, atol=1e-12)
    assert_allclose(lower, 0.0, atol=1e-12)

def test_convert_error_dB_to_linear_known():
    # value=20dB -> linear=10; upper_error=0dB->0 linear diff; lower_error same
    val_linear, upper, lower = convert_error_dB_to_linear(20.0, 0.0, 0.0)
    assert_allclose(val_linear, 10.0, rtol=1e-10)

def test_convert_error_dB_to_linear_asymmetric():
    # value=0dB=1 linear; upper_err=20dB => upper_val=20dB=10 => upper_error_linear=10-1=9
    val, upper, lower = convert_error_dB_to_linear(0.0, 20.0, 0.0)
    assert_allclose(val, 1.0, rtol=1e-12)
    assert_allclose(upper, 9.0, rtol=1e-10)

def test_convert_error_linear_to_dB_zero_error():
    val_dB, upper, lower = convert_error_linear_to_dB(1.0, 0.0, 0.0)
    assert_allclose(val_dB, 0.0, atol=1e-12)
    assert_allclose(upper, 0.0, atol=1e-12)

def test_convert_error_linear_to_dB_known():
    val_dB, upper, lower = convert_error_linear_to_dB(10.0, 0.0, 0.0)
    assert_allclose(val_dB, 20.0, rtol=1e-10)

def test_convert_error_roundtrip():
    # Convert to linear then back to dB should recover original
    original_dB = 6.0
    original_upper = 2.0
    original_lower = 1.0
    val_lin, up_lin, lo_lin = convert_error_dB_to_linear(original_dB, original_upper, original_lower)
    val_dB, up_dB, lo_dB = convert_error_linear_to_dB(val_lin, up_lin, abs(lo_lin))
    assert_allclose(val_dB, original_dB, rtol=1e-10)
    assert_allclose(up_dB, original_upper, rtol=1e-10)
    assert_allclose(lo_dB, original_lower, rtol=1e-10)

def test_split_complex_concatenates():
    data = np.array([1+2j, 3+4j])
    result = split_complex(data)
    assert_allclose(result, [1.0, 3.0, 2.0, 4.0], atol=1e-12)

def test_split_complex_pure_real():
    data = np.array([5.0+0j, 6.0+0j])
    result = split_complex(data)
    assert_allclose(result[:2], [5.0, 6.0], atol=1e-12)
    assert_allclose(result[2:], [0.0, 0.0], atol=1e-12)

def test_split_complex_wrapper_matches_split_complex():
    def identity(x):
        return x
    wrapped = split_complex_wrapper(identity)
    data = np.array([1+2j, 3+4j])
    assert_allclose(wrapped(data), split_complex(data), atol=1e-12)

def test_complex_to_mag_phase_real():
    mag, phase = complex_to_mag_phase(1.0+0j)
    assert_allclose(mag, 1.0, atol=1e-12)
    assert_allclose(phase, 0.0, atol=1e-12)

def test_complex_to_mag_phase_imag():
    mag, phase = complex_to_mag_phase(0.0+1j)
    assert_allclose(mag, 1.0, atol=1e-12)
    assert_allclose(phase, np.pi/2, atol=1e-12)

def test_complex_to_mag_phase_negative_real():
    mag, phase = complex_to_mag_phase(-1.0+0j)
    assert_allclose(mag, 1.0, atol=1e-12)
    assert_allclose(phase, np.pi, atol=1e-12)

def test_complex_to_mag_phase_known():
    c = 3.0 + 4.0j
    mag, phase = complex_to_mag_phase(c)
    assert_allclose(mag, 5.0, rtol=1e-12)
    assert_allclose(phase, np.arctan2(4.0, 3.0), rtol=1e-12)
