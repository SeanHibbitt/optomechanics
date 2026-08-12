import os
import numpy as np
from numpy.testing import assert_allclose
from optomechanics.data_management.file_management import make_path, dated_file_maker
from optomechanics.data_management.data_management import save_data_3, read_file

def test_empty(): assert make_path([])==""
def test_one(): assert make_path(["a"])=="a\\"
def test_two(): assert make_path(["a","b"])=="a\\b\\"
def test_three(): assert make_path(["a","b","c"])=="a\\b\\c\\"
def test_trailing(): r=make_path(["x"]); assert r[-1]=="\\"
def test_nonempty(): assert len(make_path(["z"]))>0


# --- File I/O round-trip tests ---

def test_save_and_read_2d_roundtrip(tmp_path):
    """save_data_3 then read_file should recover 2-D array data."""
    data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    fname = "roundtrip.dat"
    fpath = str(tmp_path) + os.sep
    headers = "col_a\tcol_b"
    save_data_3(data, fname, file_location=fpath, headers=headers)

    df, meta = read_file(fpath + fname, sep=r"\s+")
    assert len(df) == 3  # 3 rows (data_shape[1])
    assert len(df.columns) == 2  # 2 columns (data_shape[0])


def test_save_and_read_with_metadata(tmp_path):
    """Metadata written by save_data_3 should be recovered by read_file."""
    data = np.array([[10.0, 20.0]])
    fname = "meta_test.dat"
    fpath = str(tmp_path) + os.sep
    meta_in = {"sample_rate": "1000", "gain": "5"}
    headers = "value"
    save_data_3(data, fname, file_location=fpath, headers=headers, meta_data=meta_in)

    df, meta_out = read_file(fpath + fname, sep=r"\s+")
    assert meta_out["sample_rate"] == "1000"
    assert meta_out["gain"] == "5"


def test_save_and_read_1d_roundtrip(tmp_path):
    """save_data_3 with a 1-D array should be readable by read_file."""
    data = np.array([7.0, 8.0, 9.0])
    fname = "oneD.dat"
    fpath = str(tmp_path) + os.sep
    headers = "vals"
    save_data_3(data, fname, file_location=fpath, headers=headers)

    df, meta = read_file(fpath + fname, sep=r"\s+")
    assert len(df) == 3


# --- dated_file_maker tests ---

def test_dated_file_maker_creates_directory(tmp_path):
    """dated_file_maker should create a year/month/day directory hierarchy."""
    base = str(tmp_path)
    result_path = dated_file_maker(base)
    assert os.path.isdir(result_path)


def test_dated_file_maker_contains_date_segments(tmp_path):
    """The returned path should contain year, month name, and day segments."""
    from datetime import datetime
    now = datetime.now()
    base = str(tmp_path)
    result_path = dated_file_maker(base)
    # Should contain the current year as a folder name
    assert str(now.year) in result_path
    # Should contain the day number
    assert str(now.day) in result_path


def test_dated_file_maker_trailing_backslash(tmp_path):
    """The returned path should end with a backslash."""
    base = str(tmp_path)
    result_path = dated_file_maker(base)
    assert result_path.endswith("\\")


def test_dated_file_maker_idempotent(tmp_path):
    """Calling dated_file_maker twice should not raise and should return the same path."""
    base = str(tmp_path)
    path1 = dated_file_maker(base)
    path2 = dated_file_maker(base)
    assert path1 == path2
