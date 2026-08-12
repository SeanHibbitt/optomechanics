# omit (OMIT / OMIA)

Fitting routines for Optomechanically Induced Transparency (OMIT) and
Optomechanically Induced Absorption (OMIA) spectra.  The same lineshape
equation handles both effects via the sign of the amplitude parameter `A`
(positive = transparency peak, negative = absorption dip).  Two fitting
helpers are provided — one with a free background floor and one with a
fixed floor.

## Examples

```python
import numpy as np
from optomechanics.data_analysis.fitting.omit import OMIT_equation, fit_OMIT, fit_OMIT_set_floor

# Evaluate the OMIT lineshape at a set of frequencies
rel_freqs = np.linspace(-100e3, 100e3, 1001)  # relative to carrier (Hz)
transmission = OMIT_equation(
    rel_freqs,
    f_m=49e3,      # mechanical resonance frequency (Hz)
    g_m=300,       # mechanical linewidth (Hz)
    A=0.5,         # OMIT peak amplitude (linear voltage)
    floor=0.1,     # background transmission level (linear voltage)
    kk_tot=1e6,    # total optical linewidth (Hz)
)

# Fit OMIT data with floor as a free parameter
popt, pcov, amplitude_linear, guesses = fit_OMIT(
    rel_freqs, mags_dB, k_tot=1e6, floor=0.1
)
f_m, g_m, A, floor = popt

# Fit with floor held fixed
popt2, pcov2, _, _ = fit_OMIT_set_floor(
    rel_freqs, mags_dB, k_tot=1e6, floor=0.1
)
f_m2, g_m2, A2 = popt2
```

::: optomechanics.data_analysis.fitting.omit
