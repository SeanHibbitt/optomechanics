# Thermal Motion Analysis

This page describes how to post-process saved TSV files from a thermal motion
measurement to extract the vacuum optomechanical coupling rate $g_0$.

See `Scripts/DAQ_templates/SA IQ PSD/AnalysisGoodPartition.ipynb` for a working
example notebook.

## Physics background

A mechanical resonator in thermal equilibrium at temperature $T$ is driven by
Brownian (Langevin) force noise.  When $k_B T \gg \hbar\omega_m$ — which is
always true at room temperature for MHz-scale modes — the thermal force spectral
density is white (frequency-independent):

$$
S_{FF}^\text{th} = 4\, k_B\, T\, m_\text{eff}\, \gamma_m
$$

where $\gamma_m = 2\pi\Gamma_m$ is the angular damping rate.

The resulting displacement spectral density $S_{xx}$ is the product of this
flat force spectrum and the mechanical susceptibility:

$$
S_{xx}(\omega) = \frac{S_{FF}^\text{th}}{m_\text{eff}^2
\left[(\omega_m^2 - \omega^2)^2 + \gamma_m^2\,\omega^2\right]}
$$

where $\omega = 2\pi f$ and $\omega_m = 2\pi f_m$.
This is the full mechanical susceptibility (see `basic_S_ww_eq_2` in `Sww.py`).

Near resonance ($f \approx f_m$), the approximation
$\omega_m^2 - \omega^2 \approx 2\omega_m(\omega_m - \omega)$ simplifies the
susceptibility to the Lorentzian form used by `basic_S_ww_eq` and `SHO_TF_sq`:

$$
S_{ww}(\omega) = \frac{A}{\gamma_m^2 + 4(\omega - \omega_m)^2} + n_f
$$

where $A$ is the fitted amplitude and $n_f$ is the noise floor.

!!! warning "Internal angular-frequency conversion"
    `basic_S_ww_eq` accepts all inputs in **Hz** but converts to angular
    frequency ($\times 2\pi$) internally before evaluating the equation above.
    The fitted $A$ is therefore in angular-frequency units — do not plug Hz
    values into the formula directly.

### The thermal assumption

This analysis **assumes** the mechanical motion is purely thermally driven at
a **known** temperature $T$.  This lets you extract $g_0$ from the measured PSD
amplitude.  The assumption is valid when:

- $k_B T \gg \hbar\omega_m$ (classical limit — always true at room temperature)
- There is no significant optomechanical backaction cooling ($n_d$ not too high)
- No external drive is applied to the mechanics

### $G^2 S_{xx}$ normalisation

The raw spectrum analyser output is in dBm (or watts).  The code normalises it to
$G^2 S_{xx}$ by dividing by a constant derived from the cavity parameters
(see `__normalise_Sww_to_GGSxx__` in `Sww.py`):

$$
\text{normalisation} = \frac{\kappa_\text{ext}^\text{Hz}\, n_d}
{\left(\kappa_\text{tot}^\text{Hz}\right)^2}\;
\hbar\, \omega_c
$$

where $\kappa_\text{ext}^\text{Hz}$ and $\kappa_\text{tot}^\text{Hz}$ are in Hz
(as returned by the S21 fitter) and $\omega_c = 2\pi f_c$ is in rad/s.

This converts measured power to the dimensionless quantity $G^2 S_{xx}$, from which
$G$ can be extracted via the fit amplitude $A$ and the thermal force relation.

### $g_0$ extraction

From the fitted amplitude $A$ of the $G^2 S_{xx}$ Lorentzian, the code extracts
$G$ using the thermal force relation (see `__average_and_fit_S_xx__` in `Sww.py`,
line 395):

$$
G = \sqrt{\frac{A \cdot m_\text{eff}\, \omega_m^2}
{4\, k_B\, T\, \gamma_m}}
$$

where $\omega_m = 2\pi f_m$ and $\gamma_m = 2\pi\Gamma_m$ are in rad/s, and
$A$ is the amplitude from fitting $G^2 S_{xx}$ (already normalised by the cavity
parameters above).

$$
x_\text{zpf} = \sqrt{\frac{\hbar}{2\, m_\text{eff}\, \omega_m}}, \qquad
g_0 = G \cdot x_\text{zpf}
$$

!!! note "Units of the returned values"
    `__average_and_fit_S_xx__` returns $g_0$ and $G$ in **rad/s** (angular
    frequency).  Divide by $2\pi$ to convert to Hz.  The separate function
    `S_ww_constant_calculator` returns in **Hz** — do not confuse the two.

### Interpreting results

| Parameter | Typical range | What it tells you |
|---|---|---|
| $f_m$ | 100 kHz – 10 MHz | Mechanical mode frequency |
| $\Gamma_m / 2\pi$ | 0.1 – 100 Hz | Mechanical damping (narrower = higher $Q_m$) |
| $G/(2\pi)$ | $10^{12}$ – $10^{15}$ Hz/m | Frequency pull — larger means stronger coupling geometry |
| $g_0/(2\pi)$ | 0.01 – 100 Hz | Vacuum coupling rate — the key figure of merit |

---

## Overview

The analysis pipeline is:

```
Load SA + VNA TSV files
        ↓
Normalise PSD to G²S_xx  (fit_S_xx.__normalise_Sww_to_GGSxx__)
        ↓
Average over sweeps at the same drive power
        ↓
Fit basic_S_ww_eq to extract G, Γ_m, f_m
        ↓
Calculate g₀ = G · x_zpf
```

## Step 1 — Load the saved data

`sa_paths` and `vna_paths` are lists of file paths to the TSV files saved during
the measurement (see [Thermal Motion Measurement](thermal_motion_measurement.md)).
Use `glob.glob` or `pathlib.Path.glob` to collect them from the dated directories.

```python
import glob
import pandas as pd
from optomechanics.data_management.data_management import read_file

sa_paths  = sorted(glob.glob("/data/thermal_motion/*/SA_*.tsv"))
vna_paths = sorted(glob.glob("/data/thermal_motion/*/S21_*.tsv"))

# Load all SA rows into a DataFrame (one row per sweep)
sa_rows = []
for path in sorted(sa_paths):
    data, meta = read_file(path)
    row = dict(meta)
    row["data"] = data
    sa_rows.append(row)
SA_df = pd.DataFrame(sa_rows)

# Same for VNA S21
vna_rows = []
for path in sorted(vna_paths):
    data, meta = read_file(path)
    row = dict(meta)
    row["data"] = data
    vna_rows.append(row)
S21_df = pd.DataFrame(vna_rows)
```

## Step 2 — Load attenuation objects

```python
from optomechanics.data_management import attenuation_object

# Path from cavity output to SA
cavity_to_sa = attenuation_object()
cavity_to_sa.load_from_tsv("cavity_to_sa_atten.tsv")

# Path from signal generator to cavity
sg_to_cavity = attenuation_object()
sg_to_cavity.load_from_tsv("sg_to_cavity_atten.tsv")

# Extra VNA attenuation (set to None to skip)
vna_extra = attenuation_object()
vna_extra.load_from_tsv("vna_extra_atten.tsv")
# or: vna_extra = None
```

## Step 3 — Normalise and fit

`fit_S_xx` is a class whose methods handle normalisation and fitting.
`__average_and_fit_S_xx__` is the main entry point that averages sweeps at the
same drive power, normalises to $G^2 S_{xx}$, and fits the Lorentzian model.

```python
from optomechanics.data_analysis.fitting.Sww import fit_S_xx

m_eff = 150e-15  # effective mass in kg — look up for your membrane mode

result = fit_S_xx.__average_and_fit_S_xx__(
    SA_df         = SA_df,
    select        = {"drive_power": ["-20"], "domain": ["freq"]},
    # select filters rows in SA_df; values must match metadata strings as saved
    m_eff         = m_eff,
    S21_df        = S21_df,
    VNA_S21_extra_atten   = vna_extra,
    SG_cavity_to_SA_atten = cavity_to_sa,
    SG_to_cavity_atten    = sg_to_cavity,
)
```

!!! note "Internal API"
    `__average_and_fit_S_xx__` uses Python's dunder (double-underscore) naming convention,
    which typically indicates a private method. Despite this, it is currently the intended
    entry point for averaging and fitting spectral density data. The naming is a known API
    issue and will be updated in a future refactor.

## Step 4 — Extract g₀

```python
g_0   = result["g_0"]    # rad/s
G     = result["G"]      # rad/s/m  (optomechanical coupling rate)
x_zpf = result["x_zpf"]  # m

popt_mech = result["popt_S_xx"]
f_m, G_m, A, nf = popt_mech

print(f"f_m  = {f_m:.1f} Hz")
print(f"Γ_m/(2π) = {G_m:.3f} Hz")
print(f"G    = {G/(2*np.pi):.1f} Hz/m")
print(f"x_zpf = {x_zpf*1e15:.2f} fm")
print(f"g₀   = {g_0/(2*np.pi):.1f} Hz")
```

## Step 5 — Plot

```python
import plotly.graph_objects as go
import numpy as np

freqs = result["S_xx_freqs"]
GGSxx_avg = result["GG_S_norm_avg"]
GGSxx_fit = result["GG_S_norm_fit"]

fig = go.Figure()
fig.add_scatter(x=freqs, y=GGSxx_avg, name="G²S_xx (data)", mode="lines")
fig.add_scatter(x=freqs, y=GGSxx_fit, name="Fit", mode="lines",
                line=dict(dash="dash"))
fig.update_layout(
    xaxis_title="Frequency offset (Hz)",
    yaxis_title="G²S_xx",
    title=f"Mechanical PSD — g₀/(2π) = {g_0/(2*np.pi):.1f} Hz"
)
fig.show()
```

## See also

- [Thermal Motion Measurement](thermal_motion_measurement.md) — DAQ setup
- [Attenuation Processing](attenuation_processing.md) — building attenuation objects
- [API reference: `fitting.Sww`](../api_reference/data_analysis/fitting/Sww.md)
- [Parameter Glossary](glossary.md)
