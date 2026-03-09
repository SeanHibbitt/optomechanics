# OMIT / OMIA Analysis

This page describes Optomechanically Induced Transparency (OMIT) and its counterpart,
Optomechanically Induced Absorption (OMIA) — interference effects between the cavity
and mechanical responses — and how to fit OMIT/OMIA spectra using the functions in
`fitting.omit`.

## Physics background

When a strong pump tone drives the cavity and a weak probe tone sweeps across the
cavity resonance, the mechanical resonator mediates an interference between the
direct probe transmission and the probe light scattered via the mechanics.  This
creates a narrow **transparency window** (or absorption dip, depending on detuning)
at the mechanical frequency — analogous to electromagnetically induced transparency
(EIT) in atomic physics.

OMIT/OMIA appears as a sharp feature in the cavity transmission, with a width set by the
mechanical linewidth $\Gamma_m$ and an amplitude that depends on the optomechanical
cooperativity $C$.

!!! warning "Assumptions"
    The OMIT/OMIA model implemented here assumes:

    1. **Resolved sideband regime** — $\kappa_\text{tot} \ll \omega_m$, so the
       mechanical sidebands are spectrally resolved by the cavity.
    2. **Weak probe** — the probe power is negligible compared to the pump; the
       intracavity field is determined by the pump alone.
    3. **Single mechanical mode** — no mode overlap or hybridisation with other
       mechanical resonances within the measurement bandwidth.
    4. **Steady-state response** — the cavity and mechanics have reached equilibrium;
       transient effects from pump turn-on have settled.
    5. **Rotating wave approximation** — counter-rotating terms (Stokes/anti-Stokes
       mixing) are dropped.

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
| $\Gamma_m / 2\pi$ | `g_m` | Hz | Mechanical linewidth (damping rate). Code parameter is $\Gamma_m / 2\pi$. |
| $A$ | `A` | linear voltage | OMIT/OMIA amplitude (positive = peak, negative = dip) |
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
print(f"Γ_m/(2π) = {g_m:.3f} Hz")
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
| $\Gamma_m / 2\pi$ | Mechanical linewidth — may differ from Sww if backaction is significant |
| $A$ | OMIT amplitude — proportional to $g_0^2 n_d$ (cooperativity) |
| floor | Background transmission — should be consistent with off-resonance S21 |

A larger $A$ relative to `floor` indicates stronger optomechanical coupling.
The ratio is related to the cooperativity $C$.

## OMIT vs OMIA

The `OMIT_equation` function handles **both** effects via the sign of the amplitude
parameter `A`:

- **OMIT** (transparency window): `A > 0` — pump is red-detuned
  ($\Delta = -\omega_m$), producing a **peak** in cavity transmission.
- **OMIA** (absorption dip): `A < 0` — pump is blue-detuned
  ($\Delta = +\omega_m$), producing a **dip** in cavity transmission.

The fitting functions (`fit_OMIT`, `fit_OMIT_set_floor`) automatically handle both
cases.  The auto-guess logic detects whether the feature is a peak or dip and sets
the sign of `A` accordingly.

### Example: Fitting an OMIA absorption dip

When the pump is blue-detuned, the feature becomes a dip.  The same fitting
functions handle this automatically — the recovered `A` will be negative.

```python
from optomechanics.data_analysis.fitting.omit import OMIT_equation, fit_OMIT
from optomechanics.data_analysis.unit_conversions import linear_voltage_to_dB
import numpy as np

# Generate OMIA data (negative A)
freqs = np.linspace(30e3, 70e3, 2001)
omia_data = OMIT_equation(freqs, f_m=50e3, g_m=300, A=-0.05,
                           floor=0.1, kk_tot=1e6)

# Fit exactly as for OMIT — the auto-guess detects the dip
popt, _, _, _ = fit_OMIT(freqs, linear_voltage_to_dB(omia_data),
                          k_tot=1e6, floor=0.1,
                          guesses=[50e3, 300, -0.05, 0.1])
print(f"A = {popt[2]:.4f}")  # negative → OMIA
```

## Tutorial: Synthetic data round-trip

This example generates synthetic OMIT data with known parameters, adds noise,
fits the data, and compares recovered parameters against the ground truth.

```python
import numpy as np
from optomechanics.data_analysis.fitting.omit import OMIT_equation, fit_OMIT
from optomechanics.data_analysis.unit_conversions import linear_voltage_to_dB

# Known (ground truth) parameters
true_f_m = 50e3       # Hz — mechanical frequency
true_g_m = 300        # Hz — mechanical linewidth (Γ_m / 2π)
true_A = 0.5          # linear voltage — OMIT amplitude
true_floor = 0.1      # linear voltage — background
true_kk_tot = 1e6     # Hz — cavity linewidth

# Generate clean OMIT lineshape
freqs = np.linspace(30e3, 70e3, 2001)
clean = OMIT_equation(freqs, true_f_m, true_g_m, true_A,
                       true_floor, true_kk_tot)

# Add Gaussian noise to simulate a real measurement
rng = np.random.default_rng(42)
noisy = clean + rng.normal(0, 0.002, len(freqs))

# Convert to dB (as a VNA would provide)
noisy_dB = linear_voltage_to_dB(noisy)

# Fit — provide rough initial guesses
popt, pcov, lin_data, guesses = fit_OMIT(
    freqs, noisy_dB, k_tot=true_kk_tot, floor=true_floor,
    guesses=[true_f_m * 1.01, true_g_m * 0.8,
             true_A * 1.2, true_floor * 0.9],
)

f_m, g_m, A, floor = popt
print(f"f_m:   true={true_f_m:.0f} Hz,   fit={f_m:.0f} Hz")
print(f"g_m:   true={true_g_m:.0f} Hz,   fit={g_m:.0f} Hz")
print(f"A:     true={true_A:.3f},         fit={A:.3f}")
print(f"floor: true={true_floor:.3f},     fit={floor:.3f}")
```

## Cross-validation with Sww

The mechanical frequency $f_m$ and linewidth $\Gamma_m / 2\pi$ should be
consistent between OMIT/OMIA fits and Sww (thermal noise PSD) fits from the
same device.  Significant differences may indicate:

- **Dynamical backaction** — the pump modifies $\Gamma_m$ and $f_m$ via
  optical spring and damping effects.  Compare on- vs off-pump Sww to
  isolate backaction contributions.
- **Different measurement conditions** — temperature, pressure, or pump
  power changed between measurements.

## Choosing initial guesses

The `guesses` parameter accepts a list of starting values for the fit:

- `fit_OMIT`: `[f_m, g_m, A, floor]`
- `fit_OMIT_set_floor`: `[f_m, g_m, A]`

**Tips:**

| Parameter | How to estimate |
|-----------|----------------|
| `f_m` | Frequency of the peak (or dip) visible in the data |
| `g_m` | FWHM of the feature estimated by eye |
| `A` | `peak_height - floor` (positive for OMIT, negative for OMIA) |
| `floor` | Mean value of the data far from the feature |

If the auto-guessing (`guesses=False`) fails to converge, provide explicit
guesses with values close to the expected parameters.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Fit does not converge (`maxfev exceeded`) | Initial guesses too far from true values | Provide manual guesses closer to the visible feature |
| Fitted `g_m` is unreasonably large | `kk_tot` is wrong — it strongly affects the shape | Re-check your S21-derived cavity linewidth |
| Fitted `f_m` is offset from the visible peak | Frequency array may not be centred correctly | Verify `rel_freqs` is relative to the carrier |
| `A` has wrong sign | Pump detuning is opposite to what you expected | Check whether you are red- or blue-detuned |
| Fit returns `floor` much different than expected | Background has a slope the constant floor cannot capture | Fit a sub-range of data, or subtract a linear baseline first |

## References

1. Aspelmeyer, M., Kippenberg, T. J. & Marquardt, F. Cavity optomechanics.
   *Rev. Mod. Phys.* **86**, 1391-1452 (2014). doi:10.1103/RevModPhys.86.1391
2. Weis, S. et al. Optomechanically Induced Transparency.
   *Science* **330**, 1520-1523 (2010). doi:10.1126/science.1195596
3. Safavi-Naeini, A. H. et al. Electromagnetically induced transparency and
   slow light with optomechanics. *Nature* **472**, 69-73 (2011).
4. Kumar, S. *A Novel Architecture for room temperature microwave optomechanical
   experiments* (2023).

## See also

- [API reference: `fitting.omit`](../api_reference/data_analysis/fitting/omit.md)
- [S21 Fitting](s21_fitting.md) — cavity characterisation (provides $\kappa_\text{tot}$)
- [Cooperativity](cooperativity.md) — relationship between OMIT amplitude and $C$
- [Thermal Motion Analysis](thermal_motion_analysis.md) — Sww fitting for cross-validation
- [Parameter Glossary](glossary.md)
