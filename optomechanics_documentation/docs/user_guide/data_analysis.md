# Data Analysis

The `optomechanics.data_analysis` subpackage provides the core numerical analysis tools used
after a measurement is complete.

## Modules

### `unit_conversions`

A reference module of pure conversion functions (no state, no side effects). All common
RF power unit conversions are collected here so that the correct formula is used consistently
across the codebase.

Common conversions:

- dBm ↔ watts, dBw
- V\(_\text{RMS}\) ↔ dBm, watts
- V\(_\text{pp}\) / V\(_\text{p}\) ↔ V\(_\text{RMS}\)
- Linear voltage ratio ↔ dB

See [unit_conversions API](../api_reference/data_analysis/unit_conversions.md).

---

### `fitting`

Curve-fitting routines for cavity / resonator measurements.

#### S21 fitting

`fitting.S21` fits the transmission through a microwave cavity.  The model is:

$$
S_{21}(f) = \left| \frac{\kappa_\text{ext}}{\kappa_\text{tot} + 2j(f - f_0)} \right| + m\,f + c
$$

where all values are in Hz (the $2\pi$ factors cancel between numerator and
denominator).

Key functions:

- `fit_S21_peak` — fits in linear voltage ratio units
- `fit_S21_peak_dB` — convenience wrapper that accepts dB input
- `fit_S21_peak_complex` — fits real + imaginary parts simultaneously

Returned parameters: `f_0`, `κ_tot`, `κ_ext`, background slope and offset.

See [S21 API](../api_reference/data_analysis/fitting/S21.md).

#### Sww fitting

`fitting.Sww` fits the noise power spectral density $S_{ww}(f)$ of a mechanical
resonator.  The mechanical Brownian motion produces a Lorentzian peak in the PSD
centred at $f_m$ with linewidth $\Gamma_m$.  The basic model (`basic_S_ww_eq`) is:

$$
S_{ww}(\omega) = \frac{A}{\gamma_m^2 + 4(\omega - \omega_m)^2} + n_f
$$

where $\omega = 2\pi f$, $\omega_m = 2\pi f_m$, $\gamma_m = 2\pi\Gamma_m$.
The code accepts all frequencies in **Hz** and converts to angular frequency
internally.  The fitted amplitude $A$ is in angular-frequency units.

From the fitted parameters and the cavity S21 fit, the code extracts the
vacuum optomechanical coupling rate $g_0$ — see
[Thermal Motion Analysis](thermal_motion_analysis.md) for the full workflow.

See [Sww API](../api_reference/data_analysis/fitting/Sww.md).

#### OMIT / OMIA fitting

`fitting.omit` fits the OMIT/OMIA lineshape — a narrow transparency window (or absorption
dip) in cavity transmission caused by optomechanical interference when a strong pump tone
drives the cavity.  The model is:

$$
\text{OMIT}(f) = \text{floor} \times \left(1 + A \left|\frac{1}{(\omega_m^2 - \omega^2 - i\Gamma_m\omega)(\kappa - 2i\omega)}\right|\right)
$$

where $\omega = 2\pi f$, $\omega_m = 2\pi f_m$, $\Gamma_m = 2\pi\,$`g_m`,
$\kappa = 2\pi\,$`kk_tot`.  Positive $A$ fits a transparency peak (OMIT); negative $A$
fits an absorption dip (OMIA).

Key functions:

- `OMIT_equation` — evaluate the lineshape at given frequencies
- `fit_OMIT` — fit all four parameters ($f_m$, `g_m`, $A$, `floor`)
- `fit_OMIT_set_floor` — fit with fixed background floor

See [OMIT / OMIA Analysis](omit_analysis.md) | [omit API](../api_reference/data_analysis/fitting/omit.md).

---

### `square_membrane`

The `membrane` class calculates the resonance frequencies of a pre-stressed square membrane
resonator, taking into account a thin-film deposition that loads the membrane mass.

The fundamental mode frequency (with mass loading) is:

$$
f_{mn} = \frac{1}{2}\sqrt{\frac{\sigma}{\rho}\left[\left(\frac{m}{L_x}\right)^2 + \left(\frac{n}{L_y}\right)^2\right]}
$$

See [square_membrane API](../api_reference/data_analysis/square_membrane.md).

---

### `utilities`

General-purpose helpers used across the fitting routines:

- `find_closest_number` — nearest-value index search
- `split_complex` / `split_complex_wrapper` — complex → real+imag for `scipy.optimize.curve_fit`
- Error propagation helpers

See [utilities API](../api_reference/data_analysis/utilities.md).

---

### `misc_equations`

Miscellaneous physical equations that do not belong to a specific module.

See [misc_equations API](../api_reference/data_analysis/misc_equations.md).

## See also

- [Parameter Glossary](glossary.md)
