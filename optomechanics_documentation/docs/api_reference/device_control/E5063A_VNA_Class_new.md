# E5063A_VNA_Class_new

VISA driver for the Keysight E5063A vector network analyser.
Provides SCPI setter/getter methods for all key sweep parameters and a
high-level `sweep()` method that configures, acquires, and saves a full
S-parameter sweep as a TSV file.

## Examples

```python
from optomechanics.device_control.E5063A_VNA_Class_new import VNA

address = "TCPIP::PH-K-E5063A-03540.local::inst0::INSTR"

with VNA(address) as vna:
    data_pandas, meta_data = vna.sweep(
        channel=1,
        Result="S21",
        TraceName="Trc1",
        freq_start=5.0e9,
        freq_stop=7.0e9,
        number_of_points=1001,
        probe_power=-10,
        band_width=1e3,
        _file_name="my_sweep_",
        file_location="/data/",
        reset=True,
    )

frequency = data_pandas["freq[Hz]"]
amplitude_dB = data_pandas["sweep_number_mag[dB]:1"]
phase_deg = data_pandas["sweep_number_phase[deg]:1"]
```

::: optomechanics.device_control.E5063A_VNA_Class_new
