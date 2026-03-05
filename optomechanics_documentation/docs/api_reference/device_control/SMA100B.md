# SMA100B

VISA driver for the Rohde & Schwarz SMA100B microwave signal generator.
Also contains class definitions for `SMP22` and `SMF` variants that share
the same interface.

## Examples

```python
from optomechanics.device_control.SMA100B import SMA100B as Signal_Generator

address = "TCPIP::134.219.128.14::INSTR"

with Signal_Generator(address) as sg:
    sg.set_mw_frequency(7e9)   # Hz
    sg.set_mw_power(-18)       # dBm
    sg.turn_mw("On")

    # ... run experiment ...

    sg.turn_mw("Off")          # always turn off when done
```

### Combined with VNA (power-sweep workflow)

```python
from optomechanics.device_control.SMA100B import SMA100B as Signal_Generator
from optomechanics.device_control.E5063A_VNA_Class_new import VNA

with Signal_Generator(sg_address) as sg:
    with VNA(vna_address) as vna:
        sg.turn_mw("On")
        for drive_power in range(-20, 0, 2):
            sg.set_mw_power(drive_power)
            data, meta = vna.sweep(1, "S21", "Trc1", 5e9, 7e9)
        sg.turn_mw("Off")
```

::: optomechanics.device_control.SMA100B
