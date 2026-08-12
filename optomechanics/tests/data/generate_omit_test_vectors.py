"""Generate test vectors for OMIT/OMIA tests.

Run this script to regenerate the .npz files used by test_omit.py.

Parameters represent a physically plausible room-temperature microwave
optomechanical system:
- f_m = 1 MHz mechanical frequency (typical for SiN membrane)
- g_m = 10 Hz mechanical linewidth (Q ~ 1e5)
- kk_tot = 1 MHz cavity linewidth (resolved-sideband regime)
- A = 1e10 chosen to give a clearly visible peak above floor = 1.0
  at the given kk_tot (denominator scales as ~omega_m^2 * kappa ~ 1e19)
- floor = 1.0 normalised background transmission

Test vectors:
- omit_test_vector_peak.npz: OMIT peak (A > 0), 1001 points, 0.95-1.05 MHz
- omit_test_vector_dip.npz:  OMIA dip  (A < 0), same frequency range
"""
import numpy as np
import sys
import os

# Add package root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from optomechanics.data_analysis.fitting.omit import OMIT_equation

freqs = np.linspace(0.95e6, 1.05e6, 1001)

params_peak = dict(f_m=1e6, g_m=10.0, A=1e10, floor=1.0, kk_tot=1e6)
params_dip = dict(f_m=1e6, g_m=10.0, A=-1e10, floor=1.0, kk_tot=1e6)

data_dir = os.path.dirname(__file__)

np.savez(
    os.path.join(data_dir, "omit_test_vector_peak.npz"),
    freqs=freqs,
    transmission=OMIT_equation(freqs, **params_peak),
    **{k: np.float64(v) for k, v in params_peak.items()},
)

np.savez(
    os.path.join(data_dir, "omit_test_vector_dip.npz"),
    freqs=freqs,
    transmission=OMIT_equation(freqs, **params_dip),
    **{k: np.float64(v) for k, v in params_dip.items()},
)

print("Generated omit_test_vector_peak.npz and omit_test_vector_dip.npz")
