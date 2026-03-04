# Temperature_Reader

Reads temperature CSV data from a two-level directory hierarchy, returning
time-sorted arrays for downstream analysis.

## Examples

```python
from optomechanics.data_analysis.Temperature_Reader import temp_reader

# Read all temperature CSV files from a dated directory tree
temperatures, times = temp_reader("/path/to/temperature_logs/")

import matplotlib.pyplot as plt
plt.plot(times, temperatures)
plt.xlabel("Time (s)")
plt.ylabel("Temperature (K)")
plt.show()
```

::: optomechanics.data_analysis.Temperature_Reader
