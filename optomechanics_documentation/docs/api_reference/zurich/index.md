# Zurich Instruments

The `optomechanics.Zurich` subpackage provides a base class skeleton for
**Zurich Instruments LabOne API** integration.

!!! warning "Incomplete — Known Bugs"
    This subpackage is a skeleton only and contains several bugs:

    - **Class name typo**: `zuirch` should be `zurich`
    - **Hardcoded device ID**: `dev1374` and API level 6 are module-level globals
      rather than parameters
    - **Missing attribute**: `open_device()` references `self._session` which does
      not exist — should be `self.session`
    - **Missing `self`**: the `scope()` method is missing the `self` parameter
      and cannot be called as an instance method

    This subpackage is tracked for completion in the [Code Improvements Roadmap](../../roadmap/code_improvements.md).

## Intended Interface

When complete, the subpackage will allow connecting to Zurich Instruments hardware
(e.g. MFLI lock-in amplifier) via the LabOne toolkit:

```python
from optomechanics.Zurich.Device_Zurich_Super import device

dev = device()
dev.open_device()
# ... perform measurements ...
dev.close_device()
```

## Modules

| Module | Description |
|--------|-------------|
| [Device_Zurich_Super](device_zurich_super.md) | Base class for Zurich LabOne sessions |
