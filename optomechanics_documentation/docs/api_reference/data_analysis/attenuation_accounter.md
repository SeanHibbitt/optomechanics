# attenuation_accounter

Utilities for correcting measured dB data by subtracting known cable or
component attenuation.

## Examples

```python
from optomechanics.data_analysis.attenuation_accounter import account_for_attenuation

# Subtract known cable attenuation (dB) from measured signal data (dB)
corrected = account_for_attenuation(measured_db, attenuation_db)
```

::: optomechanics.data_analysis.attenuation_accounter
