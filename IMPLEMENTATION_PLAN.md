# Documentation Implementation Plan

> For use by a Claude Opus orchestrator with Sonnet sub-agents.
> Reference: `TODO.md` (open items), `TODO_ARCHIVE.md` (completed), `.claude/plans/elegant-percolating-glacier.md` (full analysis).

---

## Architecture

**Orchestrator (you, Opus):** Owns physics accuracy, sequencing, and review. Writes physics content drafts for Phase 17-19. Reviews all Sonnet output before committing.

**Opus peer (via Agent tool, subagent_type=general-purpose or Plan):** Use to verify physics equations, check derivation steps, and validate that documentation accurately reflects the source code. Bounce any non-trivial physics claim off the peer before writing it into a doc page.

**Sonnet sub-agents (via Agent tool):** Perform the mechanical work — file edits, signature verification, mkdocs.yml updates, test writing. Launch in parallel where tasks are independent.

**When to use each:**
- **You (Opus):** Draft any paragraph that contains a physics equation, derivation, or assumption. Draft the glossary. Write the displacement measurement page (new physics content).
- **Opus peer:** Verify S21 equation matches the lumped-element model. Verify g_0 extraction chain. Verify OMIT equation. Check any claim about overcoupled/undercoupled regimes. Verify the thermal vs displacement analysis distinction.
- **Sonnet sub-agents:** Fix function signatures in docs (Phase 15). Add warning admonitions. Update mkdocs.yml nav. Add module-level docstrings. Write tests (Phase 16). Enrich API reference stubs (Phase 21). Any task where the content is already decided and just needs applying.

---

## Constraints

1. **Do not edit Python source code** except: `setup.py` (fix `find_packages()`), and adding module-level docstrings (first string in file, no logic changes).
2. **Each git command is its own Bash tool call** — never chain with `&&` or `;`.
3. **Commit after every unit task** with format: `[AI][Claude] <description>`.
4. **Never delete items from TODO.md** — tick checkboxes and append commit hash.
5. **Docstring prefix:** `"""Made by Claude. ...`
6. **Python env:** `/d/miniconda3/envs/exp/python.exe`, run pytest via `-m pytest`.
7. **MkDocs build:** `cd optomechanics_documentation && /d/miniconda3/envs/exp/python.exe -m mkdocs build --strict`

---

## Verification Protocol

After **every round**, the orchestrator (you) must perform these checks before moving on.
Do not delegate verification to sub-agents — you own correctness.

### After Sonnet edits (every round):
1. **Read every file the agent modified** — don't trust the agent's summary. Read the actual file.
2. **Verify function signatures against source** — for any code example the agent wrote, read the corresponding Python source and confirm the method names, argument order, and keyword names match exactly.
3. **Check for introduced errors** — did the agent break surrounding content, remove existing sections, or introduce formatting issues?
4. **Run `mkdocs build --strict`** — confirms no broken cross-references or syntax errors.

### After physics content (Rounds 3–7):
5. **Verify every equation against source code** — read the Python function, write out the equation it implements, compare to what's in the doc. They must match.
6. **Verify parameter name mappings** — if the doc says "$\kappa_\text{tot}$" maps to code argument `k_tot`, confirm by reading the function signature.
7. **Check assumptions are stated** — every equation must say what physical model it assumes and when it's valid.
8. **Check references are present** — every equation derived from a paper must cite it.
9. **Bounce non-trivial claims off the Opus peer** — e.g. "this equation is specific to the two-port transmission topology" or "the integration method is sensitive to noise floor subtraction."

### After tests (Round 2):
10. **Run the full test suite yourself** — don't trust the agent's report. Run it and read the output.
11. **Spot-check test logic** — read 2-3 test functions, verify the expected values are correct (e.g. hand-calculate one `tau_to_Q` case).

### After each round completes:
12. **Tick the corresponding TODO.md items** with commit hashes.
13. **Commit the TODO.md update** as its own commit.

---

## Execution Order

### Round 1: Fix crashes (Phase 15) — Sonnet parallel agents

These are independent file fixes. Launch up to 3 Sonnet agents in parallel.

**Agent 1: thermal_motion_measurement.md fixes**
All 4 bug categories affect this file. Read the source files to get correct signatures, then fix:
- VNA methods: Read `optomechanics/device_control/E5063A_VNA_Class_new.py` for real method names. Replace `set_start_frequency()` etc with `sense_freq_start(channel, val)` etc. Use the pattern from `docs/user_guide/device_control.md` which correctly calls `vna.sweep(channel=1, ...)`.
- FSW methods: Read `optomechanics/device_control/RS_FSW_new.py`. Replace `set_center_frequency()` → `set_cent_freq()`, `set_rbw()` → `set_bw()`, `get_trace_data()` → `y_data_query()`, `get_frequency_data()` → `x_data_query()`.
- `dated_file_maker()`: Takes one arg (`base_path`). Remove second arg from lines ~90, ~116, ~122.
- `save_data_3()`: Real signature is `save_data_3(data, file_name, file_location="", headers=None, meta_data={})`. Fix lines ~91-98, ~116-117, ~122-125.
- Commit each fix category separately.

**Agent 2: other doc file fixes**
- Fix `docs/user_guide/data_management.md` — `dated_file_maker()` (lines 17, 36) and `save_data_3()` (lines ~38-42).
- Fix `docs/user_guide/attenuation_measurement.md` — VNA method names (~lines 21-29). Read `E5063A_VNA_Class_new.py` for real methods.
- Add warning admonition to `docs/user_guide/attenuation_processing.md` for `save_to_tsv()` not implemented. Provide numpy workaround.
- Commit each file separately.

**Agent 3: thermal_motion_analysis.md dunder note**
- Add explanatory note about `__average_and_fit_S_xx__` at lines ~88-97. Explain it's an internal entry point, dunder naming is a known API issue, will be renamed in future.
- Commit.

**Orchestrator review (you, before committing):**
- Read each modified .md file end-to-end. Verify every code block uses real method names by cross-referencing against the source files (`E5063A_VNA_Class_new.py`, `RS_FSW_new.py`, `data_management.py`, `file_management.py`).
- Check that `save_data_3()` examples use positional `data` as first arg (numpy array), `file_name` as second, and `meta_data=` (not `meta=`).
- Check that `dated_file_maker()` calls have exactly one argument.
- Run `mkdocs build --strict`.
- Tick Phase 15 items in TODO.md.

---

### Round 2: Extended tests (Phase 16) — Sonnet parallel agents

Independent test files. Launch 2-3 Sonnet agents.

**Agent 1: fitting tests**
- Create `tests/test_fitting.py` — test `ring_down_eq`, `tau_to_Q`, `line_eq`, `fit_ring_down`, `fit_linear` from `_fitting.py`.
- Create `tests/test_omit.py` — test `OMIT_equation` with known values.
- Run pytest, fix failures.

**Agent 2: Sww + S21 fitting tests**
- Add tests for `fit_S21_peak_dB`, `fit_S21_peak_complex`, `fit_S21_peak` — synthetic S21 curve, assert parameter recovery.
- Add tests for `basic_S_ww_eq_2`, `dBm_basic_S_ww_eq`, `S_ff_thermal`, `SHO_TF_sq`, `S_xx_thermal`.

**Agent 3: data I/O + utility tests**
- Create `tests/test_data_logger.py` — `logger`, `dated_logger`, `format_data_line`, all using `tmp_path`.
- Add `read_file`/`save_data_3` round-trip test.
- Add `dated_file_maker` path format test.
- Add `convert_anti_sym_linear_mag_voltage_error_to_sym` test + ValueError path.

**Orchestrator review:**
- Run the full test suite yourself: `/d/miniconda3/envs/exp/python.exe -m pytest optomechanics/tests/ -v`
- Read the test output — all tests must pass. If any fail, fix before proceeding.
- Spot-check 2-3 test functions: hand-calculate the expected value and verify the test asserts correctly (e.g. `tau_to_Q(tau=1/(pi*100), f_m=100)` should give `Q = pi * 100 * 100 / pi = 100` — check the formula).
- For fitting tests: verify the synthetic data parameters are physically reasonable and the tolerance is tight enough to be meaningful.
- Tick Phase 16 items in TODO.md.

---

### Round 3: Parameter glossary (Phase 17) — Opus writes, Sonnet applies

**You (Opus):** Draft the full glossary content. This requires physics accuracy.

Structure:
```markdown
# Parameter Glossary

## Notation conventions
- All code functions accept frequencies in Hz; internal conversions to rad/s are handled automatically
- Subscript conventions: ...

## Cavity parameters
| Symbol | Code name | Units | Description |
| $f_0$ / $\omega_\text{cav}$ | `f_0`, `f_c` | Hz | Cavity resonance frequency |
| $\kappa_\text{tot}$ | `k_tot` | Hz | Total cavity decay rate (FWHM) ... |
...

## Mechanical parameters
...

## Optomechanical parameters
...

## Measurement terms
...

## Future parameters (not yet implemented)
...
```

**Opus peer:** Verify all definitions, units, and typical value ranges.

**Sonnet agent:** Write the file, add to mkdocs.yml, add cross-reference links to all 10 existing user guide pages. Commit.

**Orchestrator review:**
- Read the glossary file. For every parameter, verify: (a) the code name matches the actual function signature in the source, (b) the units are correct, (c) the description is physically accurate.
- Check the Hz vs rad/s convention note matches reality — read a function like `S_ww_constant_calculator()` in `Sww.py` and confirm inputs are Hz and the function converts internally with `* 2*np.pi`.
- Run `mkdocs build --strict`.
- Tick Phase 17 items in TODO.md.

---

### Round 4: Inline physics — Cavity Transmission S21 (Phase 18, task C3) — Opus writes

**You (Opus):** This is the template page. Write it yourself to set the standard.

Read `optomechanics/data_analysis/fitting/S21.py` (already explored — S21_eq at line 50).

Content to add to `s21_fitting.md`:
1. Rename title to "Cavity Transmission (S21)"
2. Physics section (2-3 paragraphs): what a microwave cavity is, transmission measurement, why Lorentzian
3. Circuit model: lumped-element description (two coupling caps in series, parallel LCR between). Note this is configuration-specific — different geometries need different equations.
4. S21 equation in LaTeX with parameter mapping table to code args
5. Coupling regimes: overcoupled ($\kappa_\text{ext} > \kappa_\text{int}$), undercoupled, critically coupled
6. References: Kumar/Rojas room temperature optomechanics papers
7. "Interpreting Results" section

**Opus peer:** Verify the equation matches the code. Verify the circuit model claim. Verify coupling regime definitions.

**Orchestrator review:**
- Read `S21.py` line 50 side-by-side with the LaTeX equation you wrote. Confirm they are identical (watch for factor-of-2 errors in the denominator).
- Verify the parameter mapping table: e.g. does `p[3]` in the code correspond to `att_m` and is that what the doc calls "background slope"?
- Confirm the circuit model claim with the peer — is this equation specifically the two-port transmission coefficient for coupling caps + parallel LCR? Does a notch/reflection geometry give a different formula?
- Read the page end-to-end as a new user would. Does the physics flow logically? Is every term defined before it's used?
- Run `mkdocs build --strict`.
- Commit. This page becomes the template for all subsequent guide enhancements.

---

### Round 5: Inline physics — remaining guides (Phase 18) — Opus drafts, Sonnet applies

**You (Opus):** Draft the physics content for each page (equations, explanations, assumptions). These require accuracy.

**Then launch Sonnet agents in parallel to apply the drafts:**

**Agent 1: thermal_motion_analysis.md**
- Apply physics background, S_ww equation, G^2*S_xx normalisation explanation, g_0 extraction equations, thermal assumption statement, interpreting results section.
- Source of truth: `Sww.py` lines 21-51 (basic_S_ww_eq), 754-811 (S_ww_constant_calculator), and Rojas et al. eqs. 3-5.

**Agent 2: thermal_motion_measurement.md + spectrum_analyser.md**
- thermal_motion_measurement: measurement scheme physics, red/blue sideband, parameter table equations, two analysis paths note.
- spectrum_analyser: PSD definition, NENBW correction, conversion equation.

**Agent 3: data_analysis.md overview**
- Expand Sww section with physics summary and basic_S_ww_eq equation.

**Orchestrator review:**
- Read every modified file. For each equation added, open the corresponding source function and verify they match term-by-term.
- For `thermal_motion_analysis.md`: verify the G^2*S_xx normalisation equation matches `Sww.py` line 178 (`normalisation = (k_ext*n_d/(k_tot**2)) * h_bar* (f_c*2*np.pi)`). Verify the g_0 extraction matches `S_ww_constant_calculator()` lines 797-806.
- For `thermal_motion_measurement.md`: verify the two-analysis-paths section correctly describes the thermal assumption vs displacement measurement distinction.
- For `spectrum_analyser.md`: verify the NENBW value (4.083) matches the constant in `_fitting.py` (`RS_default_window_NENBW = 4.082911856792962`).
- Run `mkdocs build --strict`.
- Tick Phase 18 items in TODO.md.

---

### Round 6: New workflow guides (Phase 19) — Opus writes physics, Sonnet writes code examples

These are new files with significant physics content. Opus should draft each, then Sonnet can format and add code examples.

**Priority order:**
1. `displacement_measurement.md` — Opus writes (new physics: fitting vs integration methods for T_eff)
2. `omit_analysis.md` — Opus writes (verify OMIT equation against `omit.py` source, note docstring formula issues)
3. `photon_number.md` — Sonnet can handle (straightforward: show equation from `misc_equations.py`, add code example)
4. `cooperativity.md` — Opus writes (new content: C and C_0 definitions, not in code yet)
5. `end_to_end_workflow.md` — Opus writes (capstone, links everything)

**Opus peer:** Verify displacement measurement physics (both methods). Verify OMIT equation. Verify cooperativity definitions.

**Orchestrator review:**
- For `displacement_measurement.md`: verify the fitting method equation chain — with known G, does the amplitude A from `basic_S_ww_eq` correctly map to T_eff? Read `S_ww_constant_calculator()` and trace the algebra in reverse.
- For `displacement_measurement.md`: verify the integration method equation — does equipartition $\frac{1}{2} m \Omega_m^2 \langle x^2 \rangle = \frac{1}{2} k_B T$ give the correct T_eff?
- For `omit_analysis.md`: read `omit.py` OMIT_equation() and compare to the LaTeX equation in the doc. **Known issue:** the docstring formulas for A and floor may be incorrect — flag this explicitly in the doc if the peer confirms they don't match the code.
- For `cooperativity.md`: this defines C and C_0 which are NOT computed by any existing function — verify the definitions are standard (e.g. Aspelmeyer 2014 eq. 37).
- For `end_to_end_workflow.md`: follow every cross-reference link — do the linked pages exist and contain what this page claims?
- Run `mkdocs build --strict`.
- Tick Phase 19 items in TODO.md.

---

### Round 7: Roadmap section (Phase 20) — Opus drafts, Sonnet writes

**You (Opus):** Draft the planned physics content — equations for Gamma_opt, Omega_opt, OMIA, n_min, SQL. These are equations not currently in the code, so accuracy matters.

**Sonnet agents:**
- Create `docs/roadmap/index.md`, `planned_physics.md`, `code_improvements.md`
- Add to mkdocs.yml nav
- Commit each separately

**Orchestrator review:**
- For `planned_physics.md`: verify each future equation is physically correct (these are NOT in the code, so there's no source to cross-check — the Opus peer is the only verification). Confirm Gamma_opt and Omega_opt expressions are consistent with standard references (e.g. Aspelmeyer 2014 eqs. 43-44).
- For `code_improvements.md`: verify each listed issue still exists by reading the relevant source file (e.g. confirm `setup.py` still uses `py_modules`, confirm `__average_and_fit_S_xx__` still has dunder naming).
- Run `mkdocs build --strict`.
- Tick Phase 20 items in TODO.md.

---

### Round 8: API enrichment + docstrings (Phases 21-22) — Sonnet parallel agents

All mechanical work. Launch 2 Sonnet agents.

**Agent 1: Enrich 7 API reference pages**
- Read each thin API page, read the corresponding source module, write 10-15 lines of context + usage example + cross-reference to user guide.

**Agent 2: Module-level docstrings + setup.py**
- Add module-level docstrings to ~15 source files (read each first, write a 2-5 line docstring).
- Fix `setup.py`: `packages=find_packages()`, add `install_requires`.

**Orchestrator review:**
- For API reference pages: read each enriched page. Verify the usage example actually works by checking the import path and function signature against source.
- For module-level docstrings: read each modified source file. Confirm the docstring accurately describes the module's purpose and doesn't make claims about functions that don't exist.
- For `setup.py`: read the modified file. Verify `find_packages()` is imported and `install_requires` lists the actual dependencies (numpy, scipy, pandas, plotly at minimum — check imports in the source files).
- Run the full test suite (module-level docstrings shouldn't break anything, but confirm).
- Run `mkdocs build --strict`.
- Tick Phase 21-22 items in TODO.md.

---

### Final: Verification

1. Run full test suite: `/d/miniconda3/envs/exp/python.exe -m pytest optomechanics/tests/ -v`
2. Run mkdocs build: `cd optomechanics_documentation && /d/miniconda3/envs/exp/python.exe -m mkdocs build --strict`
3. Verify all TODO.md Phase 15-22 items are ticked with commit hashes.
4. Spot-check: read each modified user guide page end-to-end to verify coherence.

---

## Token/Time Efficiency Notes

- **Rounds 1-2** (fixes + tests): Pure Sonnet work, fully parallelised. No Opus peer needed.
- **Rounds 3-6** (physics content): Opus writes drafts, peer-checks equations, Sonnet applies. This is where the Opus peer saves time — catching a wrong equation before it's committed avoids a costly fix cycle.
- **Rounds 7-8** (roadmap + API): Opus drafts roadmap equations (they're speculative/future, so accuracy matters), Sonnet does the rest.
- **Estimated split:** ~60% Sonnet tokens (mechanical edits, tests, formatting), ~30% Opus orchestrator (physics drafts, review), ~10% Opus peer (equation verification).

The main efficiency gain is parallelising Sonnet agents in Rounds 1, 2, 5, and 8 — these have 2-3 independent workstreams each. Without parallelisation, these rounds would take 3x longer.
