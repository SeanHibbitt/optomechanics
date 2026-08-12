# unit_conversions

Reference module of pure RF power conversion functions.
All inputs and outputs are scalars or numpy arrays unless otherwise stated.
Covers dB/linear power ratio conversions, dBm/dBW/watts interconversions, and
RMS/peak/peak-to-peak voltage conversions for a 50 Ω system.

## Usage examples

```python
from optomechanics.data_analysis.unit_conversions import watts_to_dBm, dBm_to_watts

# 1 mW is exactly 0 dBm
watts_to_dBm(1e-3)   # → 0.0

# −30 dBm is 1 µW
dBm_to_watts(-30)    # → 1e-6
```

```python
from optomechanics.data_analysis.unit_conversions import Vpp_to_Vrms, RMS_to_dBm

# Convert a 1 V peak-to-peak signal to dBm (50 Ω)
vrms = Vpp_to_Vrms(1.0)   # → 0.354 V
RMS_to_dBm(vrms)           # → −7.0 dBm
```

::: optomechanics.data_analysis.unit_conversions
