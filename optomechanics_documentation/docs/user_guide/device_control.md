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

```python
import pyvisa
from optomechanics.device_control.E5063A_VNA_Class_new import E5063A

rm  = pyvisa.ResourceManager()
vna = E5063A(rm.open_resource("GPIB0::16::INSTR"))

frequencies, s21_dB = vna.sweep(start=6.9e9, stop=7.1e9, points=1001)
vna.close()
```

See the [API Reference](../api_reference/device_control/index.md) for all available classes
and methods.
