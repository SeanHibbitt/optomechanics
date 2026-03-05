# RS_FSW_new

VISA driver for the Rohde & Schwarz FSW signal and spectrum analyser
(updated version).
Adds IQ time-domain capture (`IQ_time_data_sweep`, `IQ_trace_sweep`) and
chunked data retrieval for large sweep-point counts on top of the original
`RS_FSW` functionality.

## Examples

### Power spectral density sweep

```python
from optomechanics.device_control.RS_FSW_new import FSW

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

### IQ time-domain capture

```python
with FSW(address, timeout=None) as sa:
    time_axis, iq_data = sa.IQ_time_data_sweep(
        central_freq=6.188e9,
        span=1e6,
        res_bw=100e3,
        file_location="/data/",
        file_name="iq_capture.tsv",
    )
```

::: optomechanics.device_control.RS_FSW_new
