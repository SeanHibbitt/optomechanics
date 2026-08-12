# data_management

Core file read/write helpers and the `attenuation_object` class for
frequency-dependent attenuation book-keeping.
`read_file` and `save_data_3` handle tab-separated data files with `#`-prefixed
metadata lines.  `attenuation_object` stores a magnitude array (dB) alongside
its frequency grid and supports `+`/`-` arithmetic with automatic interpolation
and quadrature error propagation.

## Usage examples

```python
from optomechanics.data_management.data_management import attenuation_object
import numpy as np

# Build two attenuation objects over the same frequency range
freqs = np.linspace(1e9, 10e9, 100)
cable = attenuation_object(np.full(100, 3.0), freqs)          # 3 dB flat
attenuator = attenuation_object(np.full(100, 20.0), freqs)    # 20 dB flat

total = cable + attenuator   # → 23 dB (errors propagated in quadrature)
print(total.magnitude[0])    # 23.0
```

```python
from optomechanics.data_management.data_management import attenuation_object

# Load a previously saved attenuation calibration from a TSV file
atten = attenuation_object.load_from_tsv("cable_calibration.tsv")
mag, freqs = atten()          # unpack magnitude and frequency arrays
```

::: optomechanics.data_management.data_management
