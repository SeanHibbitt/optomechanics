# HF2LI

!!! warning "Autodoc unavailable"
    This module requires `zhinst.toolkit`, which is not installed in the standard
    environment. The API is documented manually below; the source docstrings
    (NumPy style) have the full parameter descriptions.

**File:** `optomechanics/Zurich/HF2LI.py`

Driver for the Zurich Instruments **HF2LI** dual lock-in amplifier. It provides
output/input/demodulator configuration, frequency sweeps (LabOne Sweeper module),
FFT spectra and raw I/Q capture (LabOne DAQ module), and optional HDF5 saving.

---

## Classes

### `HF2LI(device_id="dev1374", server_host="localhost", port=8005)`

Subclass of [`ZurichDevice`](device_zurich_super.md). Use it as a context manager:

```python
from optomechanics.Zurich.HF2LI import HF2LI

with HF2LI() as hf:
    hf.configure_output(channel=0, amplitude=0.5e-3, range_v=0.01)
```

#### Read-back verification

Every output setting the driver writes (range, amplitude, output on/off,
oscillator enable, oscillator frequency) is read back from the device. If the
value read back isn't within 1 % of the value written, after retrying for about
1 s, the method raises:

```
RuntimeError: Verify failed for sigouts/0/amplitudes/6: wrote 5e-06, read back 0.0
```

This usually means the setting can't be represented on the device. The most
common case is an amplitude that is too small for the output range (see
[Choosing the output range](../../user_guide/hf2li_sweeps.md#choosing-the-output-range)).

!!! note "Output range read-back"
    `zhinst.toolkit` reads the HF2's `sigouts/n/range` node as an integer, which
    truncates the 0.01 V and 0.1 V ranges to 0. The driver therefore reads the range
    back as a double straight from the Data Server.

---

### Configuration methods

| Method | Description |
|--------|-------------|
| `configure_output(channel, amplitude, enable=True, osc_index=0, osc_enable=True, range_v=None, offset=None)` | Sets output range (first), amplitude (V, converted to a fraction of the range), on/off, oscillator routing and DC offset. |
| `configure_input(channel, input_range=1.0, impedance_50ohm=False, ac_coupling=False)` | Configures a signal input. |
| `configure_demodulator(index, oscselect=0, harmonic=1, rate=1000, order=4, timeconstant=None)` | Configures a demodulator: oscillator, harmonic, sample rate, filter order and time constant. |
| `set_oscillator_frequency(oscillator, frequency)` | Sets and verifies an oscillator frequency (Hz). |
| `get_demod_filter_response(freqs_rel, demod_index=0)` | Complex response $H(f) = 1/(1 + j 2\pi f\,\mathrm{TC})^n$ of the demodulator low-pass filter, using the TC and order currently on the device. |

---

### `sweep(...)`

```python
sweep(start, stop, num_points, demod_index=0, settling_time=None,
      settling_inaccuracy=None, averaging_samples=1, bandwidth_control=1,
      bandwidth_hz=None, filter_order=None, log_sweep=True, timeout=60,
      progress=False, progress_interval=60, progress_callback=None,
      output_channel=None, output_amplitude=None, output_enable=None,
      output_osc_index=0, output_osc_enable=None, output_range=None,
      save=False, filepath=None, metadata=None,
      group_index=0, append=False, prepend_datetime=True)
```

Runs a frequency sweep of oscillator `output_osc_index` with the LabOne Sweeper
module and returns the demodulator data.

| Parameter | Description |
|-----------|-------------|
| `start`, `stop`, `num_points` | Frequency range (Hz) and number of points |
| `log_sweep` | Log (`True`, default) or linear frequency spacing |
| `demod_index` | Demodulator to record (0–5) |
| `bandwidth_control` | `0` manual (demodulator's existing TC), `1` fixed (uses `bandwidth_hz`), `2` auto |
| `bandwidth_hz` | Demodulator 3 dB bandwidth for fixed mode |
| `filter_order` | Demodulator filter order (1–8); `None` leaves it unchanged |
| `settling_time`, `settling_inaccuracy` | Per-point settling; `None` uses the device default |
| `averaging_samples` | Samples averaged per point |
| `timeout` | Seconds before a `TimeoutError` (`np.inf` for no limit) |
| `progress`, `progress_interval` | Poll and print progress every `progress_interval` s |
| `progress_callback` | Called with the partial result (or `None`) at each poll; used for live plots. Needs `progress=True`; printing is suppressed. |
| `output_channel` | Output to configure before the sweep; `None` leaves outputs alone |
| `output_range` | Output range in V (0.01, 0.1, 1, 10), set before the amplitude |
| `output_amplitude` | Output amplitude in V (absolute) |
| `output_enable`, `output_osc_enable` | Output on/off and oscillator-to-output routing |
| `save`, `filepath`, `metadata` | Save to HDF5 via [`save_sweep_to_hdf5`](zurich_data_management.md#save_sweep_to_hdf5) |
| `group_index`, `append` | Store several sweeps in one file as `000/`, `001/`, ... (`append=True` reuses the file from the previous `sweep` call) |
| `prepend_datetime` | Prefix the filename with `YYYY-MM-DD_HH_MM_SS_` (default `True`) |

**Returns:** `dict` — the sweeper result, including `'frequency'`, `'r'`,
`'phase'` (radians), `'x'`, `'y'` as 1-D arrays.

**Raises:** `ValueError` (missing or non-`.h5` `filepath` with `save=True`),
`RuntimeError` (read-back failure or no data), `TimeoutError`.

!!! note
    If `output_channel` is set, the output is switched **off** when the sweep finishes.

---

### `spectrum(...)`

```python
spectrum(center_freq, span, fft_length, num_averages=10, demod_index=0,
         osc_index=0, window='hann', correction='amplitude', filter_order=4,
         filter_bandwidth_hz=None, output_channel=None, output_amplitude=None,
         output_enable=None, output_osc_index=0, output_osc_enable=None,
         output_range_v=None, output_offset=None, timeout=60,
         save=False, filepath=None, metadata=None, prepend_datetime=True)
```

Measures a spectrum around `center_freq` with the DAQ module's FFT mode. The
demodulator rate is set from `span`; windowing, averaging and the frequency axis
are done by LabOne.

**Returns:** `dict` with `'freqs'` (`(fft_length,)`, absolute Hz), `'ffts'`
(`(num_averages, fft_length)`), `'averaged'` (`(fft_length,)`) and `'params'`.

---

### `acquire_iq(...)`

```python
acquire_iq(center_freq, span, fft_length, num_segments=None, acquire_time=None,
           demod_index=0, osc_index=0, filter_order=4, filter_bandwidth_hz=None,
           timeout=60, save=False, filepath=None, metadata=None,
           prepend_datetime=True)
```

Captures raw demodulator I/Q in time-domain mode: `num_segments` blocks of
`fft_length` samples at a sample rate of `2 × span`, for windowing and FFTs
in Python.

**Returns:** `dict` with `'x'`, `'y'` (`(num_segments, fft_length)`), `'fs'` (Hz)
and `'params'` (including the filter time constant on the device).

---

## Functions

### `bandwidth_to_tc(f3db_hz, order)`

Converts a demodulator 3 dB bandwidth to a filter time constant for an
`order`-stage first-order low-pass cascade:

$$
\mathrm{TC} = \frac{\sqrt{2^{1/n} - 1}}{2\pi f_{3\,\mathrm{dB}}}
$$

### `tc_to_bandwidth(tc_s, order)`

Inverse of `bandwidth_to_tc`.
