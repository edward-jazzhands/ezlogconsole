"""
Tests for Ed's EZ Log Console - sender and receiver.

The test suite covers two things: the sender's `makePickle` method in isolation, 
and a full end-to-end integration test that spins up a real server and sends a 
log record through it.
"""

from typing import cast
import json
import logging
import logging.handlers
import struct
import threading
import time
from io import StringIO

import pytest
from rich.console import Console

import ezlogconsole.receiver as receiver
from ezlogconsole import JsonSocketHandler, LogRecordServer, LogRecordHandler


### Notes

# - Port `19020` is hardcoded in the integration test. If that port is already in use on 
#   your machine, change `test_port` in `test_ezlogconsole.py` to something else.
# - The integration test uses `time.sleep` to give the background thread time to receive 
#   and print the record. If you find the test flaky on a slow machine, increase the 
#   sleep values slightly.

# -------------
# Helpers
# -------------

def make_log_record(
    msg: str = "Hello world",
    level: int = logging.INFO,
    name: str = "test.logger",
) -> logging.LogRecord:
    """Build a minimal LogRecord without going through an actual Logger."""
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="test_file.py",
        lineno=42,
        msg=msg,
        args=(),
        exc_info=None,
    )
    return record


def decode_packet(packet: bytes) -> dict:
    """Strip the 4-byte length header and decode the JSON payload."""
    length = struct.unpack(">L", packet[:4])[0]
    payload = packet[4 : 4 + length]
    return json.loads(payload.decode("utf-8"))


@pytest.fixture
def handler() -> JsonSocketHandler:
    return JsonSocketHandler()

# These tests exercise `JsonSocketHandler.makePickle` directly with fabricated 
# `LogRecord` objects. No network or server is involved. They verify that the 
# 4-byte length header is correct, that `args` are stripped after being baked 
# into `msg`, and that exception info gets serialized to a plain string rather 
# than left as a tuple of Python objects.


def test_basic_record_round_trips(handler: JsonSocketHandler) -> None:
    record = make_log_record("Hello world", logging.INFO)
    packet = handler.makePickle(record) # remember this doesn't actually pickle it.
    data = decode_packet(packet)

    assert data["msg"] == "Hello world"
    assert data["levelno"] == logging.INFO
    assert data["name"] == "test.logger"

def test_args_are_stripped(handler: JsonSocketHandler) -> None:
    record = make_log_record("Value is %s", logging.DEBUG)
    record.args = ("something",)
    packet = handler.makePickle(record)
    data = decode_packet(packet)

    # args should be gone, and msg should already be fully formatted
    assert "args" not in data or data.get("args") is None
    assert "something" in data["msg"]

def test_length_header_matches_payload(handler: JsonSocketHandler) -> None:
    record = make_log_record("Check the header")
    packet = handler.makePickle(record)
    declared_length = struct.unpack(">L", packet[:4])[0]
    actual_length = len(packet) - 4

    assert declared_length == actual_length

def test_exception_info_is_serialized_to_string(handler: JsonSocketHandler) -> None:
    try:
        raise ValueError("something went wrong")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = make_log_record("Oops")
    record.exc_info = exc_info
    packet = handler.makePickle(record)
    data = decode_packet(packet)

    # exc_info must be a string now, not a tuple of objects
    assert isinstance(data["exc_info"], str)
    assert "ValueError" in data["exc_info"]
    assert "something went wrong" in data["exc_info"]



# This test starts a real `LogRecordServer` on port `19020` in a background daemon thread, 
# connects a `JsonSocketHandler` to it, and sends a live log record. It then checks the 
# console output to confirm the message, level, and source file all appear correctly.

# The module-level `console` in `receiver.py` is monkeypatched with a `rich.Console` backed
# by a `StringIO` buffer, so the output can be inspected as a plain string without touching
# stdout. The monkeypatch is automatically undone by pytest after the test completes.

def test_end_to_end_log_record(
        monkeypatch: pytest.MonkeyPatch, pytestconfig: pytest.Config
    ) -> None:
    """Spin up a real LogRecordServer in a background thread, send a
    log record through JsonSocketHandler, and verify the console output."""

    # 1. Swap out the module-level console for one backed by StringIO
    #    so we can inspect what got printed.
    # This is the recommended method for unit testing, by the Rich docs:
    # https://rich.readthedocs.io/en/latest/console.html#capturing-output

    test_console = Console(file=StringIO(), highlight=False)
    monkeypatch.setattr(receiver, "console", test_console)

    # 2. Start the server on a random high port to avoid conflicts.
    test_host = "localhost"
    test_port = 19020
    server = LogRecordServer((test_host, test_port), LogRecordHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True  # dies automatically when the test exits
    server_thread.start()
    handler = None
    logger = None

    try:
        # 3. Build a sender and attach it to a logger.
        handler = JsonSocketHandler(host=test_host, port=test_port)
        logger = logging.getLogger("integration_test")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Give the server a moment to be ready, then send a record.
        time.sleep(0.1)
        logger.info("Integration test message")

        # Give the server thread time to receive and print the record.
        time.sleep(0.2)

    finally:
        if handler:
            handler.close()
        server.shutdown()
        if logger and handler:
            logger.removeHandler(handler)

    # Since we set the file to an in-memory StringIO, we can just grab the value.
    output = cast(StringIO, test_console.file).getvalue()

    # verbose level 1 = v | 2 = vv | 3 = vvv
    if pytestconfig.getoption("verbose") > 1:
        pass
        print("\nLog console output:")
        print(output)

    assert "connected" in output
    assert "identified as integration_test" in output
    assert "Integration test message" in output
    assert "[INFO]" in output
    assert "test_all.py" in output
    assert "disconnected" in output

    # The console output should look like this (with the port number changed):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # ('127.0.0.1', 58652) connected.
    # ('127.0.0.1', 58652) identified as integration_test
    # 17:23:44 [INFO] Integration test message  (test_all.py:160)
    # integration_test ('127.0.0.1', 58652) disconnected.
