"""
Data management utilities for saving Zurich Instruments measurement results
(sweeps, spectra, IQ captures) to HDF5 files.
"""

import os
import numpy as np
import h5py
from datetime import datetime, timezone


def _maybe_prepend_datetime(filepath, prepend):
    """If *prepend* is True, prefix the filename component of *filepath*
    with the current date and time as ``YYYY-MM-DD_HH_MM_SS_``."""
    if not prepend:
        return filepath
    directory = os.path.dirname(filepath)
    name = os.path.basename(filepath)
    stamp = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    return os.path.join(directory, f"{stamp}_{name}")


# LabOne-format compound dtypes for sweeper module HDF5 files (LabOne 23.06).
# Matches the layout written by the Zurich Instruments LabOne sweeper module
# so that files saved here can be opened by the same downstream tools.
# `name` is a variable-length UTF-8 string; h5py needs special_dtype, which
# the numpy compound represents as an object field.
_VLEN_STR = h5py.special_dtype(vlen=str)

_CHUNKHEADER_DTYPE = np.dtype([
    ('activerow',        '<u4'),
    ('bandwidth',        '<f8'),
    ('center',           '<f8'),
    ('changedtimestamp', '<u8'),
    ('chunksizebytes',   '<u8'),
    ('color',            '<u4'),
    ('createdtimestamp', '<u8'),
    ('dataloss',         'u1'),
    ('flags',            '<u4'),
    ('gridcoldelta',     '<f8'),
    ('gridcoloffset',    '<f8'),
    ('gridcols',         '<u4'),
    ('griddirection',    '<u4'),
    ('gridmode',         '<u4'),
    ('gridoperation',    '<u4'),
    ('gridrepetitions',  '<u4'),
    ('gridrowdelta',     '<f8'),
    ('gridrowoffset',    '<f8'),
    ('gridrows',         '<u4'),
    ('groupindex',       '<u4'),
    ('mindelta',         '<u8'),
    ('moduleflags',      '<u4'),
    ('name',             _VLEN_STR),
    ('nenbw',            '<f8'),
    ('ratechange',       'u1'),
    ('status',           '<u4'),
    ('systemtime',       '<u8'),
    ('trigger',          '<u8'),
    ('triggernumber',    '<u8'),
])

_SWEEPERHEADER_DTYPE = np.dtype([
    ('samplecount',   '<u8'),
    ('flags',         'u1'),
    ('sampleformat',  'u1'),
    ('sweepmode',     'u1'),
    ('bandwidthmode', 'u1'),
])

# HF2LI clock period (1/210 MHz). Used as the sample group `timebase` attr.
_HF2LI_TIMEBASE = 1.0 / 210e6


def save_sweep_to_hdf5(filepath, result, device_id="dev1374", demod_index=0, metadata=None,
                       sweep_params=None, group_index=0, append=False,
                       prepend_datetime=True):
    """
    Save a sweep result dict to an HDF5 file, mirroring the hierarchy that
    LabOne / zhinst-toolkit uses when recording sweep data.

    The data is stored under::

        /<group_index:03d>/<device_id>/demods/<demod_index>/sample/<key>

    e.g. ``/000/dev1374/demods/0/sample/frequency``, alongside LabOne-format
    ``chunkheader`` and ``sweeperheader`` compound datasets, so the file can be
    read with the same tools as files saved by the LabOne sweeper module.
    Repeated sweeps can be stored in one file as ``000/``, ``001/``, ... by
    passing ``group_index`` and ``append=True``.

    Parameters
    ----------
    filepath : str or Path
        Destination HDF5 file path. The parent directory is created if it
        does not already exist. Existing files are overwritten unless
        ``append`` is True.
    result : dict
        Sweep result as returned by ``HF2LI.sweep()``, with keys such as
        ``'frequency'``, ``'r'``, ``'phase'``, ``'x'``, ``'y'``.  All
        values are converted to numpy arrays before saving.
    device_id : str, optional
        Device serial string used as the top-level HDF5 group.
        Default is ``'dev1374'``.
    demod_index : int, optional
        Demodulator index used to build the sub-group path.
        Default is ``0``.
    metadata : dict or None, optional
        Extra scalar attributes (e.g. sample name, notes) stored as
        ``user_<key>`` attributes on the iteration group.  Keys and values
        must be HDF5-compatible types (strings, numbers).
    sweep_params : dict or None, optional
        Sweep configuration parameters (start, stop, bandwidth, output
        amplitude, etc.).  Stored as ``sweep_<key>`` attributes on the
        iteration group so each sweep is self-describing.  ``None``
        values are stored as the string ``'None'``.
    group_index : int, optional
        Index of the iteration group (``000``, ``001``, ...). Default is 0.
    append : bool, optional
        If True, open an existing file and add/replace the ``group_index``
        group instead of overwriting the file. Default is False.
    prepend_datetime : bool, optional
        If True, prepend the current date and time to the filename in the
        format ``YYYY-MM-DD_HH_MM_SS_``.  For example, ``data.h5``
        becomes ``2026-04-11_14_30_45_data.h5``.  Default is True.

    Examples
    --------
    >>> result = hf.sweep(start=1e3, stop=1e6, num_points=200)
    >>> save_sweep_to_hdf5("data/sweep_001.h5", result,
    ...                    metadata={"sample": "resonator_A", "temperature_K": 4.2})
    """
    filepath = _maybe_prepend_datetime(filepath, prepend_datetime)
    print(f"Saving to: {filepath}")
    filepath = str(filepath)
    parent = os.path.dirname(os.path.abspath(filepath))
    if parent:
        os.makedirs(parent, exist_ok=True)

    # --- Normalise the result into a plain dict of numpy arrays ----------
    if hasattr(result, 'dtype') and result.dtype.names is not None:
        keys = result.dtype.names
        get = lambda k: result[k]
    else:
        keys = list(result.keys())
        get = lambda k: result[k]

    header_in = {}
    if 'header' in keys:
        h = get('header')
        if isinstance(h, dict):
            header_in = h

    # --- Build the chunkheader compound (1,) array -----------------------
    chunkheader = np.zeros(1, dtype=_CHUNKHEADER_DTYPE)
    chunkheader['name'] = ''   # vlen-str field; np.zeros leaves int 0, which h5py rejects
    for fname in _CHUNKHEADER_DTYPE.names:
        if fname not in header_in:
            continue
        v = header_in[fname]
        if isinstance(v, np.ndarray):
            v = v.flat[0] if v.size else 0
        if fname == 'name':
            if isinstance(v, np.bytes_):
                v = v.decode()
            chunkheader[fname] = str(v) if v is not None else ''
        else:
            chunkheader[fname] = v

    # --- Build the sweeperheader compound (1,) array ---------------------
    sweeperheader = np.zeros(1, dtype=_SWEEPERHEADER_DTYPE)
    for fname in _SWEEPERHEADER_DTYPE.names:
        if fname in keys:
            v = np.asarray(get(fname))
            sweeperheader[fname] = int(v.flat[0]) if v.size else 0

    # Fields that get packed into the compound datasets above and so should
    # NOT be written as standalone datasets in the sample group.
    _packed = set(_SWEEPERHEADER_DTYPE.names) | {'header'}

    # --- Write the file --------------------------------------------------
    mode = "a" if append else "w"
    with h5py.File(filepath, mode) as f:
        # LabOne-style root attributes — only written on a fresh file
        if not append:
            f.attrs['LabOne HDF5 Version'] = '1.0'
            f.attrs['LabOne Release']      = '23.06'
            f.attrs['LabOne Version']      = '23.06.46756'
            f.attrs['author']              = 'file created by LabOne, Zurich Instruments'
            f.attrs['devicetype']          = 'HF2LI'
            f.attrs['file creation date'] = datetime.now().strftime('%a %b %d %H:%M:%S %Y')
            f.attrs['module']              = 'sweeper'

        # LabOne wraps the sweep data inside a sweep-row group (e.g. "000/").
        # `group_index` lets callers append additional iterations as 001/, 002/...
        row_group = f.require_group(f"{group_index:03d}")
        group_path = f"{device_id}/demods/{demod_index}/sample"
        grp = row_group.require_group(group_path)
        grp.attrs['nodetype'] = 'CoreSweeperWave'
        grp.attrs['timebase'] = _HF2LI_TIMEBASE

        # Per-point data arrays
        for key in keys:
            if key in _packed:
                continue
            if key == 'timestamp':
                # LabOne stores timestamp as a (1,) uint64 dataset
                ts = np.asarray(get(key)).astype('<u8').reshape(-1)
                if ts.size == 0:
                    ts = np.zeros(1, dtype='<u8')
                grp.create_dataset('timestamp', data=ts[:1])
                continue
            grp.create_dataset(key, data=np.asarray(get(key)))

        # Compound header datasets
        grp.create_dataset('chunkheader',   data=chunkheader)
        grp.create_dataset('sweeperheader', data=sweeperheader)

        # Caller-supplied metadata is attached to this iteration's row group
        # (sibling of the device subtree), namespaced under "user_" to avoid
        # clashing with LabOne's reserved attribute names. Storing it on the
        # row group instead of the file root means each loop iteration owns
        # its own metadata.
        if sweep_params is not None:
            for k, v in sweep_params.items():
                if v is None:
                    row_group.attrs[f'sweep_{k}'] = 'None'
                else:
                    row_group.attrs[f'sweep_{k}'] = v

        if metadata is not None:
            for k, v in metadata.items():
                row_group.attrs[f'user_{k}'] = v

    print("Saved")


def save_spectrum_to_hdf5(filepath, result, device_id="dev1374", demod_index=0, metadata=None,
                          prepend_datetime=True):
    """
    Save the full spectrum result dict to an HDF5 file.

    Saves every key returned by ``HF2LI.spectrum()`` — ``'ffts'``,
    ``'freqs'``, ``'averaged'``, and all entries in ``'params'`` — so
    the file faithfully captures the complete output of the measurement.

    The data is stored under::

        /<device_id>/demods/<demod_index>/spectrum/

    Parameters
    ----------
    filepath : str or Path
        Destination HDF5 file path.  Parent directory is created if
        needed.  Existing files are overwritten.
    result : dict
        Spectrum result as returned by ``HF2LI.spectrum()``.  Must
        contain keys ``'freqs'``, ``'ffts'``, ``'averaged'``, and
        ``'params'``.
    device_id : str, optional
        Device serial used as the top-level HDF5 group.
        Default is ``'dev1374'``.
    demod_index : int, optional
        Demodulator index used to build the sub-group path.
        Default is ``0``.
    metadata : dict or None, optional
        Extra scalar attributes stored at the file root.
    prepend_datetime : bool, optional
        If True, prepend the current date and time to the filename in the
        format ``YYYY-MM-DD_HH_MM_SS_``.  Default is False.

    Examples
    --------
    >>> result = hf.spectrum(center_freq=1e3, span=100, fft_length=1024)
    >>> save_spectrum_to_hdf5("data/spectrum_001.h5", result,
    ...                       metadata={"sample": "resonator_A"})
    """
    filepath = _maybe_prepend_datetime(filepath, prepend_datetime)
    import numpy as np

    print(f"Saving to: {filepath}")
    filepath = str(filepath)
    parent = os.path.dirname(os.path.abspath(filepath))
    if parent:
        os.makedirs(parent, exist_ok=True)

    with h5py.File(filepath, "w") as f:
        group_path = f"{device_id}/demods/{demod_index}/spectrum"
        grp = f.require_group(group_path)

        grp.create_dataset("freqs",    data=np.asarray(result["freqs"]))
        grp.create_dataset("ffts",     data=np.asarray(result["ffts"]))
        grp.create_dataset("averaged", data=np.asarray(result["averaged"]))

        f.attrs["timestamp"]   = datetime.now().isoformat()
        f.attrs["device_id"]   = device_id
        f.attrs["demod_index"] = demod_index

        params = result.get("params", {})
        for k, v in params.items():
            if v is None:
                f.attrs[k] = "None"
            else:
                f.attrs[k] = v

        if metadata is not None:
            for k, v in metadata.items():
                f.attrs[k] = v

    print("Saved")


def save_iq_to_hdf5(filepath, x, y, params, device_id="dev1374", metadata=None,
                    prepend_datetime=True):
    """
    Save raw I/Q time-domain segments to an HDF5 file.

    Stores ``x`` and ``y`` arrays under::

        /<device_id>/demods/<demod_index>/iq_raw/

    All HF2LI measurement parameters (including filter TC, NENBW, ENBW)
    are saved as file-level attributes so the file is self-describing.

    Parameters
    ----------
    filepath : str or Path
        Destination HDF5 file path.  Parent directory is created if needed.
        Existing files are overwritten.
    x : array-like
        I component, shape ``(num_segments, fft_length)``.
    y : array-like
        Q component, shape ``(num_segments, fft_length)``.
    params : dict
        Measurement parameters as returned in ``HF2LI.acquire_iq()['params']``.
        Must contain: ``center_freq``, ``span``, ``fs``, ``fft_length``,
        ``num_segments``, ``demod_index``, ``osc_index``, ``filter_order``,
        ``filter_timeconstant``, ``filter_bandwidth_hz``, ``window``.
        ``nenbw`` and ``enbw`` are computed from the window and ``fs`` if
        not already present.
    device_id : str, optional
        Device serial used as the top-level HDF5 group.  Default is
        ``'dev1374'``.
    metadata : dict or None, optional
        Extra scalar attributes stored at the file root.
    prepend_datetime : bool, optional
        If True, prepend the current date and time to the filename in the
        format ``YYYY-MM-DD_HH_MM_SS_``.  Default is False.

    Examples
    --------
    >>> iq = hf.acquire_iq(center_freq=1e3, span=100, fft_length=512)
    >>> save_iq_to_hdf5("data/iq_001.h5", iq['x'], iq['y'],
    ...                  params=iq['params'])
    """
    filepath = _maybe_prepend_datetime(filepath, prepend_datetime)
    import scipy.signal

    print(f"Saving to: {filepath}")
    filepath = str(filepath)
    parent = os.path.dirname(os.path.abspath(filepath))
    if parent:
        os.makedirs(parent, exist_ok=True)

    x = np.asarray(x)
    y = np.asarray(y)

    demod_index = params.get('demod_index', 0)
    window = params.get('window', 'hann')
    fft_length = int(params['fft_length'])
    fs = float(params['fs'])

    # Compute NENBW and ENBW from the window array
    win = scipy.signal.get_window(window, fft_length)
    nenbw = fft_length * float((win ** 2).sum()) / float(win.sum()) ** 2
    enbw = nenbw * fs / fft_length

    with h5py.File(filepath, "w") as f:
        group_path = f"{device_id}/demods/{demod_index}/iq_raw"
        grp = f.require_group(group_path)
        grp.create_dataset("x", data=x)
        grp.create_dataset("y", data=y)

        f.attrs["timestamp"]            = datetime.now().isoformat()
        f.attrs["device_id"]            = device_id
        f.attrs["demod_index"]          = demod_index
        f.attrs["center_freq"]          = float(params["center_freq"])
        f.attrs["span"]                 = float(params["span"])
        f.attrs["fs"]                   = fs
        f.attrs["fft_length"]           = fft_length
        f.attrs["num_segments"]         = int(params["num_segments"])
        f.attrs["window"]               = window
        f.attrs["osc_index"]            = int(params.get("osc_index", 0))
        f.attrs["filter_order"]         = int(params["filter_order"])
        f.attrs["filter_timeconstant"]  = float(params["filter_timeconstant"])
        f.attrs["filter_bandwidth_hz"]  = (
            float(params["filter_bandwidth_hz"])
            if params.get("filter_bandwidth_hz") is not None
            else float("nan")
        )
        f.attrs["nenbw"]                = nenbw
        f.attrs["enbw"]                 = enbw

        if metadata is not None:
            for k, v in metadata.items():
                f.attrs[k] = v

    print("Saved")
