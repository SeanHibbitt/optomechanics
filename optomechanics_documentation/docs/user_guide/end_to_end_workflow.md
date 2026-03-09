# End-to-End Measurement Workflow

## Overview

A complete optomechanical characterisation proceeds through several stages, from
calibrating the microwave attenuation chain all the way to extracting the
single-photon coupling rate $g_0$ and the cooperativity $C$.  This page links
each stage to its detailed guide and shows how parameters flow from one step to
the next.  Use it as a roadmap when setting up a new measurement campaign.

## Workflow diagram

```text
Calibrate attenuation chain
        │
        ▼
Characterise cavity (S21 fit) ──► f₀, κ_tot, κ_ext
        │
        ▼
Set pump tone ──► calculate n_d
        │
        ▼
Acquire noise PSD (spectrum analyser)
        │
        ▼
Normalise PSD to G²S_xx
        │
        ▼
Fit mechanical peak ──► f_m, Γ_m, A
        │
        ▼
Extract g₀ = G · x_zpf
        │
        ▼
Calculate cooperativity C
        │
        ▼
(Optional) Displacement measurement with known g₀
```

## Step-by-step

### Step 1: Calibrate attenuation

Measure the attenuation of each cable and component path using S21 sweeps on the
VNA.  Create `attenuation_object` instances for the signal-generator-to-cavity
and cavity-to-spectrum-analyser paths.  These objects are used later to
normalise the raw PSD to physical units.

:material-arrow-right: [Attenuation Measurement](attenuation_measurement.md),
[Attenuation Processing](attenuation_processing.md)

---

### Step 2: Characterise the cavity

Sweep $S_{21}$ with the VNA and fit the transmission peak to extract the
resonance frequency $f_0$, total linewidth $\kappa_\text{tot}$, and external
coupling rate $\kappa_\text{ext}$.  These cavity parameters feed into every
subsequent calculation.

:material-arrow-right: [S21 Fitting](s21_fitting.md)

---

### Step 3: Set the pump and acquire PSD

Drive the cavity with a pump tone — on-resonance for a calibration measurement,
or red-detuned by $f_m$ for sideband cooling.  Use the spectrum analyser to
acquire the noise power spectral density (PSD) around the mechanical frequency.

:material-arrow-right: [Thermal Motion Measurement](thermal_motion_measurement.md),
[Spectrum Analyser](spectrum_analyser.md)

---

### Step 4: Normalise and fit

Normalise the raw PSD to $G^2 S_{xx}$ using the cavity parameters and
attenuation chain.  Fit the mechanical Lorentzian to extract the mechanical
frequency $f_m$, damping rate $\Gamma_m$, and the single-photon coupling rate
$g_0$.

:material-arrow-right: [Thermal Motion Analysis](thermal_motion_analysis.md)

---

### Step 5: Calculate derived quantities

Compute the intracavity photon number $n_d$ from the input power and cavity
parameters, then calculate the cooperativity
$C = 4 g_0^2 n_d / (\kappa_\text{tot} \Gamma_m)$.  These quantities summarise
the strength of the optomechanical interaction.

:material-arrow-right: [Intracavity Photon Number](photon_number.md),
[Cooperativity](cooperativity.md)

---

### Step 6 (optional): Displacement measurement

With $g_0$ known from the thermal calibration, repeat PSD measurements under
different conditions (e.g. sideband cooling at higher pump power) to extract the
effective temperature $T_\text{eff}$ or mean phonon number $\bar{n}$.

:material-arrow-right: [Displacement Measurement](displacement_measurement.md)

---

## Parameter flow table

The table below shows which step produces each key parameter and where it is
consumed downstream.

| Parameter | Produced by | Used in |
|---|---|---|
| Attenuation objects | Attenuation measurement | PSD normalisation |
| $f_0$, $\kappa_\text{tot}$, $\kappa_\text{ext}$ | S21 fit | $n_d$ calculation, PSD normalisation |
| $n_d$ | `photon_number()` | PSD normalisation, cooperativity |
| $f_m$, $\Gamma_m / 2\pi$ | Sww fit | Cooperativity, quality factor |
| $g_0$ | Thermal motion analysis | Cooperativity, displacement measurement |
| $C$ | Manual calculation | Assess coupling strength |

## Data management tips

Use `dated_file_maker()` to create date-stamped output directories for each
cooldown or measurement session, and `save_data_3()` to write arrays alongside
metadata dictionaries.  Consistent file naming makes it straightforward to
reload data weeks later for re-analysis.

:material-arrow-right: [Data Management](data_management.md)

## See also

- [Attenuation Measurement](attenuation_measurement.md)
- [Attenuation Processing](attenuation_processing.md)
- [S21 Fitting](s21_fitting.md)
- [Thermal Motion Measurement](thermal_motion_measurement.md)
- [Spectrum Analyser](spectrum_analyser.md)
- [Thermal Motion Analysis](thermal_motion_analysis.md)
- [Intracavity Photon Number](photon_number.md)
- [Cooperativity](cooperativity.md)
- [Displacement Measurement](displacement_measurement.md)
- [Data Management](data_management.md)
- [Parameter Glossary](glossary.md)
