# Optomechanics


## SSH git access
Since you'll likely have a SSH key per repo per computer, you'll need to make sure to add the correct SSH config to direct between ssh keys, e.g:

Host OptomechanicsGithub

  Hostname github.com
  
  User git
  
  IdentityFile ~/.ssh/GitHubOptomechanics
  
  IdentitiesOnly yes


Host RoomTempGithub

  Hostname github.com
  
  User git
  
  IdentityFile ~/.ssh/id_ecdsa_RT2024_data
  
  IdentitiesOnly yes
  


CMD: git clone "git@OptomechanicsGithub:SeanHibbitt/Optomechanics.git"


## updating the exp module yml file from your own:

  Before updating, rebuild from the latest yml file! PLEASE!

  Then run the following command to generate, make sure you're in the correct folder:
    conda env export > ExperimentsEnvironment.yml

  Current modules required for optomechanics:
   - pyvisa
   - numpy
   - matplotlib
   - rsinstrument
   - simple-pid
   - scipy
   - pandas?
  Optional (Zurich lock-in control, optomechanics.Zurich):
   - zhinst-toolkit
   - h5py
  Extra General modules used in lab:
   - pyqt(6)
   - 


---

## Known code issues

These are open issues with the source code itself. They are tracked here rather than in TODO.md
because they require decisions about desired behaviour before being fixed.

### Stub / unfinished implementations

- **`data_analysis/attenuation_accounter.py` — `account_for_attenuation()`**
  Body is `pass` — the function silently returns `None`. Docstring says "not yet implemented".
  Needs a real implementation before it can be used.

- **`data_management/data_management.py` — `attenuation_object.save_to_tsv()`**
  Raises `Exception("not finished")` at runtime. TSV loading (`load_from_tsv`) works;
  saving does not. Round-trip file I/O is therefore broken.

### Packaging

- **`setup.py` is broken for subpackage installs**
  Uses `py_modules=['optomechanics']` instead of `packages=find_packages()`.
  Running `pip install -e .` from a fresh clone will not correctly register the subpackages
  (`data_analysis`, `device_control`, `data_management`) on the Python path.
  Fix: replace with `packages=find_packages()` and add `install_requires` for numpy, scipy, pandas, etc.

### Potential bugs

- **`data_analysis/utilities.py` — `convert_anti_sym_linear_mag_voltage_error_to_sym()` line ~144**
  Assigns `value[value - error < 0]` to `error` — this filters a slice of the array into the
  scalar `error` variable, which is likely incorrect (probably intended to be `np.min(...)` or similar).
  Should be verified against the original derivation before fixing.

### API design notes

- **`data_analysis/fitting/Sww.py` — `fit_S_xx.__average_and_fit_S_xx__()`**
  Uses double-underscore (dunder) naming for a method users must call directly.
  In Python, dunder names trigger name-mangling in subclasses and signal "private/special".
  This should be renamed to a single-underscore (`_average_and_fit_S_xx`) or a plain public name.

- **Missing module-level docstrings (~15 files)**
  The following source files lack a module-level docstring (the first string in the file that
  mkdocstrings uses as the page description):
  `utilities.py`, `Plotting.py`, `Temperature_Reader.py`, `control_gui.py`,
  `fitting/S21.py`, `fitting/Sww.py`, `fitting/omit.py`, `fitting/_fitting.py`,
  `data_management/data_management.py`, `data_management/file_management.py`,
  `data_management/data_logger.py`, `device_control/Device_Visa_Super.py`,
  `device_control/VNA.py`, and most instrument driver files.
