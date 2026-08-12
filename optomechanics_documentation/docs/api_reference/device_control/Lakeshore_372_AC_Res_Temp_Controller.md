# Lakeshore_372_AC_Res_Temp_Controller

VISA driver for the Lakeshore Model 372 AC Resistance Bridge Temperature
Controller, used with dilution refrigerators.
Reads temperature, resistance, excitation power, heater output, PID
settings, and still output for all input channels.

## Examples

```python
from optomechanics.device_control.Lakeshore_372_AC_Res_Temp_Controller import Temp_Controller

address = "TCPIP::192.168.x.x::INSTR"

with Temp_Controller(address) as tc:
    print(tc.IDN_query())

    # Read mixing chamber temperature (channel 4)
    mc_temp = tc.ReadMCTemperature()
    print(f"Mixing chamber: {mc_temp} K")

    # Read any channel
    temp = tc.ReadTemperature(3)
    resistance = tc.ReadResistance(3)
    excitation = tc.ReadExcitationPower(3)

    # Heater and PID status
    heater_out = tc.ReadHeaterOutput(3)
    pid = tc.ReadPID(3)
    print(f"PID: {pid}")
```

### Continuous temperature logging

```python
import time, csv
from datetime import datetime

with Temp_Controller(address) as tc:
    with open("/data/temps.tsv", "w") as f:
        f.write("timestamp\ttemp_K\tresistance_ohm\n")
        while True:
            t = tc.ReadTemperature(3)
            r = tc.ReadResistance(3)
            f.write(f"{datetime.now().isoformat()}\t{t}\t{r}\n")
            f.flush()
            time.sleep(1)
```

::: optomechanics.device_control.Lakeshore_372_AC_Res_Temp_Controller
