# OMIT Analysis

This page describes Optomechanically Induced Transparency (OMIT) — an interference
effect between the cavity and mechanical responses — and how to fit OMIT spectra
using the functions in `fitting.omit`.

## Physics background

When a strong pump tone drives the cavity and a weak probe tone sweeps across the
cavity resonance, the mechanical resonator mediates an interference between the
direct probe transmission and the probe light scattered via the mechanics.  This
creates a narrow **transparency window** (or absorption dip, depending on detuning)
at the mechanical frequency — analogous to electromagnetically induced transparency
(EIT) in atomic physics.

OMIT appears as a sharp feature in the cavity transmission, with a width set by the
mechanical linewidth $\Gamma_m$ and an amplitude that depends on the optomechanical
cooperativity $C$.

### OMIT equation

The code implements the OMIT lineshape in `OMIT_equation`:

$$
\text{OMIT}(f) = \text{floor} \times \left(1 + A \left|\frac{1}{(\omega_m^2 - \omega^2 - i\gamma_m\omega)(\kappa - 2i\omega)}\right|\right)
$$

where $\omega = 2\pi f$, $\omega_m = 2\pi f_m$, $\gamma_m = 2\pi\,$`g_m`,
and $\kappa = 2\pi\,$`kk_tot`.  All code inputs are in **Hz**; the conversion
to angular frequency happens internally.

The parameters `A` and `floor` encode the cavity and optomechanical properties:

$$
A = \frac{\kappa_\text{ext} \cdot 4\omega_m g_0^2 n_d}{\sqrt{\kappa^4 + 4(\omega_p - \omega_c)^2}}
$$

$$
\text{floor} = \sqrt{\frac{\kappa_\text{ext}^2}{\sqrt{\kappa^4 + 4(\omega_p - \omega_c)^2}}}
$$

## Fit parameters

| Parameter | Code name | Units | Description |
|---|---|---|---|
| $f_m$ | `f_m` | Hz | Mechanical resonance frequency |
| $\Gamma_m$ | `g_m` | Hz | Mechanical linewidth (damping rate) |
| $A$ | `A` | linear voltage | OMIT peak amplitude |
| floor | `floor` | linear voltage | Background transmission level |
| $\kappa_\text{tot}$ | `kk_tot` | Hz | Total cavity linewidth (held fixed) |

## Fitting workflow

### Step 1 — Prepare the data

The input data should be a VNA or network analyser sweep of S21 magnitude around
the mechanical frequency, with the pump tone applied.  Convert to relative
frequencies centred on the mechanical feature.

### Step 2 — Choose a fitting function

Two fitting functions are available:

- **`fit_OMIT(rel_freqs, mags_dB, k_tot, floor, guesses)`** — fits all four
  parameters ($f_m$, $g_m$, $A$, `floor`).  Use when the background level is
  not well known.

- **`fit_OMIT_set_floor(rel_freqs, mags_dB, k_tot, floor, guesses)`** — holds
  `floor` fixed and fits only three parameters ($f_m$, $g_m$, $A$).  Use when
  the off-resonance transmission is well characterised.

Both functions:

1. Convert the input dB magnitudes to linear voltage
2. Accept optional initial guesses (auto-generated if `False`)
3. Return `popt`, `pcov`, the linear voltage data, and the guesses used

### Step 3 — Run the fit

```python
from optomechanics.data_analysis.fitting.omit import fit_OMIT, OMIT_equation
import numpy as np

# Example: fit with free floor
popt, pcov, lin_data, guesses = fit_OMIT(
    rel_freqs=rel_freqs,      # Hz, relative to carrier
    mags_dB=s21_mag_dB,       # measured S21 magnitude in dB
    k_tot=1e6,                # total cavity linewidth (Hz), from S21 fit
    floor=0.01,               # initial guess for background level
    guesses=False,            # auto-generate guesses
)

f_m, g_m, A, floor = popt
print(f"f_m = {f_m:.1f} Hz")
print(f"Γ_m = {g_m:.3f} Hz")
```

### Step 4 — Plot the result

```python
import plotly.graph_objects as go

fit_curve = OMIT_equation(rel_freqs, *popt, kk_tot=1e6)

fig = go.Figure()
fig.add_scatter(x=rel_freqs, y=lin_data, name="Data", mode="lines")
fig.add_scatter(x=rel_freqs, y=fit_curve, name="OMIT fit",
                mode="lines", line=dict(dash="dash"))
fig.update_layout(
    xaxis_title="Frequency (Hz)",
    yaxis_title="Transmission (linear voltage)",
    title="OMIT spectrum",
)
fig.show()
```

## Interpreting results

| Parameter | What it tells you |
|---|---|
| $f_m$ | Mechanical resonance — should match the Sww fit value |
| $\Gamma_m$ | Mechanical linewidth — may differ from Sww if backaction is significant |
| $A$ | OMIT amplitude — proportional to $g_0^2 n_d$ (cooperativity) |
| floor | Background transmission — should be consistent with off-resonance S21 |

A larger $A$ relative to `floor` indicates stronger optomechanical coupling.
The ratio is related to the cooperativity $C$.

## OMIT vs OMIA

The current code implements **OMIT** (transparency — a peak in transmission).
The complementary effect **OMIA** (optomechanically induced absorption — a dip)
occurs at opposite detuning.  OMIA is not yet implemented in the code.

## See also

- [API reference: `fitting.omit`](../api_reference/data_analysis/fitting/omit.md)
- [S21 Fitting](s21_fitting.md) — cavity characterisation (provides $\kappa_\text{tot}$)
- [Cooperativity](cooperativity.md) — relationship between OMIT amplitude and $C$
- [Parameter Glossary](glossary.md)
