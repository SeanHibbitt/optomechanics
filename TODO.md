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
- [x] Module docstring — rewritten to NumPy format (26edd87)

**`data_analysis/__init__.py`**
- [x] Module docstring — added NumPy docstring (835696e)

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
- [x] Module docstring — added NumPy module docstring (af02dc9)
- [x] `account_for_attenuation()` — rewritten to NumPy format (141500a)

**`data_analysis/Plotting.py`**
- [x] `lighten_color()` — rewritten to NumPy format (cda979e)
- [x] `update_plotly_layout()` — rewritten to NumPy format (def9d67)

**`data_analysis/Temperature_Reader.py`**
- [ ] `temp_reader()` — PARTIAL

**`data_analysis/control_gui.py`**
- [ ] `Control_PID()` — PARTIAL

**`data_analysis/fitting/__init__.py`**
- [x] Module docstring — added NumPy docstring (875c9f5)

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
- [x] `OMIT_equation()` — rewritten to NumPy format (05576b7)
- [x] `fit_OMIT()` — rewritten to NumPy format (623b6c0)
- [x] `fit_OMIT_set_floor()` — rewritten to NumPy format (2cfc35f)

**`data_analysis/fitting/_fitting.py`** *(private module)*
- [x] `ring_down_eq()` — rewritten to NumPy format (9b4b68b)
- [x] `tau_to_Q()` — rewritten to NumPy format (5491332)
- [x] `fit_ring_down()` — added NumPy docstring (1f109cb)
- [x] `line_eq()` — added NumPy docstring (9b10d8e)
- [x] `fit_linear()` — added NumPy docstring (039bac1)

**`data_management/__init__.py`**
- [x] Module docstring — added NumPy docstring (37cf08b)

**`data_management/data_management.py`** *(in nav)*
- [x] `read_file()` — rewritten to NumPy format (3fb6a7d)
- [x] `read_meta_data()` — added NumPy docstring (a048e0f)
- [x] `save_data_3()` — added NumPy docstring (024a427)
- [x] `attenuation_object` class — rewritten to NumPy format (90c7c3e)
- [x] `attenuation_object.__init__()` — added NumPy docstring (27e9b14)
- [x] `attenuation_object.load_from_tsv()` — rewritten to NumPy format (f714bba)
- [x] `attenuation_object.save_to_tsv()` — added NumPy docstring (1e482af)
- [x] `attenuation_object.__add__()` — added NumPy docstring (dada46a)
- [x] `attenuation_object.__sub__()` — added NumPy docstring (51d4477)
- [x] `attenuation_object.__call__()` — added NumPy docstring (7f93363)

**`data_management/file_management.py`** *(in nav)*
- [x] `make_path()` — rewritten to NumPy format (3c0d1d0)
- [x] `dated_file_maker()` — rewritten to NumPy format (019b013)

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
- [x] Module docstring — added NumPy docstring (ef0dbc0)

**`device_control/Device_Visa_Super.py`** *(in nav)*
- [x] `Device` class — added NumPy class docstring (d57106d)
- [x] `Device.__init__()` — added NumPy docstring (faf27a9)
- [x] `Device.open()` — rewritten to NumPy format (7b920d3)
- [x] `Device.__enter__()` — rewritten to NumPy format (3c4d4c9)
- [x] `Device.__exit__()` — rewritten to NumPy format (ed184a0)
- [x] `Device.connected_devices()` — rewritten to NumPy format (64233e4)
- [x] `Device.query()` — added NumPy docstring (fad1f52)
- [x] `Device.write()` — added NumPy docstring (a0f3342)
- [x] `Device.read_bytes()` — added NumPy docstring (7027ad7)
- [x] `Device.close()` — added NumPy docstring (3e0a218)
- [x] `Device.CLS()` — rewritten to NumPy format (5ab7ad8)
- [x] `Device.OPC()` — rewritten to NumPy format (45dbaa3)
- [x] `Device.PCB()` — rewritten to NumPy format (e7d3213)
- [x] `Device.PRE()` — rewritten to NumPy format (bf7dd5d)
- [x] `Device.PSC()` — rewritten to NumPy format (86cb780)
- [x] `Device.RST()` — rewritten to NumPy format (259ada9)
- [x] `Device.SRE()` — rewritten to NumPy format (d3bd0b5)
- [x] `Device.TRG()` — rewritten to NumPy format (bca5de0)
- [x] `Device.WAI()` — rewritten to NumPy format (e0aaa62)
- [x] `Device.ESE()` — rewritten to NumPy format (e918ddd)
- [x] `Device.ESE_query()` — added NumPy docstring (26bc4b1)
- [x] `Device.ESR_query()` — rewritten to NumPy format (54bd404)
- [x] `Device.IDN_query()` — rewritten to NumPy format (67148ec)
- [x] `Device.IST_query()` — rewritten to NumPy format (89eea31)
- [x] `Device.OPT_query()` — rewritten to NumPy format (65cd8c8)
- [x] `Device.STB_query()` — rewritten to NumPy format (5a36cb1)
- [x] `Device.TST_query()` — rewritten to NumPy format (58e2f77)
- [x] `Device.OPC_query()` — added NumPy docstring (7f6188d)
- [x] `Device.check_OPC_event()` — added NumPy docstring (38645ab)
- [x] `Device.wait_on_OPC()` — added NumPy docstring (f4944c3)
- [x] `Device.save_data()` — added NumPy docstring (9a17248)
- [x] `Device.save_data_2()` — added NumPy docstring (fc5f5db)
- [x] `Device.save_data_3()` — added NumPy docstring (b7fd2bf)

**`device_control/VNA.py`** *(in nav)*
- [x] `Vector_Network_Analyser` class — added NumPy class docstring (7d3b340)
- [x] `Vector_Network_Analyser.__init__()` — rewritten to NumPy format (835cfb6)
- [x] `Vector_Network_Analyser.sweep()` — added NumPy docstring (cb80725)

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
