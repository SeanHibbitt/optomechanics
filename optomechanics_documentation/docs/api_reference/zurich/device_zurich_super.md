# Device_Zurich_Super

!!! warning "Autodoc unavailable"
    This module requires `zhinst.toolkit` which is not installed in the standard
    environment. The API is documented manually below.

**File:** `optomechanics/Zurich/Device_Zurich_Super.py`

---

## Classes

### `zuirch`

!!! bug
    Class name has a typo — should be `zurich`.

Session manager for Zurich Instruments LabOne communications.

| Method | Description |
|--------|-------------|
| `open_session()` | Creates a LabOne `Session` to `localhost` |

---

### `device`

Generic device wrapper for a specific Zurich Instruments unit.

| Method | Description |
|--------|-------------|
| `open_device()` | Connects to the device by `device_id`. **Bug:** references `self._session` instead of `self.session` — will raise `AttributeError`. |
| `close_device(device_id)` | Disconnects the device |
| `scope()` | Stub — not implemented. **Bug:** missing `self` parameter. |
