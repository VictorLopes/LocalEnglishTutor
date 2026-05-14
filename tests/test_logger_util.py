"""Unit tests for Logger and LogBuffer."""
import sys
import pytest
from logger_util import Logger, LogBuffer


# ---------------------------------------------------------------------------
# LogBuffer
# ---------------------------------------------------------------------------

def test_log_buffer_stores_entry():
    buf = LogBuffer()
    buf.write("hello world")
    assert len(buf.logs) == 1
    assert "hello world" in buf.logs[0]


def test_log_buffer_adds_timestamp():
    buf = LogBuffer()
    buf.write("test message")
    # timestamps look like [HH:MM:SS]
    assert buf.logs[0].startswith("[")


def test_log_buffer_ignores_blank_writes():
    buf = LogBuffer()
    buf.write("   ")
    buf.write("\n")
    assert buf.logs == []


def test_log_buffer_respects_size_limit():
    buf = LogBuffer()
    for i in range(510):
        buf.write(f"line {i}")
    assert len(buf.logs) <= 500


def test_log_buffer_evicts_oldest_when_full():
    buf = LogBuffer()
    for i in range(501):
        buf.write(f"line {i}")
    assert "line 0" not in buf.logs[0]


# ---------------------------------------------------------------------------
# Logger singleton
# ---------------------------------------------------------------------------

def test_logger_is_singleton():
    a = Logger()
    b = Logger()
    assert a is b


def test_logger_get_logs_empty_initially():
    logger = Logger()
    assert logger.get_logs() == ""


def test_logger_capturing_redirects_stdout():
    logger = Logger()
    original = sys.stdout
    logger.start_capturing()
    try:
        print("captured line")
    finally:
        logger.stop_capturing()
    logs = logger.get_logs()
    assert "captured line" in logs
    assert sys.stdout is original


def test_logger_stop_capturing_restores_stdout():
    logger = Logger()
    original_stdout = sys.__stdout__
    logger.start_capturing()
    logger.stop_capturing()
    assert sys.stdout is logger._stdout


def test_logger_get_logs_joins_with_newlines():
    logger = Logger()
    logger.buffer.write("line one")
    logger.buffer.write("line two")
    logs = logger.get_logs()
    assert "\n" in logs
    assert "line one" in logs
    assert "line two" in logs
