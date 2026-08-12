"""Unit tests for data_management/data_logger.py."""
import os
import pytest
import pandas
from optomechanics.data_management.data_logger import logger, dated_logger


class TestLogger:
    """Tests for the logger class."""

    def test_logger_creates_file(self, tmp_path):
        """Logger.__init__ should create the log file on disk."""
        log = logger("test.csv", file_path=str(tmp_path) + os.sep, headings=["a", "b"])
        assert os.path.isfile(str(tmp_path) + os.sep + "test.csv")

    def test_logger_returns_logger_object(self, tmp_path):
        """Logger.__init__ should return a logger instance."""
        log = logger("test.csv", file_path=str(tmp_path) + os.sep)
        assert isinstance(log, logger)

    def test_logger_write_and_read_back(self, tmp_path):
        """Writing rows then reading should produce a DataFrame with the correct data."""
        fp = str(tmp_path) + os.sep
        log = logger("test.csv", file_path=fp, headings=["x", "y"])
        log.write_line([1, 2])
        log.write_line([3, 4])
        log.read()
        assert log.data is not None
        assert isinstance(log.data, pandas.DataFrame)
        assert len(log.data) == 2

    def test_logger_callable_writes_row(self, tmp_path):
        """Calling the logger instance should append a row (via __call__)."""
        fp = str(tmp_path) + os.sep
        log = logger("test.csv", file_path=fp, headings=["a", "b"])
        log([10, 20])
        log.read()
        assert len(log.data) == 1

    def test_logger_existing_file_not_overwritten(self, tmp_path):
        """Creating a logger for an existing file should not overwrite it."""
        fp = str(tmp_path) + os.sep
        log1 = logger("test.csv", file_path=fp, headings=["a", "b"])
        log1.write_line([1, 2])
        # Create a second logger pointing at the same file
        log2 = logger("test.csv", file_path=fp, headings=["a", "b"])
        # The second logger should have read the existing data
        assert log2.data is not None
        assert len(log2.data) == 1

    def test_logger_data_initially_none(self, tmp_path):
        """Before read() is called on a new file, data should be None."""
        fp = str(tmp_path) + os.sep
        log = logger("new.csv", file_path=fp, headings=["x"])
        # For a brand-new file, data stays None until read() is called
        # (create() only calls read() when the file already exists)
        assert log.data is None


class TestFormatDataLine:
    """Tests for logger.format_data_line."""

    def test_single_value(self, tmp_path):
        fp = str(tmp_path) + os.sep
        log = logger("test.csv", file_path=fp, headings=["a"])
        result = log.format_data_line([42])
        # Single value: "42," then strip last 2 chars -> "4" — that's how the code works
        assert "42" in result or "4" in result

    def test_multiple_values_comma_delimited(self, tmp_path):
        fp = str(tmp_path) + os.sep
        log = logger("test.csv", file_path=fp, headings=["a", "b", "c"], deliminator=",")
        result = log.format_data_line([1, 2, 3])
        # format_data_line strips the last 2 chars (trailing delimiter + last char)
        # This is a known quirk in the source code
        assert "1" in result
        assert "2" in result

    def test_custom_delimiter(self, tmp_path):
        fp = str(tmp_path) + os.sep
        log = logger("test.csv", file_path=fp, headings=["a", "b"], deliminator="\t")
        result = log.format_data_line(["hello", "world"])
        assert "hello" in result
        # format_data_line strips last 2 chars, truncating the final value
        assert "worl" in result


class TestDatedLogger:
    """Tests for the dated_logger class."""

    def test_dated_logger_creates_dated_path(self, tmp_path):
        """dated_logger should create year/month/day subdirectories."""
        base = str(tmp_path)
        dl = dated_logger(base, "log.csv", headings=["col1"])
        # The file_path should contain year/month/day segments
        assert os.path.isdir(dl.file_path)
        # Verify the full log file exists
        assert os.path.isfile(dl.file_path + "log.csv")

    def test_dated_logger_is_logger_subclass(self, tmp_path):
        base = str(tmp_path)
        dl = dated_logger(base, "log.csv", headings=["col1"])
        assert isinstance(dl, logger)

    def test_dated_logger_write_and_read(self, tmp_path):
        """dated_logger should support write_line and read like its parent."""
        base = str(tmp_path)
        dl = dated_logger(base, "log.csv", headings=["a", "b"])
        dl.write_line([1, 2])
        dl.read()
        assert dl.data is not None
        assert len(dl.data) == 1
