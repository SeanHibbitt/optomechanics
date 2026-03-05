# Thermal Motion Measurement

This page describes a complete DAQ workflow for measuring the thermal motion of a
mechanical resonator using a VNA for cavity characterisation and a spectrum analyser
(SA) for noise PSD acquisition.

See `Scripts/DAQ_templates/SA IQ PSD/` for working template notebooks.

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

## Step 1 — Characterise the cavity with the VNA

```python
from optomechanics.device_control.E5063A_VNA_Class_new import VNA
from optomechanics.data_analysis.fitting.S21 import fit_S21_peak_dB
import numpy as np

with VNA("GPIB0::17::INSTR") as vna:
    vna.set_start_frequency(f_cavity - 5e6)
    vna.set_stop_frequency(f_cavity + 5e6)
    vna.set_number_of_points(801)
    vna.set_IF_bandwidth(300)
    vna.sweep()

    freqs  = vna.get_frequency_data()
    s21_dB = vna.get_formatted_data()

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
    sg.set_frequency(f_pump)
    sg.set_power(P_drive)
    sg.set_output_state("ON")
```

## Step 3 — Acquire the noise PSD

```python
from optomechanics.device_control.RS_FSW_new import FSW
from optomechanics.data_management.data_management import save_data_3
from optomechanics.data_management.file_management import dated_file_maker

rbw      = 10        # Hz — set ≈ Γ_m / 10
span     = 2000      # Hz — set ≈ 5–10 × Γ_m
averages = 100

with FSW("TCPIP::192.168.0.10::INSTR") as sa:
    sa.set_center_frequency(f_pump)
    sa.set_span(span)
    sa.set_rbw(rbw)
    sa.set_sweep_count(averages)
    sa.sweep()

    sa_freqs  = sa.get_frequency_data()
    sa_powers = sa.get_trace_data()   # dBm

# Save alongside metadata
file_path = dated_file_maker("/data/thermal_motion", "run01")
save_data_3(
    file_path,
    {"freq[Hz]": sa_freqs, "powers[dBm]": sa_powers},
    meta={
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
    vna_data = {"freq[Hz]": freqs, "sweep_number_mag[dB]:1": s21_dB}
    save_data_3(dated_file_maker(base, f"S21_P{P_dBm}"), vna_data,
                meta={"timestamp[s]": time.time(), ...})

    # SA sweep → save
    sa.sweep()
    sa_data = {"freq[Hz]": sa_freqs, "powers[dBm]": sa.get_trace_data()}
    save_data_3(dated_file_maker(base, f"SA_P{P_dBm}"), sa_data,
                meta={"timestamp[s]": time.time(), "drive_power": P_dBm,
                      "drive_freq": f_pump, "res_band_width": rbw,
                      "temperature_mc[k]": temp_controller.read_temp()})
```

## See also

- [Thermal Motion Analysis](thermal_motion_analysis.md) — post-processing the saved data
- [Spectrum Analyser (IQ/PSD)](spectrum_analyser.md) — IQ capture and PSD details
- [S21 Fitting](s21_fitting.md) — fitting the cavity response
- [API reference: `device_control`](../api_reference/device_control/index.md)
