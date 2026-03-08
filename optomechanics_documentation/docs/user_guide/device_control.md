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

## SMA100B signal generator

```python
from optomechanics.device_control.SMA100B import Signal_Generator

with Signal_Generator('TCPIP::192.168.0.2::INSTR') as sg:
    sg.set_mw_frequency(7e9)   # 7 GHz
    sg.set_mw_power(-10)       # -10 dBm
    sg.turn_mw('ON')

    # ... perform measurements ...

    sg.turn_mw('Off')
# Connection is closed automatically on exit.
```

## RS FSW spectrum analyser

```python
from optomechanics.device_control.RS_FSW import FSW

with FSW('TCPIP::192.168.0.3::INSTR') as fsw:
    df, meta = fsw.sweep(
        central_freq=7e9,      # centre frequency (Hz)
        span=200e6,            # span (Hz)
        band_width=1e3,        # resolution bandwidth (Hz)
        sweep_points=1001,
        average_number=5,      # on-instrument averages
    )

import numpy as np
frequencies = np.fromstring(fsw.x_data_query(), sep=',')
power_dBm   = np.fromstring(fsw.y_data_query(), sep=',')
```

## Multi-device workflow: software VNA (SG + FSW)

`Vector_Network_Analyser` in `VNA.py` emulates a one-port VNA by combining a
signal generator and a spectrum analyser.  Connect both instruments and pass
thin wrapper callables:

```python
from optomechanics.device_control.SMA100B import Signal_Generator
from optomechanics.device_control.RS_FSW import FSW
from optomechanics.device_control.VNA import Vector_Network_Analyser

with Signal_Generator('TCPIP::192.168.0.2::INSTR') as sg, \
     FSW('TCPIP::192.168.0.3::INSTR') as fsw:

    def sg_func(freq, power, on_off):
        sg.set_mw_frequency(freq)
        sg.set_mw_power(power)
        sg.turn_mw(on_off)

    def sa_func(freq, band_width):
        fsw.set_cent_freq(freq)
        fsw.set_bw(band_width)
        fsw.write('INIT:IMM')
        fsw.WAI()
        power = fsw.y_data_query()
        freqs = fsw.x_data_query()
        return power, freqs

    vna = Vector_Network_Analyser(sg_func, sa_func)
    frequencies, s21_dB, s21_err = vna.sweep(
        central_frequency=7e9,
        span=200e6,
        sweep_points=201,
        power=-10,
        band_width=1e3,
        save_location='/path/to/data/',
        file_name='s21_sweep.tsv',
    )
# Both instrument connections are closed automatically on exit.
```

See the [API Reference](../api_reference/device_control/index.md) for all available classes
and methods.

## See also

- [Parameter Glossary](glossary.md)
