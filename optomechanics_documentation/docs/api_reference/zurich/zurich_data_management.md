# zurich_data_management

!!! warning "Autodoc unavailable"
    This module requires `h5py`, and is part of the `Zurich` subpackage that
    depends on `zhinst.toolkit`. The API is documented manually below.

**File:** `optomechanics/Zurich/zurich_data_management.py`

HDF5 writers for Zurich Instruments results. `HF2LI` calls these when you pass
`save=True`, but they can also be used on their own.

All three accept `prepend_datetime=True` (the default), which prefixes the
filename with `YYYY-MM-DD_HH_MM_SS_`, and create the parent directory if needed.

---

## `save_sweep_to_hdf5`

```python
save_sweep_to_hdf5(filepath, result, device_id="dev1374", demod_index=0,
                   metadata=None, sweep_params=None, group_index=0,
                   append=False, prepend_datetime=True)
```

Writes a sweep result in the **LabOne sweeper file layout**, so the files open in
the same tools as those saved by LabOne itself:

```
/                                   LabOne root attributes ('devicetype', 'module', 'file creation date', ...)
└── 000/                            iteration group: sweep_<param> and user_<metadata> attributes
    └── dev1374/demods/0/sample/
        ├── frequency, r, phase, x, y, ...   one dataset per result field
        ├── chunkheader                       LabOne compound header
        └── sweeperheader                     LabOne compound header
```

| Parameter | Description |
|-----------|-------------|
| `result` | Dict (or structured array) returned by `HF2LI.sweep()` |
| `metadata` | Stored as `user_<key>` attributes on the iteration group |
| `sweep_params` | Stored as `sweep_<key>` attributes (`None` → `'None'`) |
| `group_index` | Iteration group name, `f"{group_index:03d}"` |
| `append` | Open an existing file and add the group instead of overwriting the file |

Reading a sweep back:

```python
import h5py

with h5py.File("2026-10-13_10_00_00_sweep.h5", "r") as f:
    for it in f:                                   # '000', '001', ...
        grp = f[f"{it}/dev1374/demods/0/sample"]
        freq, r = grp["frequency"][:], grp["r"][:]
        amp = f[it].attrs["sweep_output_amplitude"]
        notes = f[it].attrs.get("user_notes")
```

---

## `save_spectrum_to_hdf5`

```python
save_spectrum_to_hdf5(filepath, result, device_id="dev1374", demod_index=0,
                      metadata=None, prepend_datetime=True)
```

Saves the `HF2LI.spectrum()` result (`freqs`, `ffts`, `averaged`) under
`/<device_id>/demods/<demod_index>/spectrum/`. The `params` entries and
`metadata` are stored as file attributes, along with `timestamp`, `device_id`
and `demod_index`.

---

## `save_iq_to_hdf5`

```python
save_iq_to_hdf5(filepath, x, y, params, device_id="dev1374", metadata=None,
                prepend_datetime=True)
```

Saves raw I/Q segments from `HF2LI.acquire_iq()` under
`/<device_id>/demods/<demod_index>/iq_raw/`. All measurement parameters,
including the filter time constant and the derived NENBW / ENBW, are stored as
file attributes so the file is self-describing.
