# Issues / To-Do

> **Rules:** Never remove items. When done, tick the box and append a one-line summary
> with the commit hash — e.g. `- [x] item — description (abc1234)`

## Documentation

### Missing API reference pages
The following Python modules exist in the package but have no corresponding MkDocs page:

**data_analysis/**
- [x] `attenuation_accounter.py` — added api_reference page (3aaf978)
- [x] `Plotting.py` — added api_reference page (83dfe2e)
- [x] `Temperature_Reader.py` — added api_reference page (71bdebf)
- [x] `control_gui.py` — added api_reference page (b729523)

**data_analysis/fitting/**
- [x] `omit.py` — added api_reference page (df6a9d2)

**device_control/**
- [x] `E5063A_VNA_Class_new.py` — added api_reference page (404f726)
- [x] `Rohde_Schwarz_Class.py` — added api_reference page (8c74dff)
- [x] `Rohde_Schwarz_Class_new.py` — added api_reference page (fc91d9e)
- [x] `RS_FSL.py` — added api_reference page (ccc0fbd)
- [x] `RS_FSW.py` — added api_reference page (de4b877)
- [x] `RS_FSW_new.py` — added api_reference page (2e07a07)
- [x] `SMA100B.py` — added api_reference page (7a2bc75)
- [x] `SPD3303XE.py` — added api_reference page (afb2617)
- [x] `Tektronix_AFG1022.py` — added api_reference page (55fad10)
- [x] `Yokogawa.py` — added api_reference page (9a3bbfb)
- [x] `KeithleyDMM6500.py` — added api_reference page (f87c0cb)
- [x] `Lakeshore_372_AC_Res_Temp_Controller.py` — added api_reference page (78c9aca)
- [x] `Device_Visa_Super_rs.py` — added api_reference page (445916a)

**data_management/**
- [x] `data_logger.py` — added api_reference page (4e61ed7)

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
- [x] `temp_reader()` — rewritten to NumPy format (1599526)

**`data_analysis/control_gui.py`**
- [x] `Control_PID()` — rewritten to NumPy format (369554d)

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
- [x] `logger` class — added NumPy class docstring (9eeb543)
- [x] `logger.__init__()` — added NumPy docstring (d07eab9)
- [x] `logger.create()` — rewritten to NumPy format (156591d)
- [x] `logger.read()` — rewritten to NumPy format (ff69e29)
- [x] `logger.format_data_line()` — rewritten to NumPy format (4378205)
- [x] `logger.write_line()` — rewritten to NumPy format (0e8a868)
- [x] `logger.__call__()` — rewritten to NumPy format (0db1df0)
- [x] `dated_logger` class — added NumPy class docstring (a3c7bdd)
- [x] `dated_logger.__init__()` — added NumPy docstring (4875d2e)
- [x] `dated_logger.update_file_path()` — added NumPy docstring (394d2d8)
- [x] `dated_logger.check_update_file_path()` — added NumPy docstring (0bb232e)
- [x] `dated_logger.__call__()` — added NumPy docstring (52e0afa)

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
- [x] `Device` class — rewritten to NumPy format (e6aa469)
- [x] `Device.__init__()` — added NumPy docstring (6e867b8)
- [x] `Device.open()` — rewritten to NumPy format (5c00251)
- [x] `Device.connected_devices()` — rewritten to NumPy format (329069b)

**`device_control/E5063A_VNA_Class_new.py`**
- [x] `VNA` class — added NumPy class docstring (0d3528d)
- [x] `VNA.__init__()` — added NumPy docstring (ef38d37)
- [x] All setter/getter/query methods — rewritten to NumPy format (ca87ae0–834f692)

**`device_control/Rohde_Schwarz_Class_new.py`**
- [x] `ZNA` class — added NumPy class docstring (95896b7)
- [x] `ZNA.__init__()` — added NumPy docstring (d60cc89)
- [x] All setter/getter/query/helper methods — rewritten to NumPy format (c46cf70–2cc3d7b)

### Other doc tasks
- [x] Decide whether `E5063A_VNA_Class_old.py` should be kept or removed — audited: not imported anywhere, fully superseded by `_new.py`; safe to delete but left in place pending explicit user decision

### Phase 5a — User guide: device_control usage patterns
Update `docs/user_guide/device_control.md` with `with`-block examples drawn
from the real DAQ scripts (VNA sweep, signal generator, spectrum analyser).

- [x] Add E5063A VNA `with`-block example — added with-block example to device_control.md (563b47a)
- [x] Add SMA100B signal generator `with`-block example — added with-block example to device_control.md (9406b84)
- [x] Add RS FSW spectrum analyser `with`-block example — added with-block example to device_control.md (d47036c)
- [x] Add multi-device combined workflow example (VNA + SG + FSW) — added to device_control.md (994a810)

### Phase 5b — User guide: spectrum analyser IQ/PSD page
- [x] Create `docs/user_guide/spectrum_analyser.md` with IQ capture and PSD examples from `Scripts/DAQ_templates/SA IQ PSD/` — created page and added to mkdocs.yml nav (6636395)

### Phase 6 — Legacy file audit
- [x] Audit `E5063A_VNA_Class_old.py` — not imported anywhere, fully superseded by `_new.py`; no mkdocs page; safe to delete pending user decision
- [x] Audit `Rohde_Schwarz_Class.py` — has API page (`Rohde_Schwarz_Class.md`) that already notes it is the old version and recommends `_new`; not imported anywhere; relationship is clear

### Phase 7 — Re-audit all modified files
Re-check every file touched in Phases 3–4 to ensure no docstrings were missed
and all NumPy sections (Parameters, Returns, Raises, Examples) are present
where needed.

- [x] Re-audit `data_analysis/` modules — all functions have docstrings; `wrapped` inner func in utilities.py intentionally undocumented (no params)
- [x] Re-audit `data_analysis/fitting/` modules — all 24 E5063A and 33 RS-ZNA methods have docstrings; S21/Sww/omit/_fitting all clean
- [x] Re-audit `device_control/` modules — E5063A_new (24 fns) and Rohde_Schwarz_new (33 fns) fully documented; Device_Visa_Super clean
- [x] Re-audit `data_management/` modules — data_management, file_management, data_logger all clean

### Phase 8 — Build verification
- [x] Run `mkdocs build --strict` and fix any warnings or errors — fixed 6 cross-reference warnings in Rohde_Schwarz_Class.py; build passes clean (88e22e9)
  ```
  cd optomechanics_documentation
  /c/Users/seanh/miniconda3/envs/exp/python.exe -m mkdocs build --strict
  ```

### Phase 9 — Fix broken module imports
Fourteen modules currently fail to import, so mkdocstrings generates empty API pages for them.
Two are already fixed (commit 6027572): `data_management/__init__.py` and `data_logger.py`.
The Python executable to use is `/d/miniconda3/envs/exp/python.exe`.

Run this to check current import status:
```
/d/miniconda3/envs/exp/python.exe -c "
import sys; sys.path.insert(0,'.')
for m in ['optomechanics.device_control.Rohde_Schwarz_Class_new',
          'optomechanics.device_control.SMA100B',
          'optomechanics.device_control.SPD3303XE',
          'optomechanics.device_control.KeithleyDMM6500',
          'optomechanics.device_control.Lakeshore_372_AC_Res_Temp_Controller',
          'optomechanics.device_control.RS_FSL',
          'optomechanics.device_control.RS_FSW',
          'optomechanics.device_control.RS_FSW_new',
          'optomechanics.device_control.Yokogawa',
          'optomechanics.data_analysis.fitting.Sww',
          'optomechanics.data_analysis.fitting.omit',
          'optomechanics.device_control.VNA']:
    try: __import__(m); print('OK ', m)
    except Exception as e: print('FAIL', m, e)
"
```

Fixes needed (one commit per file):

- [ ] `Rohde_Schwarz_Class_new.py` — line 20: `from optomechanics.Fitting import re_and_im_to_dB_and_phase`. The `optomechanics.Fitting` module does not exist. Define `re_and_im_to_dB_and_phase` locally (takes `re`, `im` arrays; returns `20*log10(sqrt(re²+im²))` and `arctan2(im,re)`) or import `linear_voltage_to_dB` from `unit_conversions` and `np.angle`/`np.abs` directly.
- [ ] `SMA100B.py` — line 9: `from Optomechanics import Device` → `from .Device_Visa_Super import Device`
- [ ] `SPD3303XE.py` — line 1: `from Optomechanics import Device` → `from .Device_Visa_Super import Device`
- [ ] `KeithleyDMM6500.py` — line 8: `from Optomechanics import Device` → `from .Device_Visa_Super import Device`
- [ ] `Lakeshore_372_AC_Res_Temp_Controller.py` — line 2: `from Optomechanics import Device` → `from .Device_Visa_Super import Device`
- [ ] `RS_FSL.py` — line 1: `from DeviceClasses import Device` → `from .Device_Visa_Super import Device`
- [ ] `RS_FSW.py` — line 1: `from DeviceClasses import Device` → `from .Device_Visa_Super import Device`; line 6: `from DeviceClasses.Utilities.Fitting import dBm_to_watts, watts_to_dBm` → `from optomechanics.data_analysis.unit_conversions import dBm_to_watts, watts_to_dBm`
- [ ] `RS_FSW_new.py` — line 1: `from Optomechanics.Device_Visa_Super_rs import Device` → `from .Device_Visa_Super_rs import Device`; line 6: `from Optomechanics.Utilities.Fitting import dBm_to_watts, watts_to_dBm, RMS_to_dBm` → `from optomechanics.data_analysis.unit_conversions import dBm_to_watts, watts_to_dBm, RMS_to_dBm`
- [ ] `Yokogawa.py` — line 1: `from DeviceClasses import Device` → `from .Device_Visa_Super import Device`
- [ ] Add `data_analysis/fitting/_fitting.py` API page to mkdocs nav (user requested) — create `docs/api_reference/data_analysis/fitting/_fitting.md` and add to `mkdocs.yml`
- [ ] Re-run `mkdocs build --strict` after all import fixes to confirm zero warnings

### Phase 10 — Documentation overview pages audit
Check each overview/index page to ensure all modules are listed and descriptions are accurate.

- [ ] Audit `api_reference/index.md` — verify it links to all three subpackage overviews
- [ ] Audit `api_reference/data_analysis/index.md` — verify all 8 modules listed (unit_conversions, misc_equations, utilities, square_membrane, attenuation_accounter, Plotting, Temperature_Reader, control_gui)
- [ ] Audit `api_reference/data_analysis/fitting/index.md` — verify S21, Sww, omit, _fitting listed
- [ ] Audit `api_reference/device_control/index.md` — verify all 14 drivers listed
- [ ] Audit `api_reference/data_management/index.md` — verify data_management, file_management, data_logger listed
- [ ] Audit `user_guide/index.md` — verify all guide pages linked including new ones from Phase 11

### Phase 11 — User guide: experiment workflow pages
Create end-to-end workflow guides drawing on the DAQ templates in `optomechanics/Scripts/DAQ_templates/`.
Add each new page to the `User Guide` section of `mkdocs.yml` nav.

- [ ] Create `docs/user_guide/thermal_motion_measurement.md` — complete DAQ workflow: set up VNA S21 sweep (E5063A) + SA PSD acquisition (FSW) with a pump tone (SMA100B); show how parameters (RBW, span, averages, drive power) are chosen; reference `Scripts/DAQ_templates/SA IQ PSD/`
- [ ] Create `docs/user_guide/thermal_motion_analysis.md` — post-processing workflow: load saved TSV files with `read_file`; fit S21 with `fit_S21_peak`; convert PSD to S_xx using `attenuation_object` + `basic_S_ww_eq`; extract g₀; reference `Scripts/DAQ_templates/SA IQ PSD/AnalysisGoodPartition.ipynb`
- [ ] Create `docs/user_guide/attenuation_measurement.md` — how to measure attenuation of a cable/component with the VNA; acquiring S21 as a function of frequency; saving as `attenuation_object` TSV
- [ ] Create `docs/user_guide/attenuation_processing.md` — loading `attenuation_object` from TSV; combining attenuation objects with `+`/`-`; calling the object to interpolate at a frequency; applying corrections to data
- [ ] Create `docs/user_guide/s21_fitting.md` — fitting a cavity S21 peak: load data, call `fit_S21_peak` / `fit_S21_peak_dB` / `fit_S21_peak_complex`; interpret output (f_c, κ_tot, κ_ext); plot fit vs data
- [ ] Update `docs/user_guide/data_management.md` — add practical examples for `read_file`, `save_data_3`, `dated_file_maker`, `attenuation_object`; currently this page may be sparse
- [ ] Add all new Phase 11 pages to `mkdocs.yml` nav under `User Guide`

### Phase 12 — Getting Started fixes
- [ ] Fix icon/emoji shortcodes in `docs/index.md` — `:material-download:`, `:material-rocket-launch:`, `:octicons-arrow-right-24:` are Material for MkDocs icon shortcodes that require three extra extensions in `mkdocs.yml`. Install `mkdocs-material` if not already at ≥8.x, then add to `markdown_extensions`:
  ```yaml
  - attr_list
  - md_in_html
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  ```
  Confirm with `pip show mkdocs-material` that version ≥ 8.0 is installed; if older, upgrade: `pip install "mkdocs-material>=9"`.
- [ ] Review `getting_started/quickstart.md` — check the quick-start example still works after import fixes
- [ ] Review `getting_started/installation.md` — ensure conda env setup instructions are accurate


---

## Code / Features

*(Add items here)*

---

## Bugs

*(Add items here)*
