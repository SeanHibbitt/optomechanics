# Thermal Motion Analysis

This page describes how to post-process saved TSV files from a thermal motion
measurement to extract the vacuum optomechanical coupling rate $g_0$.

See `Scripts/DAQ_templates/SA IQ PSD/AnalysisGoodPartition.ipynb` for a working
example notebook.

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

```python
import pandas as pd
from optomechanics.data_management.data_management import read_file

# Load all SA rows into a DataFrame (one row per sweep)
sa_rows = []
for path in sorted(sa_paths):
    meta, data = read_file(path)
    row = dict(meta)
    row["data"] = data
    sa_rows.append(row)
SA_df = pd.DataFrame(sa_rows)

# Same for VNA S21
vna_rows = []
for path in sorted(vna_paths):
    meta, data = read_file(path)
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

```python
from optomechanics.data_analysis.fitting.Sww import fit_S_xx

m_eff = 150e-15  # effective mass in kg — look up for your membrane mode

result = fit_S_xx.__average_and_fit_S_xx__(
    SA_df         = SA_df,
    select        = {"drive_power": ["-20"], "domain": ["freq"]},
    m_eff         = m_eff,
    S21_df        = S21_df,
    VNA_S21_extra_atten   = vna_extra,
    SG_cavity_to_SA_atten = cavity_to_sa,
    SG_to_cavity_atten    = sg_to_cavity,
)
```

## Step 4 — Extract g₀

```python
g_0   = result["g_0"]    # rad/s
G     = result["G"]      # rad/s/m  (optomechanical coupling rate)
x_zpf = result["x_zpf"]  # m

popt_mech = result["popt_S_xx"]
f_m, G_m, A, nf = popt_mech

print(f"f_m  = {f_m:.1f} Hz")
print(f"Γ_m  = {G_m:.3f} Hz")
print(f"G    = {G/(2*3.14159):.1f} Hz/m")
print(f"x_zpf = {x_zpf*1e15:.2f} fm")
print(f"g₀   = {g_0/(2*3.14159):.1f} Hz")
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
    title=f"Mechanical PSD — g₀/(2π) = {g_0/(2*3.14159):.1f} Hz"
)
fig.show()
```

## See also

- [Thermal Motion Measurement](thermal_motion_measurement.md) — DAQ setup
- [Attenuation Processing](attenuation_processing.md) — building attenuation objects
- [API reference: `fitting.Sww`](../api_reference/data_analysis/fitting/Sww.md)
