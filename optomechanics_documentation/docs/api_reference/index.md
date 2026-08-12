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
| [`attenuation_accounter`](data_analysis/attenuation_accounter.md) | module | Apply cable/component attenuation corrections |
| [`Plotting`](data_analysis/Plotting.md) | module | Colour helpers and Plotly layout utilities |
| [`Temperature_Reader`](data_analysis/Temperature_Reader.md) | module | Temperature readout helper |
| [`control_gui`](data_analysis/control_gui.md) | module | PID control GUI |
| [`fitting.S21`](data_analysis/fitting/S21.md) | module | Cavity transmission (S21) fitting |
| [`fitting.Sww`](data_analysis/fitting/Sww.md) | module | Noise PSD fitting and normalisation |
| [`fitting.omit`](data_analysis/fitting/omit.md) | module | OMIT spectral fitting |
| [`fitting._fitting`](data_analysis/fitting/_fitting.md) | module | Ring-down and linear fit primitives |

### device_control

| Item | Type | Description |
|---|---|---|
| [`Device_Visa_Super`](device_control/Device_Visa_Super.md) | module | Base `Device` class — VISA + IEEE 488.2 SCPI |
| [`Device_Visa_Super_rs`](device_control/Device_Visa_Super_rs.md) | module | R&S variant of the base `Device` class |
| [`VNA`](device_control/VNA.md) | module | Software-defined Vector Network Analyser |
| [`E5063A_VNA_Class_new`](device_control/E5063A_VNA_Class_new.md) | module | Keysight E5063A VNA driver |
| [`Rohde_Schwarz_Class`](device_control/Rohde_Schwarz_Class.md) | module | R&S ZNA VNA driver (legacy) |
| [`Rohde_Schwarz_Class_new`](device_control/Rohde_Schwarz_Class_new.md) | module | R&S ZNA VNA driver |
| [`RS_FSL`](device_control/RS_FSL.md) | module | R&S FSL spectrum analyser driver |
| [`RS_FSW`](device_control/RS_FSW.md) | module | R&S FSW spectrum analyser driver |
| [`RS_FSW_new`](device_control/RS_FSW_new.md) | module | R&S FSW spectrum analyser driver (new) |
| [`SMA100B`](device_control/SMA100B.md) | module | R&S SMA100B signal generator driver |
| [`SPD3303XE`](device_control/SPD3303XE.md) | module | Siglent SPD3303X-E power supply driver |
| [`Tektronix_AFG1022`](device_control/Tektronix_AFG1022.md) | module | Tektronix AFG1022 function generator driver |
| [`Yokogawa`](device_control/Yokogawa.md) | module | Yokogawa GS200 DC voltage/current source driver |
| [`KeithleyDMM6500`](device_control/KeithleyDMM6500.md) | module | Keithley DMM6500 digital multimeter driver |
| [`Lakeshore_372_AC_Res_Temp_Controller`](device_control/Lakeshore_372_AC_Res_Temp_Controller.md) | module | Lakeshore 372 AC resistance temperature controller driver |

### data_management

| Item | Type | Description |
|---|---|---|
| [`data_management`](data_management/data_management.md) | module | File read/write, `attenuation_object` |
| [`file_management`](data_management/file_management.md) | module | Dated directory and file path creation |
| [`data_logger`](data_management/data_logger.md) | module | Continuous data logging (`logger`, `dated_logger`) |
