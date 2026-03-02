"""
Made by Claude. Top-level package for the optomechanics experiment suite.

Provides data acquisition, analysis, and device-control tools for
optomechanical experiments.  The main sub-packages are:

- :mod:`optomechanics.data_analysis` — signal processing, fitting, and unit conversion
- :mod:`optomechanics.data_management` — file I/O and attenuation bookkeeping
- :mod:`optomechanics.device_control` — VISA instrument drivers

The :class:`~optomechanics.device_control.Device_Visa_Super.Device` base
class is re-exported here for convenience.
"""
from optomechanics.device_control.Device_Visa_Super import Device