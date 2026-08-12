# Tektronix_AFG1022

VISA driver for the Tektronix AFG1022 arbitrary function generator.
Supports standard waveforms including white noise (`PRNoise`), and
provides a `query_state()` helper that returns all current settings as a
dictionary.

## Examples

```python
from optomechanics.device_control.Tektronix_AFG1022 import AFG1022

address = "USB0::0x0699::0x0353::2031198::INSTR"

with AFG1022(address) as afg:
    print(afg.IDN_query())
    afg.RST()

    # Output white noise at 6 kHz bandwidth, 4 Vpp, zero offset
    afg.set_output_waveform("PRNoise")
    afg.set_frequency(6e3)
    afg.set_voltage_offset(0)
    afg.set_output_amplitude(4000)  # mVpp → internally converted to Vpp
    afg.set_output_state(1)

    state = afg.query_state()
    print(state)
    # {'function': 'PRN', 'voltage_offset[V]': 0.0,
    #  'amplitude[V]': 4.0, 'frequency[Hz]': 6000.0, 'state': '1'}
```

::: optomechanics.device_control.Tektronix_AFG1022
