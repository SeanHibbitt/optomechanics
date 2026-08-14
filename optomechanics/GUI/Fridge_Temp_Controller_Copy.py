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

Heater outputs.  The two are different kinds of device and are treated
differently throughout: the sample heater regulates towards a
temperature, the still heater just sits at a fixed level.

===========  =========================  ==============================
Output       Name                       How it is driven
===========  =========================  ==============================
0            Sample heater              Closed loop (PID) on a chosen
                                        thermometer, default channel 4
2            Still heater               Still mode, a constant
                                        percentage of full scale
===========  =========================  ==============================

The still's level and what its output is actually delivering are two
different numbers on this instrument, and they disagree whenever the
output's range is off: ``STILL?`` reports the level it is set to, and
``AOUT?`` what is coming out.  Both are shown and both are logged,
because "set to 10% but switched off" is a state worth being able to
see afterwards.

The thermometer the sample heater regulates against is selectable in
the GUI ("PID reference"), and is recorded in every row of the log so
it is always possible to tell afterwards what the loop was following.

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

Do not set ``SAFE_MODE = False`` until the fridge is closed and cold.

Turning on a heater range meant for mK operation while the fridge sits
at room temperature can destroy the heater and the thermometers.

``SAMPLE_HEATER_DEFAULTS`` holds the tuning this fridge is run at from
1.2 K upwards; the bands below that are a starting point rather than a
calibration, and say so.

On connecting, the instrument's own settings are read back and compared
with what this file assumes -- the heater resistance the calculated
voltage rests on, the output modes, and which thermometer the loop is
regulating on.  Anything that disagrees is printed and shown in the
window.  Nothing is corrected: the instrument is the authority on its
own state, and quietly rewriting a setting someone put there
deliberately is exactly the kind of surprise a running fridge should
never spring on anyone.

There is one deliberate exception to safe mode: the scanner dwell time
(``INSET``, set from Settings -> Thermometers) is written to the
instrument even while ``SAFE_MODE`` is True.  It changes measurement
timing only and cannot put power into the fridge.  Everything that can
dissipate energy still goes through ``Fridge_Controller.safe_write``.

Setpoints from the S21 computer
-------------------------------
A second computer runs the S21 measurement, and needs the fridge held at
each of a series of temperatures while it takes a spectrum at every one.
The two machines talk through a single plain-text file on the shared
drive, ``D:\\TemperatureData\\RemoteControl.txt``, which was already in
place and is used here unchanged::

    SetPoint: 1.4
    CurrentTemp: 1.398765
    UseManualPID: False

The other machine writes ``SetPoint``; this program notices the change,
sets the fridge going to it -- bringing the P, I, D and heater range for
that temperature with it from :data:`SAMPLE_HEATER_DEFAULTS` -- and
writes the measured temperature back as ``CurrentTemp``, which is what
the notebook on the other side waits on before it measures.  Setting
``UseManualPID: True`` sends the setpoint alone and leaves the tuning
as the GUI has it.

Two deliberate restrictions.  A setpoint arriving this way goes through
exactly the same path as one typed into the window, so ``SAFE_MODE``
blocks it in exactly the same way.  And only a *change* is acted on:
whatever is in the file at start-up is left over from the last run, and
is recorded rather than applied, so restarting this program cannot by
itself move the fridge.

Where the data goes
-------------------
Rows are written to ``DATA_BASE_PATH`` in a dated folder --
``D:\\TemperatureData\\2026\\August\\12\\Fridge_Temp_data.csv`` -- one
file per day, created by ``dated_logger``.  Restarting on the same day
appends to that day's file; a run crossing midnight rolls into the next
day's folder by itself.  Every row is flushed as it is written, so
nothing is lost if the program is closed or dies.

On start-up the last hour is read back from those files so the plot is
not empty, and asking for a longer window reads further back, across as
many days as it needs.

KNOWN ISSUE -- crash while a dialog is open
-------------------------------------------
On this machine, NI-VISA can fault the process when the polling thread
talks to the instrument while a modal dialog (a message box) is running
its own event loop on the main thread.  The symptom is a "Windows fatal
exception: access violation", usually blamed on an innocent line such as
``time.sleep`` some way after the call that really caused it.

This is not new to this file: the original version, and
``old/Temp_Controller.py`` which it was modelled on, both do the same
thing and both reproduce it.  Dialogs are wrapped in
:class:`pause_polling`, which stops instrument traffic while they are
open and makes it much rarer, but it has not been eliminated.

The data is safe either way -- every row is already on disk, and the
Lakeshore keeps regulating the fridge on its own -- but if it becomes a
nuisance, the real fix is to move the polling loop onto a ``QThread``
(or into a separate process) instead of a plain ``threading.Thread``,
which is a larger change than this file's brief.

Usage
-----
    python Fridge_Temp_Controller.py
"""
# %%

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton,
    QLabel, QHBoxLayout, QGroupBox, QFormLayout, QMessageBox, QSlider,
    QMenuBar, QAction, QGridLayout, QComboBox, QStackedWidget, QListWidget,
    QFileDialog, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtCore import pyqtSignal, QObject, Qt, QTimer, QThread
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
import pyvisa

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

#: Seconds between thermometer readings.  Editable at run time from
#: Settings -> Thermometers in the GUI.
#:
#: One cycle reads 3 thermometers x 3 quantities = 9 GPIB queries, then sleeps
#: for this long, so a row is written roughly every SAMPLE_INTERVAL plus the
#: query time (a few hundred ms on GPIB).  Every row is flushed to disk as it
#: is written.
SAMPLE_INTERVAL = 0.5

#: Seconds the Lakeshore's scanner dwells on each channel before moving to the
#: next.  Editable at run time from Settings -> Thermometers.
#:
#: Unlike :data:`SAMPLE_INTERVAL`, which only governs how often *this program*
#: asks for a reading, the dwell time is a setting held on the instrument
#: itself (``INSET``, manual p.157) and has to be written to it.  The 372
#: accepts whole seconds from 1 to 200.
SCAN_DWELL_SECONDS = 1

#: Lower and upper bounds the instrument accepts for the scanner dwell time
#: (manual p.157).  Values outside this are rejected before being sent.
SCAN_DWELL_LIMITS = (1, 200)

#: Seconds to wait before trying the instrument again after a failure.
RECONNECT_INTERVAL = 5.0

#: Seconds between GUI refreshes.
#:
#: The display is redrawn from the worker's latest readings this often, and
#: only when something has actually changed.  Two per second is faster than
#: the eye needs and keeps the plot cheap even with a long history on screen.
GUI_REFRESH_INTERVAL = 0.5

#: Heater / PID state is slow to change and slow to query, so it is only read
#: every Nth cycle.  In between, the last known values are reused.
#:
#: With SAMPLE_INTERVAL = 0.5 s this means the heater readbacks refresh about
#: every 2.5 s.  Pressing "Apply to instrument" does not wait for that: it
#: forces an immediate re-read so the readback confirms the change straight
#: away.
HEATER_POLL_EVERY = 5

#: Where the CSV log is written.  ``dated_logger`` creates a
#: ``<year>\<month name>\<day>`` sub-folder here and rolls over to a new file
#: at midnight, so each day's data lands in its own file and a run that spans
#: midnight simply continues into the next day's folder.  Restarting on the
#: same day appends to that day's existing file rather than replacing it.
#:
#: Editable at run time from Settings -> Log file in the GUI.
DATA_BASE_PATH = r"D:\TemperatureData"

#: Name of the CSV log file inside the dated folder.
DATA_FILE_NAME = "Fridge_Temp_data.csv"

#: File shared with the computer that runs the S21 measurement.
#:
#: That computer's notebook loops over the temperatures it wants a spectrum
#: at, writing each one into this file as ``SetPoint``; this program picks the
#: new value up and sets the fridge going to it, then writes the measured
#: temperature back as ``CurrentTemp`` so the notebook can wait for the fridge
#: to settle before it measures.  It is the only channel between the two
#: machines, and it is deliberately a plain text file of three lines --
#: already in place and already understood by the other side, so neither the
#: format nor the path is changed here.
#:
#: ::
#:
#:     SetPoint: 0.03
#:     CurrentTemp: 0.03
#:     UseManualPID: False
#:
#: ``SetPoint`` is in kelvin and is the only field this program obeys.
#: ``CurrentTemp`` is written by this program and ignored on the way in.
#: ``UseManualPID`` is written by the other side: ``False`` (the default)
#: lets a new setpoint bring its P, I, D and heater range with it from
#: :data:`SAMPLE_HEATER_DEFAULTS`, and ``True`` sends only the setpoint and
#: leaves the tuning exactly as the GUI has it.
#:
#: Only a *change* to ``SetPoint`` moves the fridge.  Whatever is in the file
#: when this program starts is recorded and left alone, because it is left
#: over from the previous run and acting on it would move the fridge the
#: moment the window opens.
REMOTE_CONTROL_PATH = os.path.join(DATA_BASE_PATH, "RemoteControl.txt")

#: Seconds between checks of the remote-control file.
#:
#: The file is read and written this often -- three lines on a local disk,
#: which is nothing beside the GPIB traffic the same loop is already doing.
#: It is deliberately read in full every time rather than only when its
#: modification time changes: this program writes to the same file, so its
#: own writes move that time too, and trusting it would let a setpoint from
#: the other machine be overwritten before it was ever read.
REMOTE_POLL_INTERVAL = 2.0

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

#: Channel whose reading the sample heater's closed loop regulates on.
#:
#: The mixing-chamber OLD thermometer (channel 4) is the calibrated one, so it
#: is the only sensible default: the loop cannot regulate against channel 2
#: until that thermometer has a calibration curve.  Selectable at run time
#: from the "PID reference" box, which is why it is only a starting value.
DEFAULT_PID_REFERENCE_CHANNEL = 4

# --- Heaters ---------------------------------------------------------------
# key = Lakeshore output number
#
# The two heaters are not the same kind of device, and the GUI and the log are
# both built from the "closed_loop" flag below rather than from special cases:
#
#   Sample heater (output 0) -- a current source with eight decade ranges,
#       driven by the instrument's own PID loop.  It has a setpoint, P, I, D
#       and a range, and regulates towards a temperature.
#
#   Still heater (output 2) -- the analog/still output, a voltage source
#       driving the still (manual section 3.8).  It is run in the
#       instrument's still mode at a constant percentage of full scale, with
#       no setpoint and no PID, because its job is to set the circulation
#       rate rather than to chase a temperature.
HEATERS = {
    0: {
        "name": "Sample heater",
        "closed_loop": True,
        "control_channel": DEFAULT_PID_REFERENCE_CHANNEL,
        #: OUTMODE mode 5 = closed loop (PID), manual p.163.
        "output_mode": 5,
    },
    2: {
        "name": "Still heater",
        "closed_loop": False,
        "control_channel": 3,
        #: OUTMODE mode 4 = still, manual p.163.  This is the mode the
        #: instrument was found in on this fridge, and the one the analog
        #: output is meant to be in when it drives a still: the level is then
        #: set with ``STILL`` and read back with ``STILL?`` (manual p.168) as
        #: a percentage of full scale.
        "output_mode": 4,
    },
}

# --- Heater electrical properties ------------------------------------------
# These are only used to convert the instrument's percentage readback into
# watts and volts for the log and the display.  A wrong value here makes
# those two columns wrong; it does not change what is sent to the heater, so
# it cannot damage anything.
#
# The sample heater value was read from the instrument itself with
# ``HTRSET?0``, which returned ``+1000.00,8,+0.63000,2`` on 12 August 2026 --
# a 1000 ohm heater on the 100 mA range.  Check it with that query again if
# the wiring is ever changed.

#: Heater resistance in ohms, by output number.
HEATER_RESISTANCES = {
    0: 1000.0,  # sample heater, from HTRSET?0
    2: 120.0,   # still heater; TODO confirm against the fridge wiring
}

#: Full-scale current in amps for each sample-heater range index
#: (manual p.165).  Range 0 is off, so it delivers no current.
SAMPLE_HEATER_RANGE_CURRENTS = {
    0: 0.0,
    1: 31.6e-6,
    2: 100e-6,
    3: 316e-6,
    4: 1.00e-3,
    5: 3.16e-3,
    6: 10.0e-3,
    7: 31.6e-3,
    8: 100e-3,
}

#: Full-scale voltage of the analog/still output in volts (manual section 3.8).
STILL_FULL_SCALE_VOLTS = 10.0

#: Units each heater's output level is expressed in, by output number.
#:
#: The sample heater can be configured to report and accept its level either
#: as a percentage of the range's full-scale current or as power in watts;
#: which one is a setting held on the instrument, the last field of
#: ``HTRSET`` (manual p.155).  These are only starting values -- the real
#: setting is read from the instrument on the first heater poll, so that the
#: GUI labels the number with the unit the instrument is actually using
#: rather than one this file assumed.
HEATER_LEVEL_UNITS = {
    0: "W",   # sample heater; HTRSET?0 returned display=2 (power)
    2: "%",   # still heater, a percentage of the analog output's full scale
}

#: ``HTRSET`` display-field values and the unit each one means.
HTRSET_DISPLAY_UNITS = {1: "%", 2: "W"}

# --- Default PID settings per target temperature ---------------------------
# Read as: "for any target temperature up to and including this key, use
# these settings".  The bands are looked up by :func:`default_settings_for`.
#
#   T_max [K] : (P, I, D, heater_range)
#
# Lakeshore 372 sample-heater (output 0) current ranges:
#   0 = off, 1 = 31.6 uA, 2 = 100 uA, 3 = 316 uA, 4 = 1 mA,
#   5 = 3.16 mA, 6 = 10 mA, 7 = 31.6 mA, 8 = 100 mA
#
# The 1.2, 1.4 and 1.6 K rows are the settings this fridge is actually run at.
# Range 5 (3.16 mA) is 10 mW full scale into the 1000 ohm sample heater, which
# leaves the loop headroom in both directions at the ~1-2 mW these setpoints
# need; range 4 would put 1 mW at the very top of the range with nothing in
# reserve.
#
# ###########################################################################
# #  The bands BELOW 1.2 K have not been measured on this fridge.  They     #
# #  repeat the 1.2 K tuning so that a low setpoint fills the boxes with    #
# #  something plausible rather than nothing, but they are a starting       #
# #  point, not a calibration: check the loop by hand before trusting one.  #
# ###########################################################################
SAMPLE_HEATER_DEFAULTS = {
    0.100: (30.0, 2.0, 0.0, 5),
    0.300: (30.0, 2.0, 0.0, 5),
    0.600: (30.0, 2.0, 0.0, 5),
    1.200: (30.0, 2.0, 0.0, 5),
    1.400: (30.0, 2.0, 0.0, 5),
    1.600: (30.0, 2.0, 0.0, 5),
}

# The still heater (output 2) is a voltage output run in still mode, so it
# has no PID and no setpoint.  All that can usefully be defaulted per
# temperature is the output level, as a percentage of full scale.
#
# The still is held at 0% at every setpoint this fridge is run at, so there is
# one value rather than a table of them.
#
#   T_max [K] : output [%]
STILL_HEATER_DEFAULTS = {
    1.600: 0.0,
}

DEFAULTS_TABLE = {
    0: SAMPLE_HEATER_DEFAULTS,
    2: STILL_HEATER_DEFAULTS,
}


def default_settings_for(output, target_temperature):
    """
    Made by Claude. Look up a heater's default settings at a target temperature.

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
    tuple, float or None
        For a closed-loop heater, ``(P, I, D, heater_range)`` for the
        matching band.  For the still, the output percentage for that band.
        ``None`` if ``output`` has no defaults table.
    """
    table = DEFAULTS_TABLE.get(output)
    if table is None:
        print(f"No defaults table for output {output}.")
        return None

    for t_max in sorted(table.keys()):
        if target_temperature <= t_max:
            return table[t_max]

    # Target is hotter than every band -- fall back to the highest one.
    highest = sorted(table.keys())[-1]
    print(f"Target {target_temperature} K is above the highest band "
          f"({highest} K); using the {highest} K settings.")
    return table[highest]


#: Order of the numeric columns kept in memory for plotting.
#:
#: One entry per plotted trace, after the leading timestamp.  Both the live
#: loop and :func:`load_history` build their rows in this order, so a restart
#: produces exactly the same layout as a fresh run.
def plot_column_keys():
    """
    Made by Claude. List the reading keys held in the plot history, in column order.

    Returns
    -------
    list of str
        Keys into a readings dict, matching the columns of
        :attr:`Worker.data` after the leading timestamp.
    """
    keys = [f"T_ch{channel}" for channel in sorted(THERMOMETERS)]
    # The sample heater's own output level, as the instrument reports it
    # (``HTR?``), for the right-hand axis of the PID reference panel.
    keys.append("HTR_out0")
    return keys


def dated_folder_for(base_path, day):
    """
    Made by Claude. Build the path of the log folder for one calendar day.

    Mirrors the layout produced by
    :func:`~optomechanics.data_management.file_management.dated_file_maker`
    -- ``<base>\\<year>\\<month name>\\<day>`` with the day not zero-padded
    -- so that folders written by the logger are found again on reload.

    Parameters
    ----------
    base_path : str
        Root of the dated tree.
    day : datetime.date
        The day whose folder is wanted.

    Returns
    -------
    str
        Full path of that day's folder.  It may not exist.
    """
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November",
                   "December"]
    return os.path.join(base_path, str(day.year),
                        month_names[day.month - 1], str(day.day))


def set_aside_mismatched_log(folder, file_name, headers):
    """
    Made by Claude. Move aside a log file that does not match the columns being written.

    A file is only ever appended to, so if the program's columns have
    changed since it was started -- a new quantity logged, an old one
    dropped -- the rows after that point no longer line up with the heading
    row.  ``pandas`` then refuses to read the file at all, which is fatal:
    ``dated_logger`` reads the file as it opens it, so a single mismatched
    file stops the program starting.

    Rather than append to it (which makes the mismatch worse), delete it
    (which loses data), or fail (which is what happened), the old file is
    renamed with a suffix and a fresh one started alongside it.  Nothing is
    ever thrown away: the renamed file still holds every row it did before,
    and can be read with ``pandas.read_csv(..., on_bad_lines='skip')`` or by
    hand.

    Parameters
    ----------
    folder : str
        Directory holding the log file.
    file_name : str
        Name of the log file.
    headers : list of str
        Column headings this program is about to write.

    Returns
    -------
    str or None
        The path the old file was moved to, or ``None`` if it was left
        alone -- either because it matches, or because there is nothing
        there.
    """
    path = os.path.join(folder, file_name)
    if not os.path.isfile(path):
        return None

    try:
        with open(path, "r") as handle:
            first_line = handle.readline().strip()
    except Exception as e:
        print(f"[LOG] could not read the heading row of {path}: {e}")
        return None

    if not first_line:
        return None

    existing = first_line.split(",")

    # The last heading is truncated by data_logger's known off-by-one (see
    # END_COLUMN), so compare on everything before it.
    if len(existing) == len(headers) and existing[:-1] == headers[:-1]:
        return None

    stamp = datetime.datetime.now().strftime("%H%M%S")
    stem, extension = os.path.splitext(file_name)
    moved_to = os.path.join(folder, f"{stem}_before_{stamp}{extension}")

    try:
        os.rename(path, moved_to)
    except Exception as e:
        print(f"[LOG] could not move {path} aside: {e}")
        return None

    print("=" * 70)
    print("The log file already in today's folder was written with different")
    print(f"columns ({len(existing)} against {len(headers)} now), so it has")
    print("been kept as:")
    print(f"  {moved_to}")
    print("and a new file started.  No data has been lost.")
    print("=" * 70)
    return moved_to


def load_history(base_path, file_name, hours):
    """
    Made by Claude. Reload recent logged data so the plot is not empty on restart.

    Walks back day by day from today, reading each day's CSV, until enough
    history has been collected to cover ``hours`` or there are no more days
    to look at.  This is what lets the window be closed and reopened, or the
    history selector set to 72 h, without losing the trace.

    Robustness matters more than completeness here: a day whose file is
    missing, unreadable, or written by an older version with different
    columns is skipped with a message rather than being allowed to stop the
    program starting.  Missing columns come back as NaN, which plots as a
    gap.

    Parameters
    ----------
    base_path : str
        Root of the dated tree.
    file_name : str
        Name of the CSV inside each dated folder.
    hours : float
        How many hours of history to load.

    Returns
    -------
    list of list
        Rows of ``[timestamp] + values for plot_column_keys()``, oldest
        first.  Empty if nothing could be read.
    """
    if hours is None or hours <= 0:
        return []

    cutoff = time.time() - hours * 3600
    keys = plot_column_keys()
    today = datetime.date.today()

    # Cover the requested span, plus one extra day so that a window
    # reaching just past midnight still picks up the tail of the older file.
    days_needed = int(hours // 24) + 2

    stem, extension = os.path.splitext(file_name)

    rows = []
    for days_back in range(days_needed):
        day = today - datetime.timedelta(days=days_back)
        folder = dated_folder_for(base_path, day)
        if not os.path.isdir(folder):
            continue

        # The day's file, plus any files set aside earlier that day because
        # their columns no longer matched (see set_aside_mismatched_log).
        # Those hold real readings and belong in the plot just as much.
        try:
            names = sorted(name for name in os.listdir(folder)
                           if name == file_name
                           or (name.startswith(stem)
                               and name.endswith(extension)))
        except Exception as e:
            print(f"[HISTORY] could not list {folder}: {e}")
            continue

        for name in names:
            path = os.path.join(folder, name)
            rows.extend(read_history_file(path, cutoff, keys))

    rows.sort(key=lambda row: row[0])
    return rows


def read_history_file(path, cutoff, keys):
    """
    Made by Claude. Read the readings newer than ``cutoff`` out of one log file.

    Robustness matters more than completeness here: a file that is missing,
    unreadable, or written by an older version with different columns is
    skipped or partly recovered with a message, rather than being allowed to
    stop the program starting.  Missing columns come back as NaN, which
    plots as a gap.

    Parameters
    ----------
    path : str
        Full path of the CSV.
    cutoff : float
        Unix timestamp; rows older than this are ignored.
    keys : list of str
        Reading keys wanted, in plot-column order.

    Returns
    -------
    list of list
        Rows of ``[timestamp] + values for keys``.  Empty if nothing could
        be read.
    """
    if not os.path.isfile(path):
        return []

    try:
        frame = pd.read_csv(path)
    except Exception as e:
        # A file whose rows changed width partway through cannot be parsed
        # strictly, but the rows that do match the heading row are still
        # perfectly good data.  Keep those rather than throwing the whole
        # day away.
        print(f"[HISTORY] {path} is not uniform ({e}); reading the rows "
              f"that match its heading row.")
        try:
            frame = pd.read_csv(path, on_bad_lines="skip")
            print(f"[HISTORY] recovered {len(frame)} rows from it.")
        except Exception as second_error:
            print(f"[HISTORY] could not read it at all: {second_error}")
            return []

    if "Time[s]" not in frame.columns:
        print(f"[HISTORY] {path} has no 'Time[s]' column; skipped.")
        return []

    try:
        # Older files may lack the newer columns, and any column can hold
        # NOT_READING, so coerce everything and let bad values become NaN
        # rather than raising.
        times = pd.to_numeric(frame["Time[s]"], errors="coerce")
        recent = frame[times >= cutoff]
        if recent.empty:
            return []

        columns = [pd.to_numeric(times[times >= cutoff], errors="coerce")]
        for key in keys:
            column_name = history_column_name(key)
            if column_name in recent.columns:
                columns.append(pd.to_numeric(recent[column_name],
                                             errors="coerce"))
            else:
                columns.append(pd.Series(np.nan, index=recent.index))

        print(f"[HISTORY] loaded {len(recent)} rows from {path}")
        return np.column_stack(columns).tolist()

    except Exception as e:
        print(f"[HISTORY] could not parse {path}: {e}")
        print(traceback.format_exc())
        return []


def history_column_name(key):
    """
    Made by Claude. Map a reading key to its column heading in the log file.

    Parameters
    ----------
    key : str
        A key from :func:`plot_column_keys`.

    Returns
    -------
    str
        The matching CSV column heading, or the key itself if it does not
        correspond to one.
    """
    for channel, info in THERMOMETERS.items():
        name = info["name"].replace(" ", "_")
        suffix = "" if info["calibrated"] else "_UNCALIBRATED"
        if key == f"T_ch{channel}":
            return f"T_{name}_ch{channel}[K]{suffix}"
        if key == f"P_ch{channel}":
            return f"Pexc_{name}_ch{channel}[W]"

    for output, info in HEATERS.items():
        if key == f"VOLT_out{output}":
            name = info["name"].replace(" ", "_")
            return f"{name}_out{output}_Voltage[V]_calculated"
        if key == f"HTR_out{output}":
            name = info["name"].replace(" ", "_")
            units = HEATER_LEVEL_UNITS.get(output, "%")
            return f"{name}_out{output}_Output[{units}]"

    return key


def read_remote_control(path=None):
    """
    Made by Claude. Read the setpoint the S21 computer is asking for.

    Parses the three-line file described at :data:`REMOTE_CONTROL_PATH`.
    Written to be forgiving, because the file is on a shared drive and the
    other machine may be part-way through writing it: anything unparseable
    is skipped and reported rather than raised, so a momentary bad read can
    never disturb the fridge or stop the monitor.

    Parameters
    ----------
    path : str, optional
        Full path of the remote-control file.  Defaults to
        :data:`REMOTE_CONTROL_PATH`, looked up when the function is called
        rather than when it is defined, so that changing that setting takes
        effect.

    Returns
    -------
    dict or None
        ``{"setpoint": float, "manual_pid": bool}``, or ``None`` if the file
        is missing, unreadable, or holds no usable setpoint.
    """
    if path is None:
        path = REMOTE_CONTROL_PATH

    if not os.path.isfile(path):
        return None

    try:
        with open(path, "r") as handle:
            text = handle.read()
    except Exception as e:
        print(f"[REMOTE] could not read {path}: {e}")
        return None

    fields = {}
    for line in text.splitlines():
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        fields[key.strip().lower()] = value.strip()

    if "setpoint" not in fields:
        print(f"[REMOTE] {path} has no SetPoint line; ignored.")
        return None

    try:
        setpoint = float(fields["setpoint"])
    except ValueError:
        print(f"[REMOTE] SetPoint {fields['setpoint']!r} is not a number; "
              f"ignored.")
        return None

    return {
        "setpoint": setpoint,
        # Anything other than a plain "true" is taken as False, so a garbled
        # value falls back to the ordinary behaviour rather than silently
        # suppressing the PID defaults.
        "manual_pid": fields.get("usemanualpid", "").strip().lower() == "true",
    }


def write_remote_control(setpoint, current_temperature, manual_pid,
                         path=None):
    """
    Made by Claude. Write the measured temperature back for the S21 computer to read.

    Keeps the file in exactly the three-line form the other machine already
    expects, with only ``CurrentTemp`` changed; ``SetPoint`` and
    ``UseManualPID`` are written back as they were read, so this program
    never appears to be issuing instructions to itself.

    The file is written to a temporary name and then moved into place with
    :func:`os.replace`, which is atomic.  The other machine polls this file
    continuously, and a plain write would let it read a half-finished one --
    which, since it holds the setpoint, is worth taking trouble to prevent.

    Parameters
    ----------
    setpoint : float
        The setpoint currently in force, written back unchanged.
    current_temperature : float
        The temperature just measured on the PID reference thermometer.
        ``numpy.nan`` is written as :data:`NOT_READING`, so the other side
        can tell "not measured" from a real reading.
    manual_pid : bool
        The flag as it was read, written back unchanged.
    path : str, optional
        Full path of the remote-control file.  Defaults to
        :data:`REMOTE_CONTROL_PATH`, looked up when the function is called
        rather than when it is defined, so that changing that setting takes
        effect.

    Returns
    -------
    bool
        ``True`` if the file was written.
    """
    if path is None:
        path = REMOTE_CONTROL_PATH

    if current_temperature is None or (isinstance(current_temperature, float)
                                       and np.isnan(current_temperature)):
        temperature_text = NOT_READING
    else:
        temperature_text = f"{current_temperature:.6f}"

    # The line endings the file already uses; written explicitly rather than
    # left to the platform so the two machines cannot disagree about them.
    text = (f"SetPoint: {setpoint}\r\n"
            f"CurrentTemp: {temperature_text}\r\n"
            f"UseManualPID: {manual_pid}\r\n")

    temporary = f"{path}.writing"
    try:
        with open(temporary, "w", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
        return True
    except Exception as e:
        print(f"[REMOTE] could not write {path}: {e}")
        try:
            if os.path.isfile(temporary):
                os.remove(temporary)
        except Exception:
            pass
        return False


#: The worker whose polling :func:`pause_polling` suspends.
#:
#: Set once, by the GUI, as soon as the worker exists.  A module-level
#: reference keeps :func:`tell_user` usable from any widget without every one
#: of them having to be handed the worker.
ACTIVE_WORKER = None


class pause_polling:
    """
    Made by Claude. Context manager that stops instrument polling while a dialog is open.

    A modal Qt dialog runs its own event loop on the main thread.  On this
    machine, GPIB traffic from the polling thread at the same time faults
    the VISA driver and kills the program -- usually a few lines after the
    call that actually did it, which makes it look unrelated.  Wrapping
    every dialog in this holds the polling loop still until the dialog is
    gone.

    The cost is a few missed readings while a dialog is on screen.  The
    logger simply writes nothing during that time, and the gap is visible in
    the plot, which is the honest representation of what happened.

    Asking the loop to stop is not enough on its own: it has to be given
    time to finish the query it is already in the middle of, and then to
    confirm that it really has stopped.  :meth:`__enter__` therefore waits
    for the worker to acknowledge the pause before letting the dialog open,
    rather than assuming a fixed delay is long enough.

    Examples
    --------
    >>> with pause_polling():                        # doctest: +SKIP
    ...     QMessageBox.information(self, "Title", "Message")
    """

    #: Longest to wait for the polling loop to come to a stop, in seconds.
    #: A cycle is nine GPIB queries, each of which can take a moment, so
    #: this is generous.  If it expires the dialog is shown anyway: making
    #: the program unusable would be a worse failure than the risk taken.
    TIMEOUT = 5.0

    def __enter__(self):
        worker = ACTIVE_WORKER
        if worker is None:
            return self

        worker.paused = True

        # Wait until the loop confirms it is no longer talking to the
        # instrument, so the dialog's event loop never overlaps a query.
        deadline = time.time() + self.TIMEOUT
        while time.time() < deadline:
            if worker.idle or not worker.running:
                break
            time.sleep(0.02)
        else:
            print("[GUI] the monitor did not pause in time; opening the "
                  "dialog anyway.")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if ACTIVE_WORKER is not None:
            ACTIVE_WORKER.paused = False
        return False


def tell_user(parent, title, message, warning=False):
    """
    Made by Claude. Show a message box, with instrument polling paused while it is open.

    Every dialog in this program goes through here.  See
    :class:`pause_polling` for why.

    Parameters
    ----------
    parent : QWidget
        Widget the dialog belongs to.
    title : str
        Dialog title.
    message : str
        Message to show.
    warning : bool, optional
        ``True`` for a warning dialog, ``False`` (default) for an
        informational one.

    Returns
    -------
    None
    """
    with pause_polling():
        if warning:
            QMessageBox.warning(parent, title, message)
        else:
            QMessageBox.information(parent, title, message)


def tell_user_warning(parent, title, message):
    """
    Made by Claude. Show a warning box, with instrument polling paused while it is open.

    Parameters
    ----------
    parent : QWidget
        Widget the dialog belongs to.
    title : str
        Dialog title.
    message : str
        Message to show.

    Returns
    -------
    None
    """
    tell_user(parent, title, message, warning=True)


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

#: One VISA resource manager for the whole program.
#:
#: ``Device.__init__`` makes a new ``pyvisa.ResourceManager`` every time it is
#: constructed, and this program constructs a driver on every reconnect, from
#: the polling thread.  Opening VISA resource managers repeatedly off the main
#: thread while Qt is running has been seen to fault the NI-VISA driver, so
#: one manager is made here, on the main thread, at import time, and reused.
#: :meth:`Fridge_Controller.__init__` swaps it in.
SHARED_RESOURCE_MANAGER = None


def shared_resource_manager():
    """
    Made by Claude. Return the program's single VISA resource manager, making it if needed.

    Returns
    -------
    pyvisa.ResourceManager or None
        The shared manager, or ``None`` if VISA could not be started at all,
        in which case the caller should fall back to the driver's own.
    """
    global SHARED_RESOURCE_MANAGER
    if SHARED_RESOURCE_MANAGER is None:
        try:
            # Constructing the manager here also forces pyvisa to import its
            # backend, which it otherwise does lazily on first use.  That
            # matters: the lazy import would happen on the polling thread,
            # and a Python import on a background thread while the main
            # thread is inside a modal dialog's event loop faults the
            # interpreter.  Doing it here, on the main thread, at start-up,
            # is what keeps the program alive when the fridge is switched
            # off and the reconnect loop is running.
            SHARED_RESOURCE_MANAGER = pyvisa.ResourceManager()
        except Exception as e:
            print(f"[VISA] could not open a resource manager: {e}")
            return None
    return SHARED_RESOURCE_MANAGER


#: Addresses seen on the bus when the program started.
#:
#: Filled in once, on the main thread, by :func:`scan_for_instruments`.  The
#: polling thread consults this list rather than asking VISA again, because
#: scanning the bus from a background thread while Qt is running has been
#: seen to fault the VISA driver on this machine -- see
#: :func:`instrument_is_present`.
AVAILABLE_ADDRESSES = None


# Start VISA now, while this module is being imported and therefore certainly
# on the main thread.  Everything after this point can use it from any thread;
# what is not safe is *creating* it, or letting pyvisa import its backend,
# from the polling thread.  See shared_resource_manager.
shared_resource_manager()


def scan_for_instruments():
    """
    Made by Claude. List the VISA addresses currently on the bus.

    Must be called from the main thread, before the polling thread starts.
    The result is cached in :data:`AVAILABLE_ADDRESSES`.

    Returns
    -------
    tuple of str or None
        The addresses found, or ``None`` if the bus could not be scanned.
    """
    global AVAILABLE_ADDRESSES
    manager = shared_resource_manager()
    if manager is None:
        return None
    try:
        AVAILABLE_ADDRESSES = tuple(manager.list_resources())
        print(f"[VISA] {len(AVAILABLE_ADDRESSES)} addresses on the bus.")
    except Exception as e:
        print(f"[VISA] could not list resources: {e}")
        AVAILABLE_ADDRESSES = None
    return AVAILABLE_ADDRESSES


def instrument_is_present(address):
    """
    Made by Claude. Say whether an instrument was on the bus when the program started.

    This only consults the list taken by :func:`scan_for_instruments` on the
    main thread; it never asks VISA itself.  Both scanning the bus and
    opening an absent address from a background thread have been seen to
    fault the VISA driver on this machine, taking the whole program down
    rather than raising something the reconnect loop could catch.  Checking
    against the cached list turns "the Lakeshore is switched off" into an
    ordinary "not connected" state instead of a crash.

    The consequence is that an instrument switched on *after* this program
    started is not noticed until it is restarted.  That is the right trade:
    a monitor that keeps running without the fridge is far more useful than
    one that dies, and the status banner says plainly that it is not
    connected.

    Parameters
    ----------
    address : str
        VISA resource address, e.g. ``'GPIB0::12::INSTR'``.

    Returns
    -------
    bool
        ``True`` if the address was on the bus at start-up, or if the scan
        could not be made -- in which case the caller should try anyway
        rather than refuse on the strength of a failed check.
    """
    if AVAILABLE_ADDRESSES is None:
        return True
    return address in AVAILABLE_ADDRESSES


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
        # ``Device.__init__`` builds its own ``pyvisa.ResourceManager``.  On
        # this machine, constructing one from the polling thread faults the
        # interpreter -- pyvisa imports its backend lazily, and doing that
        # import off the main thread while a modal dialog is running its own
        # event loop is fatal.  Patching the constructor for the duration of
        # the base __init__ makes it hand back the manager that was already
        # built on the main thread instead.  See SHARED_RESOURCE_MANAGER.
        manager = shared_resource_manager()
        if manager is None:
            Temp_Controller.__init__(self, *args, **kwargs)
            return

        original = pyvisa.ResourceManager
        pyvisa.ResourceManager = lambda *a, **k: manager
        try:
            Temp_Controller.__init__(self, *args, **kwargs)
        finally:
            pyvisa.ResourceManager = original
        self.rm = manager

    # --- write protection --------------------------------------------------

    def safe_write(self, cmd):
        """
        Made by Claude. Write a command to the instrument unless SAFE_MODE is active.

        This is the single point through which every setting change passes.
        While :data:`SAFE_MODE` is ``True`` the command is printed and
        discarded so that nothing can reach the hardware.

        The one exception is :meth:`SetScanDwell`, which writes measurement
        timing rather than heater power; see that method for why.

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

    def ReadHeaterLevelUnits(self, output):
        """
        Made by Claude. Read the units a heater's output level is expressed in (HTRSET?).

        The last field of ``HTRSET?`` says whether the instrument reports and
        accepts this output's level as a percentage of full-scale current or
        as power in watts (manual p.155).  Asking rather than assuming means
        the GUI labels the number with the unit the instrument is really
        using, and the value typed into the box means what the label says.

        Only ask this of the heater outputs, 0 and 1.  ``HTRSET`` is not
        defined for the analog output, but the instrument answers for it
        anyway with a copy of output 0's settings, so a caller that trusts
        the reply will mislabel the still heater's level.

        Parameters
        ----------
        output : int
            Heater output number, ``0`` or ``1``.

        Returns
        -------
        str or None
            ``"%"`` or ``"W"``, or ``None`` if it could not be read.
        """
        try:
            field = int(self.query(f"HTRSET?{output}").split(',')[-1])
            return HTRSET_DISPLAY_UNITS.get(field)
        except Exception as e:
            print(f"[READ FAIL] level units of output {output}: {e}")
            return None

    def ReadActiveScanChannel(self):
        """
        Made by Claude. Read which channel the scanner is measuring right now (SCAN?).

        This matters more than it looks.  The 372 has a single measurement
        bridge shared between the channels, so only the active one is
        actually being measured; every other channel keeps returning the
        last value it had when the scanner was last on it.  Those stale
        readings are indistinguishable from fresh ones in the reply, so the
        active channel is recorded alongside them and written to the log --
        otherwise there is no way to tell afterwards which numbers in a row
        were real measurements and which were repeats.

        Returns
        -------
        float
            The active channel number, or ``numpy.nan`` if it could not be
            read.
        """
        try:
            return float(self.query("SCAN?").split(',')[0])
        except Exception as e:
            print(f"[READ FAIL] active scan channel: {e}")
            return float('nan')

    def ReadControlChannel(self, output):
        """
        Made by Claude. Query which input channel a heater output controls on.

        The control channel is the second field of the ``OUTMODE?`` response
        (manual p.163).  Used to show, and to verify, which thermometer the
        sample heater's PID loop is regulating against.

        Parameters
        ----------
        output : int
            Heater output number.

        Returns
        -------
        float
            The control input channel number, or ``numpy.nan`` if the
            response could not be parsed.
        """
        try:
            response = self.ReadOutputMode(output)
            return float(response.split(',')[1])
        except Exception as e:
            print(f"[READ FAIL] control channel of output {output}: {e}")
            return float('nan')

    # --- writes ------------------------------------------------------------

    def SetScanDwell(self, channel, dwell):
        """
        Made by Claude. Set how long the scanner dwells on one channel (INSET).

        The 372 has no command that sets the dwell time on its own.
        ``INSET`` (manual p.157) writes five fields at once -- enabled,
        dwell, pause, curve number and temperature coefficient -- so the
        only correct way to change one of them is to read all five back,
        change that one, and send them again.  That is what this does.

        The curve number is the dangerous field.  Sending ``0`` for it
        unassigns the channel's calibration curve, and the channel then
        reports nonsense temperatures with no error of any kind.  This
        method therefore takes **no** curve argument: there is deliberately
        no way to ask it to change a curve, correctly or otherwise.  The
        curve it read back is the curve it writes back, and if the read
        fails nothing is written at all.

        This is the only write in this class that is **not** blocked by
        :data:`SAFE_MODE`.  It sets measurement timing on the scanner and
        cannot deliver power to the fridge, so it is safe to change with the
        fridge warm and open -- which is exactly when the scan rate needs
        adjusting.  Every command that *can* dissipate energy still goes
        through :meth:`safe_write`.

        Parameters
        ----------
        channel : int
            Measurement channel.
        dwell : int
            Dwell time in seconds, within :data:`SCAN_DWELL_LIMITS`.

        Returns
        -------
        bool
            ``True`` if the command was sent.  ``False`` if the dwell time
            is out of range, or the channel's present settings could not be
            read back -- in which case nothing is written, rather than risk
            guessing at them.

        Raises
        ------
        ValueError
            If the readback does not have the five fields ``INSET?`` is
            documented to return.  Writing a partly-guessed ``INSET`` could
            silently unassign a calibration curve, so an unrecognised reply
            stops the write rather than being worked around.
        """
        low, high = SCAN_DWELL_LIMITS
        if not low <= int(dwell) <= high:
            print(f"Dwell time {dwell} s is outside the instrument's "
                  f"{low}-{high} s range; channel {channel} not changed.")
            return False

        try:
            reply = self.ReadInputChannelParameter(channel)
            fields = [field.strip() for field in reply.split(',')]
            if len(fields) != 5:
                raise ValueError(
                    f"INSET?{channel} returned {reply!r}, which does not "
                    f"have the five expected fields")
            enabled, _, pause, curve_number, tempco = (int(f) for f in fields)
        except Exception as e:
            print(f"[READ FAIL] settings of channel {channel}, so its dwell "
                  f"time was left alone: {e}")
            return False

        # Every field except the dwell time is written back exactly as it was
        # read.  In particular curve_number came from the instrument and is
        # never chosen here.
        cmd = (f"INSET {channel},{enabled},{int(dwell)},{pause},"
               f"{curve_number},{tempco}")
        print(f"[SEND] {cmd}")
        self.write(cmd)

        # Confirm the curve survived.  This is the failure that matters, and
        # it is silent otherwise -- a channel with no curve still returns a
        # number, just a meaningless one.
        try:
            after = self.ReadInputCurveNumber(channel)
            if int(after) != curve_number:
                print(f"[CURVE] channel {channel} curve changed from "
                      f"{curve_number} to {int(after)}; putting it back.")
                self.write(f"INCRV {channel},{curve_number}")
        except Exception as e:
            print(f"[CURVE] could not confirm channel {channel}'s curve: {e}")

        return True

    def SetAutoscan(self, channel, autoscan=True):
        """
        Made by Claude. Start or stop the scanner stepping through the channels (SCAN).

        With autoscan off the instrument stays on one channel indefinitely,
        so every other thermometer's reading is frozen at whatever it last
        was -- which looks exactly like the other channels having stopped
        working.  With it on, the instrument visits each enabled channel in
        turn, spending its dwell time on each (manual p.167).

        Like :meth:`SetScanDwell` this is measurement timing rather than
        heater power, so it is not blocked by :data:`SAFE_MODE`.

        Parameters
        ----------
        channel : int
            Channel to start scanning from.
        autoscan : bool, optional
            ``True`` to step through the channels, ``False`` to hold on
            ``channel``.  Default ``True``.

        Returns
        -------
        bool
            ``True`` if the command was sent.
        """
        cmd = f"SCAN {channel},{1 if autoscan else 0}"
        print(f"[SEND] {cmd}")
        self.write(cmd)
        return True

    def SetStillOutput(self, percent):
        """
        Made by Claude. Set the still heater's output level (STILL on output 2).

        The still heater is run at a constant level rather than by a control
        loop, so its setting is simply a percentage of full scale.  ``STILL``
        is the command for it (manual p.168), and is the right one because
        this output is configured in still mode (``OUTMODE`` mode 4) -- which
        is how the instrument was found set up on this fridge.  ``MOUT``
        would be the command for an output in open-loop mode instead.

        Parameters
        ----------
        percent : float
            Output level as a percentage of full scale, 0 to 100.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if blocked by safe mode.
        """
        return self.safe_write(f"STILL 2,{percent}")

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

    # These signals are kept for compatibility with the rest of the group's
    # GUIs, but this program does not connect them.  Qt signals emitted from
    # a plain ``threading.Thread`` are delivered without Qt's cross-thread
    # machinery, and on this machine that corrupts memory and brings the
    # program down -- typically some lines after the emit, which makes it
    # look like an unrelated crash.  The GUI polls :meth:`snapshot` from a
    # QTimer on the main thread instead; see MainWindow.poll_worker.
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
        #: Root of the dated log tree.  Changed at run time from
        #: Settings -> Log file, which restarts the logger on the new path.
        self.base_path = DATA_BASE_PATH
        #: Seconds between readings; editable from Settings -> Thermometers.
        self.sample_interval = SAMPLE_INTERVAL
        #: Seconds the scanner spends on each channel.  Applied to the
        #: instrument whenever the connection is made, and whenever it is
        #: changed from Settings -> Thermometers.
        self.scan_dwell = SCAN_DWELL_SECONDS
        #: How much history to reload at start-up, in hours.  Set by the GUI
        #: before the thread starts, and again whenever the window is widened
        #: beyond what is already in memory.
        self.history_hours = 1.0
        #: Set by the GUI after the base path is changed, to make the polling
        #: loop open a fresh logger on the new path.
        self.restart_logger = False
        #: Instrument writes waiting to be carried out by the polling loop.
        #:
        #: The GUI must never touch the instrument itself.  Doing so means
        #: taking :attr:`lock`, which the polling thread holds for a whole
        #: read cycle, so the window freezes until that cycle finishes -- and
        #: with a long dwell time that is long enough for Windows to declare
        #: the program unresponsive.  Instead the GUI appends a job here and
        #: returns immediately; the polling loop runs it between cycles, when
        #: it already owns the instrument.
        #:
        #: Each entry is ``(description, callable, on_done)``.  ``on_done``
        #: is called with ``True`` or ``False``, from the polling thread.
        self.pending_commands = []
        #: Guards :attr:`pending_commands` only.  Separate from :attr:`lock`
        #: so that queueing a job can never wait on GPIB traffic.
        self.command_lock = threading.Lock()
        #: Guards :attr:`data`, :attr:`latest` and :attr:`revision`.
        #:
        #: Also separate from :attr:`lock`, and for the same reason: the GUI
        #: reads these every refresh, and must never be made to wait behind a
        #: GPIB cycle to do it.  It is only ever held for a list copy.
        self.data_lock = threading.Lock()
        #: While set, the polling loop stops talking to the instrument.
        #:
        #: Held by the GUI whenever a modal dialog is open.  A modal dialog
        #: runs its own event loop on the main thread, and GPIB traffic from
        #: this thread at the same time faults the VISA driver on this
        #: machine.  Pausing costs a few readings; not pausing costs the
        #: whole program.  See :func:`pause_polling`.
        self.paused = False
        #: True whenever the polling loop is *not* talking to the instrument.
        #:
        #: :class:`pause_polling` waits for this before letting a dialog
        #: open, so that a dialog's event loop never runs at the same time as
        #: a GPIB query.  Set to False for exactly as long as the instrument
        #: is in use.
        self.idle = True
        #: Latest status line and whether it is healthy, read by the GUI's
        #: timer rather than pushed to it.  See :meth:`set_status`.
        self.status = ("Starting ...", False)
        #: Bumped every time a new reading is stored, so that the GUI can
        #: tell whether anything has changed since it last looked.
        self.revision = 0
        #: Last setpoint taken from the remote-control file, so that the same
        #: value sitting in the file is acted on once rather than re-applied
        #: on every cycle.  ``None`` until one has been seen.
        self.remote_setpoint = None
        #: ``UseManualPID`` as last read; see :data:`REMOTE_CONTROL_PATH`.
        self.remote_manual_pid = False
        #: When the remote-control file was last looked at.
        self.remote_last_checked = 0.0
        #: Whether the file has been looked at at all yet.  The first look
        #: only records what is in it, so that a setpoint left over from the
        #: last run cannot move the fridge at start-up; see
        #: :meth:`check_remote_control`.
        self.remote_seen_once = False
        #: What the remote channel last did, shown in the GUI.
        self.remote_status = "Remote setpoints: waiting for the S21 computer"
        #: Disagreements found between the instrument's settings and this
        #: file's assumptions, from :meth:`check_instrument_agrees`.  Shown
        #: in the GUI so they are not only in the console.
        self.setup_problems = []

    # --- instrument writes requested by the GUI ----------------------------

    def queue_command(self, description, action, on_done=None):
        """
        Made by Claude. Ask the polling loop to run an instrument command for us.

        Returns as soon as the job is queued, so the GUI thread is never
        held up by GPIB traffic.  See :attr:`pending_commands`.

        Parameters
        ----------
        description : str
            Short description, used in console messages.
        action : callable
            Called with the live instrument as its only argument, from the
            polling thread.  Should return something truthy on success.
        on_done : callable, optional
            Called with ``True`` or ``False`` once the job has run.  Runs on
            the polling thread, so it must not touch widgets.

        Returns
        -------
        None
        """
        with self.command_lock:
            self.pending_commands.append((description, action, on_done))
        print(f"Queued: {description}")

    def run_pending_commands(self):
        """
        Made by Claude. Carry out any instrument commands the GUI has queued.

        Called from the polling loop, which already holds :attr:`lock` and
        owns the instrument, so the commands run without any extra waiting.

        Returns
        -------
        None
        """
        with self.command_lock:
            if not self.pending_commands:
                return
            jobs = self.pending_commands
            self.pending_commands = []

        for description, action, on_done in jobs:
            succeeded = False
            try:
                succeeded = bool(action(self.instrument))
            except Exception as e:
                print(f"[WRITE FAIL] {description}: {e}")
                print(traceback.format_exc())
            else:
                print(f"{'Done' if succeeded else 'Not sent'}: {description}")

            if on_done is not None:
                try:
                    on_done(succeeded)
                except Exception as e:
                    print(f"[WRITE FAIL] after {description}: {e}")

    # --- talking to the GUI ------------------------------------------------

    def set_status(self, message, healthy):
        """
        Made by Claude. Record the status line for the GUI to pick up.

        Deliberately a plain attribute write rather than a Qt signal: this
        runs on the polling thread, and emitting from a plain thread is what
        used to bring the program down.  Assigning a tuple is atomic as far
        as the GUI is concerned, so the reader can never see half of one.

        Parameters
        ----------
        message : str
            Status text to show.
        healthy : bool
            ``True`` if the instrument is answering.

        Returns
        -------
        None
        """
        self.status = (message, healthy)

    def snapshot(self):
        """
        Made by Claude. Take a consistent copy of everything the GUI displays.

        Called from the GUI's timer, on the main thread.  Takes
        :attr:`data_lock` rather than :attr:`lock`, and holds it only long
        enough to copy references, so the GUI never waits behind GPIB
        traffic.

        Returns
        -------
        dict
            ``latest`` readings, the ``data`` history, the ``status`` tuple,
            the ``log_file_path`` and the current ``revision``.
        """
        with self.data_lock:
            return {
                "latest": dict(self.latest),
                # The list is only ever appended to or replaced wholesale by
                # the worker, so a shallow copy is a consistent view.
                "data": list(self.data),
                "status": self.status,
                "log_file_path": self.log_file_path,
                "revision": self.revision,
                "remote_status": self.remote_status,
                "setup_problems": list(self.setup_problems),
            }

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

    def heater_voltage(self, output, level, heater_range):
        """
        Made by Claude. Work out the voltage a heater is being driven at.

        The 372 measures no voltage anywhere in a heater circuit, so this is
        derived from the level the instrument reports, the selected range and
        the heater's resistance (:data:`HEATER_RESISTANCES`).  It is a
        calculation, not a measurement, and is only as good as those
        resistances -- which is why the column it feeds is named
        ``..._Voltage[V]_calculated``.

        For the sample heater the range selects a full-scale current
        (:data:`SAMPLE_HEATER_RANGE_CURRENTS`).  Its level may be reported
        either as a percentage of that or directly in watts, depending on the
        instrument's own ``HTRSET`` display setting (manual p.155), so both
        are handled: from a percentage ``V = (percent/100) * I_fs * R``, and
        from a power ``V = sqrt(P * R)``.

        For the still heater, which is a voltage output with a 10 V full
        scale (manual section 3.8), the percentage is of that voltage, so
        ``V = percent/100 * 10``.

        Parameters
        ----------
        output : int
            Heater output number.
        level : float
            Output level as the instrument reports it, in the units given by
            :data:`HEATER_LEVEL_UNITS` for this output.
        heater_range : float
            Range index currently selected on the output.

        Returns
        -------
        float
            The voltage in volts, or ``numpy.nan`` if it could not be worked
            out.
        """
        nan = float('nan')
        try:
            if level is None or np.isnan(level):
                return nan

            resistance = HEATER_RESISTANCES.get(output)
            if resistance is None or resistance <= 0:
                return nan

            if HEATERS[output]["closed_loop"]:
                # The level is watts or a percentage of full-scale current,
                # depending on a setting held on the instrument.
                if HEATER_LEVEL_UNITS.get(output) == "W":
                    return float(np.sqrt(max(level, 0.0) * resistance))

                if heater_range is None or np.isnan(heater_range):
                    return nan
                full_scale = SAMPLE_HEATER_RANGE_CURRENTS.get(int(heater_range))
                if full_scale is None:
                    return nan
                return (level / 100.0) * full_scale * resistance

            # Voltage source: the percentage is of the 10 V full scale.
            return (level / 100.0) * STILL_FULL_SCALE_VOLTS

        except Exception as e:
            print(f"[CALC FAIL] voltage of output {output}: {e}")
            return nan

    def build_headers(self):
        """
        Made by Claude. Build the CSV column headings for the log file.

        Returns
        -------
        list of str
            Column headings, in the same order as the rows written by
            :meth:`run`.
        """
        # Only the active channel is freshly measured on any given row; see
        # Fridge_Controller.ReadActiveScanChannel.
        headers = ["Time[s]", "Timestamp", "ActiveScanChannel"]

        for channel, info in THERMOMETERS.items():
            name = info["name"].replace(" ", "_")
            suffix = "" if info["calibrated"] else "_UNCALIBRATED"
            headers.append(f"T_{name}_ch{channel}[K]{suffix}")
            headers.append(f"R_{name}_ch{channel}[Ohm]")
            headers.append(f"Pexc_{name}_ch{channel}[W]")

        for output, info in HEATERS.items():
            name = info["name"].replace(" ", "_")
            # The level as the instrument itself reports it, in whatever units
            # the instrument is set to use for that output; see
            # HEATER_LEVEL_UNITS.
            units = HEATER_LEVEL_UNITS.get(output, "%")
            headers.append(f"{name}_out{output}_Output[{units}]")
            # The 372 measures neither the power nor the voltage in a heater,
            # so the voltage is worked out here from the level, the range and
            # the heater resistance.  The heading says so, because a column
            # that looks like a measurement and is not is worse than no
            # column at all.
            #
            # There is deliberately no calculated power column: for a heater
            # reporting its level in watts that would be a second, worse copy
            # of the level beside it, and for one reporting a percentage the
            # voltage below already carries the same information.
            headers.append(f"{name}_out{output}_Voltage[V]_calculated")
            headers.append(f"{name}_out{output}_Range")
            if not info["closed_loop"]:
                # What the analog output is really delivering, which differs
                # from the level above whenever the range is off; see
                # poll_heaters.
                headers.append(f"{name}_out{output}_AnalogOut[%]")
            # Only a closed-loop heater has something to regulate towards.
            if info["closed_loop"]:
                headers.append(f"{name}_out{output}_Setpoint[K]")
                headers.append(f"{name}_out{output}_ControlChannel")
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
        # Which channel is really being measured; the rest are stale.  See
        # Fridge_Controller.ReadActiveScanChannel.
        readings = {"ACTIVE_CH": self.read_value(
            "active scan channel", self.instrument.ReadActiveScanChannel)}

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
        Made by Claude. Read the state of every heater output.

        What is read depends on the kind of heater.  Both report an output
        level, a range, and the power and voltage derived from them; only a
        closed-loop heater has a setpoint, a control channel and PID terms.

        The sample heater's level is read with ``HTR?``, which applies to
        that output only (manual p.155).  The still heater sits on the
        analog output, whose level is read with ``AOUT?`` (p.149).

        Returns
        -------
        dict
            Readings keyed by ``"HTR_out<n>"``, ``"VOLT_out<n>"``,
            ``"RANGE_out<n>"`` and, for closed-loop heaters,
            ``"SETP_out<n>"``, ``"CTRLCH_out<n>"``, ``"P_out<n>"``,
            ``"I_out<n>"`` and ``"D_out<n>"``.  Every one of these except
            ``VOLT_out<n>`` is read from the instrument; that one is
            calculated, see :meth:`heater_voltage`.  Any value that could not
            be read is ``numpy.nan``.
        """
        readings = {}
        for output, info in HEATERS.items():
            if info["closed_loop"]:
                readings[f"HTR_out{output}"] = self.read_value(
                    f"output level of {info['name']}",
                    self.instrument.ReadHeaterOutput, output)
            else:
                # The still runs in still mode, where its level is the one
                # STILL? reports (manual p.168).  That is the setting the
                # GUI's box holds and STILL writes, so it is the one to show
                # and to log.
                #
                # AOUT? is a different number: what the analog output is
                # actually delivering, which is zero whenever the output's
                # range is off however high the still is set.  Both are read,
                # because "set to 10% but switched off" is exactly the state
                # that is worth being able to see afterwards in the file.
                readings[f"HTR_out{output}"] = self.read_value(
                    f"output level of {info['name']}",
                    self.instrument.ReadStillOutput, output)
                readings[f"AOUT_out{output}"] = self.read_value(
                    f"analog output delivered by {info['name']}",
                    self.instrument.ReadAnalogOutput, output)

            readings[f"RANGE_out{output}"] = self.read_value(
                f"range of {info['name']}",
                self.instrument.ReadHeaterRange, output)

            readings[f"VOLT_out{output}"] = self.heater_voltage(
                output, readings[f"HTR_out{output}"],
                readings[f"RANGE_out{output}"])

            if not info["closed_loop"]:
                continue

            readings[f"SETP_out{output}"] = self.read_value(
                f"setpoint of {info['name']}",
                self.instrument.ReadSetpoint, output)
            readings[f"CTRLCH_out{output}"] = self.read_value(
                f"control channel of {info['name']}",
                self.instrument.ReadControlChannel, output)
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
        row = [f"{current_time}", stamp,
               format_for_log(readings.get("ACTIVE_CH"))]

        for channel in THERMOMETERS:
            row.append(format_for_log(readings.get(f"T_ch{channel}")))
            row.append(format_for_log(readings.get(f"R_ch{channel}")))
            row.append(format_for_log(readings.get(f"P_ch{channel}")))

        # Must stay in step with build_headers, or every column after the
        # first mismatch is written under the wrong heading.
        for output, info in HEATERS.items():
            row.append(format_for_log(readings.get(f"HTR_out{output}")))
            row.append(format_for_log(readings.get(f"VOLT_out{output}")))
            row.append(format_for_log(readings.get(f"RANGE_out{output}")))
            if not info["closed_loop"]:
                row.append(format_for_log(readings.get(f"AOUT_out{output}")))
            if info["closed_loop"]:
                row.append(format_for_log(readings.get(f"SETP_out{output}")))
                row.append(format_for_log(readings.get(f"CTRLCH_out{output}")))
                row.append(format_for_log(readings.get(f"P_out{output}")))
                row.append(format_for_log(readings.get(f"I_out{output}")))
                row.append(format_for_log(readings.get(f"D_out{output}")))

        # See END_COLUMN: absorbs the truncation bug in data_logger.
        row.append(END_COLUMN)

        return row

    # --- control, called from the GUI thread -------------------------------

    def apply_heater_settings(self, output, settings):
        """
        Made by Claude. Push a set of settings to one heater output.

        For a closed-loop heater this configures the output for PID control
        on the chosen thermometer, sets the PID terms and setpoint, and only
        then opens the heater range -- so that the loop is never switched on
        before it knows what it is aiming for.  For the still, which chases
        no temperature, it sets the mode and the output level.

        Only the settings actually present in ``settings`` are written, so a
        box the user left blank leaves that value untouched on the
        instrument.

        Every command goes through :meth:`Fridge_Controller.safe_write`, so
        while :data:`SAFE_MODE` is ``True`` this method changes nothing on
        the instrument and merely prints what it would have sent.

        Parameters
        ----------
        output : int
            Heater output number.
        settings : dict
            Any of ``"p"``, ``"i"``, ``"d"``, ``"setpoint"``, ``"range"``,
            ``"control_channel"`` (closed loop) or ``"output"`` (open loop).
            Missing keys are left unchanged on the instrument.

        Returns
        -------
        bool
            ``True`` if at least one command was sent, ``False`` if
            everything was blocked by safe mode or the instrument was
            unavailable.
        """
        info = HEATERS[output]

        def apply(instrument):
            sent = False
            if info["closed_loop"]:
                # The control channel decides which thermometer the loop
                # regulates against, so it has to be set before the loop
                # is energised.
                channel = settings.get("control_channel",
                                       info["control_channel"])
                sent |= bool(instrument.SetOutputMode(
                    output, info["output_mode"], channel))
                # Remember it, so the readback and the plot agree with
                # what was actually applied.
                info["control_channel"] = channel

                if all(key in settings for key in ("p", "i", "d")):
                    sent |= bool(instrument.SetPID(
                        output, settings["p"], settings["i"],
                        settings["d"]))
                if "setpoint" in settings:
                    sent |= bool(instrument.SetSetpoint(
                        output, settings["setpoint"]))
            else:
                sent |= bool(instrument.SetOutputMode(
                    output, info["output_mode"], info["control_channel"]))
                if "output" in settings:
                    sent |= bool(instrument.SetStillOutput(
                        settings["output"]))

            # Range last: never energise the heater before the loop or
            # the level is set up.
            if "range" in settings:
                sent |= bool(instrument.SetHeaterRange(
                    output, settings["range"]))

            # Refresh the readback now rather than waiting for the next
            # scheduled heater poll, so the user sees the change land.
            self.force_heater_poll = True
            return sent

        self.queue_command(f"apply settings to {info['name']}", apply)
        # Queued, not yet sent.  In safe mode nothing will actually reach the
        # instrument; the console says what would have been sent.
        return not SAFE_MODE

    # --- remote control, from the S21 computer ------------------------------

    def check_remote_control(self, readings):
        """
        Made by Claude. Act on the setpoint the S21 computer has asked for.

        Called once per polling cycle, and does its work at most every
        :data:`REMOTE_POLL_INTERVAL` seconds.

        A setpoint that differs from the one already acted on is applied to
        the sample heater through the same path as one typed into the GUI --
        so it goes through :meth:`Fridge_Controller.safe_write` and is
        blocked by :data:`SAFE_MODE` exactly like everything else.  Unless
        ``UseManualPID`` is set, it brings the P, I, D and heater range for
        that temperature with it from :data:`SAMPLE_HEATER_DEFAULTS`.

        The measured temperature is written back on every check, whether or
        not the setpoint changed, because that is what the other machine
        waits on to know the fridge has settled.

        Parameters
        ----------
        readings : dict
            The readings just taken, used for the temperature written back.

        Returns
        -------
        None
        """
        now = time.time()
        if now - self.remote_last_checked < REMOTE_POLL_INTERVAL:
            return
        self.remote_last_checked = now

        # The value sitting in the file at start-up is left over from the last
        # run, and acting on it would move the fridge the moment this program
        # opens -- with nobody necessarily watching.  So the first look only
        # records what is there; the fridge is moved when the S21 computer
        # writes something genuinely new.
        if not self.remote_seen_once:
            self.remote_seen_once = True
            existing = read_remote_control()
            if existing is None:
                self.remote_status = ("Remote setpoints: no setpoint in the "
                                      "file yet")
            else:
                self.remote_setpoint = existing["setpoint"]
                self.remote_manual_pid = existing["manual_pid"]
                self.remote_status = (
                    f"Remote setpoints: file holds {existing['setpoint']} K "
                    f"from a previous run; waiting for a new one")
                print(f"[REMOTE] the file already held "
                      f"{existing['setpoint']} K when this program started.  "
                      f"It has NOT been applied -- the fridge is only moved "
                      f"when the S21 computer writes a new setpoint.")
            return

        if not os.path.isfile(REMOTE_CONTROL_PATH):
            self.remote_status = ("Remote setpoints: no file at "
                                  f"{REMOTE_CONTROL_PATH}")
            return

        # Read first, then write.  The two must be in this order and the
        # modification time must not be used to decide whether to read: this
        # program writes CurrentTemp back into the same file, so its own write
        # updates the time as well, and a check that trusted it would re-read
        # the file, find the setpoint it had just written itself, conclude
        # nothing had changed, and overwrite whatever the S21 computer had put
        # there in the meantime.  A setpoint would then be silently lost.
        # Reading the whole file every couple of seconds costs nothing beside
        # the GPIB traffic this loop is already doing.
        request = read_remote_control()
        if request is not None:
            self.remote_manual_pid = request["manual_pid"]
            if request["setpoint"] != self.remote_setpoint:
                self.apply_remote_setpoint(request["setpoint"],
                                           request["manual_pid"])

        # Report back, so the other side can watch the fridge settle.
        if self.remote_setpoint is not None:
            channel = HEATERS[0]["control_channel"] if 0 in HEATERS else None
            temperature = readings.get(f"T_ch{channel}", float('nan'))
            write_remote_control(self.remote_setpoint, temperature,
                                 self.remote_manual_pid)

    def apply_remote_setpoint(self, setpoint, manual_pid):
        """
        Made by Claude. Send a setpoint that came from the S21 computer.

        Goes through :meth:`apply_heater_settings`, so the command is queued
        for the polling loop and passes through the same safe-mode check as
        one entered by hand.  Nothing here can reach the instrument while
        :data:`SAFE_MODE` is True.

        Parameters
        ----------
        setpoint : float
            Target temperature in kelvin.
        manual_pid : bool
            ``True`` to send only the setpoint, leaving the tuning alone;
            ``False`` to send the P, I, D and range for that temperature too.

        Returns
        -------
        None
        """
        settings = {"setpoint": setpoint}

        if manual_pid:
            described = "the setpoint only (UseManualPID is True)"
        else:
            defaults = default_settings_for(0, setpoint)
            if defaults is None:
                described = "the setpoint only (no defaults table)"
            else:
                p, i, d, heater_range = defaults
                settings.update({"p": p, "i": i, "d": d,
                                 "range": int(heater_range)})
                described = (f"P={p}, I={i}, D={d}, range={heater_range}")

        # Remember it before sending, so that a failure to send does not make
        # this run again on the very next cycle and every cycle after it.
        self.remote_setpoint = setpoint

        print("=" * 70)
        print(f"[REMOTE] the S21 computer asked for {setpoint} K, with "
              f"{described}.")
        print("=" * 70)

        self.apply_heater_settings(0, settings)

        self.remote_status = (f"Remote setpoint {setpoint} K "
                              f"{'requested' if SAFE_MODE else 'applied'} at "
                              f"{datetime.datetime.now().strftime('%H:%M:%S')}")
        if SAFE_MODE:
            self.remote_status += " -- SAFE MODE, nothing was sent"

    def trim_history(self):
        """
        Made by Claude. Drop plot history that is older than anything on display.

        The log file is the record; the list held here only feeds the plot.
        Without this a run left going for weeks would grow it until the
        program ran out of memory.  A generous margin over the selected
        window is kept, so widening the view usually needs no re-read.

        Returns
        -------
        None
        """
        keep_hours = max(self.history_hours * 2, 48)
        cutoff = time.time() - keep_hours * 3600
        if self.data and self.data[0][0] < cutoff:
            self.data = [row for row in self.data if row[0] >= cutoff]

    def reload_history(self):
        """
        Made by Claude. Re-read the log files to cover the currently selected span.

        Called when the history window is widened past what is already in
        memory, and at start-up.  Rows newer than the reloaded span are kept
        and re-appended, so readings taken while the files were being read
        are not lost.

        Returns
        -------
        None
        """
        try:
            # Read the files outside the lock: it is slow, and the polling
            # loop should not be held up by it.
            reloaded = load_history(self.base_path, DATA_FILE_NAME,
                                    self.history_hours)
            if not reloaded:
                return

            # Anything already in memory but newer than the last reloaded
            # row is still only in memory, so carry it over.  This is called
            # from the GUI thread while the worker may be appending, so the
            # swap itself is done under the lock.
            newest = reloaded[-1][0]
            with self.data_lock:
                live_tail = [row for row in self.data if row[0] > newest]
                self.data = reloaded + live_tail
                self.revision += 1
                held = len(self.data)
            print(f"[HISTORY] now holding {held} rows.")

        except Exception as e:
            print(f"[HISTORY] reload failed: {e}")
            print(traceback.format_exc())

    def read_heater_units(self):
        """
        Made by Claude. Ask the instrument what units each heater's level is in.

        Updates :data:`HEATER_LEVEL_UNITS` in place, so that the GUI's labels
        and the log's column headings both describe the number the
        instrument is actually giving.  Called once per connection, from
        inside the polling loop's own lock.

        Returns
        -------
        None
        """
        if self.instrument is None:
            return
        for output in HEATERS:
            # ``HTRSET`` describes the heater outputs (0 and 1) only.  Asked
            # about the analog output the instrument answers anyway, echoing
            # output 0's settings, which would mislabel the still heater's
            # level as watts when ``AOUT?`` in fact reports a percentage of
            # full scale (manual p.149).  So only ask where it means
            # something.
            if not HEATERS[output]["closed_loop"]:
                continue
            units = self.instrument.ReadHeaterLevelUnits(output)
            if units and units != HEATER_LEVEL_UNITS.get(output):
                print(f"{HEATERS[output]['name']}: the instrument reports its "
                      f"level in {units}, not "
                      f"{HEATER_LEVEL_UNITS.get(output)}.")
                HEATER_LEVEL_UNITS[output] = units
                # The column heading for that level carries the unit, so a
                # file already open was written with the old one.  Start a
                # fresh file rather than change what a heading means
                # partway down it.
                if self.log_file_path:
                    print("Starting a new log file, so that the level column "
                          "keeps one meaning throughout.")
                    self.restart_logger = True

    def check_instrument_agrees(self):
        """
        Made by Claude. Compare the instrument's own settings with what this file assumes.

        Several numbers in the configuration block are assumptions about the
        hardware rather than things this program sets:
        :data:`HEATER_RESISTANCES` is used to work out heater voltage, and the
        output modes in :data:`HEATERS` describe how each output is expected
        to be driven.  If the instrument has been set up differently -- by
        hand at the front panel, or by someone else's program -- those
        assumptions become quietly wrong, and the first sign of it is a
        column of numbers that look plausible and are not.

        This reads the relevant settings back once per connection and prints
        every disagreement.  It **changes nothing**: the instrument is the
        authority on its own state, and silently rewriting a setting someone
        put there on purpose is exactly the kind of surprise this program is
        meant not to spring on a running fridge.

        Called from inside the polling loop's own lock, so the instrument is
        already owned.

        Returns
        -------
        list of str
            One line per disagreement found; empty if everything matches.
        """
        if self.instrument is None:
            return []

        problems = []

        # Heater resistance, which the calculated voltage column rests on.
        # HTRSET? answers for the heater outputs only (manual p.155).
        for output, info in HEATERS.items():
            if not info["closed_loop"]:
                continue
            try:
                reply = self.instrument.ReadHeaterSetup(output)
                resistance = float(reply.split(',')[0])
            except Exception as e:
                problems.append(f"{info['name']}: could not read HTRSET? "
                                f"({e}), so its heater resistance is "
                                f"unconfirmed.")
                continue

            assumed = HEATER_RESISTANCES.get(output)
            if assumed is None:
                continue
            # A percent apart is measurement noise; more is a real difference.
            if abs(resistance - assumed) > max(0.01 * assumed, 0.5):
                problems.append(
                    f"{info['name']}: the instrument says the heater is "
                    f"{resistance:g} ohm, this file assumes {assumed:g} ohm.  "
                    f"The calculated voltage column will be wrong until "
                    f"HEATER_RESISTANCES is corrected.")

        # Which thermometer the closed loop is really regulating on, and in
        # what mode.  Both come from OUTMODE? (manual p.163).
        for output, info in HEATERS.items():
            try:
                fields = self.instrument.ReadOutputMode(output).split(',')
                mode = int(fields[0])
                control_channel = int(fields[1])
            except Exception as e:
                problems.append(f"{info['name']}: could not read OUTMODE? "
                                f"({e}).")
                continue

            if mode != info["output_mode"]:
                problems.append(
                    f"{info['name']}: the instrument is in output mode "
                    f"{mode}, this file expects {info['output_mode']}.  "
                    f"Applying settings will change it.")

            if info["closed_loop"] and control_channel != info["control_channel"]:
                problems.append(
                    f"{info['name']}: the loop is regulating on channel "
                    f"{control_channel}, the GUI is showing channel "
                    f"{info['control_channel']}.")
                # The instrument is right about what it is doing, so follow
                # it rather than contradicting it on screen.
                info["control_channel"] = control_channel

        # The PID terms and range that are actually in force, printed so the
        # first thing in the console is the fridge's real state.
        try:
            p, i, d = self.read_pid_values(0)
            heater_range = self.read_value("range of the sample heater",
                                           self.instrument.ReadHeaterRange, 0)
            print(f"Sample heater as found: P={p:g}, I={i:g}, D={d:g}, "
                  f"range={heater_range:.0f}.")
        except Exception as e:
            problems.append(f"Could not read the sample heater's PID or "
                            f"range: {e}")

        if problems:
            print("=" * 70)
            print("The Lakeshore is not set up the way this program assumes:")
            for problem in problems:
                print(f"  - {problem}")
            print("Nothing has been changed on the instrument.")
            print("=" * 70)
        else:
            print("The Lakeshore's settings match what this program assumes.")

        return problems

    def start_scanning(self):
        """
        Made by Claude. Put the scanner into autoscan with the configured dwell time.

        Called once each time the connection is made, from inside the
        polling loop's own lock.  Without this the instrument keeps whatever
        scan state it was left in, which on this fridge was "hold channel 3"
        -- so the 1K pot updated and the two mixing-chamber thermometers
        appeared to have stopped.

        Returns
        -------
        bool
            ``True`` if the scanner was configured.
        """
        if self.instrument is None:
            return False
        try:
            for channel in THERMOMETERS:
                self.instrument.SetScanDwell(channel, self.scan_dwell)
            self.instrument.SetAutoscan(min(THERMOMETERS), autoscan=True)
            print(f"Autoscan on, {self.scan_dwell} s per channel.")
            return True
        except Exception as e:
            print(f"[WRITE FAIL] starting the scanner: {e}")
            print(traceback.format_exc())
            return False

    def apply_scan_dwell(self, dwell):
        """
        Made by Claude. Set the scanner dwell time on every measurement channel.

        Unlike the heater settings this is written even while
        :data:`SAFE_MODE` is on -- it changes measurement timing, not heater
        power.  See :meth:`Fridge_Controller.SetScanDwell`.

        Parameters
        ----------
        dwell : int
            Dwell time in seconds, within :data:`SCAN_DWELL_LIMITS`.

        Returns
        -------
        bool
            ``True`` if the command was sent.
        """
        low, high = SCAN_DWELL_LIMITS
        if not low <= dwell <= high:
            print(f"Dwell time {dwell} s is outside the instrument's "
                  f"{low}-{high} s range; not sent.")
            return False

        # Remember it, so a later reconnect brings the same setting back.
        self.scan_dwell = dwell

        def set_dwell(instrument):
            sent = True
            for channel in THERMOMETERS:
                sent &= bool(instrument.SetScanDwell(channel, dwell))
            # Autoscan has to be on, or the instrument sits on one channel
            # and the dwell time never comes into play at all.
            sent &= bool(instrument.SetAutoscan(
                min(THERMOMETERS), autoscan=True))
            return sent

        self.queue_command(f"set scanner dwell to {dwell} s", set_dwell)
        return True

    def set_heater_range(self, output, heater_range):
        """
        Made by Claude. Set one heater's range, which is what switches it on and off.

        Range 0 is off; for the sample heater 1 to 8 select the current
        range, and for the analog output 1 is simply on (manual p.165).

        Queued for the polling loop rather than sent from here, so that the
        GUI thread never waits on the instrument; see
        :attr:`pending_commands`.

        Parameters
        ----------
        output : int
            Heater output number.
        heater_range : int
            Range index.

        Returns
        -------
        bool
            ``True`` if the command was queued, ``False`` if safe mode will
            block it.
        """
        def apply(instrument):
            sent = instrument.SetHeaterRange(output, heater_range)
            # Show the new state straight away rather than at the next
            # scheduled heater poll.
            self.force_heater_poll = True
            return sent

        what = "off" if heater_range == 0 else f"on at range {heater_range}"
        self.queue_command(f"switch {HEATERS[output]['name']} {what}", apply)
        return not SAFE_MODE

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
            ``True`` if the command was queued, ``False`` if safe mode will
            block it.
        """
        return self.set_heater_range(output, 0)

    def open_logger(self, headers):
        """
        Made by Claude. Open the dated log file, working around an unreadable old one.

        ``dated_logger`` reads the day's file as it opens it, so a file that
        ``pandas`` cannot parse -- for instance one whose rows changed width
        partway through -- raises here and, before this, stopped the program
        starting at all.  If that happens the offending file is moved aside
        and opening is tried once more, so the GUI always comes up and
        logging always continues.

        Parameters
        ----------
        headers : list of str
            Column headings to write.

        Returns
        -------
        dated_logger or None
            The open logger, or ``None`` if even a fresh file could not be
            created.
        """
        for attempt in (1, 2):
            try:
                return dated_logger(base_path=self.base_path,
                                    file_name=DATA_FILE_NAME,
                                    file_path=self.base_path + os.sep,
                                    headings=headers)
            except Exception as e:
                print(f"[LOG] could not open the log file: {e}")
                if attempt == 2:
                    print(traceback.format_exc())
                    return None

                # Most likely an existing file that cannot be parsed.  Move
                # it aside, keeping every row, and start a fresh one.
                folder = dated_folder_for(self.base_path,
                                          datetime.date.today())
                path = os.path.join(folder, DATA_FILE_NAME)
                if os.path.isfile(path):
                    stamp = datetime.datetime.now().strftime("%H%M%S")
                    stem, extension = os.path.splitext(DATA_FILE_NAME)
                    moved_to = os.path.join(
                        folder, f"{stem}_unreadable_{stamp}{extension}")
                    try:
                        os.rename(path, moved_to)
                        print(f"[LOG] kept the old file as {moved_to} and "
                              f"started a new one.")
                    except Exception as move_error:
                        print(f"[LOG] could not move it aside: {move_error}")
                        return None

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
        # the base path instead of dropping it in whatever directory the
        # program happened to be launched from.
        os.makedirs(self.base_path, exist_ok=True)

        # Recover recent data before anything is moved or created, so that a
        # file about to be set aside still contributes its readings to the
        # plot.  This reads back across midnight if the window needs it.
        self.data = load_history(self.base_path, DATA_FILE_NAME,
                                 self.history_hours)
        print(f"Recovered {len(self.data)} rows of history.")
        self.revision += 1

        # ``dated_logger`` reads the day's file as it opens it, so a file
        # whose columns do not match the ones about to be written stops the
        # program starting.  Move any such file aside now; see
        # set_aside_mismatched_log.
        today_folder = dated_folder_for(self.base_path, datetime.date.today())
        set_aside_mismatched_log(today_folder, DATA_FILE_NAME, headers)
        # ``logger.__init__`` also drops a throwaway file straight into the
        # base path before the dated folder is worked out, so that one has to
        # be checked too.
        set_aside_mismatched_log(self.base_path, DATA_FILE_NAME, headers)

        temp_logger = self.open_logger(headers)
        if temp_logger is None:
            self.set_status("Could not open the log file -- see the console",
                            False)
            print("Not starting: there is nowhere to write data.")
            self.running = False
            return

        self.log_file_path = os.path.join(temp_logger.file_path,
                                          temp_logger.file_name)
        print("=" * 70)
        print(f"SAVING DATA TO: {self.log_file_path}")
        print("=" * 70)

        current_day = datetime.datetime.now().day
        heater_readings = {}
        cycle = 0

        while self.running:
            # Outer loop: (re)connect to the instrument.
            try:
                print(f"Connecting to Lakeshore 372 at {ADDRESS} ...")
                self.set_status(f"Connecting to {ADDRESS} ...", False)

                # Check the address is really there before opening a session
                # on it.  Opening an address that does not answer has been
                # seen to fault the VISA driver rather than raise, which
                # would take the whole program down instead of landing in
                # the reconnect branch below.
                if not instrument_is_present(ADDRESS):
                    raise ConnectionError(
                        f"no instrument answering at {ADDRESS}")

                with Fridge_Controller(ADDRESS) as instrument:
                    with self.lock:
                        self.idle = False
                        try:
                            self.instrument = instrument
                            # Ask what units the heaters report their levels
                            # in, so the GUI and the log describe the numbers
                            # correctly.  Done before anything is logged.
                            self.read_heater_units()
                            # Check the instrument is set up the way this
                            # file assumes before any of it is believed.
                            # Reports only; changes nothing.
                            self.setup_problems = self.check_instrument_agrees()
                            # Without autoscan the instrument holds one
                            # channel and every other thermometer's reading
                            # stays frozen at whatever it last was, which
                            # looks like the other channels having failed.
                            # Turn it on and apply the configured dwell
                            # time, so all of them are read.
                            self.start_scanning()
                        finally:
                            self.idle = True
                    print("Connected.")
                    self.set_status(f"Connected to {ADDRESS}", True)

                    while self.running:
                        # A modal dialog is open on the main thread.  Do not
                        # touch the instrument until it closes; see
                        # Worker.paused.
                        while self.paused and self.running:
                            time.sleep(0.05)
                        if not self.running:
                            break

                        cycle += 1
                        current_time = time.time()

                        # The log file rolls over at midnight, but the plot
                        # history is not cleared with it: a window showing
                        # the last 24 h should still show them at 00:01.
                        # Old rows fall out of the plot on age alone, and
                        # trim_history keeps the list from growing forever.
                        if current_day != datetime.datetime.now().day:
                            current_day = datetime.datetime.now().day
                            print("Past midnight: continuing into a new "
                                  "log file.")

                        # The log needs a new file: either the GUI has
                        # pointed it at a different folder, or the heater
                        # units changed and its headings are now stale.
                        if self.restart_logger:
                            self.restart_logger = False
                            headers = self.build_headers()
                            new_logger = self.open_logger(headers)
                            if new_logger is None:
                                print("Kept writing to the previous file.")
                            else:
                                temp_logger = new_logger
                                self.log_file_path = os.path.join(
                                    temp_logger.file_path,
                                    temp_logger.file_name)
                                print(f"Now saving to: {self.log_file_path}")

                        with self.lock:
                            # Everything between here and the end of this
                            # block talks to the instrument, so a dialog must
                            # not open during it.  See pause_polling.
                            self.idle = False
                            try:
                                # Anything the GUI has asked for goes first,
                                # so a setting change lands promptly and the
                                # readings taken afterwards already reflect
                                # it.
                                self.run_pending_commands()
                                readings = self.poll_thermometers()
                                # Heater state changes slowly and is slow to
                                # query, so reuse the last values in between,
                                # unless the GUI has just changed something.
                                if (cycle % HEATER_POLL_EVERY == 1
                                        or not heater_readings
                                        or self.force_heater_poll):
                                    heater_readings = self.poll_heaters()
                                    self.force_heater_poll = False
                            finally:
                                self.idle = True

                        readings.update(heater_readings)
                        with self.data_lock:
                            self.latest = readings

                        # See whether the S21 computer has asked for a new
                        # setpoint, and tell it what the fridge is doing.
                        # Outside the instrument lock: this touches only a
                        # file on disk, and any command it raises is queued
                        # for the next cycle rather than sent from here.
                        self.check_remote_control(readings)

                        # Tell the user whether the instrument is actually
                        # answering, so a blank plot is never a mystery.
                        live = sum(1 for channel in THERMOMETERS
                                   if not np.isnan(readings.get(f"T_ch{channel}",
                                                                float('nan'))))
                        if live == 0:
                            self.set_status(
                                "Connected, but NO thermometer is responding", False)
                        else:
                            self.set_status(
                                f"Reading {live} of {len(THERMOMETERS)} thermometers "
                                f"| row {len(self.data) + 1}", True)

                        # Write and flush immediately: a crash costs at most
                        # the reading currently in progress.
                        temp_logger(self.build_log_row(current_time, readings))
                        # The logger rolls over at midnight, so pick up the
                        # new path when it does.
                        self.log_file_path = os.path.join(
                            temp_logger.file_path, temp_logger.file_name)

                        with self.data_lock:
                            self.data.append(
                                [current_time]
                                + [readings.get(key, float('nan'))
                                   for key in plot_column_keys()])

                            # Rebuilding the list is not free, so do it
                            # rarely.
                            if cycle % 600 == 0:
                                self.trim_history()

                            self.revision += 1

                        time.sleep(self.sample_interval)

            except KeyboardInterrupt:
                print("Monitor stopped by user.")
                self.running = False

            except Exception as e:
                print(f"[CONNECTION FAIL] {e}")
                print(traceback.format_exc())
                with self.lock:
                    self.instrument = None
                if self.running:
                    self.set_status(
                        f"NOT CONNECTED ({e}) -- retrying in "
                        f"{RECONNECT_INTERVAL:g} s", False)
                    print(f"Retrying in {RECONNECT_INTERVAL:g} s.  "
                          f"Logging will resume automatically.")
                    # Sleep in short steps so that closing the window does
                    # not have to wait out the whole delay.
                    waited = 0.0
                    while self.running and waited < RECONNECT_INTERVAL:
                        time.sleep(0.25)
                        waited += 0.25

            finally:
                with self.lock:
                    self.instrument = None

        print("Monitor finished.")
        self.set_status("Monitor stopped", False)


# %%

class WorkerThread(QThread):
    """
    Made by Claude. Qt-owned thread that runs the :class:`Worker` polling loop.

    The loop itself is ordinary Python and could run on any thread, but it
    has to be one Qt knows about.  On this machine, GPIB traffic from a plain
    ``threading.Thread`` while a modal dialog runs its own event loop on the
    main thread faults the VISA driver and takes the program down -- usually
    reported against an innocent line some way after the call that really did
    it.  Running the same loop on a ``QThread`` gives Qt the thread affinity
    it expects and avoids that.

    Parameters
    ----------
    worker : Worker
        The polling worker whose :meth:`~Worker.run` this thread executes.
    parent : QObject, optional
        Parent object.
    """

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker

    def run(self):
        """
        Made by Claude. Run the worker's polling loop until it stops.

        Returns
        -------
        None
        """
        self.worker.run()


def date_formatter(val, pos):
    """Made by Claude. Format an x-axis tick, given as a unix timestamp, as a clock time."""
    try:
        return datetime.datetime.fromtimestamp(val).strftime('%H:%M:%S')
    except Exception:
        return ""


#: Most points drawn per trace.
#:
#: A day of half-second samples is about 170,000 points, and matplotlib
#: becomes unusably slow well before that.  The history is always kept in
#: full; only what is drawn is thinned, so zooming with the toolbar still
#: shows real samples rather than an approximation of them.
MAX_PLOTTED_POINTS = 2000


def downsample(values, limit=MAX_PLOTTED_POINTS):
    """
    Made by Claude. Thin an array down to at most ``limit`` points for display.

    Takes evenly spaced samples rather than averaging, so every drawn point
    is a real measurement and a spike is never smeared into its neighbours.

    Parameters
    ----------
    values : numpy.ndarray
        Array to thin, indexed along its last axis.
    limit : int, optional
        Maximum number of points to keep.

    Returns
    -------
    numpy.ndarray
        The thinned array, or the original if it was already short enough.
    """
    if values.shape[-1] <= limit:
        return values
    step = int(np.ceil(values.shape[-1] / limit))
    return values[..., ::step]


class MplCanvas(FigureCanvas):
    """
    Made by Claude. Matplotlib canvas showing one temperature-versus-time panel per thermometer.

    Three stacked axes, one for each thermometer, in channel order.  The
    channel-2 panel is labelled UNCALIBRATED because that thermometer has
    no calibration curve loaded yet.

    The panel of whichever thermometer the sample heater's PID is regulating
    against carries one extra axis on the right: the sample heater's own
    output level, as the instrument reports it.  It moves to another panel if
    the PID reference is changed, so the panel showing the control loop is
    always the one being controlled.
    """

    def __init__(self, parent=None, width=20, height=10, dpi=100):
        try:
            channels = sorted(THERMOMETERS.keys())
            fig, axes = plt.subplots(len(channels), figsize=(width, height), sharex=True)
            super(MplCanvas, self).__init__(fig)
            self.setParent(parent)

            self.figure_handle = fig
            self.axes = {}
            self.lines = {}
            #: Right-hand heater-output axis, created on demand for the PID
            #: reference panel only.
            self.heater_axes = {}
            self.heater_lines = {}
            #: Channel whose panel currently carries the heater axis.
            self.heater_channel = None

            colours = {2: 'g', 3: 'b', 4: 'r'}

            for ax, channel in zip(axes, channels):
                info = THERMOMETERS[channel]
                label = info["label"]
                if not info["calibrated"]:
                    label += "  --  UNCALIBRATED"

                # No marker: at half-second sampling the markers merge into
                # a solid band and hide the trace.
                line, = ax.plot([], [], '-', color=colours.get(channel, 'k'),
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

    def set_heater_panel(self, channel):
        """
        Made by Claude. Put the heater-output axis on one thermometer's panel.

        Called with the channel the sample heater's PID is regulating
        against.  An axis already on another panel is removed first, so only
        the controlled thermometer ever carries it.

        The quantity plotted is the sample heater's output level as reported
        by ``HTR?`` -- the instrument's own figure for what the loop is
        driving, in the units it is set to use.  It is shown against the
        thermometer being regulated because the pair together are the control
        loop: the temperature it achieved, and the effort it took.

        Parameters
        ----------
        channel : int
            Thermometer channel that the PID controls on.

        Returns
        -------
        None
        """
        if channel == self.heater_channel:
            return

        try:
            # Take the axis off whichever panel had it before.
            for old in list(self.heater_axes):
                self.heater_axes.pop(old).remove()
                self.heater_lines.pop(old, None)

            if channel not in self.axes:
                self.heater_channel = None
                return

            units = HEATER_LEVEL_UNITS.get(0, "%")
            name = HEATERS[0]["name"] if 0 in HEATERS else "Sample heater"

            axis = self.axes[channel].twinx()
            axis.set_ylabel(f'{name} output [{units}]', color='#b06000')
            axis.tick_params(axis='y', labelcolor='#b06000')
            line, = axis.plot([], [], '-', color='#b06000', alpha=0.7,
                              label=f'{name} output [{units}]')

            self.heater_axes[channel] = axis
            self.heater_lines[channel] = line
            self.heater_channel = channel

            self.figure_handle.tight_layout()

        except Exception as e:
            print(f"Could not put the heater axis on channel {channel}.")
            print(e)
            print(traceback.format_exc())

    def update_plot(self, data, last_n_hours=None):
        """
        Made by Claude. Redraw every panel with new data.

        Parameters
        ----------
        data : list of list
            Rows of ``[time] + values for plot_column_keys()``.  NaN entries
            appear as gaps in the trace rather than breaking the plot.
        last_n_hours : float, optional
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

        plotable_data = downsample(np.array(data, dtype=float).T)
        time_data = plotable_data[0]

        channels = sorted(THERMOMETERS.keys())
        keys = plot_column_keys()

        for index, channel in enumerate(channels):
            self.lines[channel].set_data(time_data, plotable_data[index + 1])
            self.axes[channel].relim()
            self.axes[channel].autoscale_view()

        # Heater output, on the PID reference panel only.
        channel = self.heater_channel
        if channel is not None and "HTR_out0" in keys:
            heater_row = keys.index("HTR_out0") + 1
            self.heater_lines[channel].set_data(
                time_data, plotable_data[heater_row])
            self.heater_axes[channel].relim()
            self.heater_axes[channel].autoscale_view()

        self.draw()


# %%

class PlaceholderInput(QLineEdit):
    """
    Made by Claude. Line edit that shows the instrument's current value in grey.

    The value read back from the Lakeshore is shown as grey placeholder text.
    Typing replaces it with ordinary black text; clearing the box brings the
    grey value back.  An empty box therefore means "leave this setting as it
    is", which is what makes it safe to apply a form in which only one field
    was filled in.

    Parameters
    ----------
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        #: Last value read from the instrument, shown as the placeholder.
        self.instrument_value = None

    def show_instrument_value(self, value, decimals=3):
        """
        Made by Claude. Show a value read from the instrument as grey placeholder text.

        Parameters
        ----------
        value : float
            The instrument's current value, or ``numpy.nan`` if unreadable.
        decimals : int, optional
            Decimal places to display.  Default 3.

        Returns
        -------
        None
        """
        if value is None or (isinstance(value, float) and np.isnan(value)):
            self.setPlaceholderText(NOT_READING)
            self.instrument_value = None
            return

        self.instrument_value = value
        self.setPlaceholderText(f"{value:.{decimals}f}")

    def entered_value(self):
        """
        Made by Claude. Return the number typed into the box, if any.

        Returns
        -------
        float or None
            The typed value, or ``None`` if the box is empty -- meaning the
            setting should be left unchanged.

        Raises
        ------
        ValueError
            If the box holds something that is not a number.
        """
        text = self.text().strip()
        if not text:
            return None
        return float(text)


class HeaterControlGroup(QGroupBox):
    """
    Made by Claude. Group box holding the readout and control boxes for one heater output.

    The two heaters are different instruments and are shown differently.  The
    sample heater is a closed-loop controller, so it gets a setpoint, a PID
    reference thermometer, P, I, D and a range.  The still heater is held at
    a constant level, so it gets only an output level -- it has no target
    temperature to chase -- alongside a readback of what its output is
    actually delivering, which is a different number whenever its range is
    off.  Which of the two is built is decided by the ``closed_loop`` flag
    in :data:`HEATERS`, not by the output number.

    Every editable box shows the instrument's current value as grey
    placeholder text.  Typing over it sets a new value; leaving it empty
    leaves that setting untouched when "Apply to instrument" is pressed.
    Nothing here talks to the instrument by itself, and even Apply does
    nothing while :data:`SAFE_MODE` is on.

    Parameters
    ----------
    output : int
        Lakeshore heater output number.
    worker : Worker
        The polling worker, used to send settings.
    parent : QWidget, optional
        Parent widget.
    """

    #: Emitted with the channel number when the PID reference is applied, so
    #: the plot can move its voltage axes to the newly controlled panel.
    pid_reference_changed = pyqtSignal(int)

    def __init__(self, output, worker, parent=None):
        info = HEATERS[output]
        title = f"{info['name']}  (output {output})"
        if not info["closed_loop"]:
            title += "  --  still mode, no target temperature"
        super().__init__(title, parent)

        self.output = output
        self.worker = worker
        self.closed_loop = info["closed_loop"]
        #: Units the instrument reports and accepts this heater's level in.
        #: Read from the instrument on the first heater poll, because it is
        #: a setting on the instrument (``HTRSET``, manual p.155) rather
        #: than something this program chooses.  Labelled provisionally
        #: until then.
        self.units = HEATER_LEVEL_UNITS.get(output, "%")

        layout = QVBoxLayout()

        # --- live readback, not editable -----------------------------------
        # Only quantities that cannot be typed into are shown as labels;
        # everything settable shows its value greyed inside its own box, so
        # nothing is written out twice.
        #
        # The heater's own output level is reported by the instrument and is
        # shown with the other settings below.  The only thing here is the
        # voltage, which the 372 does not report for a heater and so has to
        # be worked out from the level, the range and the heater resistance
        # -- hence the label saying so.
        readback_layout = QFormLayout()
        self.voltage_readback = QLabel("N/A")
        readback_layout.addRow("Voltage across heater [V]:",
                               self.voltage_readback)

        readback_box = QGroupBox("Calculated, not measured")
        readback_box.setLayout(readback_layout)
        layout.addWidget(readback_box)

        # The still's level and what the output is actually delivering are
        # two different numbers, and they disagree whenever the range is off.
        # Showing only the level would make a switched-off still look as
        # though it were running.
        self.analog_readback = None
        if not info["closed_loop"]:
            delivered_layout = QFormLayout()
            self.analog_readback = QLabel("N/A")
            delivered_layout.addRow("Analog output now [%]:",
                                    self.analog_readback)
            delivered_box = QGroupBox("Being delivered (AOUT?)")
            delivered_box.setLayout(delivered_layout)
            layout.addWidget(delivered_box)

        # --- editable settings ---------------------------------------------
        # Kept as an attribute so that the level row can be relabelled once
        # the instrument has said what units it uses; see relabel_units.
        self.settings_form = settings_layout = QFormLayout()

        if self.closed_loop:
            # The setpoint is the one number that matters here, so it comes
            # first and drives the defaults for everything below it.
            self.setpoint_input = PlaceholderInput(self)
            settings_layout.addRow("Setpoint [K]:", self.setpoint_input)

            # Which thermometer the loop regulates against.
            self.reference_input = QComboBox(self)
            for channel in sorted(THERMOMETERS):
                label = THERMOMETERS[channel]["label"]
                if not THERMOMETERS[channel]["calibrated"]:
                    label += "  [UNCALIBRATED]"
                self.reference_input.addItem(label, channel)
            index = self.reference_input.findData(info["control_channel"])
            if index >= 0:
                self.reference_input.setCurrentIndex(index)
            settings_layout.addRow("PID reference:", self.reference_input)

            self.p_input = PlaceholderInput(self)
            self.i_input = PlaceholderInput(self)
            self.d_input = PlaceholderInput(self)
            self.range_input = PlaceholderInput(self)
            settings_layout.addRow("P:", self.p_input)
            settings_layout.addRow("I:", self.i_input)
            settings_layout.addRow("D:", self.d_input)
            settings_layout.addRow("Range (0-8):", self.range_input)

            # In closed loop the manual output is not the output: the
            # instrument adds it to whatever the PID computes (manual
            # p.162).  Changing it here would bias the loop rather than set
            # its level, so it is shown but not editable.
            self.output_readback = QLabel("N/A")
            settings_layout.addRow(f"Level, set by the PID [{self.units}]:",
                                   self.output_readback)

            # Typing a setpoint fills the tuning below it from the defaults
            # table, so there is one number to think about rather than five.
            self.setpoint_input.editingFinished.connect(
                self.fill_defaults_from_setpoint)
        else:
            # Still mode, so the level really is the output and can be set.
            #
            # No range box: for the analog output "range" is only 0 = off
            # and 1 = on (manual p.165), which is what the on/off control
            # below already does.  A box as well would be two controls for
            # one setting.
            self.output_input = PlaceholderInput(self)
            settings_layout.addRow(f"Level [{self.units}]:", self.output_input)

        settings_box = QGroupBox("Settings to send")
        settings_box.setLayout(settings_layout)
        layout.addWidget(settings_box)

        hint_text = ("Grey shows what the Lakeshore is set to now.  Type "
                     "over a box to change it; leave it empty to keep it.")
        if self.closed_loop:
            hint_text += ("\n\nThe level is set by the PID loop, so it is "
                          "shown but cannot be typed into.  The voltage is "
                          "worked out from the level, the range and the "
                          "heater resistance; the Lakeshore does not measure "
                          "it.")
        else:
            hint_text += ("\n\nThe voltage is worked out from the level and "
                          "the heater resistance; the Lakeshore does not "
                          "measure it.")
        hint = QLabel(hint_text)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: grey; font-size: 10px;")
        layout.addWidget(hint)

        # --- on / off -------------------------------------------------------
        # Two halves of one control rather than a lone "off" button: the lit
        # half is the state the heater is actually in, read back from the
        # instrument, so the panel always shows whether the heater is
        # running rather than only offering a way to stop it.
        power_layout = QHBoxLayout()
        power_layout.setSpacing(0)
        self.on_button = QPushButton("ON", self)
        self.off_button = QPushButton("OFF", self)
        for button in (self.on_button, self.off_button):
            button.setCheckable(True)
            button.setMinimumHeight(30)
            power_layout.addWidget(button)
        layout.addLayout(power_layout)

        self.on_button.clicked.connect(self.switch_on)
        self.off_button.clicked.connect(self.switch_off)
        # Nothing is known until the first readback arrives.
        self.show_power_state(None)

        # --- buttons --------------------------------------------------------
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply to instrument", self)
        self.clear_button = QPushButton("Clear boxes", self)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)

        self.apply_button.clicked.connect(self.apply_settings)
        self.clear_button.clicked.connect(self.clear_inputs)

        # Where this heater's actions report back; see report().
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: grey; font-size: 10px;")
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    # --- display -----------------------------------------------------------

    def update_readbacks(self, readings):
        """
        Made by Claude. Refresh the read-only labels and the grey placeholders.

        Parameters
        ----------
        readings : dict
            Latest readings as produced by :meth:`Worker.poll_heaters`.

        Returns
        -------
        None
        """
        output = self.output

        def show(key, decimals=3, exponential=False):
            value = readings.get(key)
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return NOT_READING
            if exponential:
                return f"{value:.{decimals}e}"
            return f"{value:.{decimals}f}"

        # The instrument reports the level itself, so the only calculated
        # figure shown is the voltage, which it does not report.
        self.voltage_readback.setText(show(f"VOLT_out{output}", 4))

        # The lit half of the on/off control is the instrument's own state,
        # so a heater switched off by the instrument shows as off here.
        heater_range = readings.get(f"RANGE_out{output}")
        self.show_power_state(heater_range)

        # The instrument's own units, which it was asked for on connection.
        self.relabel_units()

        if not self.closed_loop:
            # No range box: for the analog output the range is only on or
            # off, which the control above already shows.
            self.output_input.show_instrument_value(
                readings.get(f"HTR_out{output}"), 3)
            if self.analog_readback is not None:
                self.analog_readback.setText(show(f"AOUT_out{output}", 3))
            return

        # Grey placeholders track the instrument, so a box the user has not
        # typed in always shows what is really set.
        self.range_input.show_instrument_value(heater_range, 0)

        # Closed loop: the level is the PID's doing, so it is shown but not
        # editable.  See the note in __init__.
        self.output_readback.setText(show(f"HTR_out{output}", 3))

        self.setpoint_input.show_instrument_value(
            readings.get(f"SETP_out{output}"), 6)
        self.p_input.show_instrument_value(readings.get(f"P_out{output}"), 2)
        self.i_input.show_instrument_value(readings.get(f"I_out{output}"), 2)
        self.d_input.show_instrument_value(readings.get(f"D_out{output}"), 2)

        # Keep the PID reference dropdown showing what the instrument is
        # really controlling on, unless the user is part-way through
        # changing it.
        channel = readings.get(f"CTRLCH_out{output}")
        if channel is not None and not np.isnan(channel):
            index = self.reference_input.findData(int(channel))
            if index >= 0 and not self.reference_input.hasFocus():
                self.reference_input.setCurrentIndex(index)

    def relabel_units(self):
        """
        Made by Claude. Relabel the level row once the instrument's units are known.

        The units are a setting on the instrument, read on connection, so
        the label built before connecting may be wrong.  This corrects it,
        and does nothing on the usual case where it was already right.

        Returns
        -------
        None
        """
        units = HEATER_LEVEL_UNITS.get(self.output, "%")
        if units == self.units:
            return
        self.units = units

        widget = (self.output_readback if self.closed_loop
                  else self.output_input)
        form = self.settings_form
        if form is None:
            return
        label = form.labelForField(widget)
        if label is not None:
            label.setText(f"Level, set by the PID [{units}]:"
                          if self.closed_loop else f"Level [{units}]:")

    def fill_defaults_from_setpoint(self):
        """
        Made by Claude. Fill the tuning boxes from the defaults table for the typed setpoint.

        Runs when a setpoint is typed.  Only the boxes are changed; nothing
        is sent to the instrument, and every value can be edited afterwards
        before applying.

        Returns
        -------
        None
        """
        try:
            setpoint = self.setpoint_input.entered_value()
        except ValueError:
            return
        if setpoint is None:
            return

        defaults = default_settings_for(self.output, setpoint)
        if defaults is None:
            return

        p, i, d, heater_range = defaults
        self.p_input.setText(str(p))
        self.i_input.setText(str(i))
        self.d_input.setText(str(d))
        self.range_input.setText(str(heater_range))

        print(f"{HEATERS[self.output]['name']}: loaded defaults for "
              f"{setpoint} K -- P={p}, I={i}, D={d}, range={heater_range}. "
              f"Nothing sent to the instrument yet.")

    def clear_inputs(self):
        """
        Made by Claude. Empty every editable box, so nothing would be changed on Apply.

        Returns
        -------
        None
        """
        if self.closed_loop:
            boxes = [self.setpoint_input, self.p_input, self.i_input,
                     self.d_input, self.range_input]
        else:
            boxes = [self.output_input]

        for box in boxes:
            box.clear()

    # --- control ------------------------------------------------------------

    def read_inputs(self):
        """
        Made by Claude. Collect the settings the user has actually typed in.

        Boxes left empty are omitted, so they are left unchanged on the
        instrument.

        Returns
        -------
        dict or None
            The settings to send, or ``None`` if a box holds something that
            is not a number.
        """
        settings = {}
        try:
            if self.closed_loop:
                for name, box in (("setpoint", self.setpoint_input),
                                  ("p", self.p_input),
                                  ("i", self.i_input),
                                  ("d", self.d_input)):
                    value = box.entered_value()
                    if value is not None:
                        settings[name] = value

                # The reference dropdown always has a selection, so it is
                # always sent; it is only ever changed deliberately.
                settings["control_channel"] = self.reference_input.currentData()

                heater_range = self.range_input.entered_value()
                if heater_range is not None:
                    settings["range"] = int(heater_range)
            else:
                # The still heater has no range box: its range is only on or
                # off, and the on/off control handles that.
                value = self.output_input.entered_value()
                if value is not None:
                    settings["output"] = value

        except ValueError:
            self.report(
                "Enter a valid number, or leave the box empty to keep the "
                "value that is already set.", healthy=False)
            return None

        return settings

    def apply_settings(self):
        """
        Made by Claude. Send whatever the user has typed to the instrument.

        Blocked by :data:`SAFE_MODE`, in which case the user is told what
        would have been sent instead.

        Returns
        -------
        None
        """
        settings = self.read_inputs()
        if settings is None:
            return

        # A form with nothing but the (always present) reference in it would
        # otherwise silently re-apply the output mode for no reason.
        changes = {key: value for key, value in settings.items()
                   if key != "control_channel"}
        if not changes and self.closed_loop:
            reference = settings["control_channel"]
            if reference == HEATERS[self.output]["control_channel"]:
                self.report(
                    "Every box is empty, so there is nothing to change.  "
                    "Type a value over a grey number first.", healthy=False)
                return

        name = HEATERS[self.output]['name']
        sent = self.worker.apply_heater_settings(self.output, settings)

        if self.closed_loop and "control_channel" in settings:
            self.pid_reference_changed.emit(settings["control_channel"])

        described = ", ".join(f"{key} = {value}"
                              for key, value in settings.items())
        if sent:
            self.report(f"{name}: {described}.", healthy=True)
            self.clear_inputs()
        else:
            self.report(
                f"SAFE_MODE is on, so nothing was sent.  Would have set "
                f"{described} -- see the console.", healthy=False)

    def show_power_state(self, heater_range):
        """
        Made by Claude. Light the half of the on/off control matching the heater's state.

        The lit half is the state the instrument is actually in, not the
        last button pressed, so a heater switched off by the instrument
        itself -- a temperature limit, say -- shows as off here too.

        Parameters
        ----------
        heater_range : float or None
            The heater's range as read back.  ``0`` is off, anything higher
            is on, and ``None`` (or NaN) means it is not known yet.

        Returns
        -------
        None
        """
        lit = "font-weight: bold; color: white; background-color: {};"
        unlit = "color: #606060;"

        if heater_range is None or (isinstance(heater_range, float)
                                    and np.isnan(heater_range)):
            self.on_button.setChecked(False)
            self.off_button.setChecked(False)
            self.on_button.setStyleSheet(unlit)
            self.off_button.setStyleSheet(unlit)
            return

        is_on = int(heater_range) > 0
        self.on_button.setChecked(is_on)
        self.off_button.setChecked(not is_on)
        self.on_button.setStyleSheet(
            lit.format("#006000") if is_on else unlit)
        self.off_button.setStyleSheet(
            unlit if is_on else lit.format("#b00000"))

    def switch_on(self):
        """
        Made by Claude. Switch this heater on.

        For the still heater "on" is simply range 1.  For the sample heater
        it means choosing one of the eight current ranges, so the range in
        the box is used; if that box is empty the heater is left alone
        rather than guessing at a power level to apply to the fridge.

        Returns
        -------
        None
        """
        name = HEATERS[self.output]['name']

        if self.closed_loop:
            try:
                heater_range = self.range_input.entered_value()
            except ValueError:
                self.report(f"{name}: the range box does not hold a number.",
                            healthy=False)
                return

            if heater_range is None:
                # The grey placeholder is the instrument's current range,
                # which is 0 when the heater is off -- so there is genuinely
                # nothing to turn on to.
                self.report(
                    f"{name}: type a range (1-8) before switching it on, so "
                    f"it is clear how much power is being asked for.",
                    healthy=False)
                return

            heater_range = int(heater_range)
            if not 1 <= heater_range <= 8:
                self.report(f"{name}: the range must be between 1 and 8.",
                            healthy=False)
                return
        else:
            # The analog output is simply on or off (manual p.165).
            heater_range = 1

        sent = self.worker.set_heater_range(self.output, heater_range)
        if sent:
            self.report(f"{name}: switching on at range {heater_range}.",
                        healthy=True)
        else:
            self.report(
                f"SAFE_MODE is on, so {name} was not switched on.  The "
                f"command is printed in the console.", healthy=False)

    def switch_off(self):
        """
        Made by Claude. Switch this heater off by setting its range to zero.

        Returns
        -------
        None
        """
        name = HEATERS[self.output]['name']
        sent = self.worker.turn_heater_off(self.output)
        if sent:
            self.report(f"{name}: switching off.", healthy=True)
        else:
            self.report(
                f"SAFE_MODE is on, so {name} was not switched off.  The "
                f"command is printed in the console.", healthy=False)

    def report(self, message, healthy=True):
        """
        Made by Claude. Show the outcome of an action under this heater's controls.

        A label rather than a dialog: a modal dialog runs its own event loop
        on the main thread, which on this machine can fault the VISA driver
        while the polling thread is talking to the instrument.

        Parameters
        ----------
        message : str
            What happened.
        healthy : bool, optional
            ``True`` if the action was carried out, ``False`` if it was
            refused.  Only affects the colour.

        Returns
        -------
        None
        """
        self.message_label.setText(message)
        colour = "#006000" if healthy else "#b00000"
        self.message_label.setStyleSheet(f"color: {colour}; font-size: 10px;")
        print(message)


# %%

#: Fixed steps offered by the history slider, in hours.
#:
#: Fine near the left-hand end, where a few minutes of detail is what matters
#: while a setpoint settles, and coarse towards the right, where the question
#: is the shape of a whole cooldown.  A value outside this list can still be
#: typed into the box beside the slider.
HISTORY_STEPS = [1 / 60, 5 / 60, 15 / 60, 30 / 60, 45 / 60,
                 1, 1.5, 2, 3, 4, 6, 8, 12, 18, 24]

#: Which of :data:`HISTORY_STEPS` the slider starts on (1 hour).
DEFAULT_HISTORY_INDEX = 5


def describe_hours(hours):
    """
    Made by Claude. Put a span of hours into words for the history label.

    Parameters
    ----------
    hours : float
        A span in hours.

    Returns
    -------
    str
        A short description such as ``"15 min"``, ``"1 h 30 min"`` or
        ``"24 h"``.
    """
    minutes = hours * 60
    if minutes < 60:
        return f"{minutes:g} min"
    whole_hours = int(minutes // 60)
    remainder = int(round(minutes - whole_hours * 60))
    if remainder:
        return f"{whole_hours} h {remainder} min"
    return f"{whole_hours} h"


class SettingsPanel(QGroupBox):
    """
    Made by Claude. Collapsible panel holding the settings that are set once and left alone.

    The log-file location and the measurement timing belong here rather than
    beside the heater controls: they are changed rarely, and putting them in
    the main column would crowd out the readings that are looked at
    constantly.  Each button opens its own page, so only one set of settings
    is on screen at a time.

    Parameters
    ----------
    worker : Worker
        The polling worker whose settings these are.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(self, worker, parent=None):
        super().__init__("Settings", parent)
        self.worker = worker

        layout = QVBoxLayout()

        # --- the buttons that choose a page --------------------------------
        # Stacked rather than side by side: this column is narrow, and two
        # buttons in a row squeeze their labels and the panel's width.
        self.log_button = QPushButton("Log file", self)
        self.thermometer_button = QPushButton("Thermometers", self)
        for button in (self.log_button, self.thermometer_button):
            button.setCheckable(True)
            layout.addWidget(button)

        # --- the pages ------------------------------------------------------
        self.pages = QStackedWidget(self)
        self.pages.addWidget(self.build_log_page())
        self.pages.addWidget(self.build_thermometer_page())
        self.pages.hide()
        layout.addWidget(self.pages)

        self.log_button.clicked.connect(lambda: self.show_page(0))
        self.thermometer_button.clicked.connect(lambda: self.show_page(1))

        # Where settings changes report back.  A label rather than a dialog:
        # see MainWindow.apply_timing for why this program avoids dialogs.
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: grey; font-size: 10px;")
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def report(self, message, healthy=True):
        """
        Made by Claude. Show the outcome of a settings change in the panel.

        Used instead of a message box.  A modal dialog runs its own event
        loop on the main thread, which on this machine can fault the VISA
        driver if the polling thread is talking to the instrument at the
        time; a label carries the same information at no risk.

        Parameters
        ----------
        message : str
            What happened.
        healthy : bool, optional
            ``True`` if the change was applied, ``False`` if it was refused.
            Only affects the colour.

        Returns
        -------
        None
        """
        self.message_label.setText(message)
        colour = "#006000" if healthy else "#b00000"
        self.message_label.setStyleSheet(
            f"color: {colour}; font-size: 10px;")
        print(message)

    def show_page(self, index):
        """
        Made by Claude. Show one settings page, or hide the panel if it was already open.

        Parameters
        ----------
        index : int
            Index of the page in the stack.

        Returns
        -------
        None
        """
        buttons = [self.log_button, self.thermometer_button]

        already_open = self.pages.isVisible() and self.pages.currentIndex() == index
        for position, button in enumerate(buttons):
            button.setChecked(position == index and not already_open)

        if already_open:
            self.pages.hide()
            return

        self.pages.setCurrentIndex(index)
        self.pages.show()

    # --- pages --------------------------------------------------------------

    def build_log_page(self):
        """
        Made by Claude. Build the page showing and changing where data is saved.

        Returns
        -------
        QWidget
            The log-file settings page.
        """
        page = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Where data is being saved</b>"))

        # The live path, shown grey because it is what is in use now.
        self.current_path_label = QLabel("(opening ...)")
        self.current_path_label.setWordWrap(True)
        self.current_path_label.setStyleSheet("color: grey; font-size: 10px;")
        self.current_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.current_path_label)

        form = QFormLayout()
        self.base_path_input = PlaceholderInput(self)
        self.base_path_input.setPlaceholderText(self.worker.base_path)
        form.addRow("Base folder:", self.base_path_input)
        layout.addLayout(form)

        button_layout = QHBoxLayout()
        self.browse_button = QPushButton("Browse ...", self)
        self.apply_path_button = QPushButton("Use this folder", self)
        button_layout.addWidget(self.browse_button)
        button_layout.addWidget(self.apply_path_button)
        layout.addLayout(button_layout)

        note = QLabel("A dated folder (year / month / day) is made inside "
                      "this one, and a new file is started each day.\n"
                      "Changing the folder starts a new file there; data "
                      "already written stays where it is.")
        note.setWordWrap(True)
        note.setStyleSheet("color: grey; font-size: 10px;")
        layout.addWidget(note)

        self.browse_button.clicked.connect(self.browse_for_folder)

        layout.addStretch()
        page.setLayout(layout)
        return page

    def build_thermometer_page(self):
        """
        Made by Claude. Build the page holding the measurement timing settings.

        Returns
        -------
        QWidget
            The thermometer settings page.
        """
        page = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Measurement timing</b>"))

        form = QFormLayout()

        self.sample_interval_input = QDoubleSpinBox(self)
        self.sample_interval_input.setRange(0.1, 60.0)
        self.sample_interval_input.setSingleStep(0.1)
        self.sample_interval_input.setDecimals(1)
        self.sample_interval_input.setSuffix(" s")
        self.sample_interval_input.setValue(self.worker.sample_interval)
        form.addRow("Read every:", self.sample_interval_input)

        low, high = SCAN_DWELL_LIMITS
        self.dwell_input = QSpinBox(self)
        self.dwell_input.setRange(low, high)
        self.dwell_input.setSuffix(" s")
        self.dwell_input.setValue(SCAN_DWELL_SECONDS)
        form.addRow("Change channel every:", self.dwell_input)

        layout.addLayout(form)

        self.apply_timing_button = QPushButton("Apply timing", self)
        layout.addWidget(self.apply_timing_button)

        note = QLabel("'Read every' is how often this program asks the "
                      "Lakeshore for a reading, and so how often a row is "
                      "written.\n\n'Change channel every' is the scanner "
                      "dwell time, which is a setting held on the "
                      "instrument itself.\n\nNote: the dwell time is written "
                      "to the Lakeshore even in safe mode -- it changes "
                      "measurement timing, never heater power.")
        note.setWordWrap(True)
        note.setStyleSheet("color: grey; font-size: 10px;")
        layout.addWidget(note)

        layout.addStretch()
        page.setLayout(layout)
        return page

    # --- slots ---------------------------------------------------------------

    def browse_for_folder(self):
        """
        Made by Claude. Pick the base data folder with a directory chooser.

        Returns
        -------
        None
        """
        folder = QFileDialog.getExistingDirectory(
            self, "Choose the folder to save data in", self.worker.base_path)
        if folder:
            self.base_path_input.setText(os.path.normpath(folder))

    def update_current_path(self, path):
        """
        Made by Claude. Show the file currently being written.

        Parameters
        ----------
        path : str
            Full path of the CSV in use.

        Returns
        -------
        None
        """
        self.current_path_label.setText(path)


class MainWindow(QMainWindow):
    """
    Made by Claude. Main window of the fridge temperature monitor and heater controller.

    Three columns.  On the left, the settings that are configured once -- where
    data is saved, and how fast it is measured -- tucked behind buttons so
    they do not compete for attention with the readings.  In the middle, the
    live thermometer readings and one :class:`HeaterControlGroup` per heater.
    On the right, the plots and the controls choosing how much history they
    show.

    The everyday workflow is to type a setpoint into the sample heater, which
    fills its P, I, D and range from :data:`SAMPLE_HEATER_DEFAULTS` for that
    temperature.  Nothing is sent at that point, so the values can be adjusted
    by hand first.  Only "Apply to instrument" sends anything, and only when
    :data:`SAFE_MODE` is off.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fridge Temperature Control -- Lakeshore 372")
        self.setGeometry(100, 100, 1600, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Worker first: the control widgets need a reference to it.
        self.worker = Worker()
        self.worker.history_hours = HISTORY_STEPS[DEFAULT_HISTORY_INDEX]

        # Let every dialog in the program pause polling while it is open;
        # see pause_polling.
        global ACTIVE_WORKER
        ACTIVE_WORKER = self.worker

        # --- settings column --------------------------------------------------
        self.settings_panel = SettingsPanel(self.worker, self)
        self.settings_panel.setMaximumWidth(360)
        self.settings_panel.apply_path_button.clicked.connect(self.apply_base_path)
        self.settings_panel.apply_timing_button.clicked.connect(self.apply_timing)

        settings_column = QVBoxLayout()
        settings_column.addWidget(self.settings_panel)
        settings_column.addStretch()
        self.settings_column_widget = QWidget()
        self.settings_column_widget.setLayout(settings_column)
        main_layout.addWidget(self.settings_column_widget)

        # --- middle column ----------------------------------------------------
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

        # What the S21 computer has asked for through RemoteControl.txt.  A
        # setpoint can arrive from the other machine without anyone touching
        # this window, so it has to be visible that it did.
        self.remote_label = QLabel("")
        self.remote_label.setAlignment(Qt.AlignCenter)
        self.remote_label.setWordWrap(True)
        self.remote_label.setStyleSheet("color: #404040; font-size: 10px; "
                                        "padding: 2px;")
        self.left_layout.addWidget(self.remote_label)

        # Where the instrument disagrees with this file's assumptions, from
        # the check made on connection.  Hidden while there is nothing to
        # say, so an ordinary start-up looks ordinary.
        self.setup_label = QLabel("")
        self.setup_label.setWordWrap(True)
        self.setup_label.setStyleSheet(
            "color: #b06000; font-size: 10px; padding: 4px; "
            "border: 1px solid #b06000;")
        self.setup_label.hide()
        self.left_layout.addWidget(self.setup_label)

        self.left_layout.addWidget(self.build_thermometer_box())

        self.heater_groups = {}
        for output in HEATERS:
            group = HeaterControlGroup(output, self.worker, self)
            group.pid_reference_changed.connect(self.change_pid_reference)
            self.heater_groups[output] = group
            self.left_layout.addWidget(group)

        self.left_layout.addStretch()

        # --- right column ----------------------------------------------------
        self.right_layout = QVBoxLayout()
        self.right_layout_widget = QWidget()
        self.right_layout_widget.setLayout(self.right_layout)
        main_layout.addWidget(self.right_layout_widget, stretch=1)

        self.canvas = MplCanvas(self, width=20, height=10, dpi=100)

        # The expand button sits at the right-hand end of the plot toolbar
        # rather than in a column of its own between the controls and the
        # plots.  That column cost horizontal space permanently; here the
        # button costs nothing, and hiding the controls gives all of the
        # freed width to the plots.
        toolbar_row = QHBoxLayout()
        toolbar_row.addWidget(NavigationToolbar(self.canvas, self))
        toolbar_row.addStretch()
        self.expand_button = QPushButton("Hide controls", self)
        self.expand_button.setToolTip(
            "Hide the readings and heater controls to give the plots the "
            "whole window")
        self.expand_button.clicked.connect(self.toggle_expand)
        toolbar_row.addWidget(self.expand_button)
        self.right_layout.addLayout(toolbar_row)

        self.right_layout.addWidget(self.canvas)

        self.right_layout.addLayout(self.build_history_controls())

        # Put the heater-output axis on whichever thermometer the PID
        # controls.
        self.canvas.set_heater_panel(
            HEATERS[0]["control_channel"] if 0 in HEATERS else None)

        # --- start the worker -------------------------------------------------
        # Open VISA and scan the bus here, on the main thread, before the
        # polling thread wants either.  See SHARED_RESOURCE_MANAGER and
        # instrument_is_present.
        shared_resource_manager()
        scan_for_instruments()

        # A QThread rather than a plain threading.Thread.  Qt has to know
        # about the thread its own machinery shares a process with: with a
        # plain thread, GPIB traffic overlapping a modal dialog's event loop
        # faults the VISA driver and kills the program.  The worker's code
        # is unchanged -- it is simply moved onto a thread Qt owns.
        self.worker_thread = WorkerThread(self.worker, self)
        self.worker_thread.start()

        #: Revision of the last snapshot drawn, so that nothing is redrawn
        #: unless the worker has actually produced something new.
        self.last_revision = -1

        # The worker cannot safely push to the GUI (see Worker's signals), so
        # the GUI pulls from it on a timer running on the main thread.
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.poll_worker)
        self.refresh_timer.start(int(GUI_REFRESH_INTERVAL * 1000))

        self.setup_menubar()
        self.show()

    # --- widget construction -------------------------------------------------

    def build_history_controls(self):
        """
        Made by Claude. Build the slider and box that choose how much history to plot.

        The slider steps through :data:`HISTORY_STEPS`, from a minute up to a
        day.  The box beside it accepts any number of hours, for the
        occasions when a cooldown needs to be looked at over several days.

        Returns
        -------
        QHBoxLayout
            The assembled controls.
        """
        layout = QHBoxLayout()

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, len(HISTORY_STEPS) - 1)
        self.slider.setValue(DEFAULT_HISTORY_INDEX)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        layout.addWidget(self.slider, stretch=1)

        self.slider_label = QLabel("", self)
        self.slider_label.setAlignment(Qt.AlignCenter)
        self.slider_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.slider_label.setMinimumWidth(160)
        layout.addWidget(self.slider_label)

        layout.addWidget(QLabel("or exactly:"))
        self.history_input = QDoubleSpinBox(self)
        self.history_input.setRange(0.01, 8760.0)
        self.history_input.setDecimals(2)
        self.history_input.setSingleStep(1.0)
        self.history_input.setSuffix(" h")
        self.history_input.setValue(HISTORY_STEPS[DEFAULT_HISTORY_INDEX])
        layout.addWidget(self.history_input)

        self.apply_history_button = QPushButton("Show", self)
        layout.addWidget(self.apply_history_button)

        self.slider.valueChanged.connect(self.history_step_changed)
        self.apply_history_button.clicked.connect(self.history_box_changed)

        self.update_history_label()
        return layout

    def build_thermometer_box(self):
        """
        Made by Claude. Build the group box showing the live thermometer readings.

        Returns
        -------
        QGroupBox
            A box with one row per thermometer, showing temperature,
            resistance, excitation power and sensor voltage.
        """
        box = QGroupBox("Thermometers")
        grid = QGridLayout()

        grid.addWidget(QLabel("<b>Sensor</b>"), 0, 0)
        grid.addWidget(QLabel("<b>T [K]</b>"), 0, 1)
        grid.addWidget(QLabel("<b>R [Ohm]</b>"), 0, 2)
        grid.addWidget(QLabel("<b>Excitation [W]</b>"), 0, 3)
        grid.addWidget(QLabel("<b>Status</b>"), 0, 4)

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
            live_label = QLabel("")

            grid.addWidget(name_label, row, 0)
            grid.addWidget(t_label, row, 1)
            grid.addWidget(r_label, row, 2)
            grid.addWidget(p_label, row, 3)
            grid.addWidget(live_label, row, 4)

            self.thermometer_labels[channel] = (t_label, r_label, p_label,
                                                live_label)

        note = QLabel("The Lakeshore measures one channel at a time.  "
                      "'held' means that row is the last value seen, not a "
                      "new measurement.")
        note.setWordWrap(True)
        note.setStyleSheet("color: grey; font-size: 10px;")
        grid.addWidget(note, len(THERMOMETERS) + 1, 0, 1, 5)

        box.setLayout(grid)
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

    def poll_worker(self):
        """
        Made by Claude. Take the worker's latest state and put it on screen.

        Runs on the main thread, driven by :attr:`refresh_timer`.  This is
        how everything the worker produces reaches the GUI: the worker never
        touches a widget or emits a signal itself, because it runs on a plain
        thread where doing either is unsafe.

        Returns
        -------
        None
        """
        try:
            state = self.worker.snapshot()

            message, healthy = state["status"]
            self.update_status(message, healthy, state["log_file_path"])

            remote = state.get("remote_status", "")
            if remote and self.remote_label.text() != remote:
                self.remote_label.setText(remote)

            problems = state.get("setup_problems", [])
            if problems:
                text = ("The Lakeshore is not set up the way this program "
                        "assumes.  Nothing has been changed on it.\n- "
                        + "\n- ".join(problems))
                if self.setup_label.text() != text:
                    self.setup_label.setText(text)
                    self.setup_label.show()
            elif self.setup_label.isVisible():
                self.setup_label.hide()

            # Nothing new since the last look, so there is nothing to redraw.
            if state["revision"] == self.last_revision:
                return
            self.last_revision = state["revision"]

            if state["latest"]:
                self.update_readings(state["latest"])
            self.update_plot(state["data"])

        except Exception as e:
            # A failure here must not stop the timer, or the window freezes.
            print(f"[GUI] refresh failed: {e}")
            print(traceback.format_exc())

    def change_pid_reference(self, channel):
        """
        Made by Claude. Move the plot's heater axis to a newly chosen PID reference.

        Parameters
        ----------
        channel : int
            Thermometer channel the sample heater now controls on.

        Returns
        -------
        None
        """
        self.canvas.set_heater_panel(channel)
        self.update_plot(self.worker.data)

    def apply_base_path(self):
        """
        Made by Claude. Change the folder new data is written to.

        The change takes effect on the next daily roll-over or restart; data
        already written is left where it is.

        Returns
        -------
        None
        """
        path = self.settings_panel.base_path_input.text().strip()
        if not path:
            self.settings_panel.report(
                "Type a folder, or press Browse, before applying.",
                healthy=False)
            return

        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            self.settings_panel.report(
                f"{path} could not be created or opened: {e}", healthy=False)
            return

        self.worker.base_path = path
        self.worker.restart_logger = True
        self.settings_panel.base_path_input.clear()
        self.settings_panel.base_path_input.setPlaceholderText(path)

        self.settings_panel.report(
            f"New data will be written under {path}.  Data already saved "
            f"has been left where it is.", healthy=True)

    def apply_timing(self):
        """
        Made by Claude. Apply the reading interval and the scanner dwell time.

        Returns
        -------
        None
        """
        interval = self.settings_panel.sample_interval_input.value()
        dwell = self.settings_panel.dwell_input.value()

        self.worker.sample_interval = interval
        queued = self.worker.apply_scan_dwell(dwell)

        # Deliberately not a dialog.  A modal dialog runs its own event loop
        # on the main thread, and on this machine that overlapping GPIB
        # traffic faults the VISA driver and kills the program.  Routine
        # confirmations like this one are reported in the panel instead,
        # where they are just as visible and cost nothing.  See pause_polling.
        if queued:
            self.settings_panel.report(
                f"Reading every {interval:g} s; scanner changing channel "
                f"every {dwell} s.  The dwell time reaches the Lakeshore on "
                f"the next reading.", healthy=True)
        else:
            low, high = SCAN_DWELL_LIMITS
            self.settings_panel.report(
                f"Reading every {interval:g} s.  The dwell time was NOT "
                f"changed: the Lakeshore only accepts {low} to {high} s.",
                healthy=False)

    def history_step_changed(self, index):
        """
        Made by Claude. Apply a history span picked with the slider.

        Parameters
        ----------
        index : int
            Index into :data:`HISTORY_STEPS`.

        Returns
        -------
        None
        """
        hours = HISTORY_STEPS[index]
        self.history_input.setValue(hours)
        self.set_history_hours(hours)

    def history_box_changed(self):
        """
        Made by Claude. Apply a history span typed into the box.

        Returns
        -------
        None
        """
        self.set_history_hours(self.history_input.value())

    def set_history_hours(self, hours):
        """
        Made by Claude. Show the last ``hours`` of data, loading more from disk if needed.

        If the window reaches further back than what is in memory -- which it
        does after a restart, or when the span is widened -- the missing part
        is read back from the log files before redrawing.

        Parameters
        ----------
        hours : float
            How many hours of history to show.

        Returns
        -------
        None
        """
        self.worker.history_hours = hours
        self.update_history_label()

        state = self.worker.snapshot()
        data = state["data"]
        earliest = data[0][0] if data else time.time()
        wanted_from = time.time() - hours * 3600

        # A minute of slack, so that asking for the span already held does
        # not trigger a pointless re-read.
        if wanted_from < earliest - 60:
            self.status_label.setText(f"Loading {describe_hours(hours)} of "
                                      f"history ...")
            QApplication.processEvents()
            self.worker.reload_history()
            data = self.worker.snapshot()["data"]

        self.update_plot(data)

    def update_history_label(self):
        """Made by Claude. Update the label showing how much history is displayed."""
        self.slider_label.setText(
            f"Showing {describe_hours(self.worker.history_hours)}")

    def update_status(self, message, healthy, log_file_path=""):
        """
        Made by Claude. Update the connection-status banner and the log-file path.

        Parameters
        ----------
        message : str
            Status text to display.
        healthy : bool
            ``True`` if the instrument is answering, which shows the banner
            in green; ``False`` shows it in red.
        log_file_path : str, optional
            Full path of the file being written, shown in the settings
            panel.  Ignored if empty.

        Returns
        -------
        None
        """
        if self.status_label.text() != message:
            self.status_label.setText(message)
            colour = "#006000" if healthy else "#b00000"
            self.status_label.setStyleSheet(
                f"color: white; background-color: {colour}; padding: 4px;")

        if log_file_path:
            self.settings_panel.update_current_path(log_file_path)

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
        active = readings.get("ACTIVE_CH")
        active = None if active is None or np.isnan(active) else int(active)

        for channel, labels in self.thermometer_labels.items():
            t_label, r_label, p_label, live_label = labels
            t = readings.get(f"T_ch{channel}")
            r = readings.get(f"R_ch{channel}")
            p = readings.get(f"P_ch{channel}")

            t_label.setText(NOT_READING if t is None or np.isnan(t) else f"{t:.6f}")
            r_label.setText(NOT_READING if r is None or np.isnan(r) else f"{r:.3f}")
            p_label.setText(NOT_READING if p is None or np.isnan(p) else f"{p:.3e}")

            # The instrument measures one channel at a time, so say plainly
            # which numbers are live and which are the last value seen.
            if active is None:
                live_label.setText("")
            elif channel == active:
                live_label.setText("measuring")
                live_label.setStyleSheet("color: #006000; font-weight: bold;")
            else:
                live_label.setText("held")
                live_label.setStyleSheet("color: grey;")

        for group in self.heater_groups.values():
            group.update_readbacks(readings)

    def update_plot(self, data):
        """
        Made by Claude. Redraw the plots, honouring the history selector.

        Parameters
        ----------
        data : list of list
            Plot history from the worker.

        Returns
        -------
        None
        """
        self.canvas.update_plot(data, last_n_hours=self.worker.history_hours)

    def toggle_expand(self):
        """
        Made by Claude. Show or hide the settings and control columns.

        Hiding them hands their width to the plots, which is the point of
        the button; the wording says which way it will go rather than naming
        both directions at once.

        Returns
        -------
        None
        """
        if self.left_layout_widget.isHidden():
            self.left_layout_widget.show()
            self.settings_column_widget.show()
            self.expand_button.setText("Hide controls")
        else:
            self.left_layout_widget.hide()
            self.settings_column_widget.hide()
            self.expand_button.setText("Show controls")

    def closeEvent(self, event):
        """
        Made by Claude. Stop the worker thread cleanly when the window is closed.

        The heaters are deliberately left exactly as they are: the Lakeshore
        keeps regulating the fridge on its own after this program exits, and
        every row written so far is already on disk.

        Parameters
        ----------
        event : QCloseEvent
            The close event.

        Returns
        -------
        None
        """
        # Stop refreshing first, so the timer cannot fire while the worker
        # is being shut down.
        self.refresh_timer.stop()
        self.worker.running = False
        # Never leave a QThread running when its object is destroyed: Qt
        # aborts the program if that happens.  A cycle is nine GPIB queries,
        # so give it room to finish the one it is in.
        if not self.worker_thread.wait(15000):
            print("The monitor thread did not stop in time; asking Qt to end "
                  "it.")
            self.worker_thread.terminate()
            self.worker_thread.wait(2000)
        event.accept()


# %%

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
