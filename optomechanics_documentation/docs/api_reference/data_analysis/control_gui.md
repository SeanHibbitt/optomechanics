# control_gui

PID feedback control GUI for real-time experiment control.
Reads a configuration file, runs the PID loop, and returns the measured value.

## Examples

```python
from optomechanics.data_analysis.control_gui import Control_PID

# Launch the PID control GUI; returns float measurement or None on error
value = Control_PID(config_path="/path/to/pid_config.json")
if value is not None:
    print(f"Measured value: {value}")
```

::: optomechanics.data_analysis.control_gui
