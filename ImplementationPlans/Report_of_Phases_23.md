# Report of Phase 23 — Documentation Accuracy Audit

**Date:** 2026-03-09
**Auditor:** Claude Opus 4.6
**Scope:** Full documentation audit of the `optomechanics` Python module, benchmarked against NumPy and GWPY documentation standards.
**Branch:** `Documentation-Updates`

---

## Executive Summary

The documentation is well-structured (MkDocs Material, mkdocstrings, MathJax) and covers
the codebase broadly. However, the audit identified **8 categories of issues** ranging from
factual inaccuracies (OMIT/OMIA claims), unit convention errors, missing content, ambiguous
attribution phrasing, and test quality gaps. This report provides exact file paths, line
numbers, and specific text to change.

---

## Issue 1: OMIT Equation Handles Both OMIT AND OMIA (Documentation Claims Otherwise)

### Finding

The `OMIT_equation` function in `optomechanics/data_analysis/fitting/omit.py` (line 72)
implements:

```python
OMIT = floor*(1 + A * np.abs(1 / denominator))
```

This equation is mathematically valid for **both** OMIT (transparency peak) and OMIA
(absorption dip) through the sign of parameter `A`:

- `A > 0` produces a transparency **peak** above `floor` (OMIT)
- `A < 0` produces an absorption **dip** below `floor` (OMIA)

The auto-guess code already handles this sign flip at `omit.py` lines 129-130:

```python
if np.abs((floor_guess - np.max(amplitude_linear_voltage))) < np.abs((floor_guess - np.min(amplitude_linear_voltage))):
    A_guess = A_guess * -1
```

### Incorrect Documentation (3 locations)

**Location 1:** `optomechanics_documentation/docs/user_guide/omit_analysis.md` lines 129-133

Current text:
```markdown
## OMIT vs OMIA

The current code implements **OMIT** (transparency — a peak in transmission).
The complementary effect **OMIA** (optomechanically induced absorption — a dip)
occurs at opposite detuning.  OMIA is not yet implemented in the code.
```

Should be replaced with text explaining that the same equation handles both effects
via the sign of `A`, with a brief physics explanation of when each case arises
(red detuning = OMIT/transparency, blue detuning = OMIA/absorption).

**Location 2:** `optomechanics_documentation/docs/roadmap/planned_physics.md` lines 36-42

Current text:
```markdown
## 2. OMIA — Optomechanically Induced Absorption

OMIA is the absorption counterpart to OMIT...
OMIA requires a separate model or sign-flip in detuning with appropriate lineshape handling.

**Status:** OMIT is implemented; OMIA is not yet implemented.
```

This entire section should be updated to reflect that OMIA IS handled by the existing
`OMIT_equation` via negative `A`. The status should change to "Implemented" and this
item should be marked as complete.

**Location 3:** `optomechanics_documentation/docs/user_guide/omit_analysis.md` title and throughout

The page title is "OMIT Analysis" but should be renamed to "OMIT / OMIA Analysis" since
both effects are supported. All references to "OMIT" that should include "OMIA" need updating.

### Required Code Documentation Changes

**File:** `optomechanics/data_analysis/fitting/omit.py`

- Line 2: Module docstring says "Optomechanically Induced Transparency (OMIT) fitting functions."
  Change to: "Optomechanically Induced Transparency/Absorption (OMIT/OMIA) fitting functions."

- Line 33: `OMIT_equation` docstring says "Optomechanically induced transparency (OMIT) lineshape equation."
  Change to mention both OMIT and OMIA, explain the sign convention for `A`.

- Line 52 area: Add a note to the `A` parameter docstring:
  "Positive values produce a transparency peak (OMIT); negative values produce an absorption dip (OMIA)."

---

## Issue 2: OMIT/OMIA Fitting Missing from data_analysis.md User Guide

### Finding

**File:** `optomechanics_documentation/docs/user_guide/data_analysis.md`

This page (107 lines) describes the `fitting` sub-package with detailed subsections for:
- `#### S21 fitting` (lines 29-48) — 20 lines with equation, key functions, parameter list
- `#### Sww fitting` (lines 50-68) — 19 lines with equation, fitted parameters, workflow link

There is **no `#### OMIT / OMIA fitting` subsection**. The omit module is completely absent
from this overview page, even though it exists in the API reference index
(`optomechanics_documentation/docs/api_reference/data_analysis/index.md` line 24).

### Required Change

Add a new `#### OMIT / OMIA fitting` subsection after the Sww section (after line 68,
before the `---` separator at line 70). This section should follow the same structure
as the S21 and Sww sections:

1. Brief description of what OMIT/OMIA is
2. The OMIT equation in LaTeX (matching `omit_analysis.md` line 25)
3. Key functions list: `OMIT_equation`, `fit_OMIT`, `fit_OMIT_set_floor`
4. Returned parameters: `f_m`, `g_m` (= Gamma_m/(2pi)), `A`, `floor`
5. Link to the OMIT API reference page and the OMIT Analysis user guide

---

## Issue 3: Gamma_m Unit Convention (rad/s vs Hz)

### Finding

The user requires: **Gamma_m should always appear in rad/s. When quoting the Hz value, write Gamma_m/(2pi).**

The current documentation violates this in multiple locations.

### Error 3a: Glossary "Latin letters" claim

**File:** `optomechanics_documentation/docs/user_guide/glossary.md` line 16

Current text:
```markdown
- In the equations below, lowercase Greek ($\omega$, $\gamma$, $\kappa$) denotes
  **angular frequency** (rad/s) and Latin letters ($f$, $\Gamma$) denote **Hz**.
```

**Problem:** Gamma (capital) is a **Greek** letter, not a Latin letter. The statement is
factually wrong and confuses the convention.

**Fix:** Replace with:
```markdown
- In the equations below, Greek letters ($\omega$, $\Omega$, $\gamma$, $\Gamma$, $\kappa$)
  denote **angular frequency** (rad/s). The Latin letter $f$ denotes ordinary frequency
  (Hz). Code parameters accept Hz values (i.e. the angular quantity divided by $2\pi$).
```

### Error 3b: Glossary Gamma_m entry

**File:** `optomechanics_documentation/docs/user_guide/glossary.md` line 33

Current text:
```
| $\Gamma_m$ | `G_m`, `gamma_m` | Hz | Mechanical linewidth (FWHM damping rate) |
```

**Fix:** Change units from "Hz" to "rad/s" and clarify the code mapping:
```
| $\Gamma_m$ | `G_m`, `gamma_m` | rad/s | Mechanical damping rate (FWHM linewidth). Code parameters accept $\Gamma_m / 2\pi$ in Hz. |
```

### Error 3c: Glossary Q_m formula

**File:** `optomechanics_documentation/docs/user_guide/glossary.md` line 34

Current text:
```
| $Q_m$ | — | dimensionless | Mechanical quality factor, $Q_m = f_m / \Gamma_m$ ... |
```

If Gamma_m is in rad/s, this formula is wrong. Must use:
```
| $Q_m$ | — | dimensionless | Mechanical quality factor, $Q_m = \omega_m / \Gamma_m = 2\pi f_m / \Gamma_m$ ... |
```

### Error 3d: Glossary tau formula

**File:** `optomechanics_documentation/docs/user_guide/glossary.md` line 37

Current text:
```
| $\tau$ | `tau` | s | Ring-down time constant, $\tau = Q_m / (\pi f_m) = 1/(\pi \Gamma_m)$ |
```

If Gamma_m is in rad/s:
```
| $\tau$ | `tau` | s | Ring-down time constant, $\tau = Q_m / (\pi f_m) = 2 / \Gamma_m$ |
```

Derivation: tau = Q_m / (pi * f_m) = (omega_m / Gamma_m) / (pi * f_m) = (2pi f_m / Gamma_m) / (pi f_m) = 2/Gamma_m. Correct.

### Error 3e: OMIT analysis parameter table

**File:** `optomechanics_documentation/docs/user_guide/omit_analysis.md` line 47

Current text:
```
| $\Gamma_m$ | `g_m` | Hz | Mechanical linewidth (damping rate) |
```

**Fix:**
```
| $\Gamma_m / 2\pi$ | `g_m` | Hz | Mechanical linewidth (damping rate). The code parameter is $\Gamma_m / 2\pi$. |
```

### Error 3f: Cooperativity parameter table

**File:** `optomechanics_documentation/docs/user_guide/cooperativity.md` line 34

Current text:
```
| $\Gamma_m$          | Mechanical linewidth       | Hz    | Sww fit    |
```

**Fix:**
```
| $\Gamma_m / 2\pi$   | Mechanical linewidth       | Hz    | Sww fit    |
```

Also update the code example at line 52:
```python
G_m = 1.0      # Hz (mechanical linewidth)
```
Change to:
```python
G_m = 1.0      # Hz (= Γ_m / 2π, mechanical linewidth)
```

### Error 3g: Cooperativity equation notation

**File:** `optomechanics_documentation/docs/user_guide/cooperativity.md` lines 14-15, 22-23

The cooperativity equations use $\Gamma_m$ and $g_0$ and $\kappa_\text{tot}$. These must
all be in the same units for the formula to be dimensionally correct. Add a note below
each equation:

```markdown
where all quantities are in consistent units (either all in rad/s or all in Hz).
The code example below uses Hz throughout.
```

### Error 3h: Thermal motion analysis

**File:** `optomechanics_documentation/docs/user_guide/thermal_motion_analysis.md` line 107

Current text:
```
| $\Gamma_m$ | 0.1 – 100 Hz | Mechanical damping (narrower = higher $Q_m$) |
```

**Fix:**
```
| $\Gamma_m / 2\pi$ | 0.1 – 100 Hz | Mechanical damping (narrower = higher $Q_m$) |
```

### Error 3i: Thermal motion measurement

**File:** `optomechanics_documentation/docs/user_guide/thermal_motion_measurement.md` lines 49-50, 55-57

These lines reference "$\Gamma_m$" in the context of Hz-valued SA settings:
```
| SA span | 5–10 × $\Gamma_m$ | ...
| SA RBW  | $\Gamma_m / 10$   | ...
```

Since these are Hz-valued instrument settings, change to $\Gamma_m / 2\pi$:
```
| SA span | 5–10 × $\Gamma_m / 2\pi$ | ...
| SA RBW  | $\Gamma_m / (20\pi)$      | ...
```

Or more readably: keep the Hz symbol and add a note that these are Hz values.

### Error 3j: End-to-end workflow

**File:** `optomechanics_documentation/docs/user_guide/end_to_end_workflow.md` line 120

```
| $f_m$, $\Gamma_m$ | Sww fit | Cooperativity, quality factor |
```

Change to:
```
| $f_m$, $\Gamma_m / 2\pi$ | Sww fit | Cooperativity, quality factor |
```

### Error 3k: Photon number page

**File:** `optomechanics_documentation/docs/user_guide/photon_number.md` line 84

```
$C = 4 g_0^2\, n_d / (\Gamma_m\, \kappa_\text{tot})$
```

Add note: "(all quantities in consistent units)" or change to use angular notation.

### Error 3l: OMIT code docstrings

**File:** `optomechanics/data_analysis/fitting/omit.py` line 50

Current text:
```
    g_m : float
        Mechanical linewidth / damping rate (Hz).
```

**Fix:**
```
    g_m : float
        Mechanical linewidth / damping rate, $\Gamma_m / 2\pi$ (Hz).
```

Apply same fix to `fit_OMIT` and `fit_OMIT_set_floor` docstrings (no explicit g_m
parameter doc in those, but `g_m` appears in the guesses description).

### Summary of All Gamma_m Files Requiring Changes

| File | Lines | Nature of change |
|------|-------|-----------------|
| `docs/user_guide/glossary.md` | 15-16, 33, 34, 37, 46-47, 55 | Convention statement, Gamma_m entry, Q_m, tau, cooperativity, S_FF |
| `docs/user_guide/omit_analysis.md` | 17, 47, 95, 122 | Parameter table, print statement, interpreting table |
| `docs/user_guide/cooperativity.md` | 15, 23, 34, 52 | Equation notes, parameter table, code example |
| `docs/user_guide/thermal_motion_analysis.md` | 107, 124, 218, 221 | Parameter range table, diagram, code example |
| `docs/user_guide/thermal_motion_measurement.md` | 49-50, 55-57, 110-111 | SA parameter table, comments |
| `docs/user_guide/end_to_end_workflow.md` | 29, 81, 92, 120 | Diagram, prose, equation, parameter table |
| `docs/user_guide/displacement_measurement.md` | 73 | Parameter mention |
| `docs/user_guide/photon_number.md` | 84 | Cooperativity equation |
| `docs/roadmap/planned_physics.md` | 78 | Cooperativity equation |
| `optomechanics/data_analysis/fitting/omit.py` | 50 | Docstring parameter description |

---

## Issue 4: "Made by Claude" Phrasing is Ambiguous

### Finding

There are **206 instances** of "Made by Claude." across **25 source files**. Every docstring
(module-level, class-level, and function-level) begins with this phrase.

The phrase "Made by Claude" implies Claude **wrote the function/module**, not just the
docstring. This is misleading — Claude wrote the documentation, not the implementation code.

### Required Change

Replace all 206 instances of `Made by Claude.` with `Docstring by Claude.`

This is a simple find-and-replace across these 25 files:

| File | Count |
|------|-------|
| `optomechanics/__init__.py` | 1 |
| `optomechanics/data_analysis/__init__.py` | 1 |
| `optomechanics/data_analysis/fitting/__init__.py` | 1 |
| `optomechanics/device_control/__init__.py` | 1 |
| `optomechanics/data_management/__init__.py` | 1 |
| `optomechanics/data_analysis/unit_conversions.py` | 18 |
| `optomechanics/data_analysis/fitting/Sww.py` | 18 |
| `optomechanics/device_control/Device_Visa_Super.py` | 34 |
| `optomechanics/device_control/Rohde_Schwarz_Class_new.py` | 34 |
| `optomechanics/device_control/E5063A_VNA_Class_new.py` | 25 |
| `optomechanics/data_management/data_logger.py` | 13 |
| `optomechanics/data_management/data_management.py` | 11 |
| `optomechanics/data_analysis/fitting/S21.py` | 8 |
| `optomechanics/data_analysis/utilities.py` | 8 |
| `optomechanics/data_analysis/fitting/_fitting.py` | 6 |
| `optomechanics/device_control/Device_Visa_Super_rs.py` | 4 |
| `optomechanics/data_analysis/fitting/omit.py` | 4 |
| `optomechanics/data_management/file_management.py` | 3 |
| `optomechanics/data_analysis/Plotting.py` | 3 |
| `optomechanics/device_control/VNA.py` | 3 |
| `optomechanics/data_analysis/control_gui.py` | 2 |
| `optomechanics/data_analysis/attenuation_accounter.py` | 2 |
| `optomechanics/data_analysis/square_membrane.py` | 2 |
| `optomechanics/data_analysis/Temperature_Reader.py` | 2 |
| **Total** | **206** |

Also update the project instruction in `CLAUDE.md` (line 7-8) and the auto-memory at
`C:\Users\seanh\.claude\projects\...\memory\MEMORY.md` to use the new prefix.

**CLAUDE.md** currently says:
```markdown
- When rewriting a docstring, begin the summary line with `Made by Claude.`
```

Change to:
```markdown
- When rewriting a docstring, begin the summary line with `Docstring by Claude.`
```

---

## Issue 5: data_analysis/__init__.py Missing OMIT Reference

### Finding

**File:** `optomechanics/data_analysis/__init__.py` line 11

Current text:
```python
- :mod:`~optomechanics.data_analysis.fitting` -- S21 and S_xx spectral fitting
```

This omits OMIT/OMIA. The `fitting/__init__.py` (line 9) correctly lists omit, but the
parent `__init__.py` does not.

### Required Change

Change line 11 to:
```python
- :mod:`~optomechanics.data_analysis.fitting` -- S21, S_xx, and OMIT/OMIA spectral fitting
```

---

## Issue 6: Missing Tutorial Content (vs NumPy/GWPY Standard)

### Finding

Compared to GWPY's examples gallery and NumPy's tutorial pages, the OMIT documentation
(`optomechanics_documentation/docs/user_guide/omit_analysis.md`) is missing several
categories of content that would be expected for a physics analysis module.

### 6a: Physics Assumptions Not Stated

The OMIT analysis relies on several assumptions that are not documented:

1. **Resolved sideband regime** ($\kappa \ll \omega_m$) — not stated
2. **Weak probe approximation** — the probe tone must be much weaker than the pump
3. **Single mechanical mode** — no mode overlap or hybridisation
4. **Rotating wave approximation** — counter-rotating terms are dropped
5. **Steady-state cavity response** — transients have settled

**Required:** Add an "Assumptions" admonition box after the "Physics background" section
(after line 18 in `omit_analysis.md`).

### 6b: No Synthetic Data Tutorial

There is no worked example showing:
1. Generation of synthetic OMIT data with known parameters
2. Adding realistic noise
3. Fitting the synthetic data
4. Recovering the known parameters and comparing

**Required:** Add a "Tutorial: Synthetic Data" section with a complete code example.
This would follow the pattern used by GWPY's example gallery. The example should:
- Use `OMIT_equation` to generate clean data with known f_m, g_m, A, floor, kk_tot
- Add Gaussian noise
- Call `fit_OMIT` on the noisy data
- Print recovered vs true parameters
- Plot data + fit

### 6c: No OMIA Worked Example

Once Issue 1 is fixed (documenting that negative A = OMIA), an explicit example showing
an OMIA dip fit is needed. This example should:
- Generate data with negative A
- Show the resulting absorption dip
- Fit with `fit_OMIT` and show the negative A recovery

### 6d: No Initial Guess Guidance

The `guesses` parameter is mentioned but there is no guidance on:
- When auto-guessing fails (e.g., very noisy data, overlapping peaks)
- How to provide manual guesses
- What units the guesses should be in
- Typical ranges for each parameter

**Required:** Add a "Choosing Initial Guesses" subsection.

### 6e: No Troubleshooting Section

No guidance on common failure modes:
- Fit not converging (maxfev exceeded)
- Wrong kk_tot causing poor fits
- Units mismatch (e.g., passing rad/s when Hz expected)
- Very low signal-to-noise ratio
- Background slope not captured by constant floor

**Required:** Add a "Troubleshooting" section at the end of the page.

### 6f: No Cross-Validation with Sww

No guidance on comparing f_m and Gamma_m values from OMIT fits with those from
Sww (thermal noise PSD) fits. This is a basic sanity check in optomechanics
experiments and should be documented.

### 6g: No Academic References

No citations to:
- Aspelmeyer, Kippenberg, Marquardt, Rev. Mod. Phys. 86, 1391 (2014) — canonical review
- Weis et al., Science 330, 1520 (2010) — original OMIT observation
- Safavi-Naeini et al., Nature 472, 69 (2011) — OMIT/OMIA theory
- Kumar / Rojas papers already referenced elsewhere in the codebase

**Required:** Add a "References" section at the bottom of the page.

---

## Issue 7: Test Quality Assessment for omit.py

### Finding

**File:** `optomechanics/tests/test_omit.py` (82 lines, 8 tests)

The existing tests have several quality gaps when assessed against best practices
(explicit data sets, known input/output pairs, documentation of test data generation):

### 7a: Tests Only Cover `OMIT_equation` — Not the Fitting Functions

The 8 tests only exercise `OMIT_equation`. Neither `fit_OMIT` nor `fit_OMIT_set_floor`
are tested at all. This means the most user-facing functions (the fitting routines)
have **zero test coverage**.

### 7b: No Explicit Input/Output Data Sets

All tests use **property-based assertions** (e.g., "output should be positive",
"peak should be near f_m") rather than exact known input/output pairs. There are no:
- Pre-computed expected output arrays for given inputs
- External data files (e.g., `.csv` or `.npy`) with test vectors
- Documented derivations of expected values

### 7c: No Documentation of Test Parameter Selection

The module-level constants (line 7-12):
```python
F_M = 1e6       # 1 MHz mechanical frequency
G_M = 10.0      # 10 Hz mechanical linewidth
A = 1e10        # amplitude parameter
FLOOR = 1.0     # background floor (linear voltage)
KK_TOT = 1e6    # total optical linewidth 1 MHz
```

These are not justified — why 1e10 for A? What physical scenario does this represent?
There is no docstring or comment explaining the choice.

### 7d: No OMIA (Negative A) Tests

No test verifies the absorption dip behaviour with negative A. This is critical
given Issue 1.

### 7e: No Fitting Round-Trip Tests

The most important test for a fitting module is: generate synthetic data with known
parameters, fit it, verify the recovered parameters match within tolerance. This
test is completely absent.

### 7f: No Edge Case Tests

Missing tests for:
- Zero linewidth (`g_m = 0`) — should produce a delta function
- Very large linewidth — should flatten out
- Very small kk_tot — deep resolved sideband regime
- Single-frequency input (`f` array of length 1)
- Negative frequencies

### Required Changes

1. **Create test data files** in a `tests/data/` directory:
   - `omit_test_vector_peak.npz` — synthetic OMIT peak with known parameters,
     containing: `freqs`, `transmission`, `params` dict
   - `omit_test_vector_dip.npz` — synthetic OMIA dip with negative A
   - Include a `tests/data/README.md` documenting how each file was generated

2. **Add exact-value tests** using these data files:
   ```python
   def test_OMIT_equation_exact_values():
       """Verify OMIT_equation against pre-computed test vector."""
       data = np.load("tests/data/omit_test_vector_peak.npz")
       result = OMIT_equation(data["freqs"], ...)
       assert_allclose(result, data["transmission"], rtol=1e-10)
   ```

3. **Add fitting round-trip tests** for both `fit_OMIT` and `fit_OMIT_set_floor`:
   ```python
   def test_fit_OMIT_recovers_known_parameters():
       """Generate synthetic data, fit, recover known parameters."""
       # Generate with known params
       true_params = [f_m, g_m, A, floor]
       clean = OMIT_equation(freqs, *true_params, kk_tot)
       noisy = clean + np.random.default_rng(42).normal(0, noise_level, len(freqs))
       noisy_dB = linear_voltage_to_dB(noisy)
       # Fit
       popt, pcov, _, _ = fit_OMIT(freqs, noisy_dB, kk_tot, floor_guess)
       # Compare
       assert_allclose(popt, true_params, rtol=0.05)
   ```

4. **Add negative-A (OMIA) test**:
   ```python
   def test_OMIT_negative_A_produces_dip():
       """Negative A should produce a dip below floor (OMIA)."""
       f = np.linspace(0.99e6, 1.01e6, 1000)
       result = OMIT_equation(f, F_M, G_M, A=-1e10, floor=FLOOR, kk_tot=KK_TOT)
       assert np.min(result) < FLOOR
   ```

5. **Document all test parameters** with a module-level docstring explaining the physical
   scenario and why each value was chosen.

---

## Issue 8: Minor Issues

### 8a: Broken Link Potential

`optomechanics_documentation/docs/user_guide/omit_analysis.md` line 139 links to
`cooperativity.md`. This file exists and is in the nav, so the link is valid. No action needed.

### 8b: Code Bug in fit_OMIT Guess Handling

**File:** `optomechanics/data_analysis/fitting/omit.py` lines 118 and 184

Both `fit_OMIT` (line 118) and `fit_OMIT_set_floor` (line 184) unpack `guesses` via
tuple unpacking **before** checking `if np.any(guesses) == False`. If `guesses=False`
is passed (the default), the unpacking at line 118 will raise a `TypeError` because
`False` is not iterable.

```python
f_m_guess, g_m_guess, A_guess, floor = guesses  # line 118 — crashes if guesses=False
if np.any(guesses) == False:                     # line 121 — never reached
```

This means the auto-guess feature is **broken** for `fit_OMIT`. It only works if the
caller always provides explicit guesses. This is a code bug, not just a documentation
issue, but is noted here because the documentation describes auto-guessing as a feature.

**Recommended fix:** Move the `if` check before the unpacking, or restructure as:
```python
if guesses is False:
    # auto-generate guesses
    ...
else:
    f_m_guess, g_m_guess, A_guess, floor = guesses
```

### 8c: omit_analysis.md Line 95 Print Statement

```python
print(f"Γ_m = {g_m:.3f} Hz")
```

Should clarify this is Gamma_m/(2pi):
```python
print(f"Γ_m/(2π) = {g_m:.3f} Hz")
```

### 8d: data_analysis.md Missing "See also" Links for OMIT

**File:** `optomechanics_documentation/docs/user_guide/data_analysis.md` line 105-107

The "See also" section at the bottom only links to the glossary. After adding the OMIT
section, add links to the OMIT Analysis user guide page.

---

## Benchmark Assessment: NumPy/GWPY Comparison

### What the documentation does well (vs benchmarks)

| Criterion | Status | Notes |
|-----------|--------|-------|
| MkDocs + Material theme | Good | Professional, searchable, dark mode |
| mkdocstrings auto-extraction | Good | Consistent with NumPy pattern |
| MathJax equations | Good | Clear LaTeX rendering |
| Parameter glossary | Good | Central reference (like GWPY's glossary) |
| Separate user guides vs API ref | Good | Follows NumPy's guide/reference split |
| Code examples in guides | Good | Runnable snippets throughout |

### What's missing (vs benchmarks)

| Criterion | NumPy/GWPY has it | This project | Gap |
|-----------|-------------------|--------------|-----|
| Assumptions/limitations stated | Yes | No | Must add to OMIT and other physics pages |
| Synthetic data tutorials | Yes (GWPY examples) | No | Must add worked examples |
| Troubleshooting guides | Yes (NumPy FAQ) | No | Must add common pitfalls |
| Cross-validation guidance | Yes (GWPY) | No | Must add OMIT vs Sww comparison |
| Academic references | Yes (GWPY cites LIGO) | Partial (in source, not docs) | Must add to all physics pages |
| Version/changelog per function | Yes (NumPy) | No | Low priority |
| Unit convention page | NumPy fft has one | Glossary covers this | Adequate |

---

## Files Modified Summary

| File | Changes |
|------|---------|
| `optomechanics/data_analysis/fitting/omit.py` | OMIT/OMIA docstrings, A parameter sign note, Gamma_m unit, "Docstring by Claude" |
| `optomechanics_documentation/docs/user_guide/omit_analysis.md` | OMIT/OMIA section rewrite, assumptions, tutorials, references, troubleshooting |
| `optomechanics_documentation/docs/user_guide/data_analysis.md` | Add OMIT/OMIA fitting subsection |
| `optomechanics_documentation/docs/user_guide/glossary.md` | Fix notation convention, Gamma_m unit, Q_m, tau formulas |
| `optomechanics_documentation/docs/user_guide/cooperativity.md` | Gamma_m unit, equation notes, code example |
| `optomechanics_documentation/docs/user_guide/thermal_motion_analysis.md` | Gamma_m unit |
| `optomechanics_documentation/docs/user_guide/thermal_motion_measurement.md` | Gamma_m unit |
| `optomechanics_documentation/docs/user_guide/end_to_end_workflow.md` | Gamma_m unit |
| `optomechanics_documentation/docs/user_guide/displacement_measurement.md` | Gamma_m unit |
| `optomechanics_documentation/docs/user_guide/photon_number.md` | Gamma_m unit note |
| `optomechanics_documentation/docs/roadmap/planned_physics.md` | OMIA status update, Gamma_m note |
| `optomechanics/data_analysis/__init__.py` | Add OMIT mention |
| 25 source files | "Made by Claude" -> "Docstring by Claude" (206 instances) |
| `CLAUDE.md` | Update docstring prefix instruction |
| `optomechanics/tests/test_omit.py` | Add fitting tests, OMIA tests, exact-value tests |
| `tests/data/` (new) | Test vector files with documentation |
| `TODO.md` | Add Phase 23 entries |
