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

See each section for details, or jump straight to the
[API Reference](../api_reference/index.md) for full function documentation.
