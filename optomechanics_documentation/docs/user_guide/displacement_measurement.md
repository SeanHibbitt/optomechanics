# Displacement Measurement

This page describes how to extract an **effective temperature** $T_\text{eff}$ from
a measured mechanical PSD when the optomechanical coupling $g_0$ (or $G$,
$x_\text{zpf}$) is already known — typically from a prior
[thermal calibration](thermal_motion_analysis.md).

## When to use this analysis

The [thermal motion analysis](thermal_motion_analysis.md) assumes the mechanical
mode is purely thermally driven at a **known** temperature $T$, and uses this to
extract $g_0$.  The displacement measurement is the **inverse problem**: given a
known $g_0$, extract the effective temperature $T_\text{eff}$ of the mechanical
mode.

This is the appropriate analysis when:

- Backaction cooling is present (red-sideband pumping modifies $T_\text{eff}$)
- An external drive is applied to the mechanics
- The fridge temperature is unknown or changing
- You want to verify thermal equilibrium by comparing $T_\text{eff}$ with the
  thermometer reading

## Input parameters

| Parameter | Source | Description |
|---|---|---|
| $g_0$ | Thermal calibration | Vacuum optomechanical coupling rate (Hz) |
| $G = g_0 / x_\text{zpf}$ | Thermal calibration | Frequency pull parameter (Hz/m) |
| $x_\text{zpf}$ | Known mass + frequency | Zero-point fluctuation amplitude (m) |
| $m_\text{eff}$ | Device geometry / FEM | Effective motional mass (kg) |
| $\Omega_m$ | Sww fit | Mechanical resonance frequency (Hz) |
| PSD data | Spectrum analyser | Normalised $G^2 S_{xx}$ spectrum |

## Converting PSD to displacement

With known $G$, the normalised spectrum $G^2 S_{xx}$ from the measurement pipeline
can be converted directly to a displacement spectral density:

$$
S_{xx}(f) = \frac{G^2 S_{xx}(f)}{G^2} \quad [\text{m}^2/\text{Hz}]
$$

## Extracting $T_\text{eff}$

Two methods can extract the effective temperature from $S_{xx}$.

### Method 1 — Lorentzian fit (recommended)

Fit the displacement PSD with the Lorentzian model (`basic_S_ww_eq`):

$$
S_{xx}(f) = \frac{A}{\Gamma_m^2 + 4(f - f_m)^2} + n_f
$$

The fit amplitude $A$ relates to the thermal force spectral density via the
mechanical susceptibility.  With known $G$, the effective temperature is:

$$
T_\text{eff} = \frac{A \cdot m_\text{eff} \cdot \Omega_m^2}{4\, k_B\, G^2}
$$

where the factor comes from inverting the thermal force relation
$S_{FF}^\text{th} = 4\, k_B\, T_\text{eff}\, m_\text{eff}\, \Gamma_m$.

**Advantages:** Naturally separates the mechanical peak from the noise floor $n_f$.
Simultaneously extracts $\Gamma_m$ and $f_m$, which may change under backaction.

### Method 2 — Integration (equipartition)

Integrate $S_{xx}$ over frequency to get the mean-square displacement, then apply
the equipartition theorem:

$$
\langle x^2 \rangle = \int_{-\infty}^{\infty} S_{xx}(f)\, df
$$

$$
\frac{1}{2}\, m_\text{eff}\, \Omega_m^2\, \langle x^2 \rangle = \frac{1}{2}\, k_B\, T_\text{eff}
$$

$$
T_\text{eff} = \frac{m_\text{eff}\, \Omega_m^2\, \langle x^2 \rangle}{k_B}
$$

In practice, the integral is computed over a finite frequency range using
`numpy.trapz` (or `numpy.trapezoid`):

```python
import numpy as np

# Subtract noise floor before integrating
S_xx_subtracted = S_xx - noise_floor
x_sq = np.trapz(S_xx_subtracted, freqs)

k_b = 1.3806e-23
T_eff = m_eff * (2 * np.pi * f_m)**2 * x_sq / k_b
```

**Caveats:**

- Sensitive to noise floor subtraction — a small offset integrates to a large bias
- Requires the integration range to capture the full Lorentzian peak
- Nearby mechanical modes or spurious peaks corrupt the integral
- The fitting method is generally more robust

## Comparison with thermal motion analysis

| | Thermal motion analysis | Displacement measurement |
|---|---|---|
| **Assumes** | Known $T$ | Known $g_0$ / $G$ |
| **Extracts** | $g_0$ | $T_\text{eff}$ |
| **Use case** | Calibration at known $T$ | Cooling / heating experiments |
| **Pump position** | On-resonance (maximise $n_d$) | Red sideband (cooling) or any |

The two analyses are complementary: first calibrate $g_0$ at a known temperature,
then use the displacement measurement to track $T_\text{eff}$ as experimental
conditions change.

## See also

- [Thermal Motion Analysis](thermal_motion_analysis.md) — the inverse problem ($T$ known, extract $g_0$)
- [Thermal Motion Measurement](thermal_motion_measurement.md) — DAQ setup
- [API reference: `fitting.Sww`](../api_reference/data_analysis/fitting/Sww.md)
- [Parameter Glossary](glossary.md)
