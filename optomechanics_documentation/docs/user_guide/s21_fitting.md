# Cavity Transmission (S21)

This page explains the physics of microwave cavity transmission and how to fit
an S21 peak using `optomechanics.data_analysis.fitting.S21`.

## Physics background

In a microwave optomechanics experiment the electromagnetic cavity is typically a
lumped-element LC resonator coupled to a feedline through coupling capacitors.
Measuring the forward transmission coefficient $S_{21}$ as a function of frequency
reveals the cavity resonance as a Lorentzian peak.  The lineshape encodes three
quantities that are essential for all subsequent analysis: the resonance frequency
$f_0$, the total energy decay rate $\kappa_\text{tot}$, and the external coupling
rate $\kappa_\text{ext}$.

The Lorentzian arises because the cavity acts as a single-pole bandpass filter.
Near resonance the transmitted amplitude is proportional to
$\kappa_\text{ext} / (\kappa_\text{tot} + 2j \Delta)$, where
$\Delta = f - f_0$ is the detuning.  Away from resonance the numerator is
overwhelmed by the imaginary part of the denominator and the transmission falls.

## Circuit model

This code assumes a **two-port transmission** topology: two coupling capacitors in
series with a parallel LCR resonator between them.  The S21 equation below is the
transmission coefficient for this specific geometry.  Other topologies — notch
(hanger) or reflection — give different functional forms and should not be fitted
with this equation.

## S21 equation

The code computes (see `S21_eq` in `fitting/S21.py`):

$$
S_{21}(f) = \left| \frac{\kappa_\text{ext}}{\kappa_\text{tot} + 2j(f - f_0)} \right| + m \cdot f + c
$$

where $m$ and $c$ are a linear background.  Note that all frequencies are in Hz —
the factors of $2\pi$ cancel between numerator and denominator.

| LaTeX symbol | Code parameter | Description |
|---|---|---|
| $f_0$ | `f_0` / `p[0]` | Cavity resonance frequency (Hz) |
| $\kappa_\text{tot}$ | `k_tot` / `p[1]` | Total cavity linewidth (Hz) |
| $\kappa_\text{ext}$ | `k_ext` / `p[2]` | External coupling rate (Hz) |
| $m$ | `att_m` / `p[3]` | Linear background slope |
| $c$ | `att_c` / `p[4]` | Background offset |

## Coupling regimes

The ratio $\kappa_\text{ext} / \kappa_\text{tot}$ determines the coupling regime:

- **Overcoupled** ($\kappa_\text{ext} > \kappa_\text{int}$): most energy leaves through
  the ports.  On-resonance transmission is high.
- **Critically coupled** ($\kappa_\text{ext} = \kappa_\text{int}$): maximum extinction
  in reflection; transmission is exactly half.
- **Undercoupled** ($\kappa_\text{ext} < \kappa_\text{int}$): internal losses dominate.
  On-resonance transmission is low.

Here $\kappa_\text{int} = \kappa_\text{tot} - \kappa_\text{ext}$ is the intrinsic
(internal) loss rate.

## References

- "A Novel Architecture for room temperature microwave optomechanical experiments" —
  source of the photon number equation used alongside S21 fits.
- S. Kumar (2023) — thermal force PSD and SHO model.
- X. Rojas et al. (2022-11-28) eqs. 3–5 — $g_0$ extraction from fitted $S_{ww}$.

## Interpreting results

| Parameter | Typical range | Notes |
|---|---|---|
| $f_0$ | 1–10 GHz | Set by cavity geometry |
| $\kappa_\text{tot}$ | 10 kHz – 10 MHz | Narrower = higher Q |
| $\kappa_\text{ext}/\kappa_\text{tot}$ | 0.3–0.7 | < 0.5 undercoupled, > 0.5 overcoupled |
| `att_m` | small negative | Cable loss increasing with frequency |
| `att_c` | ≈ 0 | Residual background level |

---

## Overview

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
# read_file returns (data_pandas, meta_data)
data, meta = read_file("path/to/sweep.tsv")
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

- [Parameter Glossary](glossary.md) — definitions of all optomechanical parameters
- [API reference: `fitting.S21`](../api_reference/data_analysis/fitting/S21.md)
- [Device Control: VNA sweep example](device_control.md)
