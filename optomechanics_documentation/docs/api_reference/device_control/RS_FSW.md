# RS_FSW

VISA driver for the Rohde & Schwarz FSW signal and spectrum analyser
(original version).
Supports power-spectral-density sweeps and a pseudo-VNA mode.
For IQ time-domain capture use `RS_FSW_new`.

## Examples

```python
from optomechanics.device_control.RS_FSW import FSW

address = "TCPIP::134.219.128.115::hislip0::INSTR"

with FSW(address, timeout=None) as sa:
    powers, frequencies = sa.sweep(
        central_freq=6.188e9,
        span=100e3,
        band_width=1,
        sweep_points=100001,
        video_band_width=1,
        average_number=50,
        sweep_time=0.01,
        ref_level=-100,
        detector_type="SAMPLE",
        ref="EXT",
        save=True,
        file_location="/data/",
        file_name="fsw_sweep.tsv",
    )
```

::: optomechanics.device_control.RS_FSW
