# square_membrane

Resonance frequency calculator for a pre-stressed square membrane resonator
with an optional thin-film deposition.
The `membrane` class computes bare and mass-loaded resonance frequencies for
arbitrary mode indices (m, n), using the stress-dominated dispersion relation
for a silicon nitride membrane.

## Usage examples

```python
from optomechanics.data_analysis.square_membrane import membrane

# 1 mm × 1 mm SiN membrane, 100 nm thick, no deposition (density → 0)
mem = membrane(
    length_x=1e-3,
    length_y=1e-3,
    height_of_sin=100e-9,
    depth_deposition=0,
    density_of_deposition=0,
)

# Fundamental mode (1,1)
f_loaded, f_bare = mem.fm(1, 1)
print(f"Bare frequency: {f_bare/1e3:.1f} kHz")
print(f"Mass-loaded frequency: {f_loaded/1e3:.1f} kHz")
```

```python
# Estimate frequency shift from a 10 nm aluminium deposition
mem_al = membrane(
    length_x=1e-3,
    length_y=1e-3,
    height_of_sin=100e-9,
    depth_deposition=10e-9,
    density_of_deposition=2700,   # Al density (kg/m³)
)
f_al, _ = mem_al.fm(1, 1)
```

::: optomechanics.data_analysis.square_membrane
