# Zurich Instruments

The `optomechanics.Zurich` subpackage controls **Zurich Instruments lock-in
amplifiers** (currently the HF2LI) through
[`zhinst-toolkit`](https://docs.zhinst.com/zhinst-toolkit/en/latest/), and saves
the results to HDF5.

!!! note "Extra dependencies"
    This subpackage needs `zhinst-toolkit` and `h5py`, which are not in
    `setup.py`'s `install_requires`. The LabOne Data Server must be running
    (the HF2 uses its own server on port **8005**).

## Quick example

```python
from optomechanics.Zurich.HF2LI import HF2LI

with HF2LI() as hf:                     # dev1374 on localhost:8005
    result = hf.sweep(start=20, stop=2000, num_points=199,
                      log_sweep=False, bandwidth_hz=1.098,
                      output_channel=0, output_range=0.01,
                      output_amplitude=0.5e-3, output_enable=True,
                      output_osc_enable=True,
                      save=True, filepath="data/sweep.h5")

freq, r, phase = result["frequency"], result["r"], result["phase"]
```

See the [HF2LI Frequency Sweeps](../../user_guide/hf2li_sweeps.md) user guide
for the full workflow and the reference notebook.

## Modules

| Module | Description |
|--------|-------------|
| [Device_Zurich_Super](device_zurich_super.md) | `ZurichDevice` base class: LabOne session and device connection lifecycle |
| [HF2LI](hf2li.md) | `HF2LI` driver: output/input/demodulator configuration, frequency sweeps, spectra, raw I/Q capture |
| [zurich_data_management](zurich_data_management.md) | HDF5 writers for sweep, spectrum and I/Q results |

## Class hierarchy

```
ZurichDevice (Device_Zurich_Super)
└── HF2LI    — Zurich Instruments HF2LI dual lock-in amplifier
```

`ZurichDevice` follows the same open/close and context-manager pattern as the
VISA `Device` base class. The raw `zhinst.toolkit` objects are exposed as
`self.session` and `self.device`, so anything the convenience methods don't
cover can be done directly through the toolkit API.
