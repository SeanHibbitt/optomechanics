# Device_Zurich_Super

!!! warning "Autodoc unavailable"
    This module requires `zhinst.toolkit`, which is not installed in the standard
    environment. The API is documented manually below.

**File:** `optomechanics/Zurich/Device_Zurich_Super.py`

Base class for Zurich Instruments devices using `zhinst.toolkit`. It mirrors the
`Device_Visa_Super` lifecycle (context manager, `open` / `close`) while wrapping
a `zhinst.toolkit.Session`.

---

## Classes

### `ZurichDevice(device_id, server_host="localhost", port=8004)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | str | Device serial, e.g. `'dev1374'` |
| `server_host` | str | LabOne Data Server hostname. Default `'localhost'` |
| `port` | int | Data Server port. Default `8004` (the HF2 server uses `8005`; `HF2LI` sets this for you) |

**Attributes**

| Attribute | Description |
|-----------|-------------|
| `session` | `zhinst.toolkit.Session`, or `None` when closed |
| `device` | `zhinst.toolkit` device object, or `None` when closed |
| `device_id`, `server_host`, `port` | Connection settings |

**Methods**

| Method | Description |
|--------|-------------|
| `open()` | Opens a session to the Data Server and connects the device. Returns `self`. |
| `close()` | Disconnects the device and drops the session. |
| `__enter__` / `__exit__` | `with ZurichDevice(...) as dev:` opens on entry and closes on exit, even after an exception. |
| `connected_devices(server_host="localhost", port=8004)` | *Static.* Returns the list of device IDs visible to the Data Server. |

```python
from optomechanics.Zurich.Device_Zurich_Super import ZurichDevice

print(ZurichDevice.connected_devices(port=8005))   # e.g. ['dev1374']

with ZurichDevice("dev1374", port=8005) as dev:
    print(dev.device.oscs[0].freq())              # raw toolkit access
```
