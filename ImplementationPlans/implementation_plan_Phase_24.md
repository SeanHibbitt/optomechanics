# Implementation Plan — Phase 24: Test Quality & Bug Fixes

**Date:** 2026-03-09
**Related report:** `ImplementationPlans/Report_of_Phases_23.md` (Issues 7 and 8b)
**Prerequisite:** Phase 23 (documentation accuracy corrections — completed)
**Branch:** `Documentation-Updates`

---

## Context

Phase 23 corrected documentation inaccuracies (OMIT/OMIA claims, Gamma_m units,
"Made by Claude" phrasing, missing tutorials). Two categories of work remain from
the Phase 23 audit report:

1. **Issue 7** — Test quality gaps in `test_omit.py`: no exact-value tests, no OMIA
   tests, no fitting round-trip tests, no test data files, undocumented parameter
   choices.
2. **Issue 8b** — Code bug in `fit_OMIT` and `fit_OMIT_set_floor` where tuple
   unpacking of `guesses` occurs before the `False` check, crashing on default call.

---

## Sub-phase 24a: Fix `fit_OMIT` Guess-Handling Bug

**Report reference:** Issue 8b
**File:** `optomechanics/data_analysis/fitting/omit.py`

### Problem

Both `fit_OMIT` (line 118) and `fit_OMIT_set_floor` (line 184) unpack `guesses`
via tuple assignment **before** checking whether `guesses` is `False` (the default).
This means calling `fit_OMIT(freqs, data, k_tot, floor)` without explicit guesses
will raise `TypeError: cannot unpack non-iterable bool` at line 118, and the
auto-guess logic (lines 121-137) is never reached.

```python
# Current broken order (fit_OMIT, lines 118-121):
f_m_guess, g_m_guess, A_guess, floor = guesses   # line 118 — crashes if guesses=False
if np.any(guesses) == False:                       # line 121 — never reached
    # auto-generate guesses ...
```

### Required Fix

Restructure both functions to check `guesses` before unpacking. Use `is False`
instead of `np.any(guesses) == False` for clarity and correctness.

#### In `fit_OMIT` (around line 118)

Replace the current block:
```python
f_m_guess, g_m_guess, A_guess, floor = guesses

if np.any(guesses) == False:
    # auto-guess logic ...
    f_m_guess = ...
    g_m_guess = ...
    A_guess = ...
    floor_guess = ...
```

With:
```python
if guesses is False:
    # auto-guess logic (existing lines 122-137, unchanged)
    f_m_guess = freqs[np.argmax(amplitude_linear_voltage)]
    g_m_guess = ...
    A_guess = ...
    floor_guess = ...
else:
    f_m_guess, g_m_guess, A_guess, floor_guess = guesses
```

Note: the existing code uses `floor` as the unpacked variable name (shadowing the
`floor` parameter). The restructured version should use `floor_guess` consistently
to avoid confusion. Check that all downstream references to the unpacked guess
values use the correct variable name.

#### In `fit_OMIT_set_floor` (around line 184)

Apply the same restructuring. This function unpacks 3 values (no floor):
```python
if guesses is False:
    # auto-guess logic (existing lines ~188-200, unchanged)
    f_m_guess = ...
    g_m_guess = ...
    A_guess = ...
else:
    f_m_guess, g_m_guess, A_guess = guesses
```

### Verification

After this fix, calling `fit_OMIT(freqs, data_dB, k_tot, floor)` without
`guesses` should use auto-guessing instead of crashing. The fitting round-trip
tests in Sub-phase 24c will verify this.

**Commit:** `[AI][Claude] Fix fit_OMIT/fit_OMIT_set_floor guess handling — check before unpacking`

---

## Sub-phase 24b: Create Test Data Infrastructure

**Report reference:** Issue 7b, 7c
**Directory:** `optomechanics/tests/data/`

### 24b-1. Create test data generation script

**File:** `optomechanics/tests/data/generate_omit_test_vectors.py`

This script already exists (created during Phase 23 planning but never run).
Verify its content matches the following and run it:

```python
"""Generate test vectors for OMIT/OMIA tests.

Run this script to regenerate the .npz files used by test_omit.py.

Parameters represent a physically plausible room-temperature microwave
optomechanical system:
- f_m = 1 MHz mechanical frequency (typical for SiN membrane)
- g_m = 10 Hz mechanical linewidth (Q ~ 1e5)
- kk_tot = 1 MHz cavity linewidth (resolved-sideband regime)
- A = 1e10 chosen to give a clearly visible peak above floor = 1.0
  at the given kk_tot (denominator scales as ~omega_m^2 * kappa ~ 1e19)
- floor = 1.0 normalised background transmission

Test vectors:
- omit_test_vector_peak.npz: OMIT peak (A > 0), 1001 points, 0.95-1.05 MHz
- omit_test_vector_dip.npz:  OMIA dip  (A < 0), same frequency range
"""
import numpy as np
import sys
import os

# Add package root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from optomechanics.data_analysis.fitting.omit import OMIT_equation

freqs = np.linspace(0.95e6, 1.05e6, 1001)

params_peak = dict(f_m=1e6, g_m=10.0, A=1e10, floor=1.0, kk_tot=1e6)
params_dip = dict(f_m=1e6, g_m=10.0, A=-1e10, floor=1.0, kk_tot=1e6)

data_dir = os.path.dirname(__file__)

np.savez(
    os.path.join(data_dir, "omit_test_vector_peak.npz"),
    freqs=freqs,
    transmission=OMIT_equation(freqs, **params_peak),
    **{k: np.float64(v) for k, v in params_peak.items()},
)

np.savez(
    os.path.join(data_dir, "omit_test_vector_dip.npz"),
    freqs=freqs,
    transmission=OMIT_equation(freqs, **params_dip),
    **{k: np.float64(v) for k, v in params_dip.items()},
)

print("Generated omit_test_vector_peak.npz and omit_test_vector_dip.npz")
```

### 24b-2. Run the generation script

```bash
/c/Users/seanh/miniconda3/envs/exp/python.exe optomechanics/tests/data/generate_omit_test_vectors.py
```

This produces two `.npz` files in `optomechanics/tests/data/`.

### 24b-3. Create README for test data

**File:** `optomechanics/tests/data/README.md`

```markdown
# Test Data Files

## OMIT / OMIA Test Vectors

Generated by `generate_omit_test_vectors.py` using `OMIT_equation` with known
parameters. Used by `test_omit.py` for exact-value regression tests.

### Files

| File | Description | Key parameter |
|------|-------------|---------------|
| `omit_test_vector_peak.npz` | OMIT transparency peak | A = +1e10 |
| `omit_test_vector_dip.npz`  | OMIA absorption dip    | A = −1e10 |

### Contents of each `.npz` file

| Array/scalar | Type | Description |
|-------------|------|-------------|
| `freqs` | float64[1001] | Frequency axis, 0.95–1.05 MHz |
| `transmission` | float64[1001] | OMIT_equation output |
| `f_m` | float64 | 1e6 Hz — mechanical frequency |
| `g_m` | float64 | 10.0 Hz — mechanical linewidth (Γ_m/2π) |
| `A` | float64 | ±1e10 — amplitude (sign sets OMIT vs OMIA) |
| `floor` | float64 | 1.0 — background floor |
| `kk_tot` | float64 | 1e6 Hz — total cavity linewidth |

### Regenerating

```bash
python generate_omit_test_vectors.py
```

Run from this directory, or from the repo root:
```bash
python optomechanics/tests/data/generate_omit_test_vectors.py
```
```

**Commit:** `[AI][Claude] Create OMIT/OMIA test data files and README`

---

## Sub-phase 24c: Improve `test_omit.py`

**Report reference:** Issues 7a–7f
**File:** `optomechanics/tests/test_omit.py`

### 24c-1. Add module-level docstring

Replace the existing file docstring (if any) with a comprehensive docstring
explaining the test parameters and their physical justification:

```python
"""
Unit tests for optomechanics.data_analysis.fitting.omit.

Test parameters represent a physically plausible room-temperature microwave
optomechanical system:

- F_M = 1 MHz mechanical frequency (typical for SiN membrane)
- G_M = 10 Hz mechanical linewidth (Q ~ 1e5, room-temperature Q)
- KK_TOT = 1 MHz cavity linewidth (resolved-sideband regime: kk_tot ≈ f_m)
- A = 1e10 chosen to give a clearly visible peak above FLOOR = 1.0
  at the given kk_tot. The OMIT denominator scales as
  ~omega_m^2 * kappa ~ (2π × 1e6)^2 × (2π × 1e6) ~ 1e19 (rad/s)^3,
  so A ~ 1e10 produces a peak height of order 1 above the floor.
- FLOOR = 1.0 normalised background transmission (linear voltage).

Test data files (in tests/data/):
- omit_test_vector_peak.npz: OMIT peak (A > 0), 1001 points, 0.95–1.05 MHz
- omit_test_vector_dip.npz:  OMIA dip  (A < 0), same frequency range
See tests/data/README.md for file format and regeneration instructions.
"""
```

### 24c-2. Add imports and constants

Add these imports at the top of the file (after existing imports):

```python
from pathlib import Path
from numpy.testing import assert_allclose
from optomechanics.data_analysis.fitting.omit import fit_OMIT, fit_OMIT_set_floor
from optomechanics.data_analysis.unit_conversions import linear_voltage_to_dB

DATA_DIR = Path(__file__).parent / "data"
```

Keep the existing `OMIT_equation` import and module-level constants (`F_M`, `G_M`,
`A`, `FLOOR`, `KK_TOT`).

### 24c-3. Add exact-value test using peak data file

```python
def test_OMIT_equation_exact_values_peak():
    """Verify OMIT_equation reproduces pre-computed OMIT peak test vector."""
    data = np.load(DATA_DIR / "omit_test_vector_peak.npz")
    result = OMIT_equation(
        data["freqs"],
        float(data["f_m"]),
        float(data["g_m"]),
        float(data["A"]),
        float(data["floor"]),
        float(data["kk_tot"]),
    )
    assert_allclose(result, data["transmission"], rtol=1e-12,
                    err_msg="OMIT peak does not match pre-computed test vector")
```

### 24c-4. Add exact-value test using dip data file

```python
def test_OMIT_equation_exact_values_dip():
    """Verify OMIT_equation reproduces pre-computed OMIA dip test vector."""
    data = np.load(DATA_DIR / "omit_test_vector_dip.npz")
    result = OMIT_equation(
        data["freqs"],
        float(data["f_m"]),
        float(data["g_m"]),
        float(data["A"]),
        float(data["floor"]),
        float(data["kk_tot"]),
    )
    assert_allclose(result, data["transmission"], rtol=1e-12,
                    err_msg="OMIA dip does not match pre-computed test vector")
```

### 24c-5. Add negative-A (OMIA) property tests

```python
def test_OMIT_negative_A_produces_dip():
    """Negative A should produce an absorption dip below floor (OMIA)."""
    f = np.linspace(0.99e6, 1.01e6, 1000)
    result = OMIT_equation(f, F_M, G_M, A=-1e10, floor=FLOOR, kk_tot=KK_TOT)
    assert np.min(result) < FLOOR, "OMIA dip should go below floor"
    # Minimum should be near f_m
    dip_freq = f[np.argmin(result)]
    assert abs(dip_freq - F_M) < 10 * G_M, "OMIA dip should be near f_m"


def test_OMIT_negative_A_is_mirror_of_positive():
    """OMIA dip depth should equal OMIT peak height (relative to floor)."""
    f = np.linspace(0.99e6, 1.01e6, 1000)
    peak = OMIT_equation(f, F_M, G_M, A=1e10, floor=FLOOR, kk_tot=KK_TOT)
    dip = OMIT_equation(f, F_M, G_M, A=-1e10, floor=FLOOR, kk_tot=KK_TOT)
    peak_height = np.max(peak) - FLOOR
    dip_depth = FLOOR - np.min(dip)
    assert_allclose(peak_height, dip_depth, rtol=1e-10,
                    err_msg="OMIT peak and OMIA dip should be symmetric about floor")
```

### 24c-6. Add fitting round-trip test for `fit_OMIT`

This test requires Sub-phase 24a (bug fix) to be completed first, because
`fit_OMIT` with explicit guesses must work correctly.

```python
def test_fit_OMIT_recovers_known_parameters():
    """Generate clean OMIT data, fit with explicit guesses, verify recovery."""
    freqs = np.linspace(0.95e6, 1.05e6, 1001)
    true_params = [1e6, 10.0, 1e10, 1.0]  # f_m, g_m, A, floor
    kk_tot = 1e6

    clean = OMIT_equation(freqs, *true_params, kk_tot)
    clean_dB = linear_voltage_to_dB(clean)

    # Provide exact guesses for deterministic convergence
    popt, pcov, lin_data, guesses_out = fit_OMIT(
        freqs, clean_dB, kk_tot, floor=1.0,
        guesses=[1e6, 10.0, 1e10, 1.0],
    )

    assert_allclose(popt[0], true_params[0], rtol=0.01,
                    err_msg="f_m not recovered")
    assert_allclose(popt[1], true_params[1], rtol=0.01,
                    err_msg="g_m not recovered")
    assert_allclose(popt[2], true_params[2], rtol=0.01,
                    err_msg="A not recovered")
    assert_allclose(popt[3], true_params[3], rtol=0.01,
                    err_msg="floor not recovered")
```

### 24c-7. Add fitting round-trip test for `fit_OMIT_set_floor`

```python
def test_fit_OMIT_set_floor_recovers_known_parameters():
    """Generate clean OMIT data, fit with fixed floor, verify recovery."""
    freqs = np.linspace(0.95e6, 1.05e6, 1001)
    true_params = [1e6, 10.0, 1e10]  # f_m, g_m, A (floor is fixed)
    kk_tot = 1e6
    floor = 1.0

    clean = OMIT_equation(freqs, *true_params, floor, kk_tot)
    clean_dB = linear_voltage_to_dB(clean)

    popt, pcov, lin_data, guesses_out = fit_OMIT_set_floor(
        freqs, clean_dB, kk_tot, floor=floor,
        guesses=[1e6, 10.0, 1e10],
    )

    assert_allclose(popt[0], true_params[0], rtol=0.01,
                    err_msg="f_m not recovered")
    assert_allclose(popt[1], true_params[1], rtol=0.01,
                    err_msg="g_m not recovered")
    assert_allclose(popt[2], true_params[2], rtol=0.01,
                    err_msg="A not recovered")
```

### 24c-8. Add auto-guess fitting test (requires 24a bug fix)

```python
def test_fit_OMIT_auto_guess():
    """fit_OMIT with guesses=False should auto-detect parameters."""
    freqs = np.linspace(0.95e6, 1.05e6, 1001)
    true_params = [1e6, 10.0, 1e10, 1.0]
    kk_tot = 1e6

    clean = OMIT_equation(freqs, *true_params, kk_tot)
    clean_dB = linear_voltage_to_dB(clean)

    # This call uses auto-guessing (guesses=False is the default)
    popt, pcov, lin_data, guesses_out = fit_OMIT(
        freqs, clean_dB, kk_tot, floor=1.0,
    )

    # Auto-guess may not be as precise, so use wider tolerance
    assert_allclose(popt[0], true_params[0], rtol=0.05,
                    err_msg="f_m not recovered via auto-guess")
```

### Summary of new tests

| Test name | Category | Report issue |
|-----------|----------|-------------|
| `test_OMIT_equation_exact_values_peak` | Exact-value regression | 7b |
| `test_OMIT_equation_exact_values_dip` | Exact-value regression | 7b |
| `test_OMIT_negative_A_produces_dip` | OMIA property | 7d |
| `test_OMIT_negative_A_is_mirror_of_positive` | OMIA property | 7d |
| `test_fit_OMIT_recovers_known_parameters` | Fitting round-trip | 7a, 7e |
| `test_fit_OMIT_set_floor_recovers_known_parameters` | Fitting round-trip | 7a, 7e |
| `test_fit_OMIT_auto_guess` | Auto-guess + bug fix | 7a, 8b |

Total: 7 new tests added to the existing 8, bringing `test_omit.py` to 15 tests.

**Commit:** `[AI][Claude] Improve test_omit.py with exact-value, OMIA, and fitting round-trip tests`

---

## Sub-phase 24d: Housekeeping

### 24d-1. Update TODO.md

Add Phase 23 (completed) and Phase 24 entries to `TODO.md`. Mark Phase 23 tasks
as done with commit hashes. Add Phase 24 sub-phase items as checkboxes.

**Commit:** `[AI][Claude] Update TODO.md with Phase 23 and Phase 24 entries`

### 24d-2. Update auto-memory

Update `MEMORY.md` to reflect:
- Docstring prefix is now `Docstring by Claude.` (not `Made by Claude.`)
- Phase 23 is complete, Phase 24 is the current phase
- Any new file paths or conventions

No git commit needed (memory files are not tracked).

### 24d-3. Run full test suite

```bash
/c/Users/seanh/miniconda3/envs/exp/python.exe -m pytest optomechanics/tests/ -v
```

All tests must pass. If any fail, fix before marking Phase 24 complete.

### 24d-4. Verify no "Made by Claude" remains

```bash
grep -r "Made by Claude" optomechanics/
```

Should return zero matches (this was done in Phase 23 but verify it stuck).

---

## Execution Order and Dependencies

```
24a (bug fix)
    └── 24c-6, 24c-7, 24c-8 (fitting tests depend on the bug fix)

24b (test data)
    └── 24c-3, 24c-4 (exact-value tests depend on .npz files)

Recommended order:
1. Sub-phase 24a — fix the bug first
2. Sub-phase 24b — generate test data
3. Sub-phase 24c — add all new tests
4. Sub-phase 24d — housekeeping and verification
```

---

## Commit Summary

| # | Message | Sub-phase |
|---|---------|-----------|
| 1 | `[AI][Claude] Fix fit_OMIT/fit_OMIT_set_floor guess handling — check before unpacking` | 24a |
| 2 | `[AI][Claude] Create OMIT/OMIA test data files and README` | 24b |
| 3 | `[AI][Claude] Improve test_omit.py with exact-value, OMIA, and fitting round-trip tests` | 24c |
| 4 | `[AI][Claude] Update TODO.md with Phase 23 and Phase 24 entries` | 24d |
