# Rohde_Schwarz_Class_new

VISA driver for the Rohde & Schwarz ZNA vector network analyser using the
`RsInstrument` backend.
Provides SCPI setters for all sweep parameters and a high-level `sweep()`
method that configures, acquires, and saves multi-sweep S-parameter data.

## Examples

```python
from optomechanics.device_control.Rohde_Schwarz_Class_new import ZNA

address = "TCPIP::134.219.128.115::hislip0::INSTR"

with ZNA(address) as zna:
    data_pandas, meta_data = zna.sweep(
        channel=1,
        Result="S21",
        TraceName="Trc1",
        freq_start=5.0e9,
        freq_stop=7.0e9,
        number_of_points=1001,
        probe_power=-10,
        band_width=1e3,
        sweep_count=1,
        sense_average_state="OFF",
        ext_ref=True,
        _file_name="zna_sweep_",
        file_location="/data/",
    )

frequency = data_pandas["freq[Hz]"]
amplitude_dB = data_pandas["sweep_number_mag[dB]:1"]
phase_rad = data_pandas["sweep_number_phase[rad]:1"]
```

::: optomechanics.device_control.Rohde_Schwarz_Class_new
