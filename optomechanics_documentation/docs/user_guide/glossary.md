# Parameter Glossary

This page defines the optomechanical parameters used throughout the codebase and
documentation.

## Notation conventions

- All code functions accept frequencies in **Hz**.  Internal conversions to
  angular frequency ($\omega = 2\pi f$) are handled automatically.
- Subscript conventions: `_tot` = total, `_ext` = external, `_int` = internal,
  `_m` = mechanical.
- The code returns $g_0$ and $G$ in **Hz** (not rad/s) unless otherwise noted in
  the function docstring.  **Exception:** `__average_and_fit_S_xx__` returns
  $g_0$ and $G$ in **rad/s** — divide by $2\pi$ to get Hz.
- In the equations below, lowercase Greek ($\omega$, $\gamma$, $\kappa$) denotes
  **angular frequency** (rad/s) and Latin letters ($f$, $\Gamma$) denote **Hz**.

## Cavity parameters

| Symbol | Code name | Units | Description |
|--------|-----------|-------|-------------|
| $f_0$ | `f_0`, `f_c` | Hz | Cavity resonance frequency |
| $\kappa_\text{tot}$ | `k_tot`, `k_totHz` | Hz | Total cavity decay rate (FWHM linewidth) |
| $\kappa_\text{ext}$ | `k_ext`, `k_extHz` | Hz | External coupling rate (port coupling) |
| $\kappa_\text{int}$ | — | Hz | Internal (intrinsic) loss rate, $\kappa_\text{int} = \kappa_\text{tot} - \kappa_\text{ext}$ |
| $Q$ | — | dimensionless | Loaded quality factor, $Q = f_0 / \kappa_\text{tot}$ |

## Mechanical parameters

| Symbol | Code name | Units | Description |
|--------|-----------|-------|-------------|
| $f_m$ / $\Omega_m$ | `f_m`, `omega_m` | Hz | Mechanical resonance frequency |
| $\Gamma_m$ | `G_m`, `gamma_m` | Hz | Mechanical linewidth (FWHM damping rate) |
| $Q_m$ | — | dimensionless | Mechanical quality factor, $Q_m = f_m / \Gamma_m$ (also $Q = \pi f_m \tau$ via ring-down) |
| $m_\text{eff}$ | `m_eff` | kg | Effective motional mass of the mechanical mode |
| $x_\text{zpf}$ | `x_zpf` | m | Zero-point fluctuation amplitude, $x_\text{zpf} = \sqrt{\hbar / (2 m_\text{eff}\, \omega_m)}$ where $\omega_m = 2\pi f_m$ |
| $\tau$ | `tau` | s | Ring-down time constant, $\tau = Q_m / (\pi f_m) = 1/(\pi \Gamma_m)$ |

## Optomechanical parameters

| Symbol | Code name | Units | Description |
|--------|-----------|-------|-------------|
| $G$ | `G` | Hz/m | Frequency pull parameter, $G = d\omega_\text{cav}/dx$ |
| $g_0$ | `g_0` | Hz | Vacuum optomechanical coupling rate, $g_0 = G \cdot x_\text{zpf}$ |
| $n_d$ | `n_d` | dimensionless | Intracavity photon number (from `photon_number()` in `misc_equations.py`) |
| $C$ | — | dimensionless | Optomechanical cooperativity, $C = 4g_0^2 n_d / (\Gamma_m \kappa_\text{tot})$ *(not yet in code)* |
| $C_0$ | — | dimensionless | Single-photon cooperativity, $C_0 = 4g_0^2 / (\Gamma_m \kappa_\text{tot})$ *(not yet in code)* |

## Spectral density parameters

| Symbol | Code name | Units | Description |
|--------|-----------|-------|-------------|
| $A$ | `A` | varies | Amplitude scaling in `basic_S_ww_eq` Lorentzian fit |
| $n_f$ | `nf` | varies | Noise floor offset in `basic_S_ww_eq` |
| $S_{FF}^\text{th}$ | via `S_ff_thermal()` | N²/Hz | Thermal force spectral density, $S_{FF} = 4 k_B T m_\text{eff}\, \gamma_m$ where $\gamma_m = 2\pi\Gamma_m$ |
| $|\chi_m|^2$ | via `SHO_TF_sq()` | m²/N² | Mechanical susceptibility (SHO transfer function squared) |
| $S_{xx}$ | via `S_xx_thermal()` | m²/Hz | Displacement spectral density, $S_{xx} = |\chi_m|^2 S_{FF}$ |

## Measurement terms

| Term | Code name | Units | Description |
|------|-----------|-------|-------------|
| NENBW | `RS_default_window_NENBW` = 4.083 | dimensionless | Normalised equivalent noise bandwidth — window function correction factor for the R&S spectrum analyser |
| ENBW | — | Hz | Equivalent noise bandwidth, ENBW = NENBW × RBW |
| RBW | — | Hz | Resolution bandwidth of the spectrum analyser |
| PSD | — | W/Hz or V²/Hz | Power spectral density — power per unit frequency bandwidth |

## Background / fit parameters

| Symbol | Code name | Units | Description |
|--------|-----------|-------|-------------|
| $m$ | `att_m` | 1/Hz | Linear background slope in S21 fit |
| $c$ | `att_c` | dimensionless | Background offset in S21 fit |
| `floor` | `floor` | V (linear) | Background floor in OMIT fit |

## Physical constants (defined in `_fitting.py`)

| Constant | Code name | Value |
|----------|-----------|-------|
| $\hbar$ | `h_bar` | $1.0546 \times 10^{-34}$ J·s |
| $k_B$ | `k_b` | $1.3806 \times 10^{-23}$ J/K |

## Future parameters (not yet implemented)

These parameters appear in the optomechanics literature but are not yet computed
by this package:

| Symbol | Name | Description |
|--------|------|-------------|
| $\Gamma_\text{opt}$ | Optical damping rate | Backaction modification of mechanical linewidth |
| $\Omega_\text{opt}$ | Optical spring shift | Backaction modification of mechanical frequency |
| $n_\text{min}$ | Minimum phonon number | Quantum ground state cooling limit |
