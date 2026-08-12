# Device_Visa_Super_rs

Base VISA device class backed by the Rohde & Schwarz `RsInstrument` library
instead of PyVISA.  Intended for use with R&S instruments (ZNA, FSW, etc.)
that benefit from the `RsInstrument` backend.

Inherits all IEEE 488.2 / SCPI commands from `Device_Visa_Super`.

## Examples

```python
from optomechanics.device_control.Device_Visa_Super_rs import Device

# List all connected VISA instruments
print(Device.connected_devices())

# Connect to a specific instrument
address = "TCPIP::134.219.128.115::hislip0::INSTR"

with Device(address) as dev:
    print(dev.IDN_query())
    dev.RST()
    dev.CLS()
```

!!! note
    The timeout is fixed at 25 000 ms regardless of the value passed to
    `__init__`.  To change the timeout after construction, set
    `dev._device.timeout` directly.

::: optomechanics.device_control.Device_Visa_Super_rs
