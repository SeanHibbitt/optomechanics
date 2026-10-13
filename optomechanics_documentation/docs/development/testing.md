# Testing

## Running the Test Suite

```bash
python -m pytest optomechanics/tests/ -v
```

All tests run without physical hardware. VISA device driver modules are not tested (they
require connected instruments); the Zurich drivers are tested against a mocked `zhinst.toolkit`.

## Test Files

| File | Module tested | Tests | Coverage |
|------|--------------|-------|----------|
| `test_unit_conversions.py` | `data_analysis/unit_conversions.py` | 39 | Extensive |
| `test_Sww.py` | `data_analysis/fitting/Sww.py` | 24 | Broad |
| `test_S21.py` | `data_analysis/fitting/S21.py` | 16 | Good |
| `test_utilities.py` | `data_analysis/utilities.py` | 21 | Good |
| `test_data_logger.py` | `data_management/data_logger.py` | 12 | Good |
| `test_file_management.py` | `data_management/file_management.py` | 13 | Good |
| `test_fitting.py` | `data_analysis/fitting/_fitting.py` | 14 | Good |
| `test_data_management.py` | `data_management/data_management.py` | 11 | Good |
| `test_omit.py` | `data_analysis/fitting/omit.py` | 16 | Good |
| `test_square_membrane.py` | `data_analysis/square_membrane.py` | 6 | Limited |
| `test_misc_equations.py` | `data_analysis/misc_equations.py` | 4 | Limited |
| `test_zurich.py` | `Zurich/` (`ZurichDevice`, `HF2LI`, `zurich_data_management`) | 113 | Broad (mocked hardware) |

**Total: 290 tests across 12 files.**

## Test Data

Frozen fixture files for OMIT/OMIA regression tests are stored in `tests/data/`.
See [`tests/data/README.md`](https://github.com/example/optomechanics/blob/main/optomechanics/tests/data/README.md) for details.

!!! warning "Do not regenerate fixtures automatically"
    The `.npz` snapshot files are committed as frozen reference values. Only regenerate
    them intentionally after a deliberate change to `OMIT_equation`.

## Coverage Gaps

The following subpackages have **no unit tests**:

| Subpackage | Reason |
|-----------|--------|
| `device_control/` | Requires physical instruments connected via GPIB/VISA |
| `GUI/` | Requires a display and PyQt5 event loop |
| `Misc/` | Informal scripts folder, not part of the public API |

Device driver tests would require mock VISA instruments or a hardware-in-the-loop
test environment, which is not currently set up.
