"""
Docstring by Claude. Zurich Instruments sub-package for the optomechanics suite.

Provides lock-in amplifier control via ``zhinst.toolkit`` and HDF5 saving of
the results.  Key modules include:

- :mod:`~optomechanics.Zurich.Device_Zurich_Super` -- ``ZurichDevice`` base class (session / connect lifecycle)
- :mod:`~optomechanics.Zurich.HF2LI` -- HF2LI driver: output/demod configuration, frequency sweeps, spectra
- :mod:`~optomechanics.Zurich.zurich_data_management` -- HDF5 writers for sweep, spectrum and IQ results

Importing this package does not import ``zhinst``; import the submodules
directly, e.g. ``from optomechanics.Zurich.HF2LI import HF2LI``.
"""
