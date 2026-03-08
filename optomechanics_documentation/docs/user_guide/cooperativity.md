# Optomechanical Cooperativity

The cooperativity $C$ is a dimensionless figure of merit that compares the
optomechanical interaction strength to dissipation.  When $C > 1$,
optomechanical effects (back-action cooling, OMIT) dominate over thermal
decoherence.

---

## Definitions

### Multi-photon cooperativity

$$
C = \frac{4\, g_0^2\, n_d}{\Gamma_m\, \kappa_\text{tot}}
$$

### Single-photon cooperativity

Sets the scale without any driving field:

$$
C_0 = \frac{4\, g_0^2}{\Gamma_m\, \kappa_\text{tot}} = \frac{C}{n_d}
$$

---

## Parameter table

| Symbol              | Meaning                    | Units | Source in code                                      |
|---------------------|----------------------------|-------|-----------------------------------------------------|
| $g_0$               | Vacuum coupling rate       | Hz    | Thermal motion analysis (`fit_S_xx` result)         |
| $n_d$               | Intracavity photon number  | —     | `photon_number()` in `misc_equations.py`            |
| $\Gamma_m$          | Mechanical linewidth       | Hz    | Sww fit                                             |
| $\kappa_\text{tot}$ | Total cavity linewidth     | Hz    | S21 fit                                             |

---

## Manual calculation example

Cooperativity is not yet a dedicated function in the codebase, but it is
straightforward to compute from fitted parameters:

```python
import numpy as np

# From S21 fit
k_tot = 1e6    # Hz

# From Sww fit
g_0 = 10       # Hz (vacuum coupling rate)
G_m = 1.0      # Hz (mechanical linewidth)

# From photon_number()
n_d = 1e6      # intracavity photons

C_0 = 4 * g_0**2 / (G_m * k_tot)
C = C_0 * n_d

print(f"C_0 = {C_0:.2e}")
print(f"C   = {C:.1f}")
print(f"C > 1: {C > 1}")
```

Expected output:

```
C_0 = 4.00e-04
C   = 400.0
C > 1: True
```

---

## Physical significance

| Regime          | Interpretation                                                                 |
|-----------------|-------------------------------------------------------------------------------|
| $C > 1$         | Optomechanical coupling exceeds thermal decoherence — sideband cooling becomes effective. |
| $C \gg 1$       | Strong back-action regime — significant modification of mechanical linewidth and frequency. |
| $C_0 > 1$       | Single-photon strong coupling (extremely rare at room temperature).            |

**Typical room-temperature values:** $C_0 \sim 10^{-12}$ to $10^{-8}$, but $C$
can exceed 1 with sufficiently high $n_d$.

---

!!! note "Not yet in code"
    Cooperativity helper functions are planned but not yet implemented.
    See the [Parameter Glossary](glossary.md) "Future parameters" section for
    the roadmap.

---

## See also

- [Intracavity Photon Number](photon_number.md)
- [Thermal Motion Analysis](thermal_motion_analysis.md)
- [Parameter Glossary](glossary.md)
