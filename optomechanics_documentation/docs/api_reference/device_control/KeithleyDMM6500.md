# KeithleyDMM6500

VISA driver for the Keithley DMM6500 digital multimeter.
Supports voltage, current, resistance, temperature, frequency, period,
capacitance, continuity, diode, and ratio measurements with automatic
timeout management based on the measurement aperture.

## Examples

```python
from optomechanics.device_control.KeithleyDMM6500 import DMM6500

address = "TCPIP::192.168.x.x::INSTR"

with DMM6500(address) as dmm:
    # DC voltage measurement
    v = dmm.measure("VOLTage:DC")
    print(f"Voltage: {v} V")

    # Resistance measurement
    r = dmm.measure("RESistance")
    print(f"Resistance: {r} Ω")

    # Temperature (with appropriate probe connected)
    t = dmm.measure("TEMPerature")
    print(f"Temperature: {t} K")

    # Check for errors
    n_errors = dmm.number_of_errors()
    if n_errors > 0:
        print(dmm.current_errors())
```

::: optomechanics.device_control.KeithleyDMM6500
