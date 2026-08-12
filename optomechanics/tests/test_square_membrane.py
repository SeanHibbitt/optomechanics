"""Unit tests for data_analysis/square_membrane.py."""
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_analysis.square_membrane import membrane

def make_bare():
    return membrane(1e-3,1e-3,100e-9,0.0,0.0,2820,1e9)

def test_fm_fundamental_formula(capsys):
    m = make_bare()
    L=1e-3; sigma=1e9; rho=2820
    expected = 0.5*np.sqrt((sigma/rho)*((1/L)**2+(1/L)**2))
    _, fm = m.fm(1,1)
    assert_allclose(fm, expected, rtol=1e-10)

def test_fm_no_deposition_reduced_equals_bare(capsys):
    m = make_bare()
    red, bare = m.fm(1,1)
    assert_allclose(red, bare, rtol=1e-10)

def test_fm_higher_mode_larger_frequency(capsys):
    m = make_bare()
    _,f11 = m.fm(1,1)
    _,f22 = m.fm(2,2)
    assert f22 > f11

def test_fm_deposition_reduces_frequency(capsys):
    m_bare = make_bare()
    m_loaded = membrane(1e-3,1e-3,100e-9,50e-9,2000.0,2820,1e9)
    _,f_bare = m_bare.fm(1,1)
    f_loaded,_ = m_loaded.fm(1,1)
    assert f_loaded < f_bare

def test_fm_square_modes_12_21_equal(capsys):
    m = make_bare()
    _,f12 = m.fm(1,2)
    _,f21 = m.fm(2,1)
    assert_allclose(f12, f21, rtol=1e-12)

def test_fm_returns_positive(capsys):
    m = make_bare()
    red, bare = m.fm(1,1)
    assert red > 0 and bare > 0
