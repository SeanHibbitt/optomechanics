# User Guide

This guide provides a conceptual overview of the three main subpackages and explains how they
fit together in a typical measurement workflow.

## Subpackages

| Subpackage | Purpose |
|---|---|
| [Data Analysis](data_analysis.md) | Fitting, unit conversions, membrane mechanics, plotting utilities |
| [Device Control](device_control.md) | VISA instrument drivers for lab hardware |
| [Data Management](data_management.md) | File creation, data logging, attenuation accounting |

## Typical workflow

```
Device Control          →   Data Management          →   Data Analysis
─────────────────           ───────────────────          ─────────────────────
Configure VNA           →   Save sweep to dated file →   Fit S21 peak
Set signal generator    →   Log temperature          →   Convert units
Read spectrum analyser  →   Account for attenuation  →   Plot results
```

## Experiment workflows

End-to-end guides for common measurement and analysis tasks:

| Guide | Description |
|---|---|
| [S21 Fitting](s21_fitting.md) | Fit a microwave cavity transmission peak |
| [Attenuation Measurement](attenuation_measurement.md) | Measure cable/component attenuation with the VNA |
| [Attenuation Processing](attenuation_processing.md) | Load, combine, and apply `attenuation_object` corrections |
| [Thermal Motion Measurement](thermal_motion_measurement.md) | DAQ workflow: VNA + SA + pump tone |
| [Thermal Motion Analysis](thermal_motion_analysis.md) | Post-processing: normalise PSD, fit S_ww, extract g₀ |
| [Spectrum Analyser (IQ/PSD)](spectrum_analyser.md) | IQ capture and PSD acquisition with the R&S FSW |

See each section for details, or jump straight to the
[API Reference](../api_reference/index.md) for full function documentation.

## See also

- [Parameter Glossary](glossary.md)
