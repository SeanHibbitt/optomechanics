"""
Docstring by Claude. Data management sub-package for the optomechanics suite.

Provides file I/O, metadata handling, and attenuation bookkeeping.  Key
modules include:

- :mod:`~optomechanics.data_management.data_management` -- file reading/writing and attenuation_object
- :mod:`~optomechanics.data_management.file_management` -- dated directory creation
- :mod:`~optomechanics.data_management.data_logger` -- timestamped data logging
"""

from .data_management import save_data_3, attenuation_object, read_file, read_meta_data
