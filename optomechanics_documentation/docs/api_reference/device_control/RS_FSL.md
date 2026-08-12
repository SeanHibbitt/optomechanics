# RS_FSL

VISA driver for the Rohde & Schwarz FSL spectrum analyser.
Lower-end FSL variant: minimum IF bandwidth 300 Hz, maximum 10 001 sweep
points.  For higher performance use `RS_FSW` or `RS_FSW_new`.

## Examples

```python
from optomechanics.device_control.RS_FSL import FSL

address = "TCPIP::192.168.x.x::INSTR"

with FSL(address) as sa:
    powers, frequencies = sa.sweep(
        central_freq=6.188e9,
        span=100e3,
        band_width=10,
        sweep_points=1001,
        video_band_width=10,
        average_number=10,
        sweep_time=0.1,
        ref_level=-60,
        detector_type="SAMPLE",
        ref="INT",
        save=True,
        file_location="/data/",
        file_name="fsl_sweep.tsv",
    )
```

::: optomechanics.device_control.RS_FSL
