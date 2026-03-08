# Spectrum Analyser (IQ / PSD)

This page covers using the **R&S FSW** spectrum analyser driver (`RS_FSW.FSW`)
for power-spectral-density (PSD) and IQ-domain measurements, which are the
primary techniques used in thermal-motion and optomechanical sideband experiments.

## What is a PSD?

A **power spectral density** (PSD) measures how signal power is distributed
across frequency.  It has units of power per unit bandwidth (W/Hz or dBm/Hz).
A PSD is the correct quantity for characterising noise — unlike raw power, it
is independent of the measurement bandwidth.

## The NENBW correction

A spectrum analyser applies a **window function** to each time segment before
computing the FFT.  This window suppresses spectral leakage but broadens the
effective bandwidth of each frequency bin beyond the nominal resolution
bandwidth (RBW).

The **Normalised Equivalent Noise Bandwidth** (NENBW) quantifies this
broadening as a dimensionless ratio.  For the R&S FSW in its default
(Gaussian) filter mode, NENBW ≈ 4.083.  The effective noise bandwidth is:

$$
\text{ENBW} = \text{NENBW} \times \text{RBW}
$$

To convert raw SA power (watts) to a true PSD (W/Hz), divide by ENBW:

$$
S(f) \;[\text{W/Hz}] = \frac{P_\text{SA}(f) \;[\text{W}]}{\text{ENBW} \;[\text{Hz}]}
$$

The NENBW value 4.083 is stored in the code as `RS_default_window_NENBW` in
`_fitting.py`.

!!! note
    Set the spectrum analyser to **PSD mode** (Watts/Hz or dBm/Hz) before
    acquiring data.  If a different mode is used, note the window function so
    that you can apply the correct normalisation factor in post-processing.

## Basic PSD sweep

```python
import numpy as np
from optomechanics.device_control.RS_FSW import FSW

with FSW('TCPIP::192.168.0.3::INSTR') as fsw:
    powers_dBm, frequencies = fsw.sweep(
        central_freq=7e9,      # centre frequency (Hz)
        span=200e6,            # span (Hz)
        band_width=1e3,        # resolution bandwidth, RBW (Hz)
        sweep_points=1001,
        average_number=10,     # number of on-instrument sweeps to average
        ref_level='auto',      # auto-set reference level
        save=True,
        file_location='/path/to/data/',
        file_name='psd_sweep',
    )
```

`powers_dBm` and `frequencies` are `numpy.ndarray` objects.

## Converting from power to PSD

The FSW returns power in dBm.  To convert to a one-sided PSD in dBm/Hz you
need to divide by the **effective noise bandwidth** (ENBW):

```python
from optomechanics.data_analysis.unit_conversions import dBm_to_watts, watts_to_dBm

# Noise Equivalent Noise Bandwidth factor — instrument-dependent.
# For the FSW in default (Gaussian) filter mode:
NENBW = 4.082911856792962  # dimensionless
ENBW = NENBW * band_width   # effective noise bandwidth (Hz)

# Convert dBm → watts, divide by ENBW, convert back to dBm/Hz
psd_dBm_Hz = watts_to_dBm(dBm_to_watts(powers_dBm) / ENBW)
```

## Acquiring a single trace manually

For scripts that need lower-level control (e.g. to embed a sweep inside a
longer acquisition loop):

```python
import numpy as np
from optomechanics.device_control.RS_FSW import FSW

with FSW('TCPIP::192.168.0.3::INSTR') as fsw:
    # Configure
    fsw.set_cent_freq(7e9)
    fsw.set_span(200e6)
    fsw.set_bw(1e3)           # RBW
    fsw.set_video_bw(1e3)     # VBW — keep equal to or less than RBW
    fsw.set_sweep_points(1001)
    fsw.auto_level()

    # Trigger a single sweep and wait
    fsw.write('INIT:CONT OFF')
    fsw.write('INIT:IMM')
    fsw.WAI()

    # Retrieve data
    frequencies = np.fromstring(fsw.x_data_query(), dtype=float, sep=',')
    powers_dBm  = np.fromstring(fsw.y_data_query(), dtype=float, sep=',')
```

## PSD measurement workflow (thermal motion)

The typical workflow for measuring mechanical thermal motion via the spectrum
analyser is:

1. **Set up a drive tone** with `SMA100B.Signal_Generator` at the pump frequency.
2. **Acquire a PSD** around the pump frequency with the FSW, centred on the
   mechanical sideband.
3. **Convert to physical units** using the cavity S21 parameters and the
   attenuation chain.

A condensed example:

```python
import numpy as np
from optomechanics.device_control.SMA100B import Signal_Generator
from optomechanics.device_control.RS_FSW import FSW
from optomechanics.data_analysis.unit_conversions import dBm_to_watts, watts_to_dBm

pump_freq  = 6.188e9   # Hz — pump at cavity resonance
drive_pwr  = -10       # dBm
RBW        = 1e3       # Hz
NENBW      = 4.082911856792962

with Signal_Generator('TCPIP::192.168.0.2::INSTR') as sg, \
     FSW('TCPIP::192.168.0.3::INSTR') as fsw:

    sg.set_mw_frequency(pump_freq)
    sg.set_mw_power(drive_pwr)
    sg.turn_mw('ON')

    powers_dBm, frequencies = fsw.sweep(
        central_freq=pump_freq,
        span=2e6,            # ±1 MHz around the pump
        band_width=RBW,
        sweep_points=100001,
        average_number=1,
        save=True,
        file_location='/path/to/data/',
        file_name='thermal_psd',
    )

    sg.turn_mw('Off')

# Convert to PSD
ENBW = NENBW * RBW
psd_dBm_Hz = watts_to_dBm(dBm_to_watts(powers_dBm) / ENBW)

# Frequency axis relative to the pump
rel_frequencies = frequencies - pump_freq
```

## See also

- [RS_FSW API reference](../api_reference/device_control/RS_FSW.md)
- [RS_FSW_new API reference](../api_reference/device_control/RS_FSW_new.md)
- [Device Control user guide](device_control.md) — `with`-block patterns for all instruments
- [Sww fitting API reference](../api_reference/data_analysis/fitting/Sww.md) — functions for fitting mechanical PSDs
- [Parameter Glossary](glossary.md)
