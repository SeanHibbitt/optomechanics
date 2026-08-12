"""
Mock launcher for Temp_Controller.py — no hardware required.

Simulates the Lakeshore 372 AC Resistance Bridge over GPIB so the full GUI
can be tested without a physical instrument connection.

Usage:
    python mock_temp_controller.py

Simulated values
----------------
Channel 3  (T1K / 1K pot)  : ~1.30 K  with slow drift and noise
Channel 4  (TMC / mix. ch.) : ~0.050 K with slow drift and noise
"""

import sys
import os
import math
import time
import random

# ---------------------------------------------------------------------------
# 1.  Mock pyvisa BEFORE any other local import touches it
# ---------------------------------------------------------------------------

class _MockInstrument:
    """Emulates GPIB query responses from a Lakeshore Model 372."""

    def __init__(self):
        self._t0 = time.time()

    def query(self, command):
        command = command.strip()
        elapsed = time.time() - self._t0

        if command == 'KRDG?4':          # Mixing chamber (K)
            noise = random.gauss(0, 0.0002)
            drift = 0.003 * math.sin(elapsed / 45.0)
            return str(round(0.050 + drift + noise, 6))

        if command == 'KRDG?3':          # 1K pot (K)
            noise = random.gauss(0, 0.003)
            drift = 0.04 * math.sin(elapsed / 90.0)
            return str(round(1.300 + drift + noise, 6))

        return '0.0'                     # safe default for any other query

    def close(self):
        pass

    def write(self, command):
        pass


class _MockResourceManager:
    """Emulates pyvisa.ResourceManager."""

    def open_resource(self, address):
        print(f'[MOCK VISA] Opened resource: {address}')
        return _MockInstrument()

    def list_resources(self):
        return ()        # No real hardware visible — safe for connected_devices()

    def close(self):
        pass


# Monkey-patch pyvisa in-place.  Every module that does `import pyvisa` will
# share the same module object, so replacing ResourceManager here is enough.
import pyvisa as _pyvisa
_pyvisa.ResourceManager = _MockResourceManager

# ---------------------------------------------------------------------------
# 2.  Redirect dated_logger to test_data/ instead of D:\Experiment Data
# ---------------------------------------------------------------------------

import optomechanics.data_management.data_logger as _dl_mod

_TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
os.makedirs(_TEST_DATA_DIR, exist_ok=True)

_real_dated_logger = _dl_mod.dated_logger


def _redirected_dated_logger(*args, **kwargs):
    """Use real dated_logger but always write to test_data/."""
    kwargs.pop('base_path', None)
    print(f'[MOCK] dated_logger: redirecting output to {_TEST_DATA_DIR}')
    return _real_dated_logger(*args, base_path=_TEST_DATA_DIR, **kwargs)


_dl_mod.dated_logger = _redirected_dated_logger

# ---------------------------------------------------------------------------
# 3.  Load Temp_Controller as a module (skips the __main__ block)
# ---------------------------------------------------------------------------

import importlib.util

_gui_dir = os.path.dirname(os.path.abspath(__file__))
_tc_path = os.path.join(_gui_dir, 'Temp_Controller.py')

_spec = importlib.util.spec_from_file_location('Temp_Controller', _tc_path)
_tc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tc)

# ---------------------------------------------------------------------------
# 4.  Subclass MainWindow to re-enable PID buttons (safe: no hardware calls)
# ---------------------------------------------------------------------------

class MockMainWindow(_tc.MainWindow):
    """MainWindow with PID controls unlocked for mock testing."""

    def __init__(self):
        super().__init__()
        # Re-enable buttons that were disabled to protect real hardware.
        # All these actions are purely software-side (worker.pid + JSON files).
        self.step_up_button.setEnabled(True)
        self.step_down_button.setEnabled(True)
        self.load_pid_settings_button.setEnabled(True)
        self.save_pid_settings_button.setEnabled(True)
        self.initialize_settings_button.setEnabled(True)
        self.remove_pid_settings_button.setEnabled(True)
        print('[MOCK] PID control buttons enabled.')

# ---------------------------------------------------------------------------
# 5.  Launch the GUI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MockMainWindow()
    window.show()
    sys.exit(app.exec_())
