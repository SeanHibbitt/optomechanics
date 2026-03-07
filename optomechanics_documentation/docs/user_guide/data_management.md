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

file_path = dated_file_maker("/data/sweeps")
# → "/data/sweeps/2024/July/15/"  (example)
```

### `data_management`

Core read/write helpers for saving and loading numpy arrays and metadata alongside
measurement data files.

**Saving data:**

```python
from optomechanics.data_management.data_management import save_data_3
from optomechanics.data_management.file_management import dated_file_maker
import numpy as np

freqs  = np.linspace(6.99e9, 7.01e9, 801)
s21_dB = np.random.randn(801)   # replace with real data

file_path = dated_file_maker("/data/sweeps")

data = np.array([freqs, s21_dB])
save_data_3(
    data,
    "cavity_S21.tsv",
    file_location=file_path,
    headers="freq[Hz]\tsweep_number_mag[dB]:1",
    meta_data={"timestamp[s]": 1721000000, "IF_bandwidth": 300}
)
```

**Loading data:**

`read_file` returns a `(data, meta)` tuple: a `pandas.DataFrame` of data rows and a
`dict` of metadata key-value pairs.

```python
from optomechanics.data_management.data_management import read_file

data, meta = read_file("path/to/cavity_S21.tsv")
freqs  = data["freq[Hz]"]
s21_dB = data["sweep_number_mag[dB]:1"]
print(meta)   # dict of metadata key-value pairs
```

**Reading metadata only:**

```python
from optomechanics.data_management.data_management import read_meta_data

meta = read_meta_data("path/to/cavity_S21.tsv")
```

### `data_logger`

Provides continuous logging functionality for slow quantities such as temperature or
pressure during a long measurement.

**One-shot logger:**

```python
from optomechanics.data_management.data_logger import logger

log = logger("temperature_log.tsv", columns=["time[s]", "T_mc[K]"])
log.create()

import time
for _ in range(10):
    t = time.time()
    T = temp_controller.read_temp()
    log({"time[s]": t, "T_mc[K]": T})
    time.sleep(60)
```

**Dated logger** (automatically rolls over to a new file at midnight):

```python
from optomechanics.data_management.data_logger import dated_logger

log = dated_logger("/data/logs", "temperature", columns=["time[s]", "T_mc[K]"])
log.create()

log({"time[s]": time.time(), "T_mc[K]": T})
# File path is updated automatically each day
```

## Attenuation accounting

The `attenuation_object` (imported via `optomechanics.data_management`) keeps track of the
total signal attenuation between the device and the measurement instrument.  Fitting
routines in `data_analysis.fitting` accept this object to automatically correct
measured powers before fitting.

```python
from optomechanics.data_management import attenuation_object

# Load a previously measured attenuation profile
path_loss = attenuation_object()
path_loss.load_from_tsv("path/to/cable_attenuation.tsv")

# Interpolate at a specific frequency
loss_at_7GHz = path_loss(7e9)   # dB

# Apply to a data array
import numpy as np
sa_powers_dBm = np.array([...])
sa_freqs      = np.array([...])
measured = attenuation_object(sa_powers_dBm, sa_freqs)
corrected_dBm = (measured - path_loss).magnitude
```

See the [Attenuation Processing](attenuation_processing.md) guide for more detail.

## See also

- [API Reference: `data_management`](../api_reference/data_management/index.md)
- [Attenuation Measurement](attenuation_measurement.md)
- [Attenuation Processing](attenuation_processing.md)
