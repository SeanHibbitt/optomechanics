# file_management

Utilities for constructing dated directory paths for measurement data.
`dated_file_maker` automatically creates a `year/month_name/day` folder
hierarchy under a given base path, making it straightforward to organise
experimental data by date without manual directory creation.

## Usage examples

```python
from optomechanics.data_management.file_management import dated_file_maker

# Creates (if absent) e.g. C:\Data\2026\March\8\
save_path = dated_file_maker(r"C:\Data")
print(save_path)   # → 'C:\Data\2026\March\8\'
```

```python
from optomechanics.data_management.file_management import dated_file_maker
from optomechanics.data_management.data_management import save_data_3
import numpy as np

freqs = np.linspace(1e9, 2e9, 501)
power = np.random.randn(501)

path = dated_file_maker(r"C:\ExperimentData")
save_data_3(
    [freqs, power],
    file_name="spectrum.tsv",
    file_location=path,
    headers="Frequency[Hz]\tPower[dBm]",
    meta_data={"instrument": "VNA", "averages": "10"},
)
```

::: optomechanics.data_management.file_management
