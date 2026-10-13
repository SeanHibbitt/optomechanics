# Release Notes

## Unreleased

### New features

- **`Zurich`** — working Zurich Instruments support, replacing the previous skeleton:
  `ZurichDevice` base class, `HF2LI` lock-in driver (frequency sweeps, FFT spectra,
  raw I/Q capture, output/demodulator configuration with read-back verification)
  and HDF5 writers (`zurich_data_management`). Brought in from the acoustic
  isolation experiment with 113 mocked tests.
- **`Scripts/DAQ_templates/Zurich/SweepZurich_V5.3.ipynb`** — reference notebook
  for multi-iteration HF2LI sweeps with live plotting.

### Fixes

- `HF2LI` now reads the output range back as a double; `zhinst.toolkit` truncated the
  0.01 V / 0.1 V ranges to 0, which made sweeps on those ranges fail verification.

## v1.0 (current)

Initial public release of the `optomechanics` package.

### New features

- **`data_analysis.fitting.S21`** — microwave cavity transmission fitting
  (magnitude, dB, and complex variants)
- **`data_analysis.fitting.Sww`** — mechanical noise PSD fitting and normalisation
  to $G^2 S_{xx}$
- **`data_analysis.unit_conversions`** — complete set of RF power unit conversions
- **`data_analysis.square_membrane`** — resonance frequency calculator for
  mass-loaded square membrane resonators
- **`data_analysis.utilities`** — array helpers, error propagation, complex splitting
- **`data_analysis.misc_equations`** — intra-cavity photon number and related equations
- **`device_control`** — VISA drivers for Keysight E5063A VNA,
  Rohde & Schwarz FSL/FSW spectrum analysers, SMA100B signal generator,
  Siglent SPD3303XE power supply, Tektronix AFG1022, Keithley DMM6500,
  Lakeshore 372 temperature controller
- **`data_management`** — dated directory creation, tab-separated file I/O,
  frequency-dependent attenuation accounting
