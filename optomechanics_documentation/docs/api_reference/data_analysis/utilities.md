# utilities

General-purpose array helpers and error-propagation tools used internally
by the fitting modules.
Includes nearest-value lookup, dB/linear error conversion, and complex-data
splitting utilities needed when passing complex model functions to
`scipy.optimize` routines.

## Usage examples

```python
import numpy as np
from optomechanics.data_analysis.utilities import find_closest_number

freqs = np.linspace(5.9e9, 6.1e9, 1000)
idx = find_closest_number(freqs, 6.0e9)   # index of element nearest 6 GHz
print(freqs[idx])
```

```python
from optomechanics.data_analysis.utilities import split_complex

data = np.array([1+2j, 3+4j, 5+6j])
real_concat = split_complex(data)
# → array([1., 3., 5., 2., 4., 6.])  (real part then imag part)
```

::: optomechanics.data_analysis.utilities
