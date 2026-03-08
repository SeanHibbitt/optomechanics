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
- [x] Fix `docs/user_guide/data_management.md` lines 17 and 36 — removed second filename argument (9284406)
- [x] Fix `docs/user_guide/thermal_motion_measurement.md` lines ~90, ~116, ~122 — removed second arg (b2441ce)

#### VNA convenience wrapper methods — do not exist in source
`E5063A_VNA_Class_new.py` exposes low-level SCPI methods only (e.g. `sense_freq_start(channel, val)`).
The following methods shown in the docs **do not exist** and will raise `AttributeError`:
`set_start_frequency()`, `set_stop_frequency()`, `set_number_of_points()`, `set_IF_bandwidth()`,
`set_measurement_parameter()`, `get_frequency_data()`, `get_formatted_data()`.
Rewrite the affected examples to use the real SCPI methods with explicit channel parameters.
- [x] Fix `docs/user_guide/attenuation_measurement.md` — rewrote VNA block to use real sweep() method (ec00222)
- [x] Fix `docs/user_guide/thermal_motion_measurement.md` — rewrote VNA block with SCPI methods (5755060)

#### `save_data_3()` — wrong call signature in examples
Actual signature: `save_data_3(data, file_name, file_location="", headers=None, meta_data={}, delimiter="\t")`
Docs show a dict as first arg and `meta=` keyword — both wrong. Correct pattern:
```python
save_data_3(np.column_stack([freqs, s21_dB]), file_path, headers=["freq[Hz]", "S21[dB]"], meta_data={"key": val})
```
- [x] Fix `docs/user_guide/data_management.md` lines ~38–42 — fixed save_data_3 signature (9284406)
- [x] Fix `docs/user_guide/thermal_motion_measurement.md` lines ~91–98, ~116–117, ~122–125 — fixed save_data_3 calls (b2441ce)

#### RS_FSW_new — wrong method names in examples
Actual method names differ from what docs show:
- `set_cent_freq(val)` ← docs show `set_center_frequency(val)`
- `set_bw(val)` ← docs show `set_rbw(val)`
- Data retrieval: use `y_data_query()` — `get_trace_data()` and `get_frequency_data()` do not exist
- [x] Fix `docs/user_guide/thermal_motion_measurement.md` lines ~79–87 — corrected SA method names (5755060)

#### `fit_S_xx.__average_and_fit_S_xx__()` — dunder method exposed to users
This is a dunder-named internal method that the docs instruct users to call directly.
Add a note explaining what it does and that it is an internal entry point pending API refactor.
- [x] Fix `docs/user_guide/thermal_motion_analysis.md` lines ~88–97 — added Internal API admonition (5755060)

#### `save_to_tsv()` — not implemented
`attenuation_object.save_to_tsv()` raises `Exception("not finished")` at runtime.
- [x] Add warning admonition to `docs/user_guide/attenuation_processing.md` — added with numpy workaround (d50c59c)

---

## Phase 16 — Extended test coverage

Gaps identified by the Phase 14 coverage audit.

#### fitting/_fitting.py — 0% coverage (5 functions)
- [x] Add `tests/test_fitting.py` — 14 tests for ring_down_eq, tau_to_Q, line_eq, fit_ring_down, fit_linear (64efe3e)

#### fitting/omit.py — 0% coverage (3 functions)
- [x] Add `tests/test_omit.py` — 8 tests for OMIT_equation lineshape, symmetry, scaling (6be90a5)

#### data_management/data_logger.py — 0% coverage
- [x] Add `tests/test_data_logger.py` — 12 tests for logger, dated_logger, format_data_line (1753792)

#### fitting/S21.py — fitting functions untested
- [x] Add tests for `fit_S21_peak_dB`, `fit_S21_peak_complex`, `fit_S21_peak` — 16 tests total (5f3e56a)

#### fitting/Sww.py — 13 of 14 functions untested
- [x] Add tests for `basic_S_ww_eq_2`, `dBm_basic_S_ww_eq`, `S_ff_thermal`, `SHO_TF_sq`, `S_xx_thermal` — 22 tests (cc9bc62)

#### File I/O tests
- [x] Add tests for `read_file` and `save_data_3` — round-trip tests with tmp_path (b955315)
- [x] Add test for `dated_file_maker` — path contains year/day segments, trailing backslash (b955315)

#### utilities.py — one missing test
- [x] Add test for `convert_anti_sym_linear_mag_voltage_error_to_sym` + `ValueError` path (4e176d1)

---

## Phase 17 — Parameter glossary

Create a single reference page defining every optomechanical parameter used in the codebase.
All other pages will link to it. This is the foundation for all physics-enhanced documentation.

- [x] Create `docs/user_guide/glossary.md` with parameter table (symbol, name, units, typical values, description) (bd72ca2)
  - Cavity: $\omega_\text{cav}$, $\kappa_\text{tot}$, $\kappa_\text{ext}$, $\kappa_\text{int}$, $Q$
  - Mechanical: $\Omega_m$, $\Gamma_m$, $Q_m$, $m_\text{eff}$, $x_\text{zpf}$
  - Optomechanical: $G$, $g_0$, $n_d$, $C$, $C_0$
  - Measurement: NENBW, ENBW, RBW, PSD
  - Notation conventions: Hz vs rad/s (code uses Hz inputs, converts internally)
  - Flag future parameters: $\Gamma_\text{opt}$, $\Omega_\text{opt}$, $n_\text{min}$ as "not yet implemented"
- [x] Add to `mkdocs.yml` nav under User Guide (d3f7abc)
- [x] Add glossary cross-references to all existing user guide pages (bb1df4d)

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
- [x] Rename page title to "Cavity Transmission (S21)" (600e759)
- [x] Add the S21 equation in LaTeX (600e759)
- [x] Explain lumped-element circuit model (600e759)
- [x] Explain overcoupled / undercoupled / critically coupled regimes (600e759)
- [x] Add references to Kumar/Rojas papers (600e759)
- [x] Add "Interpreting Results" section with typical parameter ranges (600e759)

#### Thermal Motion Analysis — enhance `thermal_motion_analysis.md`
The thermal motion analysis assumes the mechanical motion is **thermally driven** at a known temperature $T$.
This allows extraction of $g_0$ from the measured PSD using $S_{FF}^\text{th} = 4 k_B T m_\text{eff} \Gamma_m$.
- [x] Add physics background (2–3 paragraphs): thermal motion, thermal drive assumption, g₀ extraction (bb1df4d)
- [x] Add S_ww Lorentzian equation in LaTeX, mapped to `basic_S_ww_eq` code arguments (bb1df4d)
- [x] Explain $G^2 S_{xx}$ normalisation with equation (bb1df4d)
- [x] Add $g_0$ extraction equations: $G$, $x_\text{zpf}$, $g_0 = G \cdot x_\text{zpf}$ (Rojas et al. eqs. 3–5) (bb1df4d)
- [x] Add "Interpreting Results" section with typical parameter ranges (bb1df4d)
- [x] Clearly state the thermal assumption and when it is valid (bb1df4d)

#### Thermal Motion Measurement — enhance `thermal_motion_measurement.md`
- [x] Add measurement scheme physics: pump tone, sidebands, modulation (6636cd5)
- [x] Explain red vs blue sideband detuning and sideband cooling (6636cd5)
- [x] Add equations behind parameter table guidelines (6636cd5)
- [x] Cite Kumar (2023) for thermal force/SHO model (6636cd5)
- [x] Note the two analysis paths from the same measurement data (6636cd5)

#### Spectrum Analyser — enhance `spectrum_analyser.md`
- [x] Explain what a PSD is (power per unit frequency bandwidth) (6636cd5)
- [x] Explain NENBW correction: window function, 4.083 origin, conversion equation (6636cd5)
- [x] Add conversion equation in LaTeX (6636cd5)

#### Data Analysis overview — enhance `data_analysis.md`
- [x] Expand Sww fitting section: what $S_{ww}$ is, parameters, connection to $g_0$ (6636cd5)
- [x] Add the `basic_S_ww_eq` Lorentzian equation (6636cd5)

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
