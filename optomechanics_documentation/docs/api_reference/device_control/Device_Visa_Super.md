# Device_Visa_Super

Base VISA device class. Provides connection management and all standard
IEEE 488.2 / SCPI commands (`*IDN?`, `*RST`, `*OPC`, etc.).

All instrument-specific drivers in `device_control` inherit from `Device`.

::: optomechanics.device_control.Device_Visa_Super
