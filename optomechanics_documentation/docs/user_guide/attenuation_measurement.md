# Attenuation Measurement

This page explains how to measure the frequency-dependent attenuation of a cable or
component chain using the E5063A VNA and save the result as an `attenuation_object`.

## Overview

The VNA measures $|S_{21}|$ across a frequency span.  For a through-connected cable
this gives the insertion loss (attenuation) as a function of frequency.  Saving this
as an `attenuation_object` lets the fitting routines automatically correct measured
powers to account for the path loss.

## Step 1 — VNA sweep

Connect the cable under test between VNA port 1 and port 2, then sweep:

```python
from optomechanics.device_control.E5063A_VNA_Class_new import VNA

with VNA("GPIB0::17::INSTR") as vna:
    vna.set_start_frequency(1e6)       # 1 MHz
    vna.set_stop_frequency(10e9)       # 10 GHz
    vna.set_number_of_points(1601)
    vna.set_IF_bandwidth(1000)         # 1 kHz IF BW
    vna.set_measurement_parameter("S21")
    vna.sweep()

    freqs   = vna.get_frequency_data()
    s21_dB  = vna.get_formatted_data()  # |S21| in dB
```

## Step 2 — Build the attenuation_object

The S21 magnitude in dB **is** the attenuation (a negative number means loss):

```python
import numpy as np
from optomechanics.data_management import attenuation_object

# Attenuation is the negative of S21 (positive dB = loss convention)
atten = attenuation_object(-s21_dB, freqs)

# Save for later use
atten.save_to_tsv("cable_attenuation.tsv")
```

!!! note "Sign convention"
    `attenuation_object` stores **positive** values for loss.  If your VNA returns
    S21 as a negative number (which is typical for a lossy cable), negate it before
    wrapping in `attenuation_object`.

## Step 3 — Verify

Plot the result to check for unexpected resonances or noise:

```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_scatter(x=freqs/1e9, y=atten.magnitude, mode="lines")
fig.update_layout(
    xaxis_title="Frequency (GHz)",
    yaxis_title="Attenuation (dB)",
    title="Cable insertion loss"
)
fig.show()
```

## Combining multiple segments

If the signal passes through several cables and attenuators, measure each separately
and add them:

```python
from optomechanics.data_management import attenuation_object

cable_a = attenuation_object(); cable_a.load_from_tsv("cable_a.tsv")
cable_b = attenuation_object(); cable_b.load_from_tsv("cable_b.tsv")
pad_20dB = attenuation_object(20.0, 7e9)   # flat 20 dB attenuator

total_path = cable_a + cable_b + pad_20dB
total_path.save_to_tsv("total_path.tsv")
```

## See also

- [Attenuation Processing](attenuation_processing.md) — using `attenuation_object` in analysis
- [API reference: `data_management`](../api_reference/data_management/data_management.md)
- [Device Control: VNA examples](device_control.md)
