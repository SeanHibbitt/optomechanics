# HF2LI Frequency Sweeps

This guide covers measuring transfer functions with the Zurich Instruments
**HF2LI** lock-in amplifier: drive a system from one of the lock-in's outputs,
sweep the oscillator frequency, and record the demodulated response (R, phase,
X, Y) at each point. It uses
[`optomechanics.Zurich.HF2LI`](../api_reference/zurich/hf2li.md).

---

## Setup

- Install `zhinst-toolkit` and `h5py` in the `exp` environment (they are not
  installed by `pip install -e .`).
- Start the **HF2 Data Server** (LabOne). It listens on port **8005**, which is
  the `HF2LI` default.
- Check the device is visible:

```python
from optomechanics.Zurich.Device_Zurich_Super import ZurichDevice
ZurichDevice.connected_devices(port=8005)      # ['dev1374']
```

---

## A single sweep

```python
import numpy as np
from optomechanics.Zurich.HF2LI import HF2LI

with HF2LI() as hf:
    result = hf.sweep(
        start=20, stop=2000, num_points=199, log_sweep=False,
        bandwidth_control=1, bandwidth_hz=1.098, filter_order=4,
        settling_inaccuracy=500e-6,
        output_channel=0, output_range=0.01, output_amplitude=0.5e-3,
        output_enable=True, output_osc_enable=True,
        timeout=np.inf,
        save=True, filepath=r"D:\data\TF.h5",
        metadata={"notes": "drive at plate, geophone on mass"},
    )
```

- The output is configured before the sweep, and switched off again afterwards.
- `bandwidth_control=1` (fixed) applies `bandwidth_hz`. Use `0` to keep the
  demodulator's existing time constant, or `2` to let the sweeper choose.
- Each point takes roughly a few filter time constants to settle, so the sweep
  time scales with `num_points / bandwidth_hz`. Narrow bandwidths are slow.
- `phase` is in radians.

To watch the sweep as it runs, pass `progress=True` and a `progress_callback`.
The callback receives the partial result every `progress_interval` seconds.
The reference notebook uses this for its live plot.

---

## Choosing the output range

The HF2 sets the output amplitude as a **fraction of the output range**
(0.01, 0.1, 1 or 10 V). `HF2LI` converts your absolute amplitude for you
(`amplitude / range`) and reads the value back to check it was applied.

If the fraction is too small, the device rounds it to zero and the check fails:

```
RuntimeError: Verify failed for sigouts/0/amplitudes/6: wrote 5e-06, read back 0.0
```

Here 0.05 mV was requested on the 10 V range (fraction 5×10⁻⁶). Pick the
smallest range that holds your largest amplitude:

| Amplitudes | Range |
|------------|-------|
| up to 10 mV | `0.01` |
| 10 – 100 mV | `0.1` |
| 0.1 – 1 V | `1` |
| 1 – 10 V | `10` |

A smaller range also gives better amplitude resolution and lower output noise.

---

## Multi-iteration sweeps: the reference notebook

`optomechanics/Scripts/DAQ_templates/Zurich/SweepZurich_V5.3.ipynb` is the
notebook used for the acoustic isolation (geophone) measurements. Copy it next
to your data and edit the paths before running. It is organised as follows.

### 1. Sweep plan

A list of `parts`, each a dict describing a block of sweeps:

```python
{
    "id":         "P1",
    "averages":   2,                          # repeat the whole block
    "amplitudes": [0.05e-3, 0.1e-3, 0.25e-3, 0.5e-3],
    "enable":     [0, 1],                     # output off, then on
    "start": 20, "stop": 2000,
    "range":      0.01,                       # output range [V]
    "npts":       199,
    "BW":         1.098,                      # demod bandwidth [Hz]
}
```

`Use_Sets` selects which parts to run. Each part expands into
`averages × len(enable) × len(amplitudes)` iterations. The cell prints a
table of every iteration so you can check the plan before starting. With
`enable = [0, 1]`, each amplitude is measured once with the output off (a
background/noise reference) and once with it on. `Delay` (hours) waits
before starting.

### 2. Sweep variables

Every `hf.sweep` argument appears here as a variable. Any of them can be a
single value or a list. All lists must have the same length `N`, and the sweep
runs `N` times with the *i*-th element of each list. The save mode follows
`Filename`:

- a single `Filename`: one `.h5` file with iterations stored as `000/`, `001/`, ...
- a list of `Filename`s: one file per iteration (`Filepath` may also be a list).

`Metadata` (including `Notes`) is stored with every iteration.

### 3. Run sweep with live plot

The sweep cell runs the iterations, with a live R/phase plot in a Qt window.
The title shows per-iteration and overall progress, plus an estimated time
remaining from a rolling rate (weighted by bandwidth, since narrow-bandwidth
sweeps take longer per point). The last three completed iterations stay on the
plot in grey. After each iteration, an interactive Plotly `.html` of all
iterations so far is written next to the data.

### 4. Afterwards

- **Final plot**: all iterations overlaid.
- **Index CSV**: appends a summary row (frequency span, bandwidths, amplitudes,
  ranges, drive source, notes, path) to a master index CSV (`Index_File`). Set
  `Append_To_Index = False` if you don't keep one.
- **Copy notebook**: saves the notebook and copies it next to the data file,
  so the exact settings are stored with the data.

---

## Reading the data back

```python
import h5py

with h5py.File(path, "r") as f:
    for it in f:                                       # '000', '001', ...
        grp   = f[f"{it}/dev1374/demods/0/sample"]
        freq  = grp["frequency"][:]
        r     = grp["r"][:]
        phase = grp["phase"][:]
        amp   = f[it].attrs["sweep_output_amplitude"]  # sweep settings: sweep_*
        on    = f[it].attrs["sweep_output_enable"]
        notes = f[it].attrs.get("user_notes")          # your metadata: user_*
```

See [`save_sweep_to_hdf5`](../api_reference/zurich/zurich_data_management.md#save_sweep_to_hdf5)
for the full file layout.

---

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `Verify failed for sigouts/n/amplitudes/m: wrote …, read back 0.0` | Amplitude too small for the output range; use a smaller range (see above). |
| `Verify failed for sigouts/n/range: wrote 0.01, read back 0.0` | Old `HF2LI` copy that read the range through `zhinst.toolkit` (which truncates it to an integer). Use `optomechanics.Zurich.HF2LI`. |
| Changes to `HF2LI.py` have no effect | Python caches imported modules. Restart the kernel, or use `%autoreload 2` (the notebook enables it). |
| `TimeoutError: Sweep timed out` | Increase `timeout` (the notebook uses `np.inf`). |
| Can't connect | Check the HF2 Data Server is running and you're using port 8005; `ZurichDevice.connected_devices(port=8005)` should list the device. |
