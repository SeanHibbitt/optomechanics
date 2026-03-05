# Device Control

The `optomechanics.device_control` subpackage contains VISA instrument drivers for all
hardware used in the lab.

## Architecture

All drivers inherit from `Device_Visa_Super.Device`, which wraps a `pyvisa` resource and
provides common open/close and query helpers.

```
Device (Device_Visa_Super)
├── E5063A_VNA_Class          — Keysight E5063A Vector Network Analyser
├── Rohde_Schwarz_Class       — R&S FSL / FSW Spectrum Analyser
├── RS_FSW / RS_FSW_new       — R&S FSW (alternative interfaces)
├── SMA100B                   — R&S SMA100B Signal Generator
├── SPD3303XE                 — Siglent SPD3303XE Power Supply
├── Tektronix_AFG1022         — Tektronix AFG1022 Function Generator
├── KeithleyDMM6500           — Keithley DMM6500 Multimeter
└── Lakeshore_372             — Lakeshore 372 AC Resistance Bridge
```

`VNA` is a higher-level composite class that combines a signal generator and a spectrum
analyser to implement a software-defined VNA sweep.

## Usage pattern

All drivers support the Python `with` statement, which automatically opens and
closes the VISA connection:

```python
from optomechanics.device_control.E5063A_VNA_Class_new import VNA

with VNA('TCPIP::192.168.0.1::INSTR') as vna:
    df, meta = vna.sweep(
        channel=1,
        Result='S21',
        TraceName=1,
        freq_start=6.9e9,
        freq_stop=7.1e9,
        number_of_points=1001,
        probe_power=-10,
        band_width=1e3,
    )
```

`df` is a `pandas.DataFrame` with columns `freq[Hz]`, magnitude (dB), and
phase (rad).  `meta` is a dict of sweep parameters and timestamps.

See the [API Reference](../api_reference/device_control/index.md) for all available classes
and methods.
