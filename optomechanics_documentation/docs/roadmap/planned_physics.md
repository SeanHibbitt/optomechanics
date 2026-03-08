# Planned Physics Capabilities

The table below lists physical effects and analysis routines that are planned for the package but have not yet been implemented.

---

## 1. Dynamical Backaction

Radiation pressure from a cavity drive shifts and damps the mechanical mode. Two effects arise:

**Optical spring** — the cavity field modifies the effective mechanical frequency:

$$
\Omega_\text{eff}^2 = \Omega_m^2 + g_0^2 n_d \cdot [\text{detuning-dependent terms}]
$$

**Optical damping** — the cavity field adds (or removes) damping:

$$
\Gamma_\text{opt} = g_0^2 n_d \cdot [\text{detuning-dependent terms}]
$$

where $g_0$ is the single-photon coupling rate and $n_d$ is the intracavity photon number.

**Status:** Not yet implemented.

---

## 2. OMIA — Optomechanically Induced Absorption

OMIA is the absorption counterpart to OMIT (Optomechanically Induced Transparency). It occurs at the opposite sign of detuning and produces a dip in cavity transmission rather than a transparency window.

OMIT fitting is already implemented via the `omit` module. OMIA requires a separate model or sign-flip in detuning with appropriate lineshape handling.

**Status:** OMIT is implemented; OMIA is not yet implemented.

---

## 3. Sideband Resolution Classification

The sideband resolution regime determines the accessible cooling limit and the shape of many optomechanical responses.

- **Resolved sideband** regime: $\kappa_\text{tot} \ll \Omega_m$
- **Unresolved sideband** regime: $\kappa_\text{tot} \gg \Omega_m$

A planned helper would accept $\kappa_\text{tot}$ and $\Omega_m$ and return the regime label plus a quantitative ratio $\kappa_\text{tot} / \Omega_m$.

**Status:** Not yet implemented.

---

## 4. Quantum Ground State Cooling

In the resolved-sideband limit the minimum achievable phonon occupation is:

$$
n_\text{min} = \left(\frac{\kappa_\text{tot}}{4\,\Omega_m}\right)^2
$$

A planned function would compute $n_\text{min}$ from $\kappa_\text{tot}$ and $\Omega_m$ and compare it against a measured phonon number to assess proximity to the ground state.

**Status:** Not yet implemented.

---

## 5. Cooperativity Helper Functions

The single-photon cooperativity $C_0$ and the many-photon cooperativity $C$ are central figures of merit:

$$
C_0 = \frac{4 g_0^2}{\kappa_\text{tot}\,\Gamma_m}, \qquad C = C_0\,n_d
$$

Manual calculation is described in the [Cooperativity user guide](../user_guide/cooperativity.md), but no dedicated helper functions exist in the package yet.

**Status:** No helper functions yet; planned.

---

## 6. Standard Quantum Limit

The standard quantum limit (SQL) describes the minimum total measurement noise when imprecision noise and backaction noise are equal. Approaching the SQL requires balancing:

$$
S_\text{imp} \cdot S_\text{ba} \geq \frac{\hbar^2}{4}
$$

A planned module would compute the SQL-referenced imprecision and backaction contributions from measured noise spectra and system parameters.

**Status:** Not yet implemented.

---

## 7. `account_for_attenuation()` — Stub Method

The `account_for_attenuation()` method exists in the attenuation object but contains only a placeholder body. It is intended to apply a stored attenuation profile to a measured signal, correcting for cable and component losses.

**Status:** Stub in source code — raises `NotImplementedError` or returns without performing a calculation.

---

## 8. `save_to_tsv()` — Stub Method

The `save_to_tsv()` method raises `Exception("not finished")` when called. It is intended to serialise a dataset to a tab-separated values file for interoperability with external analysis tools.

**Status:** Stub in source code — raises an exception at runtime.
