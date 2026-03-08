# Intracavity Photon Number

This page documents the intracavity photon number $n_d$ and the corresponding
`photon_number` function in the codebase.

## What is $n_d$?

The intracavity photon number $n_d$ is the steady-state number of photons
circulating inside the microwave cavity during a driven measurement.  It depends
on the input power $P_\text{in}$, the detuning between the drive and cavity
frequencies, and the cavity linewidths (external coupling rate and total loss
rate).

$n_d$ sets the strength of the linearised optomechanical interaction: a higher
photon number means a stronger effective coupling $g = g_0 \sqrt{n_d}$.

## Equation

$$
n_d = \frac{2\,\kappa_\text{ext}\, P_\text{in}}
           {\hbar\, \omega_c \left(\kappa_\text{tot}^2
            + 4(\omega_d - \omega_c)^2\right)}
$$

All $\omega$ and $\kappa$ values are **angular frequencies** (rad/s).  The code
accepts ordinary frequencies in Hz and converts internally via $\omega = 2\pi f$
and $\kappa = 2\pi k$.

!!! note "On resonance"
    When the drive is on resonance ($\omega_d = \omega_c$), the detuning term
    vanishes and the expression simplifies to

    $$
    n_d = \frac{2\,\kappa_\text{ext}\, P_\text{in}}
               {\hbar\, \omega_c\, \kappa_\text{tot}^2}
    $$

**Reference:** "A Novel Architecture for room temperature microwave
optomechanical experiments", eq. 3.

## Parameter mapping

| Symbol | Code argument | Description |
|--------|--------------|-------------|
| $\omega_d$ | `f_d` | Drive frequency (Hz) |
| $\omega_c$ | `f_c` | Cavity resonance frequency (Hz) |
| $\kappa_\text{ext}$ | `k_extHz` | External coupling rate (Hz) |
| $\kappa_\text{tot}$ | `k_totHz` | Total linewidth (Hz) |
| $P_\text{in}$ | `P_in` | Input power at the cavity (watts) |

## Code example

```python
from optomechanics.data_analysis.misc_equations import photon_number

n_d = photon_number(
    f_d=6.188e9,       # drive frequency (Hz)
    f_c=6.188e9,       # cavity resonance (Hz) — on resonance
    k_extHz=500e3,     # external coupling rate (Hz)
    k_totHz=1e6,       # total linewidth (Hz)
    P_in=1e-6,         # input power (watts) = -30 dBm
)
print(f"n_d = {n_d:.0f} photons")
```

## Detuning dependence

$n_d$ is maximised on resonance and falls off as a Lorentzian in the detuning
$\Delta = \omega_d - \omega_c$:

$$
n_d(\Delta) = \frac{n_d(0)}{1 + \left(\frac{2\Delta}{\kappa_\text{tot}}\right)^2}
$$

At a detuning of $|\Delta| = \kappa_\text{tot}/2$ the photon number drops to
half its on-resonance value.

## Where $n_d$ is used

The intracavity photon number appears throughout the optomechanical analysis:

- **$G^2 S_{xx}$ normalisation** — the thermal-motion PSD is normalised by a
  factor proportional to $n_d$ (see `__normalise_Sww_to_GGSxx__` in `Sww.py`).
- **Cooperativity** — $C = 4 g_0^2\, n_d / (\Gamma_m\, \kappa_\text{tot})$.
- **OMIT amplitude** — the optomechanically induced transparency window depth
  depends on $n_d$ through the cooperativity.

## See also

- [Thermal Motion Analysis](thermal_motion_analysis.md)
- [API reference: `misc_equations`](../api_reference/data_analysis/misc_equations.md)
- [Parameter Glossary](glossary.md)
