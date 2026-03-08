# Code Improvements

The items below are known technical debt and packaging issues earmarked for a future refactor. None of them block normal usage, but each represents a rough edge worth smoothing.

---

## 1. `setup.py` — Packaging Configuration

The current `setup.py` uses:

```python
py_modules=['optomechanics']
```

This installs only a single top-level module file rather than the full package tree. The correct approach is:

```python
from setuptools import setup, find_packages

setup(
    name='optomechanics',
    packages=find_packages(),
    install_requires=[
        # list dependencies here
    ],
)
```

**Workaround until fixed:** install in editable mode from the repository root:

```bash
pip install -e .
```

This makes the source directory itself importable, so the full package structure is available regardless of the `py_modules` misconfiguration.

---

## 2. `__average_and_fit_S_xx__` — Dunder Method Exposed to Users

The method `__average_and_fit_S_xx__` follows Python's dunder (double-underscore) convention, which is normally reserved for special protocol methods (`__init__`, `__repr__`, etc.). This name signals "internal implementation detail" to both Python and to users, yet users are expected to call it directly.

**Planned fix:** rename to a public name (e.g. `average_and_fit_Sxx`) or a single-underscore private name (`_average_and_fit_Sxx`) with clear documentation indicating whether it is part of the public API.

---

## 3. Parameter Naming Standardisation

Several parameter names are inconsistent across functions in the package. Known examples:

| Current name | Context | Suggested standard name |
|---|---|---|
| `A` | Amplitude in fitting routines | `amplitude` |
| `nf` | Noise floor | `noise_floor` |
| `kk_tot` | Total linewidth (used alongside `kappa_tot`) | `kappa_tot` |
| `height_of_sin` | Sinusoidal peak height | `sin_amplitude` |

A future refactor would standardise these across all functions, updating call sites and docstrings consistently.

---

## 4. Dead Code in `data_management.py`

`data_management.py` contains unused code paths — functions or branches that are never reached during normal operation and have not been removed. These add noise to the module and make it harder to understand the intended API.

**Planned fix:** audit the file, confirm which code paths are unreachable, and remove or deprecate them with a clear deprecation notice before deletion.
