# data_logger

Rolling file logger for time-stamped experiment data.
`logger` writes lines to a fixed file; `dated_logger` extends it with
automatic midnight roll-over so each calendar day gets its own file.

## Examples

```python
from optomechanics.data_management.data_logger import logger, dated_logger

# Fixed-file logger
log = logger(file_path="/data/run.tsv", columns=["time", "temp", "power"])
log.create()          # create file with header (no-op if it already exists)
log("12:00:00", 4.2, -30.1)  # append one data row

# Read logged data back into memory
log.read()
print(log.data)

# Dated logger — rolls over at midnight
dlog = dated_logger(
    file_path="/data/",
    file_name="temps",
    columns=["time", "temperature"],
)
dlog(import_time="12:00:00", temperature=4.2)
```

::: optomechanics.data_management.data_logger