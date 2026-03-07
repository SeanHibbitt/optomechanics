# Issues / To-Do

> **Rules:** When done, tick the box and append a one-line summary with the commit hash.
> Completed items from Phases 1–14 have been moved to `TODO_ARCHIVE.md`.

---

## Phase 15 — Fix broken doc examples

Findings from the Phase 13 deep-accuracy audit. All fixes are documentation-only (no source code changes).
These examples will crash if copy-pasted — fix before writing any new content.

#### `dated_file_maker()` — wrong signature in examples
The function takes **one argument** (`base_path`), but five doc examples call it with two.
Correct usage: `dir_path = dated_file_maker("/base/path")` — returns a dated directory path.
- [ ] Fix `docs/user_guide/data_management.md` lines 17 and 36 — remove second filename argument
- [ ] Fix `docs/user_guide/thermal_motion_measurement.md` lines ~90, ~116, ~122 — same fix

#### VNA convenience wrapper methods — do not exist in source
`E5063A_VNA_Class_new.py` exposes low-level SCPI methods only (e.g. `sense_freq_start(channel, val)`).
The following methods shown in the docs **do not exist** and will raise `AttributeError`:
`set_start_frequency()`, `set_stop_frequency()`, `set_number_of_points()`, `set_IF_bandwidth()`,
`set_measurement_parameter()`, `get_frequency_data()`, `get_formatted_data()`.
Rewrite the affected examples to use the real SCPI methods with explicit channel parameters.
- [ ] Fix `docs/user_guide/attenuation_measurement.md` — rewrite VNA setup/data-retrieval block (~lines 21–29)
- [ ] Fix `docs/user_guide/thermal_motion_measurement.md` — rewrite VNA block (~lines 37–44)

#### `save_data_3()` — wrong call signature in examples
Actual signature: `save_data_3(data, file_name, file_location="", headers=None, meta_data={}, delimiter="\t")`
Docs show a dict as first arg and `meta=` keyword — both wrong. Correct pattern:
```python
save_data_3(np.column_stack([freqs, s21_dB]), file_path, headers=["freq[Hz]", "S21[dB]"], meta_data={"key": val})
```
- [ ] Fix `docs/user_guide/data_management.md` lines ~38–42
- [ ] Fix `docs/user_guide/thermal_motion_measurement.md` lines ~91–98, ~116–117, ~122–125

#### RS_FSW_new — wrong method names in examples
Actual method names differ from what docs show:
- `set_cent_freq(val)` ← docs show `set_center_frequency(val)`
- `set_bw(val)` ← docs show `set_rbw(val)`
- Data retrieval: use `y_data_query()` — `get_trace_data()` and `get_frequency_data()` do not exist
- [ ] Fix `docs/user_guide/thermal_motion_measurement.md` lines ~79–87 — correct all SA method names

#### `fit_S_xx.__average_and_fit_S_xx__()` — dunder method exposed to users
This is a dunder-named internal method that the docs instruct users to call directly.
Add a note explaining what it does and that it is an internal entry point pending API refactor.
- [ ] Fix `docs/user_guide/thermal_motion_analysis.md` lines ~88–97 — add explanatory note

#### `save_to_tsv()` — not implemented
`attenuation_object.save_to_tsv()` raises `Exception("not finished")` at runtime.
- [ ] Add warning admonition to `docs/user_guide/attenuation_processing.md` noting it's unimplemented, with workaround

---

## Phase 16 — Extended test coverage

Gaps identified by the Phase 14 coverage audit.

#### fitting/_fitting.py — 0% coverage (5 functions)
- [ ] Add `tests/test_fitting.py` — test `ring_down_eq`, `tau_to_Q`, `line_eq`, `fit_ring_down`, `fit_linear`

#### fitting/omit.py — 0% coverage (3 functions)
- [ ] Add `tests/test_omit.py` — test `OMIT_equation` with known lineshape values; test monotonicity/symmetry

#### data_management/data_logger.py — 0% coverage
- [ ] Add `tests/test_data_logger.py` — test `logger` and `dated_logger` creation, write/read, `format_data_line`; use `tmp_path`

#### fitting/S21.py — fitting functions untested
- [ ] Add tests for `fit_S21_peak_dB`, `fit_S21_peak_complex`, `fit_S21_peak` with synthetic data

#### fitting/Sww.py — 13 of 14 functions untested
- [ ] Add tests for `basic_S_ww_eq_2`, `dBm_basic_S_ww_eq`, `S_ff_thermal`, `SHO_TF_sq`, `S_xx_thermal`

#### File I/O tests
- [ ] Add tests for `read_file` and `save_data_3` — round-trip equality with `tmp_path`
- [ ] Add test for `dated_file_maker` — assert path contains year/month/day segments

#### utilities.py — one missing test
- [ ] Add test for `convert_anti_sym_linear_mag_voltage_error_to_sym` + `ValueError` path

---

## Phase 17 — Parameter glossary

Create a single reference page defining every optomechanical parameter used in the codebase.
All other pages will link to it. This is the foundation for all physics-enhanced documentation.

- [ ] Create `docs/user_guide/glossary.md` with parameter table (symbol, name, units, typical values, description)
  - Cavity: $\omega_\text{cav}$, $\kappa_\text{tot}$, $\kappa_\text{ext}$, $\kappa_\text{int}$, $Q$
  - Mechanical: $\Omega_m$, $\Gamma_m$, $Q_m$, $m_\text{eff}$, $x_\text{zpf}$
  - Optomechanical: $G$, $g_0$, $n_d$, $C$, $C_0$
  - Measurement: NENBW, ENBW, RBW, PSD
  - Notation conventions: Hz vs rad/s (code uses Hz inputs, converts internally)
  - Flag future parameters: $\Gamma_\text{opt}$, $\Omega_\text{opt}$, $n_\text{min}$ as "not yet implemented"
- [ ] Add to `mkdocs.yml` nav under User Guide
- [ ] Add glossary cross-references to all existing user guide pages

---

## Phase 18 — Add inline physics to existing user guides

Transform guides from "how to call the function" to "how to understand and use the function."
Each page should include: physics motivation, equations in LaTeX (matching the code), parameter tables,
configuration assumptions, academic paper references, and interpretation guidance.

The module builds on the room temperature optomechanics work of Sumit Kumar and Xavier Rojas.
References already in source code:
- "A Novel Architecture for room temperature microwave optomechanical experiments" (`misc_equations.py:25`, `Sww.py:173`)
- S. Kumar (2023) eq. 5 (`Sww.py:529`)
- X. Rojas et al. (2022-11-28) eqs. 3–5 (`Sww.py:758`)

#### Cavity Transmission (S21) — rename and enhance `s21_fitting.md`
- [ ] Rename page title to "Cavity Transmission (S21)"
- [ ] Add the S21 equation in LaTeX: $S_{21}(f) = \left|\frac{\kappa_\text{ext}}{\kappa_\text{tot} + 2j(f - f_0)}\right| + m \cdot f + c$
- [ ] Explain lumped-element circuit model (two coupling capacitors in series, parallel LCR between them) — this equation is configuration-specific
- [ ] Explain overcoupled / undercoupled / critically coupled regimes
- [ ] Add references to Kumar/Rojas papers
- [ ] Add "Interpreting Results" section with typical parameter ranges

#### Thermal Motion Analysis — enhance `thermal_motion_analysis.md`
The thermal motion analysis assumes the mechanical motion is **thermally driven** at a known temperature $T$.
This allows extraction of $g_0$ from the measured PSD using $S_{FF}^\text{th} = 4 k_B T m_\text{eff} \Gamma_m$.
- [ ] Add physics background (2–3 paragraphs): what thermal motion is, the thermal drive assumption, why known $T$ lets you extract $g_0$
- [ ] Add S_ww Lorentzian equation in LaTeX, mapped to `basic_S_ww_eq` code arguments
- [ ] Explain $G^2 S_{xx}$ normalisation: what it represents, why each step exists (cite "A Novel Architecture...")
- [ ] Add $g_0$ extraction equations: $G$, $x_\text{zpf}$, $g_0 = G \cdot x_\text{zpf}$ (cite Rojas et al. eqs. 3–5)
- [ ] Add "Interpreting Results" section: what $g_0$, $G$, $\Gamma_m$ values mean, how to sanity-check
- [ ] Clearly state the thermal assumption and when it is valid (e.g. $k_B T \gg \hbar \Omega_m$, no significant backaction cooling)

#### Thermal Motion Measurement — enhance `thermal_motion_measurement.md`
- [ ] Add measurement scheme physics: pump tone creates intracavity photons, mechanical motion modulates cavity frequency, sidebands appear in transmitted signal
- [ ] Explain red vs blue sideband detuning and sideband cooling
- [ ] Add equations behind parameter table guidelines (why VNA span = 10 × $\kappa_\text{tot}$, etc.)
- [ ] Cite Kumar (2023) for thermal force/SHO model
- [ ] Note the two analysis paths from the same measurement data:
  - **Thermal motion analysis** — assumes thermal drive at known $T$, extracts $g_0$ (see thermal_motion_analysis.md)
  - **Displacement measurement** — requires known $g_0$/$G$, extracts $T_\text{eff}$ (see displacement_measurement.md)

#### Spectrum Analyser — enhance `spectrum_analyser.md`
- [ ] Explain what a PSD is (power per unit frequency bandwidth)
- [ ] Explain NENBW correction: why raw SA output is not a PSD, what the window function does, where 4.083 comes from
- [ ] Add conversion equation in LaTeX

#### Data Analysis overview — enhance `data_analysis.md`
- [ ] Expand Sww fitting section: what $S_{ww}$ is, what parameters it extracts, connection to $g_0$
- [ ] Add the `basic_S_ww_eq` Lorentzian equation

---

## Phase 19 — New workflow guides

New user guide pages for measurement/analysis workflows not currently documented.

#### Displacement measurement (no thermal assumption)
The displacement measurement path does **not** assume thermal drive. Instead it requires a known
$g_0$ (or $G$, $x_\text{zpf}$) as input — typically from a prior thermal calibration. Given these,
the measured PSD can be converted to a displacement spectral density $S_{xx}$, and an **effective
temperature** $T_\text{eff}$ can be extracted from the area under the mechanical peak.
This is the appropriate analysis when backaction cooling or an external drive is present.

- [ ] Create `docs/user_guide/displacement_measurement.md` — explain the no-thermal-assumption path:
  - Input: known $g_0$ / $G$ / $x_\text{zpf}$ (from prior thermal calibration)
  - Convert measured PSD to $S_{xx}$ using known coupling
  - Two methods for extracting $T_\text{eff}$ (document both, recommend fitting):
    1. **Fitting method (recommended):** Fit $S_{xx}$ with the Lorentzian model (`basic_S_ww_eq`); with known $G$, the fit amplitude $A$ maps to $T_\text{eff}$ via $S_{FF}^\text{th} = 4 k_B T_\text{eff} m_\text{eff} \Gamma_m$. More robust — naturally separates peak from background and simultaneously extracts $\Gamma_m$.
    2. **Integration method:** Integrate $S_{xx}$ over frequency to get $\langle x^2 \rangle$, then use equipartition $\frac{1}{2} m_\text{eff} \Omega_m^2 \langle x^2 \rangle = \frac{1}{2} k_B T_\text{eff}$. Simpler conceptually but sensitive to noise floor subtraction, frequency range, and nearby peaks.
  - Contrast with thermal motion analysis (which assumes $T$ to extract $g_0$ — the inverse problem)
  - Show code examples using existing Sww functions

- [ ] Create `docs/user_guide/omit_analysis.md` — OMIT physics (interference between cavity and mechanical response), OMIT equation in LaTeX, fit workflow using `fit_OMIT`/`fit_OMIT_set_floor`, interpretation
- [ ] Create `docs/user_guide/photon_number.md` — what $n_d$ is, equation, code example using `photon_number()`, detuning dependence
- [ ] Create `docs/user_guide/cooperativity.md` — define $C = 4g_0^2 n_d / (\Gamma_m \kappa)$ and $C_0$, manual calculation from S21+Sww results, what $C > 1$ means
- [ ] Create `docs/user_guide/end_to_end_workflow.md` — capstone guide linking all steps: calibrate attenuation → characterise cavity → set pump → acquire PSD → normalise → extract $g_0$ → calculate $C$ → verify
- [ ] Add all new pages to `mkdocs.yml` nav

---

## Phase 20 — Roadmap section

New top-level nav section (same level as User Guide) documenting future module capabilities.
For each planned feature: physics equation, what it would be used for, existing partial implementation.

- [ ] Create `docs/roadmap/index.md` — overview of planned features
- [ ] Create `docs/roadmap/planned_physics.md` — planned physics capabilities:
  - $\Gamma_\text{opt}$, $\Omega_\text{opt}$ (dynamical backaction / optical spring effect)
  - OMIA (only OMIT currently exists)
  - Sideband resolution regime classification (resolved vs unresolved)
  - Quantum ground state cooling ($n_\text{min}$, quantum threshold)
  - Cooperativity functions ($C$, $C_0$ — currently manual calculation only)
  - Standard quantum limit
  - `account_for_attenuation()` implementation (currently a stub)
  - `save_to_tsv()` implementation (currently raises exception)
- [ ] Create `docs/roadmap/code_improvements.md` — technical debt:
  - `setup.py` fix (`py_modules` → `find_packages()`)
  - `__average_and_fit_S_xx__` dunder method renaming
  - Parameter naming standardisation (`A`, `nf`, `kk_tot`, `height_of_sin`)
  - Dead code cleanup in `data_management.py`
- [ ] Add Roadmap section to `mkdocs.yml` nav

---

## Phase 21 — Enrich API reference pages

Seven API pages are currently empty autodoc stubs (just `:::` directives).
Add usage examples, context, and cross-references to each.

- [ ] `docs/api_reference/data_analysis/unit_conversions.md` — add examples and context
- [ ] `docs/api_reference/data_analysis/misc_equations.md` — add examples and context
- [ ] `docs/api_reference/data_analysis/utilities.md` — add examples and context
- [ ] `docs/api_reference/data_analysis/square_membrane.md` — add examples and context
- [ ] `docs/api_reference/data_management/data_management.md` — add examples and context
- [ ] `docs/api_reference/data_management/file_management.md` — add examples and context
- [ ] `docs/api_reference/device_control/Device_Visa_Super.md` — add examples and context

---

## Phase 22 — Module-level docstrings and setup.py

~15 source files lack a module-level docstring (used as page header by mkdocstrings).
These are documentation-only edits — a single docstring at the top of each file, no logic changes.

- [ ] Add module-level docstrings to: `utilities.py`, `Plotting.py`, `Temperature_Reader.py`, `control_gui.py`, `fitting/S21.py`, `fitting/Sww.py`, `fitting/omit.py`, `fitting/_fitting.py`, `data_management.py`, `file_management.py`, `data_logger.py`, `Device_Visa_Super.py`, `VNA.py`, and instrument driver files
- [ ] Fix `setup.py` — replace `py_modules=['optomechanics']` with `packages=find_packages()` and add `install_requires`

---

## Code / Features

*(Add items here)*

---

## Bugs

*(Add items here)*
