# S21 Fitting

This page explains how to fit a microwave cavity transmission (S21) peak using
`optomechanics.data_analysis.fitting.S21`.

## Overview

A microwave cavity measured in transmission shows a Lorentzian peak in $|S_{21}|$.
The fit extracts three physical parameters:

| Parameter | Symbol | Meaning |
|---|---|---|
| Resonance frequency | $f_0$ | Centre of the cavity resonance (Hz) |
| Total linewidth | $\kappa_\text{tot}$ | Full linewidth at half maximum (Hz) |
| External coupling | $\kappa_\text{ext}$ | Coupling rate to the feedline (Hz) |

From these you can derive the internal coupling rate
$\kappa_\text{int} = \kappa_\text{tot} - \kappa_\text{ext}$
and the loaded quality factor $Q = f_0 / \kappa_\text{tot}$.

## Fitting from dB data

The most common case: your VNA returns $|S_{21}|$ in dB.

```python
import numpy as np
from optomechanics.data_management.data_management import read_file
from optomechanics.data_analysis.fitting.S21 import fit_S21_peak_dB

# Load a saved sweep (TSV produced by Device.save_data_3 or similar)
data = read_file("path/to/sweep.tsv")
freqs   = np.array(data["freq[Hz]"])
s21_dB  = np.array(data["sweep_number_mag[dB]:1"])

# Fit — returns popt, pcov, guesses, fitted_trace, fitted_freqs, errors
popt, pcov, guesses, s21_fit, freqs_fit, errors = fit_S21_peak_dB(s21_dB, freqs)

f0, k_tot, k_ext, slope, offset = popt

print(f"Resonance:      {f0/1e9:.6f} GHz")
print(f"Total linewidth: {k_tot/1e6:.3f} MHz")
print(f"Ext. coupling:   {k_ext/1e6:.3f} MHz")
print(f"Int. coupling:   {(k_tot - k_ext)/1e6:.3f} MHz")
print(f"Loaded Q:        {f0/k_tot:.0f}")
```

## Fitting from complex data

If your instrument returns real and imaginary parts (e.g. from the R&S ZNA or FSW in
IQ mode), use `fit_S21_peak_complex`:

```python
from optomechanics.data_analysis.fitting.S21 import fit_S21_peak_complex

re = np.array(data["re"])
im = np.array(data["im"])
s21_complex = re + 1j * im

popt, pcov, guesses, s21_fit, freqs_fit, errors = fit_S21_peak_complex(
    s21_complex, freqs
)
```

## Fitting from linear magnitude

If you have $|S_{21}|$ in linear (voltage) units, use `fit_S21_peak`:

```python
from optomechanics.data_analysis.fitting.S21 import fit_S21_peak

popt, pcov, guesses, s21_fit, freqs_fit, errors = fit_S21_peak(s21_linear, freqs)
```

## Suppressing a drive tone

When a pump tone is present inside the cavity bandwidth during measurement, the fitter
needs to notch it out.  Pass `signal_applied` with the bandwidth and power:

```python
popt, pcov, *_ = fit_S21_peak_dB(
    s21_dB, freqs,
    signal_applied=[bandwidth_hz, power_linear]
)
```

## Plotting the result

```python
import plotly.graph_objects as go
from optomechanics.data_analysis.unit_conversions import linear_voltage_to_dB

fig = go.Figure()
fig.add_scatter(x=freqs/1e9, y=s21_dB, name="Data")
fig.add_scatter(x=freqs_fit/1e9, y=linear_voltage_to_dB(s21_fit), name="Fit")
fig.update_layout(xaxis_title="Frequency (GHz)", yaxis_title="|S21| (dB)")
fig.show()
```

## See also

- [API reference: `fitting.S21`](../api_reference/data_analysis/fitting/S21.md)
- [Device Control: VNA sweep example](device_control.md)
