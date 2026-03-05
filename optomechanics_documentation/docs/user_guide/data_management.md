# Data Management

The `optomechanics.data_management` subpackage handles file I/O, data logging, and
attenuation book-keeping.

## Modules

### `file_management`

Provides `dated_file_maker`, which creates a uniquely dated file path under a given base
directory.  Keeping raw data in dated folders makes it easy to trace measurements back to
specific experimental sessions.

```python
from optomechanics.data_management.file_management import dated_file_maker

file_path = dated_file_maker("/data/sweeps", "S21_run01")
# → "/data/sweeps/2024-07-15/S21_run01.csv"  (example)
```

### `data_management`

Core read/write helpers for saving and loading numpy arrays and metadata alongside
measurement data files.

### `data_logger`

Provides continuous logging functionality for slow quantities such as temperature or
pressure during a long measurement.

## Attenuation accounting

The `attenuation_object` (imported via `optomechanics.data_management`) keeps track of the
total signal attenuation between the device and the measurement instrument.  Fitting
routines in `data_analysis.fitting` accept this object to automatically correct
measured powers before fitting.

See the [API Reference](../api_reference/data_management/index.md) for full details.
