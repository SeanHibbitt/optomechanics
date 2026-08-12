# SPD3303XE

VISA driver for the Siglent SPD3303XE triple-output programmable DC power
supply.  Supports voltage and current set/measure on channels CH1, CH2,
and CH3.

## Examples

```python
from optomechanics.device_control.SPD3303XE import SPD

address = "TCPIP::192.168.x.x::INSTR"

with SPD(address) as psu:
    # Set CH1 to 5 V
    psu.set_value("CH1", "VOLTage", 5.0)

    # Limit CH1 current to 0.5 A
    psu.set_value("CH1", "CURRent", 0.5)

    # Read back actual output voltage and current
    v = psu.measure_value("CH1", "VOLTage")
    i = psu.measure_value("CH1", "CURRent")
    print(f"CH1: {v} V, {i} A")

    # Query the programmed set-point
    v_set = psu.query_set_value("CH1", "VOLTage")
```

::: optomechanics.device_control.SPD3303XE
