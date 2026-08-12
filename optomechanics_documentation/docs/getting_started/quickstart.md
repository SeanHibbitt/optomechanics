# Quick Start

This page shows the most common operations you will perform with the package.

## Fitting an S21 cavity response

```python
import numpy as np
from optomechanics.data_analysis.fitting.S21 import fit_S21_peak_dB

# Load your frequency sweep data
frequencies = np.linspace(6.99e9, 7.01e9, 1001)   # Hz
powers_dB   = np.zeros(1001)                        # replace with measured S21 in dB

# Fit — returns optimal parameters, covariance, initial guesses,
#        the fitted trace, the frequency axis for the fit, and fit errors
popt, pcov, guesses, s21_fit, freqs_fit, errors = fit_S21_peak_dB(
    powers_dB, frequencies
)

f_0    = popt[0]   # resonance frequency (Hz)
k_tot  = popt[1]   # total linewidth (Hz)
k_ext  = popt[2]   # external coupling rate (Hz)

print(f"f_0   = {f_0/1e9:.6f} GHz")
print(f"k_tot = {k_tot/1e6:.3f} MHz")
print(f"k_ext = {k_ext/1e6:.3f} MHz")
```

## Unit conversions

```python
from optomechanics.data_analysis.unit_conversions import dBm_to_watts, Vrms_to_dBm

power_W   = dBm_to_watts(-20)    # -20 dBm → watts
power_dBm = Vrms_to_dBm(1e-3)   # 1 mV RMS → dBm (50 Ω)
```

## Membrane resonance frequency

```python
from optomechanics.data_analysis.square_membrane import membrane

mem = membrane(
    length_x=1.5e-3,           # m
    length_y=1.5e-3,           # m
    height_of_sin=100e-9,      # m  (SiN thickness)
    depth_deposition=10e-9,    # m
    density_of_deposition=19300,  # kg/m³  (gold)
)

# Fundamental mode (1,1)
f_reduced, f_bare = mem.fm(m_x=1, n_y=1)
print(f"Bare frequency:    {f_bare/1e3:.1f} kHz")
print(f"Reduced frequency: {f_reduced/1e3:.1f} kHz")
```

## Next steps

- [User Guide](../user_guide/index.md) — conceptual overview of each subpackage
- [API Reference](../api_reference/index.md) — full function and class documentation
