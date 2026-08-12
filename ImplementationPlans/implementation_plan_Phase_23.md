# Implementation Plan — Phase 23: Documentation Accuracy Audit & Corrections

**Date:** 2026-03-09
**Related report:** `ImplementationPlans/Report_of_Phases_23.md`
**Branch:** `Documentation-Updates`

---

## Context

Phase 23 addresses documentation accuracy issues found during an independent audit of the
`optomechanics` module. The audit compared documentation against the actual Python source code
and benchmarked against NumPy and GWPY documentation standards. Key issues: incorrect OMIT/OMIA
claims, unit convention errors for Gamma_m, ambiguous "Made by Claude" attribution, missing
tutorial content, and test quality gaps.

---

## Progress Status

| Task | Status | Commit |
|------|--------|--------|
| Task 1: Fix OMIT/OMIA documentation | DONE | `ddee648` |
| Task 2: Add OMIT/OMIA section to data_analysis.md | DONE | `a03ced2` |
| Task 3: Fix Gamma_m unit convention | DONE | `96972dc` |
| Task 4: Change "Made by Claude" -> "Docstring by Claude" | DONE | `f21fcf3` |
| Task 5: Fix __init__.py + Task 7: Update CLAUDE.md | DONE | `9d9c5aa` |
| Task 6: Enhance OMIT docs (tutorials, refs) | DONE (included in Task 1 commit) | `ddee648` |
| Task 8: Improve test quality for omit.py | NOT STARTED | — |
| Task 9: Update TODO.md | NOT STARTED | — |
| Verification: Run full test suite | NOT STARTED | — |
| Update auto-memory MEMORY.md | NOT STARTED | — |

---

## Task 1: Fix OMIT/OMIA Documentation

**Goal:** Correct the false claim that OMIA is not implemented.

### 1a. Update `optomechanics/data_analysis/fitting/omit.py`

- **Line 2:** Change module docstring from:
  `"Made by Claude. Optomechanically Induced Transparency (OMIT) fitting functions."`
  to:
  `"Docstring by Claude. Optomechanically Induced Transparency / Absorption (OMIT/OMIA) fitting functions."`
  (Note: also applies the "Docstring by Claude" fix from Task 4)

- **Line 33:** Change `OMIT_equation` summary from:
  `"Made by Claude. Optomechanically induced transparency (OMIT) lineshape equation."`
  to:
  `"Docstring by Claude. OMIT/OMIA lineshape equation for optomechanically induced transparency or absorption."`

- **Lines 51-52:** Update `A` parameter docstring to:
  ```
  A : float
      OMIT/OMIA peak amplitude (linear voltage units). Positive for
      transparency peak (OMIT), negative for absorption dip (OMIA).
  ```

### 1b. Update `optomechanics_documentation/docs/user_guide/omit_analysis.md`

- **Line 1:** Change title from `# OMIT Analysis` to `# OMIT / OMIA Analysis`
- **Lines 3-5:** Update opening paragraph to mention both OMIT and OMIA
- **Lines 129-133:** Replace the "OMIT vs OMIA" section with an explanation that the
  equation handles both via the sign of `A`:

  ```markdown
  ## OMIT vs OMIA

  The `OMIT_equation` function handles **both** effects via the sign of the amplitude
  parameter `A`:

  - **OMIT** (transparency window): `A > 0` — pump is red-detuned ($\Delta = -\omega_m$),
    producing a peak in cavity transmission.
  - **OMIA** (absorption dip): `A < 0` — pump is blue-detuned ($\Delta = +\omega_m$),
    producing a dip in cavity transmission.

  The fitting functions (`fit_OMIT`, `fit_OMIT_set_floor`) automatically handle both cases.
  The auto-guess logic detects whether the feature is a peak or dip and sets the sign of
  `A` accordingly.
  ```

### 1c. Update `optomechanics_documentation/docs/roadmap/planned_physics.md`

- **Lines 36-42:** Change section 2 status from "not yet implemented" to:
  ```markdown
  ## 2. OMIA — Optomechanically Induced Absorption

  OMIA is the absorption counterpart to OMIT. It occurs at the opposite sign of detuning
  (blue-detuned pump, $\Delta = +\omega_m$) and produces a dip in cavity transmission.

  The existing `OMIT_equation` function handles OMIA via a negative amplitude parameter `A`.
  Both `fit_OMIT` and `fit_OMIT_set_floor` support OMIA fits.

  **Status:** Implemented (via negative `A` in `fitting.omit`).
  ```

### 1d. Update `optomechanics_documentation/docs/user_guide/omit_analysis.md` nav reference

- In `optomechanics_documentation/mkdocs.yml` line 45, change:
  `- OMIT Analysis: user_guide/omit_analysis.md`
  to:
  `- OMIT / OMIA Analysis: user_guide/omit_analysis.md`

### 1e. Update `optomechanics_documentation/docs/api_reference/data_analysis/fitting/omit.md`

- **Line 1:** Change title from `# omit` to `# omit (OMIT / OMIA)`
- **Line 3:** Update description to mention both OMIT and OMIA

**Commit:** `[AI][Claude] Fix OMIT/OMIA documentation — equation handles both via sign of A`

---

## Task 2: Add OMIT/OMIA Section to data_analysis.md

**Goal:** Add the missing OMIT/OMIA fitting subsection to the data_analysis user guide.

**File:** `optomechanics_documentation/docs/user_guide/data_analysis.md`

Insert after line 68 (after the Sww section, before the `---` at line 70):

```markdown

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
```

**Commit:** `[AI][Claude] Add OMIT/OMIA fitting section to data_analysis.md`

---

## Task 3: Fix Gamma_m Unit Convention

**Goal:** Make Gamma_m consistently rad/s across all documentation. Code parameters
that accept Hz should be documented as Gamma_m/(2pi).

### 3a. Fix glossary notation convention

**File:** `optomechanics_documentation/docs/user_guide/glossary.md`

**Line 15-16** — Replace:
```markdown
- In the equations below, lowercase Greek ($\omega$, $\gamma$, $\kappa$) denotes
  **angular frequency** (rad/s) and Latin letters ($f$, $\Gamma$) denote **Hz**.
```
With:
```markdown
- In the equations below, Greek letters ($\omega$, $\Omega$, $\gamma$, $\Gamma$, $\kappa$)
  denote **angular frequency** (rad/s). The Latin letter $f$ denotes ordinary frequency
  (Hz). Code parameters accept values in Hz (i.e. the angular quantity divided by $2\pi$).
```

### 3b. Fix glossary mechanical parameters table

**File:** `optomechanics_documentation/docs/user_guide/glossary.md`

**Line 33** — Replace:
```
| $\Gamma_m$ | `G_m`, `gamma_m` | Hz | Mechanical linewidth (FWHM damping rate) |
```
With:
```
| $\Gamma_m$ | `G_m`, `gamma_m` | rad/s | Mechanical damping rate (FWHM). Code parameters accept $\Gamma_m / 2\pi$ in Hz. |
```

**Line 34** — Replace:
```
| $Q_m$ | — | dimensionless | Mechanical quality factor, $Q_m = f_m / \Gamma_m$ (also $Q = \pi f_m \tau$ via ring-down) |
```
With:
```
| $Q_m$ | — | dimensionless | Mechanical quality factor, $Q_m = \omega_m / \Gamma_m = 2\pi f_m / \Gamma_m$ (also $Q = \pi f_m \tau$ via ring-down) |
```

**Line 37** — Replace:
```
| $\tau$ | `tau` | s | Ring-down time constant, $\tau = Q_m / (\pi f_m) = 1/(\pi \Gamma_m)$ |
```
With:
```
| $\tau$ | `tau` | s | Ring-down time constant, $\tau = Q_m / (\pi f_m) = 2 / \Gamma_m$ |
```

**Lines 46-47** — The cooperativity formulas use $\Gamma_m$ in the denominator. Add a
note after line 47:
```
All symbols in cooperativity formulas are in consistent units (rad/s).
```

**Line 55** — The $S_{FF}$ formula says "where $\gamma_m = 2\pi\Gamma_m$". With Gamma_m
now in rad/s, $\gamma_m$ and $\Gamma_m$ are the same thing. Simplify to:
```
| $S_{FF}^\text{th}$ | via `S_ff_thermal()` | N²/Hz | Thermal force spectral density, $S_{FF} = 4 k_B T m_\text{eff}\, \Gamma_m$ |
```

### 3c. Fix OMIT analysis parameter table

**File:** `optomechanics_documentation/docs/user_guide/omit_analysis.md`

**Line 47** — Replace:
```
| $\Gamma_m$ | `g_m` | Hz | Mechanical linewidth (damping rate) |
```
With:
```
| $\Gamma_m / 2\pi$ | `g_m` | Hz | Mechanical linewidth (damping rate). Code parameter is $\Gamma_m / 2\pi$. |
```

**Line 95** (in code example) — Replace:
```python
print(f"Γ_m = {g_m:.3f} Hz")
```
With:
```python
print(f"Γ_m/(2π) = {g_m:.3f} Hz")
```

**Line 122** — Replace:
```
| $\Gamma_m$ | Mechanical linewidth — may differ from Sww if backaction is significant |
```
With:
```
| $\Gamma_m / 2\pi$ | Mechanical linewidth — may differ from Sww if backaction is significant |
```

### 3d. Fix cooperativity page

**File:** `optomechanics_documentation/docs/user_guide/cooperativity.md`

**After line 15 and after line 23** — Add below each equation:
```markdown
where all quantities ($g_0$, $\Gamma_m$, $\kappa_\text{tot}$) are in angular frequency (rad/s).
```

**Line 34** — Replace:
```
| $\Gamma_m$          | Mechanical linewidth       | Hz    | Sww fit    |
```
With:
```
| $\Gamma_m / 2\pi$   | Mechanical linewidth       | Hz    | Sww fit    |
```

**Line 52** — Replace:
```python
G_m = 1.0      # Hz (mechanical linewidth)
```
With:
```python
G_m = 1.0      # Hz (= Γ_m/(2π), mechanical linewidth)
```

### 3e. Fix thermal motion analysis

**File:** `optomechanics_documentation/docs/user_guide/thermal_motion_analysis.md`

**Line 107** — Replace:
```
| $\Gamma_m$ | 0.1 – 100 Hz | Mechanical damping (narrower = higher $Q_m$) |
```
With:
```
| $\Gamma_m / 2\pi$ | 0.1 – 100 Hz | Mechanical damping (narrower = higher $Q_m$) |
```

**Line 221** (in code example) — Replace:
```python
print(f"Γ_m  = {G_m:.3f} Hz")
```
With:
```python
print(f"Γ_m/(2π) = {G_m:.3f} Hz")
```

### 3f. Fix thermal motion measurement

**File:** `optomechanics_documentation/docs/user_guide/thermal_motion_measurement.md`

**Lines 49-50** — Replace:
```
| SA span | 5–10 × $\Gamma_m$ | Resolve the mechanical peak |
| SA RBW | $\Gamma_m / 10$ | At least 10 points across the peak |
```
With:
```
| SA span | $5\text{–}10 \times \Gamma_m / 2\pi$ | Resolve the mechanical peak |
| SA RBW | $\Gamma_m / (20\pi)$ | At least 10 points across the peak |
```

**Lines 55-57** — Update prose to match new notation.

### 3g. Fix end-to-end workflow

**File:** `optomechanics_documentation/docs/user_guide/end_to_end_workflow.md`

**Line 120** — Replace:
```
| $f_m$, $\Gamma_m$ | Sww fit | Cooperativity, quality factor |
```
With:
```
| $f_m$, $\Gamma_m / 2\pi$ | Sww fit | Cooperativity, quality factor |
```

### 3h. Fix displacement measurement

**File:** `optomechanics_documentation/docs/user_guide/displacement_measurement.md`

**Line 73** — Replace any standalone $\Gamma_m$ in Hz context with $\Gamma_m / 2\pi$.

### 3i. Fix photon number page

**File:** `optomechanics_documentation/docs/user_guide/photon_number.md`

**Line 84** — After the cooperativity equation, add:
"(all quantities in rad/s)" or rewrite using Hz variables.

### 3j. Fix planned_physics.md cooperativity

**File:** `optomechanics_documentation/docs/roadmap/planned_physics.md`

**Line 78** — Add note after cooperativity equation that all quantities are in rad/s
(matching the convention on line 30 for dynamical backaction).

### 3k. Fix omit.py docstring

**File:** `optomechanics/data_analysis/fitting/omit.py`

**Line 49-50** — Replace:
```
    g_m : float
        Mechanical linewidth / damping rate (Hz).
```
With:
```
    g_m : float
        Mechanical linewidth / damping rate, $\Gamma_m / 2\pi$ (Hz).
```

**Commit:** `[AI][Claude] Fix Gamma_m unit convention: rad/s throughout docs, code params are Gamma_m/(2pi) in Hz`

---

## Task 4: Change "Made by Claude" to "Docstring by Claude"

**Goal:** Replace all 206 instances across 25 files.

**Method:** For each file, use the Edit tool with `replace_all=true`:
- `old_string`: `Made by Claude.`
- `new_string`: `Docstring by Claude.`

Files (in order of instance count):
1. `optomechanics/device_control/Device_Visa_Super.py` (34)
2. `optomechanics/device_control/Rohde_Schwarz_Class_new.py` (34)
3. `optomechanics/device_control/E5063A_VNA_Class_new.py` (25)
4. `optomechanics/data_analysis/unit_conversions.py` (18)
5. `optomechanics/data_analysis/fitting/Sww.py` (18)
6. `optomechanics/data_management/data_logger.py` (13)
7. `optomechanics/data_management/data_management.py` (11)
8. `optomechanics/data_analysis/fitting/S21.py` (8)
9. `optomechanics/data_analysis/utilities.py` (8)
10. `optomechanics/data_analysis/fitting/_fitting.py` (6)
11. `optomechanics/device_control/Device_Visa_Super_rs.py` (4)
12. `optomechanics/data_analysis/fitting/omit.py` (4)
13. `optomechanics/data_management/file_management.py` (3)
14. `optomechanics/data_analysis/Plotting.py` (3)
15. `optomechanics/device_control/VNA.py` (3)
16. `optomechanics/data_analysis/control_gui.py` (2)
17. `optomechanics/data_analysis/attenuation_accounter.py` (2)
18. `optomechanics/data_analysis/square_membrane.py` (2)
19. `optomechanics/data_analysis/Temperature_Reader.py` (2)
20. `optomechanics/__init__.py` (1)
21. `optomechanics/data_analysis/__init__.py` (1)
22. `optomechanics/data_analysis/fitting/__init__.py` (1)
23. `optomechanics/device_control/__init__.py` (1)
24. `optomechanics/data_management/__init__.py` (1)

Also update:
- `CLAUDE.md` line ~8: Change prefix instruction from `Made by Claude.` to `Docstring by Claude.`
- Memory file `MEMORY.md`: Update the NumPy Docstring Format section

**Commit:** `[AI][Claude] Change 'Made by Claude' to 'Docstring by Claude' across all docstrings`

---

## Task 5: Fix data_analysis/__init__.py

**File:** `optomechanics/data_analysis/__init__.py` line 11

Replace:
```python
- :mod:`~optomechanics.data_analysis.fitting` -- S21 and S_xx spectral fitting
```
With:
```python
- :mod:`~optomechanics.data_analysis.fitting` -- S21, S_xx, and OMIT/OMIA spectral fitting
```

**Commit:** `[AI][Claude] Add OMIT/OMIA to data_analysis __init__.py fitting description`

---

## Task 6: Enhance OMIT Documentation with Tutorials and Physics

**Goal:** Bring the OMIT/OMIA user guide up to NumPy/GWPY standard.

**File:** `optomechanics_documentation/docs/user_guide/omit_analysis.md`

### 6a. Add Assumptions section (after line 18)

Insert:
```markdown
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
```

### 6b. Add Synthetic Data Tutorial (new section before "Interpreting results")

Insert a complete worked example:
```markdown
## Tutorial: Synthetic Data Round-Trip

This example generates synthetic OMIT data with known parameters, adds noise,
fits the data, and compares recovered parameters against the ground truth.

```python
import numpy as np
from optomechanics.data_analysis.fitting.omit import OMIT_equation, fit_OMIT
from optomechanics.data_analysis.unit_conversions import linear_voltage_to_dB

# Known parameters
true_f_m = 50e3       # Hz — mechanical frequency
true_g_m = 300        # Hz — mechanical linewidth (Γ_m / 2π)
true_A = 0.5          # linear voltage — OMIT amplitude
true_floor = 0.1      # linear voltage — background
true_kk_tot = 1e6     # Hz — cavity linewidth

# Generate clean data
freqs = np.linspace(30e3, 70e3, 2001)
clean = OMIT_equation(freqs, true_f_m, true_g_m, true_A, true_floor, true_kk_tot)

# Add Gaussian noise
rng = np.random.default_rng(42)
noisy = clean + rng.normal(0, 0.002, len(freqs))

# Convert to dB for fitting
noisy_dB = linear_voltage_to_dB(noisy)

# Fit
popt, pcov, lin_data, guesses = fit_OMIT(
    freqs, noisy_dB, k_tot=true_kk_tot, floor=true_floor,
    guesses=[true_f_m * 1.01, true_g_m * 0.8, true_A * 1.2, true_floor * 0.9],
)

f_m, g_m, A, floor = popt
print(f"f_m:   true={true_f_m:.0f} Hz,   fit={f_m:.0f} Hz")
print(f"g_m:   true={true_g_m:.0f} Hz,   fit={g_m:.0f} Hz")
print(f"A:     true={true_A:.3f},       fit={A:.3f}")
print(f"floor: true={true_floor:.3f},    fit={floor:.3f}")
```
```

### 6c. Add OMIA Worked Example

```markdown
## Example: Fitting an OMIA Absorption Dip

When the pump is blue-detuned, the feature becomes a dip. The same fitting
functions handle this automatically — the sign of `A` will be negative.

```python
# Generate OMIA data (negative A)
omia_data = OMIT_equation(freqs, true_f_m, true_g_m, A=-0.05, floor=0.1, kk_tot=1e6)
# Fit exactly as before — the auto-guess detects the dip
popt, _, _, _ = fit_OMIT(freqs, linear_voltage_to_dB(omia_data), k_tot=1e6, floor=0.1)
print(f"A = {popt[2]:.4f}")  # should be negative
```
```

### 6d. Add Choosing Initial Guesses section

```markdown
## Choosing initial guesses

The `guesses` parameter accepts a list of starting values for the fit:

- `fit_OMIT`: `[f_m, g_m, A, floor]`
- `fit_OMIT_set_floor`: `[f_m, g_m, A]`

**Tips:**

- `f_m`: Set to the frequency of the peak (or dip) visible in the data.
- `g_m`: Estimate the FWHM of the feature by eye.
- `A`: Estimate `peak_height - floor` (positive for OMIT, negative for OMIA).
- `floor`: Use the mean value far from the feature.
- If auto-guessing fails, provide explicit guesses with values close to the
  expected parameters.
```

### 6e. Add Troubleshooting section

```markdown
## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Fit does not converge (`maxfev exceeded`) | Initial guesses too far from true values | Provide manual guesses closer to the visible feature |
| Fitted `g_m` is unreasonably large | `kk_tot` is wrong — it strongly affects the shape | Re-check your S21-derived cavity linewidth |
| Fitted `f_m` is offset from the visible peak | Frequency array may not be centred correctly | Verify `rel_freqs` is relative to the carrier |
| `A` has wrong sign | Pump detuning is opposite to what you expected | Check whether you are red- or blue-detuned |
| Fit returns `floor` much larger/smaller than expected | Background has a slope that the constant floor cannot capture | Consider fitting a sub-range of data, or subtracting a linear baseline first |
```

### 6f. Add References section

```markdown
## References

1. Aspelmeyer, M., Kippenberg, T. J. & Marquardt, F. Cavity optomechanics.
   *Rev. Mod. Phys.* **86**, 1391–1452 (2014). doi:10.1103/RevModPhys.86.1391
2. Weis, S. et al. Optomechanically Induced Transparency.
   *Science* **330**, 1520–1523 (2010). doi:10.1126/science.1195596
3. Safavi-Naeini, A. H. et al. Electromagnetically induced transparency and
   slow light with optomechanics. *Nature* **472**, 69–73 (2011).
4. Kumar, S. *A Novel Architecture for room temperature microwave optomechanical
   experiments* (2023).
```

**Commit:** `[AI][Claude] Enhance OMIT/OMIA docs with assumptions, tutorials, troubleshooting, references`

---

## Task 7: Update CLAUDE.md Docstring Prefix

**File:** `c:\Users\seanh\OneDrive\Documents\Python_Scripts\optomechanics\CLAUDE.md`

Replace:
```markdown
- When rewriting a docstring, begin the summary line with `Made by Claude.`
```
With:
```markdown
- When rewriting a docstring, begin the summary line with `Docstring by Claude.`
```

Also update the auto-memory file at:
`C:\Users\seanh\.claude\projects\c--Users-seanh-OneDrive-Documents-Python-Scripts-optomechanics\memory\MEMORY.md`

**Commit:** `[AI][Claude] Update CLAUDE.md docstring prefix to 'Docstring by Claude'`

---

## Task 8: Improve Test Quality for omit.py

**File:** `optomechanics/tests/test_omit.py`

### 8a. Add module docstring documenting test parameter choices

```python
"""
Unit tests for data_analysis/fitting/omit.py.

Test parameters represent a physically plausible room-temperature microwave
optomechanical system:
- F_M = 1 MHz mechanical frequency (typical for SiN membrane)
- G_M = 10 Hz mechanical linewidth (Q ~ 1e5)
- KK_TOT = 1 MHz cavity linewidth (matching resolved-sideband regime)
- A = 1e10 chosen to give a clearly visible peak above FLOOR = 1.0
  at the given kk_tot (the denominator scales as ~omega_m^2 * kappa ~ 1e19)
- FLOOR = 1.0 normalised background transmission

Test data files in tests/data/:
- omit_test_vector_peak.npz: OMIT peak (A > 0) generated with OMIT_equation
  using the parameters above, evaluated at 1001 points from 0.95-1.05 MHz.
- omit_test_vector_dip.npz: OMIA dip (A < 0) with A = -1e10.
"""
```

### 8b. Create test data generation script

Create `optomechanics/tests/data/generate_omit_test_vectors.py`:
```python
"""Generate test vectors for OMIT/OMIA tests.

Run this script to regenerate the .npz files. Parameters are documented
in the test module docstring.
"""
import numpy as np
from optomechanics.data_analysis.fitting.omit import OMIT_equation

params_peak = dict(f_m=1e6, g_m=10.0, A=1e10, floor=1.0, kk_tot=1e6)
params_dip = dict(f_m=1e6, g_m=10.0, A=-1e10, floor=1.0, kk_tot=1e6)
freqs = np.linspace(0.95e6, 1.05e6, 1001)

np.savez("omit_test_vector_peak.npz", freqs=freqs,
         transmission=OMIT_equation(freqs, **params_peak), **params_peak)
np.savez("omit_test_vector_dip.npz", freqs=freqs,
         transmission=OMIT_equation(freqs, **params_dip), **params_dip)
```

### 8c. Add exact-value test using data file

```python
def test_OMIT_equation_exact_values_peak():
    """Verify OMIT_equation against pre-computed peak test vector."""
    data = np.load(DATA_DIR / "omit_test_vector_peak.npz")
    result = OMIT_equation(data["freqs"], data["f_m"], data["g_m"],
                           data["A"], data["floor"], data["kk_tot"])
    assert_allclose(result, data["transmission"], rtol=1e-12)
```

### 8d. Add negative-A (OMIA) test

```python
def test_OMIT_negative_A_produces_dip():
    """Negative A should produce an absorption dip below floor (OMIA)."""
    f = np.linspace(0.99e6, 1.01e6, 1000)
    result = OMIT_equation(f, F_M, G_M, A=-1e10, floor=FLOOR, kk_tot=KK_TOT)
    assert np.min(result) < FLOOR
    # Minimum should be near f_m
    dip_freq = f[np.argmin(result)]
    assert abs(dip_freq - F_M) < 10 * G_M
```

### 8e. Add fitting round-trip test

```python
def test_fit_OMIT_recovers_known_parameters():
    """Generate synthetic OMIT data, fit, verify parameter recovery."""
    freqs = np.linspace(0.95e6, 1.05e6, 1001)
    true = [1e6, 10.0, 1e10, 1.0]  # f_m, g_m, A, floor
    kk_tot = 1e6
    clean = OMIT_equation(freqs, *true, kk_tot)
    noisy_dB = linear_voltage_to_dB(clean)  # no noise for deterministic test
    popt, _, _, _ = fit_OMIT(freqs, noisy_dB, kk_tot, floor=1.0,
                             guesses=[1e6, 10.0, 1e10, 1.0])
    assert_allclose(popt, true, rtol=0.01)
```

### 8f. Add fitting round-trip test for fit_OMIT_set_floor

```python
def test_fit_OMIT_set_floor_recovers_known_parameters():
    """Generate synthetic data, fit with fixed floor, verify recovery."""
    freqs = np.linspace(0.95e6, 1.05e6, 1001)
    true = [1e6, 10.0, 1e10]  # f_m, g_m, A (floor fixed)
    kk_tot = 1e6
    floor = 1.0
    clean = OMIT_equation(freqs, *true, floor, kk_tot)
    noisy_dB = linear_voltage_to_dB(clean)
    popt, _, _, _ = fit_OMIT_set_floor(freqs, noisy_dB, kk_tot, floor=floor,
                                        guesses=[1e6, 10.0, 1e10])
    assert_allclose(popt, true, rtol=0.01)
```

**Commit:** `[AI][Claude] Improve test_omit.py with exact-value, OMIA, and fitting round-trip tests`

---

## Task 9: Update TODO.md

Add Phase 23 section to `TODO.md` with all sub-tasks and their completion status.

**Commit:** `[AI][Claude] Add Phase 23 to TODO.md`

---

## Verification

After all changes:

1. Run full test suite:
   ```bash
   /c/Users/seanh/miniconda3/envs/exp/python.exe -m pytest optomechanics/tests/ -v
   ```

2. Build docs (if mkdocs is available):
   ```bash
   cd optomechanics_documentation && mkdocs build --strict
   ```

3. Verify no "Made by Claude" remains:
   ```bash
   grep -r "Made by Claude" optomechanics/
   ```

---

## Commit Order

1. `[AI][Claude] Fix OMIT/OMIA documentation — equation handles both via sign of A`
2. `[AI][Claude] Add OMIT/OMIA fitting section to data_analysis.md`
3. `[AI][Claude] Fix Gamma_m unit convention: rad/s throughout, code params are Gamma_m/(2pi)`
4. `[AI][Claude] Change 'Made by Claude' to 'Docstring by Claude' across all docstrings`
5. `[AI][Claude] Add OMIT/OMIA to data_analysis __init__.py fitting description`
6. `[AI][Claude] Enhance OMIT/OMIA docs with assumptions, tutorials, troubleshooting, references`
7. `[AI][Claude] Update CLAUDE.md docstring prefix to 'Docstring by Claude'`
8. `[AI][Claude] Improve test_omit.py with exact-value, OMIA, and fitting round-trip tests`
9. `[AI][Claude] Add Phase 23 to TODO.md`
