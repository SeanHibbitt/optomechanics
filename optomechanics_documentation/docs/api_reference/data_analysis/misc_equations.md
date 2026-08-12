# misc_equations

Contains physics equations used in optomechanical experiments.
Currently provides `photon_number`, which calculates the steady-state intracavity
photon number for a microwave cavity driven on or near resonance.
All frequency arguments must be supplied in Hz (not angular frequency).

## Usage examples

```python
from optomechanics.data_analysis.misc_equations import photon_number
from optomechanics.data_analysis.unit_conversions import dBm_to_watts

# Typical microwave cavity at ~6 GHz, −20 dBm drive power
f_c     = 6.0e9          # cavity resonance (Hz)
f_d     = f_c            # drive on resonance
k_ext   = 1e6            # coupling linewidth (Hz)
k_tot   = 3e6            # total linewidth (Hz)
P_in    = dBm_to_watts(-20)

n_cav = photon_number(f_d, f_c, k_ext, k_tot, P_in)
print(f"Intracavity photon number: {n_cav:.2e}")
```

::: optomechanics.data_analysis.misc_equations
