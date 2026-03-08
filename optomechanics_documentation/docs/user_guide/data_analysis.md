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
S_{21}(f) = \left| \frac{2\pi\kappa_\text{ext}}{2\pi\kappa_\text{tot} + 4\pi i(f - f_0)} \right| + \text{background}
$$

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
S_{ww}(f) = \frac{A}{\Gamma_m^2 + 4(f - f_m)^2} + n_f
$$

where $A$ is the amplitude, $f_m$ the mechanical resonance frequency, $\Gamma_m$
the damping rate, and $n_f$ the noise floor.  All frequencies are in Hz; the code
converts internally to angular frequency ($\times 2\pi$).

From the fitted parameters and the cavity S21 fit, the code extracts the
vacuum optomechanical coupling rate $g_0$ — see
[Thermal Motion Analysis](thermal_motion_analysis.md) for the full workflow.

See [Sww API](../api_reference/data_analysis/fitting/Sww.md).

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
