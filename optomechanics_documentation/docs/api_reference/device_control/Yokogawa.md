# Yokogawa

VISA driver for the Yokogawa GS200 DC voltage / current source.
Provides a clean interface to set voltage or current output levels and
toggle the output on or off.

## Examples

```python
from optomechanics.device_control.Yokogawa import GS200

address = "TCPIP::192.168.x.x::INSTR"

with GS200(address) as source:
    # Voltage source mode: sweep gate voltage
    source.source_function("VOLT")
    source.output_state("ON")

    for gate_v in [0.0, 0.1, 0.2, 0.5, 1.0]:
        source.set_voltage(gate_v)
        # ... take measurement ...

    source.set_voltage(0.0)
    source.output_state("OFF")
```

### Current source

```python
with GS200(address) as source:
    source.source_function("CURR")
    source.set_current(1e-6)   # 1 µA
    source.output_state("ON")
```

::: optomechanics.device_control.Yokogawa
