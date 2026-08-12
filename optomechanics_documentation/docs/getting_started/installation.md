# Installation

## Prerequisites

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda
- Git with SSH access configured (see the project README for SSH key setup)

## Clone the repository

```bash
git clone <repository-url>
cd optomechanics
```

## Create the conda environment

The project ships an `ExperimentsEnvironment.yml` file that reproduces the full
`exp` environment used in the lab.

```bash
conda env create -f ExperimentsEnvironment.yml
conda activate exp
```

!!! note "Updating the environment"
    Before regenerating the file from your own machine, always rebuild first from
    the latest `ExperimentsEnvironment.yml` to avoid conflicts.  Then export:

    ```bash
    conda env export > ExperimentsEnvironment.yml
    ```

## Install the package

From the root of the repository (where `setup.py` lives):

```bash
pip install -e .
```

The `-e` flag installs in *editable* mode so that any source changes are
immediately visible without reinstalling.

## Verify

```python
import optomechanics
```

If no `ImportError` is raised the installation succeeded.
