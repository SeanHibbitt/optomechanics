# Attenuation Processing

This page explains how to work with `attenuation_object` to track and apply signal
attenuation corrections in your analysis.

## What is an attenuation_object?

An `attenuation_object` stores a frequency-dependent attenuation profile (in dB) for
a cable, attenuator, or chain of components.  It supports:

- Loading from / saving to TSV files
- Adding or subtracting attenuation profiles with `+` / `-`
- Calling as a function to interpolate attenuation at any frequency

```python
from optomechanics.data_management import attenuation_object
```

## Loading from a TSV file

TSV files contain two columns: `freq[Hz]` and `atten[dB]`.

```python
atten = attenuation_object()
atten.load_from_tsv("path/to/cable_atten.tsv")
```

## Combining attenuation objects

Use `+` to add attenuations (e.g. two cables in series) and `-` to remove a known
attenuation from a measurement:

```python
cable1 = attenuation_object(); cable1.load_from_tsv("cable1.tsv")
cable2 = attenuation_object(); cable2.load_from_tsv("cable2.tsv")

total = cable1 + cable2           # total loss of both cables in series
corrected = measurement - cable1  # remove cable1 loss from measured data
```

## Interpolating at a specific frequency

Call the object like a function to get the attenuation at one or more frequencies:

```python
freq_hz = 7.0e9
loss_dB = atten(freq_hz)          # scalar
loss_dB_arr = atten(freqs_array)  # array, same shape as freqs_array
```

## Applying corrections to measured data

A common pattern is to remove the path attenuation from a measured power array:

```python
import numpy as np
from optomechanics.data_management import attenuation_object

# Load path attenuation measured with VNA
path_atten = attenuation_object()
path_atten.load_from_tsv("path/to/path_atten.tsv")

# Measured SA powers (dBm) and frequencies
sa_powers_dBm = np.array(...)   # shape (N,)
sa_freqs_hz   = np.array(...)   # shape (N,)

# Create a temporary attenuation_object for the data array, then subtract
measured = attenuation_object(sa_powers_dBm, sa_freqs_hz)
corrected_powers_dBm = (measured - path_atten).magnitude
```

## Saving an attenuation_object

```python
atten.save_to_tsv("output_attenuation.tsv")
```

!!! warning "Not yet implemented"
    `save_to_tsv()` is not yet implemented and will raise an exception at runtime.
    As a workaround, use NumPy directly:
    ```python
    import numpy as np
    np.savetxt("output.tsv", data, delimiter="\t", header="col1\tcol2")
    ```

## See also

- [API reference: `data_management`](../api_reference/data_management/data_management.md)
- [Attenuation Measurement](attenuation_measurement.md) — how to measure cable attenuation with the VNA
- [Parameter Glossary](glossary.md)
