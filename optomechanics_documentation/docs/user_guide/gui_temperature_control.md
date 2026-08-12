# Temperature Control GUI

The `optomechanics.GUI` subpackage contains a PyQt5-based graphical interface for
real-time temperature readout and PID control of cryogenic refrigerator systems.

!!! warning "Experimental — Known Bugs"
    This GUI is **not production-ready**. Three known bugs prevent it from running
    correctly out of the box:

    1. **Wrong import case** — imports use `Optomechanics` (capital O) instead of
       `optomechanics`. These will raise `ModuleNotFoundError` on case-sensitive systems.
    2. **PID not instantiated** — `Worker.load_pid_settings()` reads settings from
       `pid_settings.json` but never calls `self.pid = PID(...)`. Any subsequent access
       to `self.pid.Kp` etc. will raise `AttributeError`.
    3. **File I/O logic error** — `Control_PID()` opens `remote_control.json` for writing
       (`'w'`) before attempting to read it with `json.load()`. This truncates the file
       before reading, causing a `JSONDecodeError`.

    These bugs are tracked and will be fixed in a future release. See
    [Code Improvements](../roadmap/code_improvements.md) for the roadmap.

---

## Purpose

The GUI is designed to:

- Connect to a **Lakeshore 372 AC Resistance Temperature Controller** via GPIB
- Read temperature from two channels simultaneously:
  - **Channel 3** — 1K pot
  - **Channel 4** — Mixing chamber (coldest stage)
- Display a **real-time rolling temperature plot** with a 1–24 hour zoom slider
- Manage **PID controller settings** (load, save, remove profiles) via JSON files
- Support **step-temperature control** through a dedicated dialog

---

## Architecture

The GUI is built around three main classes:

### `MainWindow`

The top-level `QMainWindow`. Contains:

- A `MplCanvas` widget for live temperature plotting
- Controls for Lakeshore channel selection, PID profile management, zoom level
- A `Worker` running in a background thread for all device I/O

### `Worker` (QObject)

Background thread class that:

- Connects to the Lakeshore 372 at `GPIB0::12::INSTR`
- Polls both channels at a configurable interval
- Applies PID corrections and writes output to `remote_control.json`
- Emits Qt signals to update the `MainWindow` plot

### `MplCanvas`

A `FigureCanvasQTAgg` subclass embedding a Matplotlib figure directly in the Qt window.
Used for rolling temperature traces.

---

## Instrument Connection

| Instrument | Interface | Address |
|-----------|-----------|---------|
| Lakeshore 372 | GPIB | `GPIB0::12::INSTR` |

The connection is established via the `optomechanics.device_control.Lakeshore_372_AC_Res_Temp_Controller`
driver. See the [Device Control](device_control.md) guide for general connection patterns.

---

## Temperature Conversion

The `temperature(res)` function converts a PT1000 resistance reading (Ohms) to temperature
(Kelvin) using a polynomial calibration model.

```python
from optomechanics.GUI.Temp_Controller import temperature

T_K = temperature(1000.0)  # PT1000 at 0°C = 273.15 K
```

---

## PID Settings Files

Two JSON files control PID behaviour:

| File | Purpose |
|------|---------|
| `pid_settings.json` | Named PID profiles (P, I, D gains per profile) |
| `remote_control.json` | Active PID setpoint written by `Control_PID()` |

### `pid_settings.json` schema

```json
{
  "profile_name": {
    "Kp": 1.0,
    "Ki": 0.1,
    "Kd": 0.01,
    "setpoint": 4.2
  }
}
```

---

## Running the GUI

Once the known bugs are fixed, launch with:

```python
from optomechanics.GUI.Temp_Controller import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
```

Or directly from the command line:

```bash
python optomechanics/GUI/Temp_Controller.py
```

---

## See Also

- [Device Control](device_control.md) — instrument connection guide
- [Parameter Glossary](glossary.md) — temperature measurement parameters
- [Code Improvements Roadmap](../roadmap/code_improvements.md)
