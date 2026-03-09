# Temp_Controller

!!! warning "Autodoc unavailable"
    This module requires `PyQt5` and has broken import paths, so mkdocstrings cannot
    collect it automatically. The API is documented manually below.

**File:** `optomechanics/GUI/Temp_Controller.py`

---

## Functions

### `temperature(res)`

Converts a PT1000 resistance reading (Ohms) to temperature (Kelvin) using a
polynomial calibration model.

| Parameter | Type | Description |
|-----------|------|-------------|
| `res` | float | Resistance in Ohms |

**Returns:** `float` — Temperature in Kelvin.

---

### `Control_PID(pid_settings)`

Writes a PID settings dict to `remote_control.json`.

!!! bug
    Currently opens the file in write mode (`'w'`) before attempting to read it,
    which truncates the file. This will be fixed in a future release.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pid_settings` | dict | PID parameters to write |

---

## Classes

### `Worker`

Background `QObject` running in a separate thread, handling all device I/O and
PID control logic.

| Method | Description |
|--------|-------------|
| `load_pid_settings()` | Reads PID profiles from `pid_settings.json` |
| `run()` | Main polling loop — reads Lakeshore 372 channels and applies PID |

---

### `MplCanvas`

`FigureCanvasQTAgg` subclass embedding a Matplotlib figure in the Qt window for
real-time temperature trace plotting.

---

### `StepTemperatureDialog`

`QDialog` subclass for entering step-temperature control parameters.

---

### `MainWindow`

Top-level `QMainWindow`. Hosts the `MplCanvas`, control widgets, and manages the
`Worker` thread lifecycle.
