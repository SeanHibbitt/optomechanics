# Device_Visa_Super

Base VISA device class. Provides connection management and all standard
IEEE 488.2 / SCPI commands (`*IDN?`, `*RST`, `*OPC`, etc.).

All instrument-specific drivers in `device_control` inherit from `Device`.
Use a `with` block to ensure the VISA resource is always closed cleanly, even
if an exception is raised during measurement.

## Usage examples

```python
from optomechanics.device_control.Device_Visa_Super import Device

# List all instruments currently visible on the bus
print(Device.connected_devices())
```

```python
from optomechanics.device_control.Device_Visa_Super import Device

# Connect, query identity, then disconnect automatically on exit
with Device('TCPIP::192.168.0.10::INSTR') as dev:
    print(dev.IDN_query())
    dev.RST()               # restore instrument defaults
```

!!! note
    Subclass `Device` to add instrument-specific commands.  The `__enter__` /
    `__exit__` methods call `open` and `close` respectively, so the `with`
    pattern is the recommended way to manage connections.

::: optomechanics.device_control.Device_Visa_Super
