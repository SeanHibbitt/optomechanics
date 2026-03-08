# Thermal Motion Measurement

This page describes a complete DAQ workflow for measuring the thermal motion of a
mechanical resonator using a VNA for cavity characterisation and a spectrum analyser
(SA) for noise PSD acquisition.

See `Scripts/DAQ_templates/SA IQ PSD/` for working template notebooks.

## Measurement scheme

A microwave pump tone at frequency $f_\text{pump}$ drives intracavity photons
($n_d$).  The mechanical resonator's thermal motion modulates the cavity
resonance frequency, which phase-modulates the intracavity field and creates
sidebands at $f_\text{pump} \pm f_m$.  The spectrum analyser measures the
power in these sidebands; their height encodes the mechanical displacement.

**Red sideband** ($f_\text{pump} = f_0 - f_m$): the pump is detuned below
resonance.  This enables sideband cooling — energy is extracted from the
mechanics.  Used for backaction cooling experiments.

**On resonance** ($f_\text{pump} = f_0$): maximises intracavity photon number
for a given input power.  Used for thermal calibration measurements.

### Two analysis paths from the same data

The same PSD measurement supports two complementary analyses:

1. **Thermal motion analysis** — assumes thermal drive at known $T$, extracts
   $g_0$.  See [Thermal Motion Analysis](thermal_motion_analysis.md).
2. **Displacement measurement** — requires known $g_0$/$G$ (from a prior
   thermal calibration), extracts $T_\text{eff}$.

## Instruments required

| Role | Driver |
|---|---|
| Cavity VNA | `E5063A_VNA_Class_new.VNA` |
| Pump tone | `SMA100B.Signal_Generator` |
| Noise PSD | `RS_FSW_new.FSW` (or `RS_FSW.FSW`) |
| Temperature | `Lakeshore_372_AC_Res_Temp_Controller.Temp_Controller` |

## Choosing measurement parameters

| Parameter | Typical value | Guideline |
|---|---|---|
| VNA span | 10 × $\kappa_\text{tot}$ | Resolve the full cavity lineshape |
| VNA IF BW | 100–1000 Hz | Narrow for low noise, wide for speed |
| SA centre | pump frequency | Measure sidebands in the lab frame |
| SA span | 5–10 × $\Gamma_m$ | Resolve the mechanical peak |
| SA RBW | $\Gamma_m / 10$ | At least 10 points across the peak |
| SA averages | 50–200 | Reduce noise floor |

The VNA span guideline ($10 \times \kappa_\text{tot}$) ensures the full
Lorentzian lineshape is captured for a reliable fit.  The SA span
($5\text{–}10 \times \Gamma_m$) captures the mechanical peak with sufficient
baseline for noise floor estimation.  The RBW should be at least $\Gamma_m / 10$
to place ≥10 points across the mechanical linewidth.

## Step 1 — Characterise the cavity with the VNA

```python
from optomechanics.device_control.E5063A_VNA_Class_new import VNA
from optomechanics.data_analysis.fitting.S21 import fit_S21_peak_dB
import numpy as np

with VNA("GPIB0::17::INSTR") as vna:
    channel = 1
    trace   = 1
    vna.sense_freq_start(channel, f_cavity - 5e6)
    vna.sense_freq_stop(channel, f_cavity + 5e6)
    vna.sense_sweep_points(channel, 801)
    vna.sense_bandwidth_resolution(channel, 300)
    vna.calculate_parameter_define(channel, trace, "S21")
    vna.calculate_data_format(channel, trace, "MLOGarithmic")
    vna.initiate_sweep(channel)

    freqs  = np.fromstring(vna.sense_freq_data(channel), sep=",")
    s21_dB = np.fromstring(vna.calculate_data_fdata_query(channel, trace), sep=",")[0::2]

popt, *_ = fit_S21_peak_dB(s21_dB, freqs)
f0, k_tot, k_ext, *_ = popt
print(f"f0={f0/1e9:.4f} GHz  k_tot={k_tot/1e6:.2f} MHz  k_ext={k_ext/1e6:.2f} MHz")
```

## Step 2 — Apply the pump tone

Set the signal generator to the red sideband ($f_\text{pump} = f_0 - f_m$) for
sideband cooling, or to the cavity resonance for a calibration measurement:

```python
from optomechanics.device_control.SMA100B import Signal_Generator

f_pump   = f0 - f_mech          # red-sideband drive
P_drive  = -20                   # dBm at SG output

with Signal_Generator("GPIB0::20::INSTR") as sg:
    sg.set_mw_frequency(f_pump)
    sg.set_mw_power(P_drive)
    sg.turn_mw("ON")
```

## Step 3 — Acquire the noise PSD

```python
from optomechanics.device_control.RS_FSW_new import FSW
from optomechanics.data_management.data_management import save_data_3
from optomechanics.data_management.file_management import dated_file_maker
import numpy as np

rbw      = 10        # Hz — set ≈ Γ_m / 10
span     = 2000      # Hz — set ≈ 5–10 × Γ_m
averages = 100

with FSW("TCPIP::192.168.0.10::INSTR") as sa:
    sa.set_cent_freq(f_pump)
    sa.set_span(span)
    sa.set_bw(rbw)
    sa.set_sweep_count(averages)
    sa.sweep()

    sa_freqs  = np.fromstring(sa.x_data_query(), dtype=float, sep=",")
    sa_powers = np.fromstring(sa.y_data_query(), dtype=float, sep=",")  # dBm

# Save alongside metadata
file_path = dated_file_maker("/data/thermal_motion")
save_data_3(
    np.column_stack([sa_freqs, sa_powers]),
    "run01.tsv",
    file_location=file_path,
    headers="freq[Hz]\tpowers[dBm]",
    meta_data={
        "drive_freq":    f_pump,
        "drive_power":   P_drive,
        "res_band_width": rbw,
    }
)
```

## Step 4 — Log the VNA S21 alongside each SA sweep

The analysis routines require a simultaneously acquired S21 sweep for each SA sweep
(to normalise the photon number).  Loop over drive powers or temperatures and save
both:

```python
for P_dBm in drive_powers:
    # Update SG power
    sg.set_power(P_dBm)

    # VNA sweep → save
    vna.sweep()
    vna_data = np.column_stack([freqs, s21_dB])
    file_loc = dated_file_maker(base)
    save_data_3(vna_data, f"S21_P{P_dBm}.tsv", file_location=file_loc,
                headers="freq[Hz]\tsweep_number_mag[dB]:1",
                meta_data={"timestamp[s]": time.time()})

    # SA sweep → save
    sa.sweep()
    sa_data = np.column_stack([sa_freqs, np.fromstring(sa.y_data_query(), dtype=float, sep=",")])
    save_data_3(sa_data, f"SA_P{P_dBm}.tsv", file_location=file_loc,
                headers="freq[Hz]\tpowers[dBm]",
                meta_data={"timestamp[s]": time.time(), "drive_power": P_dBm,
                           "drive_freq": f_pump, "res_band_width": rbw,
                           "temperature_mc[k]": temp_controller.read_temp()})
```

## See also

- [Thermal Motion Analysis](thermal_motion_analysis.md) — post-processing the saved data
- [Spectrum Analyser (IQ/PSD)](spectrum_analyser.md) — IQ capture and PSD details
- [S21 Fitting](s21_fitting.md) — fitting the cavity response
- [API reference: `device_control`](../api_reference/device_control/index.md)
- [Parameter Glossary](glossary.md)
