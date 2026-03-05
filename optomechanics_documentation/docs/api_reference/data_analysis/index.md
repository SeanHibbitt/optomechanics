# data_analysis

The `optomechanics.data_analysis` subpackage contains all numerical analysis tools.

## Modules

| Module | Description |
|---|---|
| [`unit_conversions`](unit_conversions.md) | RF power unit conversions |
| [`misc_equations`](misc_equations.md) | Physical equations (photon number, …) |
| [`utilities`](utilities.md) | Array search, error propagation, complex helpers |
| [`square_membrane`](square_membrane.md) | Membrane resonance frequency calculator |
| [`attenuation_accounter`](attenuation_accounter.md) | Apply cable/component attenuation corrections to data |
| [`Plotting`](Plotting.md) | Colour helpers and Plotly layout utilities |
| [`Temperature_Reader`](Temperature_Reader.md) | Temperature readout helper |
| [`control_gui`](control_gui.md) | PID control GUI |

## fitting sub-package

| Module | Description |
|---|---|
| [`fitting.S21`](fitting/S21.md) | Cavity transmission (S21) fitting |
| [`fitting.Sww`](fitting/Sww.md) | Noise PSD (S_ww) fitting and normalisation |
| [`fitting.omit`](fitting/omit.md) | OMIT spectral fitting |
| [`fitting._fitting`](fitting/_fitting.md) | Ring-down and linear fit primitives (shared internals) |
