# Issues / To-Do

> **Rules:** Never remove items. When done, tick the box and append a one-line summary
> with the commit hash — e.g. `- [x] item — description (abc1234)`

## Documentation

### Missing API reference pages
The following Python modules exist in the package but have no corresponding MkDocs page:

**data_analysis/**
- [ ] `attenuation_accounter.py`
- [ ] `Plotting.py`
- [ ] `Temperature_Reader.py`
- [ ] `control_gui.py`

**data_analysis/fitting/**
- [ ] `omit.py`

**device_control/**
- [ ] `E5063A_VNA_Class_new.py`
- [ ] `Rohde_Schwarz_Class.py`
- [ ] `Rohde_Schwarz_Class_new.py`
- [ ] `RS_FSL.py`
- [ ] `RS_FSW.py`
- [ ] `RS_FSW_new.py`
- [ ] `SMA100B.py`
- [ ] `SPD3303XE.py`
- [ ] `Tektronix_AFG1022.py`
- [ ] `Yokogawa.py`
- [ ] `KeithleyDMM6500.py`
- [ ] `Lakeshore_372_AC_Res_Temp_Controller.py`
- [ ] `Device_Visa_Super_rs.py`

**data_management/**
- [ ] `data_logger.py`

### Missing / incomplete NumPy docstrings
Legend: **NO** = no docstring at all · **PARTIAL** = plain text / `:param` style · **SECTIONS** = has NumPy structure but missing some sections

> Priority: fix files that are already in the MkDocs nav first.

**`optomechanics/__init__.py`**
- [ ] Module docstring — PARTIAL

**`data_analysis/__init__.py`**
- [ ] Module docstring — NO

**`data_analysis/unit_conversions.py`** *(in nav)*
- [x] All functions (`watts_ratio_to_dB`, `dB_to_watts_ratio`, `dB_to_linear_voltage`, `linear_voltage_to_dB`, `Vpp_to_Vrms`, `Vp_to_Vrms`, `Vrms_to_Vpp`, `Vrms_to_Vp`, `Vrms_to_watts`, `watts_to_dBw`, `RMS_to_dBw`, `RMS_to_dBm`, `dBw_to_watts`, `dBm_to_dBw`, `dBm_to_RMS`, `watts_to_dBm`, `dBm_to_watts`, `Vrms_squared_to_watts`) — rewritten to NumPy format, each committed individually (45f98bd–c5427e9)

**`data_analysis/misc_equations.py`** *(in nav)*
- [x] `photon_number()` — rewritten to NumPy format (5488932)

**`data_analysis/utilities.py`** *(in nav)*
- [x] `find_closest_number()` — rewritten to NumPy format (b9074d6)
- [x] `convert_error_dB_to_linear()` — added NumPy docstring (b001b8d)
- [x] `convert_error_linear_to_dB()` — added NumPy docstring (d492fd5)
- [x] `convert_anti_sym_linear_mag_voltage_error_to_sym()` — added NumPy docstring (d7b8c18)
- [x] `split_complex()` — added NumPy docstring (b534352)
- [x] `split_complex_wrapper()` — rewritten to NumPy format (07aa63e)
- [x] `complex_to_mag_phase()` — rewritten to NumPy format (237e95a)

**`data_analysis/square_membrane.py`** *(in nav)*
- [x] `membrane.__init__()` — added NumPy Parameters + Attributes to class docstring (0f6339a)
- [x] `membrane.fm()` — rewritten to NumPy format (fd88a4b)

**`data_analysis/attenuation_accounter.py`**
- [ ] Module docstring — PARTIAL (exists as comment, not docstring)
- [ ] `account_for_attenuation()` — PARTIAL

**`data_analysis/Plotting.py`**
- [ ] `lighten_color()` — PARTIAL
- [ ] `update_plotly_layout()` — PARTIAL

**`data_analysis/Temperature_Reader.py`**
- [ ] `temp_reader()` — PARTIAL

**`data_analysis/control_gui.py`**
- [ ] `Control_PID()` — PARTIAL

**`data_analysis/fitting/__init__.py`**
- [ ] Module docstring — NO

**`data_analysis/fitting/S21.py`** *(in nav)*
- [x] `S21_eq()` — rewritten to NumPy format (56dbdc2)
- [x] `S21_eq_complex()` — rewritten to NumPy format (b2f5700)
- [x] `S21_eq_phase()` — rewritten to NumPy format (2e89a64)
- [x] `S21_eq_dB()` — rewritten to NumPy format (cdbf162)
- [x] `fit_S21_peak_dB()` — rewritten to NumPy format (65377a6)
- [x] `fit_S21_peak_complex()` — rewritten to NumPy format (b8f9e77)
- [x] `fit_S21_peak()` — rewritten to NumPy format (06f9311)

**`data_analysis/fitting/Sww.py`** *(in nav)*
- [x] `fit_S_xx` class — added NumPy class docstring (dbbb320)
- [x] `fit_S_xx.__normalise_Sww_to_GGSxx__()` — rewritten to NumPy format (abc1e36)
- [x] `fit_S_xx.__average_and_fit_S_xx__()` — rewritten to NumPy format (ff751ee)
- [x] `basic_S_ww_eq()` — added NumPy docstring (b9baf3f)
- [x] `basic_S_ww_eq_2()` — rewritten to NumPy format (70386ba)
- [x] `dBm_basic_S_ww_eq()` — added NumPy docstring (79eca35)
- [x] `S_ff_thermal()` — rewritten to NumPy format (41c63a5)
- [x] `SHO_TF_sq()` — rewritten to NumPy format (5213458)
- [x] `S_xx_thermal()` — added NumPy docstring (8e9fc24)
- [x] `S_hh_24_25_exp_14_4()` — rewritten to NumPy format (5c56014)
- [x] `S_xx_impre()` — rewritten to NumPy format (3b35481)
- [x] `S_FF_back()` — rewritten to NumPy format (20c15f7)
- [x] `S_xx_back()` — added NumPy docstring (a2b77b6)
- [x] `S_ww_constant_calculator()` — added NumPy docstring (285a005)
- [x] `fit_basic_S_ww_eq_linear_power()` — rewritten to NumPy format (08a6704)
- [x] `fit_basic_S_ww_eq()` — rewritten to NumPy format (78fb10e)
- [x] `FWHM_guesser()` — rewritten to NumPy format (a9ab139)

**`data_analysis/fitting/omit.py`**
- [ ] `OMIT_equation()` — PARTIAL
- [ ] `fit_OMIT()` — PARTIAL
- [ ] `fit_OMIT_set_floor()` — PARTIAL

**`data_analysis/fitting/_fitting.py`** *(private module)*
- [ ] `ring_down_eq()` — PARTIAL *(private)*
- [ ] `tau_to_Q()` — PARTIAL *(private)*
- [ ] `fit_ring_down()` — NO *(private)*
- [ ] `line_eq()` — NO *(private)*
- [ ] `fit_linear()` — NO *(private)*

**`data_management/__init__.py`**
- [ ] Module docstring — NO

**`data_management/data_management.py`** *(in nav)*
- [ ] `read_file()` — PARTIAL (`:param` style)
- [ ] `read_meta_data()` — NO
- [ ] `save_data_3()` — NO
- [ ] `attenuation_object` class — PARTIAL
- [ ] `attenuation_object.__init__()` — NO
- [ ] `attenuation_object.load_from_tsv()` — PARTIAL
- [ ] `attenuation_object.save_to_tsv()` — NO
- [ ] `attenuation_object.__add__()` — NO
- [ ] `attenuation_object.__sub__()` — NO
- [ ] `attenuation_object.__call__()` — NO

**`data_management/file_management.py`** *(in nav)*
- [ ] `make_path()` — PARTIAL
- [ ] `dated_file_maker()` — PARTIAL

**`data_management/data_logger.py`**
- [ ] `logger.__init__()` — NO
- [ ] `logger.create()` — PARTIAL
- [ ] `logger.read()` — PARTIAL
- [ ] `logger.format_data_line()` — PARTIAL
- [ ] `logger.write_line()` — PARTIAL
- [ ] `logger.__call__()` — PARTIAL
- [ ] `dated_logger` class — PARTIAL
- [ ] `dated_logger.__init__()` — NO
- [ ] `dated_logger.update_file_path()` — NO
- [ ] `dated_logger.check_update_file_path()` — NO
- [ ] `dated_logger.__call__()` — NO

**`device_control/__init__.py`**
- [ ] Module docstring — NO

**`device_control/Device_Visa_Super.py`** *(in nav)*
- [ ] `Device.__init__()` — NO
- [ ] `Device.open()` — PARTIAL
- [ ] `Device.__enter__()` — PARTIAL
- [ ] `Device.__exit__()` — PARTIAL
- [ ] `Device.connected_devices()` — PARTIAL

**`device_control/VNA.py`** *(in nav)*
- [ ] `Vector_Network_Analyser` class — NO
- [ ] `Vector_Network_Analyser.sweep()` — NO

**`device_control/Device_Visa_Super_rs.py`**
- [ ] `Device` class — PARTIAL
- [ ] `Device.__init__()` — NO
- [ ] `Device.open()` — PARTIAL
- [ ] `Device.connected_devices()` — PARTIAL

**`device_control/E5063A_VNA_Class_new.py`**
- [ ] `VNA.__init__()` — NO
- [ ] All setter/getter methods — PARTIAL (plain text, no NumPy sections)

**`device_control/Rohde_Schwarz_Class_new.py`**
- [ ] `ZNA.__init__()` — NO
- [ ] All setter/getter methods — PARTIAL (plain text, no NumPy sections)

### Other doc tasks
- [ ] Decide whether `E5063A_VNA_Class_old.py` should be kept or removed

---

## Code / Features

*(Add items here)*

---

## Bugs

*(Add items here)*
