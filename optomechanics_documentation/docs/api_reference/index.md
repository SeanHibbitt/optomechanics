# API Reference

Complete reference documentation for all public modules, classes, and functions.
Auto-generated from source docstrings.

## Subpackages

| Module | Contents |
|---|---|
| [`data_analysis`](data_analysis/index.md) | Fitting, unit conversions, membrane mechanics, error propagation |
| [`device_control`](device_control/index.md) | VISA instrument drivers |
| [`data_management`](data_management/index.md) | File I/O, data logging, attenuation accounting |

---

## Quick index

### data_analysis

| Item | Type | Description |
|---|---|---|
| [`unit_conversions`](data_analysis/unit_conversions.md) | module | RF power unit conversions |
| [`misc_equations`](data_analysis/misc_equations.md) | module | Physical equations (photon number, etc.) |
| [`utilities`](data_analysis/utilities.md) | module | Array helpers, error propagation, complex splitting |
| [`square_membrane`](data_analysis/square_membrane.md) | module | `membrane` class — resonance frequency calculator |
| [`fitting.S21`](data_analysis/fitting/S21.md) | module | Cavity transmission fitting |
| [`fitting.Sww`](data_analysis/fitting/Sww.md) | module | Noise PSD fitting and normalisation |

### device_control

| Item | Type | Description |
|---|---|---|
| [`Device_Visa_Super`](device_control/Device_Visa_Super.md) | module | Base `Device` class — VISA + SCPI |
| [`VNA`](device_control/VNA.md) | module | Software-defined VNA |

### data_management

| Item | Type | Description |
|---|---|---|
| [`data_management`](data_management/data_management.md) | module | File read/write, `attenuation_object` |
| [`file_management`](data_management/file_management.md) | module | Dated directory creation |
