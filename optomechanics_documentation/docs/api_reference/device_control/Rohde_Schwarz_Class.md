# Rohde_Schwarz_Class

VISA driver for the Rohde & Schwarz ZNA vector network analyser (original
version using PyVISA directly).

For new code prefer `Rohde_Schwarz_Class_new`, which uses the
`RsInstrument` backend and has a more complete docstring coverage.

## Examples

```python
from optomechanics.device_control.Rohde_Schwarz_Class import ZNA

address = "TCPIP::192.168.x.x::INSTR"

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
        _file_name="zna_sweep_",
        file_location="/data/",
    )
```

::: optomechanics.device_control.Rohde_Schwarz_Class
