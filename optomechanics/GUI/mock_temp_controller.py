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
# 2.  Mock dated_logger so we don't need D:\Experiment Data to exist
# ---------------------------------------------------------------------------

import pandas as pd


class _MockDatedLogger:
    """Minimal stand-in for dated_logger — stores rows in memory only."""

    def __init__(self, *args, **kwargs):
        self.data = pd.DataFrame()        # empty: Worker will skip pre-load

    def __call__(self, row):
        pass                              # silently discard each data row


def _mock_dated_logger(*args, **kwargs):
    print('[MOCK] dated_logger: logging to memory only (no file written)')
    return _MockDatedLogger(*args, **kwargs)


# Patch it inside the data_management module before Temp_Controller loads
import optomechanics.data_management.data_logger as _dl_mod
_dl_mod.dated_logger = _mock_dated_logger

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
# 4.  Launch the GUI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = _tc.MainWindow()
    window.show()
    sys.exit(app.exec_())
