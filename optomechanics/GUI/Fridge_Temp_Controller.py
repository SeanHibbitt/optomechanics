"""
Made by Claude. Dilution-fridge temperature monitor and heater control GUI.

Created August 2026, for the cryogenic fridge (Lakeshore Model 372 AC
resistance bridge / temperature controller).

This module is the cryogenic counterpart of ``Temp_Controller.py``
(@author: Hagen Thompson, plotting and file-saving credited to Sean
Hibbitt, see RoomTemp.py).  ``Temp_Controller.py`` was written to
regulate a room-temperature sample plate with a software PID driving a
bench power supply.  Here the structure is reused -- ``Worker`` on a
background thread, ``MplCanvas`` for plotting, ``dated_logger`` for
crash-safe CSV logging, PyQt5 ``MainWindow`` for the front end -- but
the control itself is handed to the Lakeshore 372's own internal closed
loop, which is what the instrument is designed for at mK temperatures
and which keeps the fridge regulated even if this GUI dies.

Hardware layout
---------------
Thermometers (resistance bridge input channels)

===========  ====================================  =========================
Channel      Location                              Notes
===========  ====================================  =========================
2            Mixing chamber -- NEW thermometer      UNCALIBRATED, see below
3            1K pot                                 --
4            Mixing chamber -- OLD thermometer      Sample-heater control input
===========  ====================================  =========================

Heater outputs

===========  ====================================  =========================
Output       Name                                   Control input
===========  ====================================  =========================
0            Sample heater (mixing chamber)         Channel 4
2            Still heater (still)                   Channel 3
===========  ====================================  =========================

Channel 2 is a new thermometer sitting next to the old one in the mixing
chamber, and is the reason this program exists: the point of the
measurement is to calibrate it against channel 4.  Until a calibration
curve is loaded onto the instrument, ``KRDG?2`` returns a meaningless
number.  Its resistance is therefore always logged -- that is the real
calibration data -- and every kelvin reading from channel 2 is labelled
UNCALIBRATED in the file header, in the GUI, and in the plot legend.

SAFETY
------
``SAFE_MODE`` at the top of this file is ``True``.  While it is True,
*nothing at all is written to the Lakeshore* -- every command that would
change an instrument setting is printed to the console instead
("[SAFE MODE] would send: ...") and discarded.  Reading is always live.
The whole front end stays usable so the GUI can be exercised with the
fridge open and at room temperature, which is the situation this file
was written in.

Do not set ``SAFE_MODE = False`` until

1. the fridge is closed and cold, and
2. every row of ``SAMPLE_HEATER_DEFAULTS`` and ``STILL_HEATER_DEFAULTS``
   below has been replaced with values measured on a real cooldown.

Turning on a heater range meant for mK operation while the fridge sits
at room temperature can destroy the heater and the thermometers.

Usage
-----
    python Fridge_Temp_Controller.py
"""
# %%

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton,
    QLabel, QHBoxLayout, QGroupBox, QFormLayout, QMessageBox, QSlider,
    QMenuBar, QAction, QGridLayout
)
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

import sys
import os
import time
import datetime
import threading
import traceback
import numpy as np
import pandas as pd

from optomechanics.device_control.Lakeshore_372_AC_Res_Temp_Controller import Temp_Controller
from optomechanics.data_management.data_logger import dated_logger


# %% Configuration
# ---------------------------------------------------------------------------
# Everything a user should normally need to change lives in this block.
# ---------------------------------------------------------------------------

#: While True no command is ever written to the Lakeshore.  See module docstring.
SAFE_MODE = True

#: GPIB address of the Lakeshore 372.
ADDRESS = 'GPIB0::12::INSTR'

#: Seconds between thermometer readings.
#:
#: One cycle reads 3 thermometers x 3 quantities = 9 GPIB queries, then sleeps
#: for this long, so a row is written roughly every SAMPLE_INTERVAL plus the
#: query time (a few hundred ms on GPIB).  Every row is flushed to disk as it
#: is written.
SAMPLE_INTERVAL = 1.0

#: Heater / PID state is slow to change and slow to query, so it is only read
#: every Nth cycle.  In between, the last known values are reused.
#:
#: With SAMPLE_INTERVAL = 1 s this means the heater readbacks refresh about
#: every 5 s.  Pressing "Apply to instrument" does not wait for that: it forces
#: an immediate re-read so the readback confirms the change straight away.
HEATER_POLL_EVERY = 5

#: Where the CSV log is written.  ``dated_logger`` creates a dated sub-folder
#: here and rolls over to a new file at midnight.
#: For real cooldowns swap this for the group's experiment drive:
# DATA_BASE_PATH = r"D:\Experiment Data"
DATA_BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")

#: Name of the CSV log file inside the dated folder.
DATA_FILE_NAME = "Fridge_Temp_data.csv"

#: Written into the file and shown in the GUI whenever a value cannot be read.
NOT_READING = "not reading"

#: Name of a throwaway final column, present only as a workaround.
#:
#: ``logger.format_data_line`` in ``optomechanics/data_management/data_logger.py``
#: ends with ``to_write = to_write[:-2]``, which is meant to strip the trailing
#: delimiter.  With a one-character delimiter such as "," it strips the
#: delimiter *and the last character of the final field*, so a row ending in
#: "not reading" is written as "not readin".  Every row here therefore ends
#: with this dummy column, which absorbs the truncation and keeps the real
#: data intact.  Remove it if ``data_logger`` is ever fixed to use
#: ``[:-len(self.deliminator)]``.
END_COLUMN = "END"

# --- Thermometers ----------------------------------------------------------
# key = Lakeshore input channel number
THERMOMETERS = {
    2: {"name": "MC new",   "label": "Mixing chamber, NEW (ch2)", "calibrated": False},
    3: {"name": "1K pot",   "label": "1K pot (ch3)",              "calibrated": True},
    4: {"name": "MC old",   "label": "Mixing chamber, OLD (ch4)", "calibrated": True},
}

# --- Heaters ---------------------------------------------------------------
# key = Lakeshore output number
HEATERS = {
    0: {"name": "Sample heater", "control_channel": 4},
    2: {"name": "Still heater",  "control_channel": 3},
}

# --- Default PID settings per target temperature ---------------------------
# ###########################################################################
# #  TODO -- THESE ARE PLACEHOLDERS.  THEY ARE NOT MEASURED VALUES.         #
# #  Every row must be replaced with numbers taken from a real cooldown     #
# #  before SAFE_MODE is set to False.  Until then, applying them to a      #
# #  cold fridge will not regulate properly, and applying them to a warm    #
# #  fridge can damage the heater.                                          #
# ###########################################################################
#
# Read as: "for any target temperature up to and including this key, use
# these settings".  The bands are looked up by :func:`default_settings_for`.
#
#   T_max [K] : (P, I, D, heater_range)
#
# Lakeshore 372 sample-heater (output 0) current ranges:
#   0 = off, 1 = 31.6 uA, 2 = 100 uA, 3 = 316 uA, 4 = 1 mA,
#   5 = 3.16 mA, 6 = 10 mA, 7 = 31.6 mA, 8 = 100 mA
SAMPLE_HEATER_DEFAULTS = {
    0.030: (10.0, 20.0, 0.0, 3),
    0.050: (10.0, 20.0, 0.0, 4),
    0.100: (10.0, 20.0, 0.0, 5),
    0.300: (10.0, 20.0, 0.0, 6),
    1.000: (10.0, 20.0, 0.0, 7),
}

# The still heater (output 2) is a voltage output; its "range" is simply
# 0 = off, 1 = on, and the level is set as a percentage via MOUT/STILL.
STILL_HEATER_DEFAULTS = {
    0.030: (10.0, 20.0, 0.0, 1),
    0.050: (10.0, 20.0, 0.0, 1),
    0.100: (10.0, 20.0, 0.0, 1),
    0.300: (10.0, 20.0, 0.0, 1),
    1.000: (10.0, 20.0, 0.0, 1),
}

DEFAULTS_TABLE = {
    0: SAMPLE_HEATER_DEFAULTS,
    2: STILL_HEATER_DEFAULTS,
}


def default_settings_for(output, target_temperature):
    """
    Made by Claude. Look up the default PID settings for a heater at a target temperature.

    Finds the lowest temperature band in the relevant defaults table whose
    key is greater than or equal to ``target_temperature``.  If the target
    is above every band, the highest band is returned.

    Parameters
    ----------
    output : int
        Lakeshore heater output number (a key of :data:`HEATERS`).
    target_temperature : float
        Desired temperature in kelvin.

    Returns
    -------
    tuple or None
        ``(P, I, D, heater_range)`` for the matching band, or ``None`` if
        ``output`` has no defaults table.
    """
    table = DEFAULTS_TABLE.get(output)
    if table is None:
        print(f"No default PID table for output {output}.")
        return None

    for t_max in sorted(table.keys()):
        if target_temperature <= t_max:
            return table[t_max]

    # Target is hotter than every band -- fall back to the highest one.
    highest = sorted(table.keys())[-1]
    print(f"Target {target_temperature} K is above the highest band "
          f"({highest} K); using the {highest} K settings.")
    return table[highest]


def format_for_log(value):
    """
    Made by Claude. Format a reading for the log file, substituting a marker for failures.

    Parameters
    ----------
    value : float
        A reading.  ``numpy.nan`` indicates the value could not be read.

    Returns
    -------
    str
        The value as a string, or :data:`NOT_READING` if it is NaN.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return NOT_READING
    return f"{value}"


# %%

class Fridge_Controller(Temp_Controller):
    """
    Made by Claude. Lakeshore 372 driver with the write commands needed for heater control.

    Extends
    :class:`~optomechanics.device_control.Lakeshore_372_AC_Res_Temp_Controller.Temp_Controller`
    (which is read-only) with the closed-loop control commands, and routes
    every one of them through :meth:`safe_write` so that :data:`SAFE_MODE`
    can block all writes to the instrument.

    Command references are page numbers in the Lakeshore Model 372 user
    manual, chapter 6 (Remote Operation).
    """

    def __init__(self, *args, **kwargs):
        Temp_Controller.__init__(self, *args, **kwargs)

    # --- write protection --------------------------------------------------

    def safe_write(self, cmd):
        """
        Made by Claude. Write a command to the instrument unless SAFE_MODE is active.

        This is the single point through which every setting change passes.
        While :data:`SAFE_MODE` is ``True`` the command is printed and
        discarded so that nothing can reach the hardware.

        Parameters
        ----------
        cmd : str
            The SCPI command string to send.

        Returns
        -------
        bool
            ``True`` if the command was actually sent, ``False`` if it was
            blocked by safe mode.
        """
        if SAFE_MODE:
            print(f"[SAFE MODE] would send: {cmd}")
            return False
        print(f"[SEND] {cmd}")
        self.write(cmd)
        return True

    # --- reads -------------------------------------------------------------

    def ReadSetpoint(self, output):
        """Made by Claude. Query the control setpoint of a heater output (SETP?)."""
        return self.query(f"SETP?{output}")

    def ReadOutputMode(self, output):
        """Made by Claude. Query the output mode of a heater output (OUTMODE?)."""
        return self.query(f"OUTMODE?{output}")

    # --- writes (all safe-mode protected) ----------------------------------

    def SetPID(self, output, p, i, d):
        """
        Made by Claude. Set the P, I and D terms of a heater's closed loop (PID).

        Parameters
        ----------
        output : int
            Heater output number.
        p, i, d : float
            Proportional, integral and derivative terms.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if blocked by safe mode.
        """
        return self.safe_write(f"PID {output},{p},{i},{d}")

    def SetSetpoint(self, output, setpoint):
        """
        Made by Claude. Set the control setpoint of a heater output (SETP).

        Parameters
        ----------
        output : int
            Heater output number.
        setpoint : float
            Target temperature in kelvin.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if blocked by safe mode.
        """
        return self.safe_write(f"SETP {output},{setpoint}")

    def SetHeaterRange(self, output, heater_range):
        """
        Made by Claude. Set the heater range of an output (RANGE).

        Parameters
        ----------
        output : int
            Heater output number.
        heater_range : int
            Range index.  For the sample heater (output 0), 0 = off through
            8 = 100 mA.  For the still heater (output 2), 0 = off, 1 = on.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if blocked by safe mode.
        """
        return self.safe_write(f"RANGE {output},{heater_range}")

    def SetManualOutput(self, output, percent):
        """
        Made by Claude. Set the manual output level of a heater output (MOUT).

        Parameters
        ----------
        output : int
            Heater output number.
        percent : float
            Output level as a percentage of the current range.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if blocked by safe mode.
        """
        return self.safe_write(f"MOUT {output},{percent}")

    def SetOutputMode(self, output, mode, input_channel, powerup_enable=0,
                      polarity=0, use_filter=0, delay=1):
        """
        Made by Claude. Configure a heater output's control mode (OUTMODE).

        Parameters
        ----------
        output : int
            Heater output number.
        mode : int
            0 = off, 1 = monitor out, 2 = open loop, 3 = zone,
            4 = still, 5 = closed loop, 6 = warm up.
        input_channel : int
            Input channel used as the control sensor.
        powerup_enable : int, optional
            0 = output off after power cycle, 1 = output stays on.  Default 0,
            which is the safe choice.
        polarity : int, optional
            0 = unipolar, 1 = bipolar.  Default 0.
        use_filter : int, optional
            0 = unfiltered, 1 = filtered.  Default 0.
        delay : int, optional
            Setpoint change delay in seconds, 1 to 255.  Default 1.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if blocked by safe mode.
        """
        return self.safe_write(
            f"OUTMODE {output},{mode},{input_channel},{powerup_enable},"
            f"{polarity},{use_filter},{delay}"
        )


# %%

class Worker(QObject):
    """
    Made by Claude. Background worker that polls the Lakeshore 372 and logs its readings.

    Runs :meth:`run` on its own thread.  Each cycle it reads every
    thermometer and (less often) every heater, appends one row to the CSV
    log, and emits the accumulated numeric data for plotting.

    The guiding principle of this class is that it must never crash.  Every
    instrument read is individually wrapped: a channel that fails yields
    ``numpy.nan``, which is written to the file as :data:`NOT_READING` and
    plotted as a gap, while every other channel carries on.  If the whole
    connection drops, the outer loop waits and reconnects.  Every row is
    flushed to disk as it is written, so a crash costs at most the reading
    in progress.

    Attributes
    ----------
    data : list of list
        Numeric plot history, one row of
        ``[time, T_ch2, T_ch3, T_ch4]`` per cycle.  Failed reads are NaN.
    latest : dict
        Most recent reading of every quantity, keyed by column name.  Read
        by the GUI to fill in its display boxes.
    running : bool
        Set to ``False`` to stop the loop and end the thread.
    instrument : Fridge_Controller or None
        The live connection, or ``None`` while disconnected.
    lock : threading.Lock
        Held whenever the instrument is used, so that GUI-initiated writes
        and the polling loop cannot talk over each other on the GPIB bus.
    """

    finished = pyqtSignal()
    plot_data_updated = pyqtSignal(list)
    readings_updated = pyqtSignal(dict)
    status_updated = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self.data = []
        self.latest = {}
        self.running = True
        self.instrument = None
        self.lock = threading.Lock()
        #: Full path of the CSV currently being written, shown in the GUI.
        self.log_file_path = ""
        #: Set by the GUI after a settings change to force an immediate
        #: heater re-read, instead of waiting for the next scheduled poll.
        self.force_heater_poll = False

    # --- helpers -----------------------------------------------------------

    def read_value(self, description, read_function, *args):
        """
        Made by Claude. Perform one instrument read, returning NaN instead of raising.

        Parameters
        ----------
        description : str
            Human-readable name of the quantity, used in the error message.
        read_function : callable
            Bound driver method to call, e.g. ``self.instrument.ReadTemperature``.
        *args
            Arguments forwarded to ``read_function``.

        Returns
        -------
        float
            The reading as a float, or ``numpy.nan`` if it could not be read.
        """
        try:
            return float(read_function(*args))
        except Exception as e:
            print(f"[READ FAIL] {description}: {e}")
            return float('nan')

    def read_pid_values(self, output):
        """
        Made by Claude. Read the P, I and D terms of one heater output.

        The 372 returns all three from a single ``PID?`` query as a
        comma-separated string.

        Parameters
        ----------
        output : int
            Heater output number.

        Returns
        -------
        tuple of float
            ``(P, I, D)``, each ``numpy.nan`` if it could not be read.
        """
        try:
            response = self.instrument.ReadPID(output)
            p, i, d = [float(value) for value in response.split(',')[:3]]
            return p, i, d
        except Exception as e:
            print(f"[READ FAIL] PID of output {output}: {e}")
            return float('nan'), float('nan'), float('nan')

    def build_headers(self):
        """
        Made by Claude. Build the CSV column headings for the log file.

        Returns
        -------
        list of str
            Column headings, in the same order as the rows written by
            :meth:`run`.
        """
        headers = ["Time[s]", "Timestamp"]

        for channel, info in THERMOMETERS.items():
            name = info["name"].replace(" ", "_")
            suffix = "" if info["calibrated"] else "_UNCALIBRATED"
            headers.append(f"T_{name}_ch{channel}[K]{suffix}")
            headers.append(f"R_{name}_ch{channel}[Ohm]")
            headers.append(f"Pexc_{name}_ch{channel}[W]")

        for output, info in HEATERS.items():
            name = info["name"].replace(" ", "_")
            headers.append(f"{name}_out{output}_Output[%]")
            headers.append(f"{name}_out{output}_Range")
            headers.append(f"{name}_out{output}_Setpoint[K]")
            headers.append(f"{name}_out{output}_P")
            headers.append(f"{name}_out{output}_I")
            headers.append(f"{name}_out{output}_D")

        # See END_COLUMN: absorbs the truncation bug in data_logger.
        headers.append(END_COLUMN)

        return headers

    # --- polling -----------------------------------------------------------

    def poll_thermometers(self):
        """
        Made by Claude. Read temperature, resistance and excitation power of every thermometer.

        Returns
        -------
        dict
            Readings keyed by ``"T_ch<n>"``, ``"R_ch<n>"`` and
            ``"P_ch<n>"``.  Any value that could not be read is
            ``numpy.nan``.
        """
        readings = {}
        for channel, info in THERMOMETERS.items():
            readings[f"T_ch{channel}"] = self.read_value(
                f"T of {info['name']} (ch{channel})",
                self.instrument.ReadTemperature, channel)
            readings[f"R_ch{channel}"] = self.read_value(
                f"R of {info['name']} (ch{channel})",
                self.instrument.ReadResistance, channel)
            readings[f"P_ch{channel}"] = self.read_value(
                f"excitation power of {info['name']} (ch{channel})",
                self.instrument.ReadExcitationPower, channel)
        return readings

    def poll_heaters(self):
        """
        Made by Claude. Read output level, range, setpoint and PID terms of every heater.

        Returns
        -------
        dict
            Readings keyed by ``"HTR_out<n>"``, ``"RANGE_out<n>"``,
            ``"SETP_out<n>"``, ``"P_out<n>"``, ``"I_out<n>"`` and
            ``"D_out<n>"``.  Any value that could not be read is
            ``numpy.nan``.
        """
        readings = {}
        for output, info in HEATERS.items():
            readings[f"HTR_out{output}"] = self.read_value(
                f"output level of {info['name']}",
                self.instrument.ReadHeaterOutput, output)
            readings[f"RANGE_out{output}"] = self.read_value(
                f"range of {info['name']}",
                self.instrument.ReadHeaterRange, output)
            readings[f"SETP_out{output}"] = self.read_value(
                f"setpoint of {info['name']}",
                self.instrument.ReadSetpoint, output)
            p, i, d = self.read_pid_values(output)
            readings[f"P_out{output}"] = p
            readings[f"I_out{output}"] = i
            readings[f"D_out{output}"] = d
        return readings

    def build_log_row(self, current_time, readings):
        """
        Made by Claude. Assemble one CSV row from a set of readings.

        Parameters
        ----------
        current_time : float
            Unix timestamp of the reading.
        readings : dict
            Combined thermometer and heater readings.

        Returns
        -------
        list of str
            One row, in the order given by :meth:`build_headers`, with
            unreadable values replaced by :data:`NOT_READING`.
        """
        stamp = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
        row = [f"{current_time}", stamp]

        for channel in THERMOMETERS:
            row.append(format_for_log(readings.get(f"T_ch{channel}")))
            row.append(format_for_log(readings.get(f"R_ch{channel}")))
            row.append(format_for_log(readings.get(f"P_ch{channel}")))

        for output in HEATERS:
            row.append(format_for_log(readings.get(f"HTR_out{output}")))
            row.append(format_for_log(readings.get(f"RANGE_out{output}")))
            row.append(format_for_log(readings.get(f"SETP_out{output}")))
            row.append(format_for_log(readings.get(f"P_out{output}")))
            row.append(format_for_log(readings.get(f"I_out{output}")))
            row.append(format_for_log(readings.get(f"D_out{output}")))

        # See END_COLUMN: absorbs the truncation bug in data_logger.
        row.append(END_COLUMN)

        return row

    # --- control, called from the GUI thread -------------------------------

    def apply_heater_settings(self, output, p, i, d, setpoint, heater_range):
        """
        Made by Claude. Push a full set of closed-loop settings to one heater output.

        Configures the output for closed-loop control on its assigned
        thermometer, sets the PID terms and setpoint, and only then opens
        the heater range -- so that the loop is never switched on before it
        knows what it is aiming for.

        Every command goes through :meth:`Fridge_Controller.safe_write`, so
        while :data:`SAFE_MODE` is ``True`` this method changes nothing on
        the instrument and merely prints what it would have sent.

        Parameters
        ----------
        output : int
            Heater output number.
        p, i, d : float
            PID terms.
        setpoint : float
            Target temperature in kelvin.
        heater_range : int
            Heater range index.

        Returns
        -------
        bool
            ``True`` if the settings were sent, ``False`` if they were
            blocked by safe mode or the instrument was unavailable.
        """
        with self.lock:
            if self.instrument is None:
                print("Cannot apply settings: not connected to the Lakeshore.")
                return False

            info = HEATERS[output]
            try:
                # Closed loop (mode 5) on this heater's own thermometer.
                self.instrument.SetOutputMode(output, 5, info["control_channel"])
                self.instrument.SetPID(output, p, i, d)
                self.instrument.SetSetpoint(output, setpoint)
                # Range last: never energise the heater before the loop is set up.
                sent = self.instrument.SetHeaterRange(output, heater_range)
                # Refresh the readback now rather than waiting for the next
                # scheduled heater poll, so the user sees the change land.
                self.force_heater_poll = True
                return sent
            except Exception as e:
                print(f"[WRITE FAIL] applying settings to {info['name']}: {e}")
                print(traceback.format_exc())
                return False

    def turn_heater_off(self, output):
        """
        Made by Claude. Switch one heater output off by setting its range to zero.

        Parameters
        ----------
        output : int
            Heater output number.

        Returns
        -------
        bool
            ``True`` if the command was sent, ``False`` if it was blocked by
            safe mode or the instrument was unavailable.
        """
        with self.lock:
            if self.instrument is None:
                print("Cannot switch heater off: not connected to the Lakeshore.")
                return False
            try:
                sent = self.instrument.SetHeaterRange(output, 0)
                self.force_heater_poll = True
                return sent
            except Exception as e:
                print(f"[WRITE FAIL] switching off output {output}: {e}")
                return False

    # --- main loop ---------------------------------------------------------

    def run(self):
        """
        Made by Claude. Poll the instrument and log readings until :attr:`running` is False.

        Opens the connection, creates the dated log file, then loops:
        read, log, emit.  Any failure inside the loop is caught, printed
        and retried rather than allowed to end the run; a failure of the
        connection itself drops out to the reconnect loop, which waits and
        tries again.  The log file is closed and reopened by
        ``dated_logger`` at midnight.

        Returns
        -------
        None
        """
        print("Starting fridge temperature monitor.")
        if SAFE_MODE:
            print("=" * 70)
            print("SAFE MODE IS ON -- no command will be written to the Lakeshore.")
            print("=" * 70)

        headers = self.build_headers()

        # ``logger.__init__`` creates the file straight away, before
        # ``dated_logger`` has worked out the dated sub-folder.  Passing
        # file_path here keeps that first, empty, throwaway file inside
        # DATA_BASE_PATH instead of dropping it in whatever directory the
        # program happened to be launched from.
        os.makedirs(DATA_BASE_PATH, exist_ok=True)
        temp_logger = dated_logger(base_path=DATA_BASE_PATH,
                                   file_name=DATA_FILE_NAME,
                                   file_path=DATA_BASE_PATH + os.sep,
                                   headings=headers)

        self.log_file_path = os.path.join(temp_logger.file_path,
                                          temp_logger.file_name)
        print("=" * 70)
        print(f"SAVING DATA TO: {self.log_file_path}")
        print("=" * 70)

        # Recover today's data so the plot is not empty on restart.
        dataframe = temp_logger.data
        if isinstance(dataframe, pd.DataFrame):
            print(f"Recovered {len(dataframe)} existing rows from today's log.")

        current_day = datetime.datetime.now().day
        heater_readings = {}
        cycle = 0

        while self.running:
            # Outer loop: (re)connect to the instrument.
            try:
                print(f"Connecting to Lakeshore 372 at {ADDRESS} ...")
                self.status_updated.emit(f"Connecting to {ADDRESS} ...", False)
                with Fridge_Controller(ADDRESS) as instrument:
                    with self.lock:
                        self.instrument = instrument
                    print("Connected.")
                    self.status_updated.emit(f"Connected to {ADDRESS}", True)

                    while self.running:
                        cycle += 1
                        current_time = time.time()

                        # Clear the plot history at midnight, matching the
                        # daily roll-over of the log file.
                        if current_day != datetime.datetime.now().day:
                            self.data = []
                            current_day = datetime.datetime.now().day

                        with self.lock:
                            readings = self.poll_thermometers()
                            # Heater state changes slowly and is slow to
                            # query, so reuse the last values in between,
                            # unless the GUI has just changed something.
                            if (cycle % HEATER_POLL_EVERY == 1
                                    or not heater_readings
                                    or self.force_heater_poll):
                                heater_readings = self.poll_heaters()
                                self.force_heater_poll = False

                        readings.update(heater_readings)
                        self.latest = readings

                        # Tell the user whether the instrument is actually
                        # answering, so a blank plot is never a mystery.
                        live = sum(1 for channel in THERMOMETERS
                                   if not np.isnan(readings.get(f"T_ch{channel}",
                                                                float('nan'))))
                        if live == 0:
                            self.status_updated.emit(
                                "Connected, but NO thermometer is responding", False)
                        else:
                            self.status_updated.emit(
                                f"Reading {live} of {len(THERMOMETERS)} thermometers "
                                f"| row {len(self.data) + 1}", True)

                        # Write and flush immediately: a crash costs at most
                        # the reading currently in progress.
                        temp_logger(self.build_log_row(current_time, readings))

                        self.data.append([
                            current_time,
                            readings.get("T_ch2", float('nan')),
                            readings.get("T_ch3", float('nan')),
                            readings.get("T_ch4", float('nan')),
                        ])

                        self.readings_updated.emit(readings)
                        self.plot_data_updated.emit(self.data)

                        time.sleep(SAMPLE_INTERVAL)

            except KeyboardInterrupt:
                print("Monitor stopped by user.")
                self.running = False

            except Exception as e:
                print(f"[CONNECTION FAIL] {e}")
                print(traceback.format_exc())
                with self.lock:
                    self.instrument = None
                if self.running:
                    self.status_updated.emit(
                        f"NOT CONNECTED ({e}) -- retrying in 5 s", False)
                    print("Retrying in 5 s.  Logging will resume automatically.")
                    time.sleep(5)

            finally:
                with self.lock:
                    self.instrument = None

        print("Monitor finished.")
        self.finished.emit()


# %%

def date_formatter(val, pos):
    """Made by Claude. Format an x-axis tick, given as a unix timestamp, as a clock time."""
    try:
        return datetime.datetime.fromtimestamp(val).strftime('%H:%M:%S')
    except Exception:
        return ""


class MplCanvas(FigureCanvas):
    """
    Made by Claude. Matplotlib canvas showing one temperature-versus-time panel per thermometer.

    Three stacked axes, one for each thermometer, in channel order.  The
    channel-2 panel is labelled UNCALIBRATED because that thermometer has
    no calibration curve loaded yet.
    """

    def __init__(self, parent=None, width=20, height=10, dpi=100):
        try:
            channels = sorted(THERMOMETERS.keys())
            fig, axes = plt.subplots(len(channels), figsize=(width, height), sharex=True)
            super(MplCanvas, self).__init__(fig)
            self.setParent(parent)

            self.axes = {}
            self.lines = {}
            colours = {2: 'g', 3: 'b', 4: 'r'}

            for ax, channel in zip(axes, channels):
                info = THERMOMETERS[channel]
                label = info["label"]
                if not info["calibrated"]:
                    label += "  --  UNCALIBRATED"

                line, = ax.plot([], [], 'x-', color=colours.get(channel, 'k'),
                                alpha=0.8, label=label)
                ax.set_ylabel('Temperature [K]')
                ax.legend(loc='upper left')
                ax.xaxis.set_major_formatter(plt.FuncFormatter(date_formatter))

                self.axes[channel] = ax
                self.lines[channel] = line

            axes[-1].set_xlabel('Time')
            fig.tight_layout()

        except Exception as e:
            print("Failed to build the plot canvas.")
            print(e)
            print(traceback.format_exc())

    def update_plot(self, data, last_n_hours=None):
        """
        Made by Claude. Redraw every panel with new data.

        Parameters
        ----------
        data : list of list
            Rows of ``[time, T_ch2, T_ch3, T_ch4]``.  NaN entries appear as
            gaps in the trace rather than breaking the plot.
        last_n_hours : int, optional
            If given, only data from the last this-many hours is shown.

        Returns
        -------
        None
        """
        if len(data) == 0:
            return

        if last_n_hours:
            current_time = datetime.datetime.now().timestamp()
            selected_time = current_time - last_n_hours * 3600
            data = [d for d in data if d[0] >= selected_time]
            if len(data) == 0:
                return

        plotable_data = np.array(data, dtype=float).T
        time_data = plotable_data[0]

        channels = sorted(THERMOMETERS.keys())
        for index, channel in enumerate(channels):
            self.lines[channel].set_data(time_data, plotable_data[index + 1])
            self.axes[channel].relim()
            self.axes[channel].autoscale_view()

        self.draw()


# %%

class HeaterControlGroup(QGroupBox):
    """
    Made by Claude. Group box holding the readout and control boxes for one heater output.

    Shows the live values read back from the instrument, and provides
    editable boxes for P, I, D, setpoint and heater range.  Nothing here
    talks to the instrument by itself -- the boxes are only sent when
    "Apply to instrument" is pressed, and even then only if
    :data:`SAFE_MODE` is off.

    Parameters
    ----------
    output : int
        Lakeshore heater output number.
    worker : Worker
        The polling worker, used to send settings.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, output, worker, parent=None):
        info = HEATERS[output]
        super().__init__(f"{info['name']}  (output {output}, controlled on channel "
                         f"{info['control_channel']})", parent)

        self.output = output
        self.worker = worker

        #: Set once the editable boxes have been filled from the instrument's
        #: own settings, which happens on the first successful heater read.
        #: After that the boxes belong to the user and are never overwritten
        #: automatically.
        self.initialised_from_instrument = False

        layout = QVBoxLayout()

        # --- live readback, not editable -----------------------------------
        readback_layout = QFormLayout()
        self.output_readback = QLabel("N/A")
        self.range_readback = QLabel("N/A")
        self.setpoint_readback = QLabel("N/A")
        self.pid_readback = QLabel("N/A")
        readback_layout.addRow("Output level [%]:", self.output_readback)
        readback_layout.addRow("Range:", self.range_readback)
        readback_layout.addRow("Setpoint [K]:", self.setpoint_readback)
        readback_layout.addRow("P / I / D:", self.pid_readback)

        readback_box = QGroupBox("Read from instrument")
        readback_box.setLayout(readback_layout)
        layout.addWidget(readback_box)

        # --- editable settings ---------------------------------------------
        settings_layout = QFormLayout()
        self.p_input = QLineEdit(self)
        self.i_input = QLineEdit(self)
        self.d_input = QLineEdit(self)
        self.setpoint_input = QLineEdit(self)
        self.range_input = QLineEdit(self)
        settings_layout.addRow("P:", self.p_input)
        settings_layout.addRow("I:", self.i_input)
        settings_layout.addRow("D:", self.d_input)
        settings_layout.addRow("Setpoint [K]:", self.setpoint_input)
        settings_layout.addRow("Range:", self.range_input)

        settings_box = QGroupBox("Settings to send")
        settings_box.setLayout(settings_layout)
        layout.addWidget(settings_box)

        # --- buttons --------------------------------------------------------
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply to instrument", self)
        self.copy_button = QPushButton("Copy from instrument", self)
        self.off_button = QPushButton("Heater OFF", self)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.off_button)
        layout.addLayout(button_layout)

        self.apply_button.clicked.connect(self.apply_settings)
        self.copy_button.clicked.connect(self.copy_from_instrument)
        self.off_button.clicked.connect(self.switch_off)

        self.setLayout(layout)

    # --- display -----------------------------------------------------------

    def update_readbacks(self, readings):
        """
        Made by Claude. Refresh the read-only labels from the latest instrument readings.

        Parameters
        ----------
        readings : dict
            Latest readings as produced by :meth:`Worker.poll_heaters`.

        Returns
        -------
        None
        """
        output = self.output

        def show(key, decimals=3):
            value = readings.get(key)
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return NOT_READING
            return f"{value:.{decimals}f}"

        self.output_readback.setText(show(f"HTR_out{output}", 3))
        self.range_readback.setText(show(f"RANGE_out{output}", 0))
        self.setpoint_readback.setText(show(f"SETP_out{output}", 6))
        self.pid_readback.setText(
            f"{show(f'P_out{output}', 2)} / "
            f"{show(f'I_out{output}', 2)} / "
            f"{show(f'D_out{output}', 2)}"
        )

        # On start-up the editable boxes should show what the Lakeshore is
        # actually set to, not be empty and not be some target's defaults.
        # This runs once, on the first read that returns a complete set; from
        # then on the boxes are the user's and are left alone.
        if not self.initialised_from_instrument:
            if self.fill_inputs(readings):
                self.initialised_from_instrument = True
                print(f"{HEATERS[self.output]['name']}: boxes initialised from "
                      f"the instrument's current settings.")

    def load_defaults(self, target_temperature):
        """
        Made by Claude. Fill the editable boxes with the default settings for a target temperature.

        Only the boxes are changed; nothing is sent to the instrument.  The
        values can be edited freely afterwards without affecting the target.

        Parameters
        ----------
        target_temperature : float
            Desired temperature in kelvin.

        Returns
        -------
        None
        """
        defaults = default_settings_for(self.output, target_temperature)
        if defaults is None:
            return
        p, i, d, heater_range = defaults

        self.p_input.setText(str(p))
        self.i_input.setText(str(i))
        self.d_input.setText(str(d))
        self.setpoint_input.setText(str(target_temperature))
        self.range_input.setText(str(heater_range))

        print(f"{HEATERS[self.output]['name']}: loaded defaults for "
              f"{target_temperature} K -- P={p}, I={i}, D={d}, range={heater_range}. "
              f"Nothing sent to the instrument yet.")

    def fill_inputs(self, readings):
        """
        Made by Claude. Fill the editable boxes with the instrument's own current settings.

        Only fills if every one of the five values is available, so that a
        partial read cannot leave a half-populated set of settings sitting in
        the boxes ready to be applied.

        Parameters
        ----------
        readings : dict
            Readings as produced by :meth:`Worker.poll_heaters`.

        Returns
        -------
        bool
            ``True`` if the boxes were filled, ``False`` if any value was
            missing or unreadable.
        """
        output = self.output
        keys = {
            "p": f"P_out{output}",
            "i": f"I_out{output}",
            "d": f"D_out{output}",
            "setpoint": f"SETP_out{output}",
            "range": f"RANGE_out{output}",
        }

        values = {}
        for name, key in keys.items():
            value = readings.get(key)
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return False
            values[name] = value

        self.p_input.setText(str(values["p"]))
        self.i_input.setText(str(values["i"]))
        self.d_input.setText(str(values["d"]))
        self.setpoint_input.setText(str(values["setpoint"]))
        # The range is an index, so show it as a whole number.
        self.range_input.setText(str(int(values["range"])))
        return True

    def copy_from_instrument(self):
        """
        Made by Claude. Copy the instrument's current settings into the editable boxes.

        Discards whatever is in the boxes and replaces it with what the
        Lakeshore is actually set to.  Used by the "Copy from instrument"
        button, and automatically on start-up.

        Returns
        -------
        None
        """
        if not self.fill_inputs(self.worker.latest):
            QMessageBox.warning(
                self, "Nothing to copy",
                f"The settings of the {HEATERS[self.output]['name']} could not "
                "be read from the Lakeshore, so the boxes were left alone.")

    # --- control ------------------------------------------------------------

    def read_inputs(self):
        """
        Made by Claude. Parse the editable boxes into numbers.

        Returns
        -------
        tuple or None
            ``(P, I, D, setpoint, heater_range)``, or ``None`` if any box
            does not contain a valid number.
        """
        try:
            return (float(self.p_input.text()),
                    float(self.i_input.text()),
                    float(self.d_input.text()),
                    float(self.setpoint_input.text()),
                    int(float(self.range_input.text())))
        except ValueError:
            QMessageBox.warning(self, "Input Error",
                                "Please enter valid numbers in every box "
                                f"of the {HEATERS[self.output]['name']}.")
            return None

    def apply_settings(self):
        """
        Made by Claude. Send the contents of the editable boxes to the instrument.

        Blocked by :data:`SAFE_MODE`, in which case the user is told what
        would have been sent instead.

        Returns
        -------
        None
        """
        values = self.read_inputs()
        if values is None:
            return
        p, i, d, setpoint, heater_range = values

        sent = self.worker.apply_heater_settings(self.output, p, i, d,
                                                 setpoint, heater_range)
        if sent:
            QMessageBox.information(
                self, "Settings applied",
                f"{HEATERS[self.output]['name']} updated:\n"
                f"P = {p}, I = {i}, D = {d}\n"
                f"Setpoint = {setpoint} K, range = {heater_range}")
        else:
            QMessageBox.information(
                self, "Safe mode",
                "SAFE_MODE is on, so nothing was sent to the Lakeshore.\n\n"
                "The commands that would have been sent are printed in the "
                "console.\n\nSet SAFE_MODE = False at the top of "
                "Fridge_Temp_Controller.py only when the fridge is cold.")

    def switch_off(self):
        """
        Made by Claude. Switch this heater off by setting its range to zero.

        Returns
        -------
        None
        """
        sent = self.worker.turn_heater_off(self.output)
        if sent:
            QMessageBox.information(self, "Heater off",
                                    f"{HEATERS[self.output]['name']} switched off.")
        else:
            QMessageBox.information(
                self, "Safe mode",
                "SAFE_MODE is on, so nothing was sent to the Lakeshore.")


# %%

class MainWindow(QMainWindow):
    """
    Made by Claude. Main window of the fridge temperature monitor and heater controller.

    Left-hand column: live thermometer readings, the target-temperature
    box, and one :class:`HeaterControlGroup` per heater.  Right-hand side:
    the plots and a slider selecting how much history to show.

    The target-temperature box is the intended everyday workflow.  Typing a
    temperature and pressing "Load defaults for target" fills every heater's
    PID and range boxes from :data:`SAMPLE_HEATER_DEFAULTS` and
    :data:`STILL_HEATER_DEFAULTS`.  Nothing is sent at that point, so the
    values can be adjusted by hand afterwards without the target changing
    them back.  Only "Apply to instrument" sends anything, and only when
    :data:`SAFE_MODE` is off.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fridge Temperature Control -- Lakeshore 372")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Worker first: the control widgets need a reference to it.
        self.worker = Worker()

        # --- left column ----------------------------------------------------
        self.left_layout = QVBoxLayout()
        self.left_layout_widget = QWidget()
        self.left_layout_widget.setLayout(self.left_layout)
        main_layout.addWidget(self.left_layout_widget)

        if SAFE_MODE:
            safe_label = QLabel("SAFE MODE -- nothing is written to the Lakeshore")
            safe_label.setAlignment(Qt.AlignCenter)
            safe_label.setFont(QFont('Arial', 11, QFont.Bold))
            safe_label.setStyleSheet("color: white; background-color: #b00000; padding: 6px;")
            self.left_layout.addWidget(safe_label)

        # Connection status: makes it obvious whether the blank plot means
        # "nothing has happened yet" or "the instrument is not answering".
        self.status_label = QLabel("Starting ...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.status_label.setStyleSheet("color: white; background-color: grey; padding: 4px;")
        self.left_layout.addWidget(self.status_label)

        # Where the data is going, so it never has to be hunted for.
        self.file_label = QLabel("Log file: (opening ...)")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: #303030; font-size: 10px;")
        self.file_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.left_layout.addWidget(self.file_label)

        self.left_layout.addWidget(self.build_thermometer_box())
        self.left_layout.addWidget(self.build_target_box())

        self.heater_groups = {}
        for output in HEATERS:
            group = HeaterControlGroup(output, self.worker, self)
            self.heater_groups[output] = group
            self.left_layout.addWidget(group)

        self.left_layout.addStretch()

        # --- expand / minimise ----------------------------------------------
        self.expand_button = QPushButton("Expand/Minimize", self)
        main_layout.addWidget(self.expand_button)
        self.expand_button.clicked.connect(self.toggle_expand)

        # --- right column ----------------------------------------------------
        self.right_layout = QVBoxLayout()
        self.right_layout_widget = QWidget()
        self.right_layout_widget.setLayout(self.right_layout)
        main_layout.addWidget(self.right_layout_widget)

        self.canvas = MplCanvas(self, width=20, height=10, dpi=100)
        toolbar = NavigationToolbar(self.canvas, self)
        self.right_layout.addWidget(toolbar)
        self.right_layout.addWidget(self.canvas)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(1, 24)
        self.slider.setValue(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.right_layout.addWidget(self.slider)

        self.slider_label = QLabel("Show Last N Hours: 1", self)
        self.slider_label.setAlignment(Qt.AlignCenter)
        self.slider_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.right_layout.addWidget(self.slider_label)

        self.slider.valueChanged.connect(self.update_slider_label)
        self.slider.valueChanged.connect(self.update_plot_with_slider)

        # --- start the worker -------------------------------------------------
        self.worker_thread = threading.Thread(target=self.worker.run)
        self.worker_thread.start()

        self.worker.plot_data_updated.connect(self.update_plot)
        self.worker.readings_updated.connect(self.update_readings)
        self.worker.status_updated.connect(self.update_status)

        self.setup_menubar()
        self.show()

    # --- widget construction -------------------------------------------------

    def build_thermometer_box(self):
        """
        Made by Claude. Build the group box showing the live thermometer readings.

        Returns
        -------
        QGroupBox
            A box with one row per thermometer, showing temperature,
            resistance and excitation power.
        """
        box = QGroupBox("Thermometers")
        grid = QGridLayout()

        grid.addWidget(QLabel("<b>Sensor</b>"), 0, 0)
        grid.addWidget(QLabel("<b>T [K]</b>"), 0, 1)
        grid.addWidget(QLabel("<b>R [Ohm]</b>"), 0, 2)
        grid.addWidget(QLabel("<b>Excitation [W]</b>"), 0, 3)

        self.thermometer_labels = {}
        for row, channel in enumerate(sorted(THERMOMETERS.keys()), start=1):
            info = THERMOMETERS[channel]
            name = info["label"]
            if not info["calibrated"]:
                name += "  [UNCALIBRATED]"

            name_label = QLabel(name)
            if not info["calibrated"]:
                name_label.setStyleSheet("color: #b06000;")

            t_label = QLabel("N/A")
            r_label = QLabel("N/A")
            p_label = QLabel("N/A")

            grid.addWidget(name_label, row, 0)
            grid.addWidget(t_label, row, 1)
            grid.addWidget(r_label, row, 2)
            grid.addWidget(p_label, row, 3)

            self.thermometer_labels[channel] = (t_label, r_label, p_label)

        box.setLayout(grid)
        return box

    def build_target_box(self):
        """
        Made by Claude. Build the target-temperature group box.

        Returns
        -------
        QGroupBox
            A box with the target temperature input and the button that
            loads the default PID settings for that target into every
            heater's boxes.
        """
        box = QGroupBox("Target temperature")
        layout = QVBoxLayout()

        form = QFormLayout()
        self.target_input = QLineEdit(self)
        self.target_input.setPlaceholderText("e.g. 0.030 for 30 mK")
        form.addRow("Target [K]:", self.target_input)
        layout.addLayout(form)

        self.load_defaults_button = QPushButton("Load defaults for target", self)
        self.load_defaults_button.clicked.connect(self.load_defaults_for_target)
        layout.addWidget(self.load_defaults_button)

        note = QLabel("Loading defaults only fills the boxes below.\n"
                      "Nothing is sent until you press 'Apply to instrument',\n"
                      "and you may edit any box afterwards without\n"
                      "changing the target.")
        note.setStyleSheet("color: grey;")
        layout.addWidget(note)

        box.setLayout(layout)
        return box

    def setup_menubar(self):
        """Made by Claude. Set up the File menu."""
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        file_menu = menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    # --- slots ---------------------------------------------------------------

    def load_defaults_for_target(self):
        """
        Made by Claude. Load the default PID settings for the target temperature into every heater.

        Reads the target-temperature box and asks each
        :class:`HeaterControlGroup` to fill its editable boxes from the
        defaults table.  Nothing is sent to the instrument.

        Returns
        -------
        None
        """
        try:
            target = float(self.target_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input",
                                "Please enter a valid target temperature in kelvin.")
            return

        for group in self.heater_groups.values():
            group.load_defaults(target)

        QMessageBox.information(
            self, "Defaults loaded",
            f"Default settings for {target} K have been loaded into the "
            "heater boxes.\n\nNothing has been sent to the Lakeshore. "
            "Edit the values if you want to, then press 'Apply to "
            "instrument'.")

    def update_status(self, message, healthy):
        """
        Made by Claude. Update the connection-status banner and the log-file path.

        Parameters
        ----------
        message : str
            Status text to display.
        healthy : bool
            ``True`` if the instrument is answering, which shows the banner
            in green; ``False`` shows it in red.

        Returns
        -------
        None
        """
        self.status_label.setText(message)
        colour = "#006000" if healthy else "#b00000"
        self.status_label.setStyleSheet(
            f"color: white; background-color: {colour}; padding: 4px;")

        if self.worker.log_file_path:
            self.file_label.setText(f"Log file: {self.worker.log_file_path}")

    def update_readings(self, readings):
        """
        Made by Claude. Refresh every live display from the latest readings.

        Parameters
        ----------
        readings : dict
            Latest combined thermometer and heater readings.

        Returns
        -------
        None
        """
        for channel, (t_label, r_label, p_label) in self.thermometer_labels.items():
            t = readings.get(f"T_ch{channel}")
            r = readings.get(f"R_ch{channel}")
            p = readings.get(f"P_ch{channel}")

            t_label.setText(NOT_READING if t is None or np.isnan(t) else f"{t:.6f}")
            r_label.setText(NOT_READING if r is None or np.isnan(r) else f"{r:.3f}")
            p_label.setText(NOT_READING if p is None or np.isnan(p) else f"{p:.3e}")

        for group in self.heater_groups.values():
            group.update_readbacks(readings)

    def update_plot(self, data):
        """
        Made by Claude. Redraw the plots, honouring the history slider.

        Parameters
        ----------
        data : list of list
            Plot history from the worker.

        Returns
        -------
        None
        """
        self.canvas.update_plot(data, last_n_hours=self.slider.value())

    def update_slider_label(self, value):
        """Made by Claude. Update the label showing how many hours of history are displayed."""
        self.slider_label.setText(f"Show Last N Hours: {value}")

    def update_plot_with_slider(self):
        """Made by Claude. Redraw the plots when the history slider is moved."""
        self.update_plot(self.worker.data)

    def toggle_expand(self):
        """Made by Claude. Show or hide the left-hand control column."""
        if self.left_layout_widget.isHidden():
            self.left_layout_widget.show()
            self.expand_button.setText("Minimize")
        else:
            self.left_layout_widget.hide()
            self.expand_button.setText("Expand")

    def closeEvent(self, event):
        """
        Made by Claude. Stop the worker thread cleanly when the window is closed.

        The heaters are deliberately left exactly as they are: the Lakeshore
        keeps regulating the fridge on its own after this program exits.

        Parameters
        ----------
        event : QCloseEvent
            The close event.

        Returns
        -------
        None
        """
        self.worker.running = False
        self.worker_thread.join(timeout=10)
        event.accept()


# %%

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
