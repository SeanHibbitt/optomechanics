"""
Tests for pure functions in optomechanics/GUI/Temp_Controller.py.

GUI and instrument libraries (PyQt5, pyvisa, matplotlib, simple_pid, etc.)
are mocked out via sys.modules so no display or hardware is required.
"""

import sys
import pytest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Stub out every external / GUI dependency before the module is imported
# ---------------------------------------------------------------------------
_MOCKED_MODULES = [
    "PyQt5",
    "PyQt5.QtWidgets",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.backends",
    "matplotlib.backends.backend_qt5agg",
    "pyvisa",
    "simple_pid",
    "pandas",
    "optomechanics.device_control.KeithleyDMM6500",
    "optomechanics.device_control.SPD3303XE",
    "optomechanics.data_management.data_logger",
]
for _mod in _MOCKED_MODULES:
    sys.modules.setdefault(_mod, MagicMock())

# Make attribute access on the PyQt5 stubs return MagicMock (needed for
# class-level decoration like pyqtSignal and Qt.AlignCenter).
sys.modules["PyQt5.QtCore"].pyqtSignal = MagicMock(return_value=MagicMock())
sys.modules["PyQt5.QtCore"].Qt = MagicMock()

from Optomechanics.optomechanics.GUI.old.Temp_Controller import temperature, R_0, alpha  # noqa: E402


# ---------------------------------------------------------------------------
# temperature(res)  — formula: T = (res - R_0) / alpha
#   R_0 = 1000 ohm,  alpha = 3.85 ohm/K
# ---------------------------------------------------------------------------

class TestTemperatureConversion:

    def test_at_R0_gives_zero(self):
        """Resistance equal to R_0 should give 0 °C."""
        assert temperature(1000) == pytest.approx(0.0)

    def test_100_degrees(self):
        """R_0 + 100*alpha = 1385 ohm → 100 °C."""
        assert temperature(1385) == pytest.approx(100.0)

    def test_minus_100_degrees(self):
        """R_0 - 100*alpha = 615 ohm → -100 °C."""
        assert temperature(615) == pytest.approx(-100.0)

    def test_10_degrees(self):
        """R_0 + 10*alpha = 1038.5 ohm → 10 °C."""
        assert temperature(1038.5) == pytest.approx(10.0)

    def test_string_input_is_accepted(self):
        """String resistance values should be cast to float without error."""
        assert temperature("1000") == pytest.approx(0.0)

    def test_string_100_degrees(self):
        """String '1385' should still resolve to 100 °C."""
        assert temperature("1385") == pytest.approx(100.0)

    def test_formula_matches_constants(self):
        """Spot-check: result must equal (res - R_0) / alpha for an arbitrary value."""
        res = 1500.0
        expected = (res - R_0) / alpha
        assert temperature(res) == pytest.approx(expected)

    def test_negative_resistance_offset(self):
        """Resistance below R_0 should give a negative temperature."""
        assert temperature(999) < 0
