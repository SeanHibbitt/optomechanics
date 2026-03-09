# Misc

The `optomechanics.Misc` subpackage is an **informal scripts folder** — it contains
experimental and one-off scripts used during development. It is **not part of the
public API**.

!!! note "Not for production use"
    The scripts in this folder may contain hardcoded paths, broken imports, or
    incomplete implementations. They are provided for reference only.

## Contents

| File | Description |
|------|-------------|
| `SG_test.py` | Example script: connect to SMA100B signal generator at a fixed IP, set microwave power (10 dBm) and frequency (3.68 GHz), wait 10 minutes. Contains a broken import path (`Optomechanics` instead of `optomechanics`). |
| `class_1.py` | Empty stub file. |
