"""Receiver module for Ed's EZ Log Console - The cross-platform log console.
This server/receiver just takes JSON on a TCP socket, so it can have messages
sent to it from any process that can reach it. The default settings are
configured for local development.

For other python apps, you can add this library and import the `JsonSocketHandler`
class from the `sender` module. Or just copy it. It's 16 lines of code, not including
the comments and imports, because its a child of the standard library SocketHandler."""

# Standard library
# from __future__ import annotations
from typing import Any, TypeAlias
import errno
import logging
import logging.handlers
import socketserver
from socketserver import BaseRequestHandler
from socket import socket
import struct
from datetime import datetime
import sys
import os
import threading
import json
import re

# from dataclasses import dataclass

# Rich
from rich.rule import Rule
from rich.console import Console  # , ConsoleOptions, RenderResult
from rich.text import Text
from rich.style import Style

# from rich.segment import Segment
# from rich.logging import RichHandler


LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "cyan",
    logging.INFO: "green",
    logging.WARNING: "yellow",
    logging.ERROR: "bold bright_red",
    logging.CRITICAL: "white on red",
}

# I couldn't just import theirs because its marked private and the
# type checker doesn't like it.
_RequestType: TypeAlias = socket | tuple[bytes, socket]

# Create the rich console
# This has to be at the top level so the entire module can access it.
console = Console()


class LogRecordServer(socketserver.ThreadingTCPServer):
    # Allow reusing the port immediately after the server stops
    allow_reuse_address = True

    def __init__(
        self, server_address: tuple[str, int], RequestHandlerClass: type[BaseRequestHandler]
    ):
        # We need to keep track of the active senders.
        self.active_senders: dict[Any, str | None] = {}

        # Create a lock to keep the shared set safe
        self.set_lock = threading.Lock()

        super().__init__(server_address, RequestHandlerClass)


class LogRecordHandler(socketserver.StreamRequestHandler):
    # Since we pass this into the LogRecordServer in the main function
    # below, which is a ThreadingTCPServer, the TCP Server creates a new
    # LogRecordHandler instance in its own thread for each client connection.
    # So keep in mind that connections can't share data through this class
    # unless you were to store it as a class attribute. But that's not
    # a good idea here

    def __init__(
        self, request: _RequestType, client_address: tuple[str, int], server: LogRecordServer
    ):
        # super.init calls handle(), so any stuff that we want to add must
        # go before that.

        # Grab the lock and active senders attributes from the server object.
        # We want all the handlers to use the server's lock to be thread-safe.
        # We don't set a default value here because we want it to fail fast.
        try:
            self.set_lock: threading.Lock = getattr(server, "set_lock")
        except AttributeError:
            missing_attribute_error("set_lock")
            # A handler can't raise errors (they get swallowed by the logger), so
            # we have to exit the program manually. This has to be an os-level
            # exit call, even using server.shutdown() doesn't work here.
            os._exit(1)
        try:
            self.active_senders: dict[Any, str | None] = getattr(server, "active_senders")
        except AttributeError:
            missing_attribute_error("active_senders")
            os._exit(1)

        # Add the client address to the active senders dict. `None` in this
        # case just means we don't know the identity string from the sender yet.
        # But we still want to add the client address to the dict immediately.
        with self.set_lock:
            self.active_senders[client_address] = None

        console.print(Rule(characters="- - "))
        console.print(f"[green]{client_address} connected.")

        super().__init__(request, client_address, server)

    def handle(self) -> None:

        while True:
            try:
                # 1. Every TCP packet that Python's SocketHandler sends over the wire is
                # prefixed with a 4-byte header that encodes the length of the payload
                # that follows. So before you can read the packet, you need
                # to read those 4 bytes first to know how much is coming next.
                # rfile.read(4) blocks until all 4 bytes arrive or the connection drops.
                chunk = self.rfile.read(4)

                # If the length is less than 4 bytes, it means the connection has been
                # closed. In that case, we should break out of the loop.
                if len(chunk) < 4:
                    self.remove_client_address()
                    break

                # 2. This converts those 4 raw bytes into a Python integer. The format
                # string ">L" means big-endian (>) unsigned long (L), which is the format
                # Python's SocketHandler uses when it writes the length prefix on the sender
                # side. struct.unpack always returns a tuple even when there's one
                # value, so [0] pulls out that single integer.
                length = struct.unpack(">L", chunk)[0]

                # 2 and 1/2. Safety check- If the length is too long, we just skip it.
                # who knows what the sender is sending us.
                # A typical log message in JSON is a few hundred bytes. Here I've set
                # the limit to 10kb. That should be plenty for most people.
                # NOTE: This could be a config option in the future.
                if length > 10000:
                    console.print(f"[bright_red]Error: Log message length too long: {length}")
                    continue

                # 3. Read JSON payload
                data = self.rfile.read(length)

            except (ConnectionResetError, BrokenPipeError):
                self.remove_client_address()
                break
            except Exception as e:
                console.print(f"[bright_red]Error reading data-stream: {e}")
                self.remove_client_address()
                break

            try:
                # 4. Decode and Process
                log_dict = json.loads(data.decode("utf-8"))
                record = logging.makeLogRecord(log_dict)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                console.print(f"[bright_red]Error decoding JSON: {e}")
                # For JSON decoding errors, we just skip and continue
                continue

            # If we have a record name, see if the sender is still named 'None'.
            # It's required for python LogRecords but not necessarily for
            # other languages, so I'd like to leave the door open.
            if record.name and not self.active_senders[self.client_address]:
                with self.set_lock:
                    self.active_senders[self.client_address] = record.name
                console.print(f"[green]{self.client_address} identified as " f"{record.name}")

            # aaaand print it
            print_record(record)

    def remove_client_address(self) -> None:

        # Check if the client was given a name in the active senders dict.
        # The client address is added to the active senders dict in the
        # constructor, so logically this should be a safe operation.
        if self.active_senders[self.client_address]:
            console.print(
                f"[blue]{self.active_senders[self.client_address]} "
                f"{self.client_address} disconnected."
            )
        else:
            console.print(f"[blue]{self.client_address} disconnected.")

        with self.set_lock:
            del self.active_senders[self.client_address]


def missing_attribute_error(attrib: str) -> None:

    console.print(
        f"[bright_red]FATAL ERROR: Could not find `{attrib}` attribute "
        "on the server object. This LogRecordHandler is designed to work "
        "with the LogRecordServer class, so if you're seeing this error, "
        "you must have used it with a different server class. Ensure "
        "your duck typing matches what is expected."
    )


def print_record(record: logging.LogRecord) -> None:

    # NOTE: One might traditionally use the Rich Handler for this, as
    # shown below. But I don't really like the formatting that much, I find
    # its not great for very skinny log consoles. So I designed my own
    # formatting using the Text class. But below is the code for the
    # traditional easy way of doing this:

    # rich_handler = RichHandler(
    #     console=console,
    #     log_time_format="[%X]",
    # )
    # rich_handler.emit(record)

    # My code below is designed to look good on skinny consoles.
    # It does this by putting everything in a single line and letting
    # the console word wrap do its thing.

    color = LEVEL_COLORS.get(record.levelno, "white")
    line = Text()
    ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
    line.append(f"{ts} ", style="dim")
    line.append(f"[{record.levelname}] ", style=color)
    # Colorize message using the function below:
    line.append(message_colorizer(record.getMessage()))
    line.append(f"  ({record.filename}:{record.lineno})", style="grey23 italic")
    console.print(line)

    # Now we want to check if there's an exception attached to the record.
    # If there is, we want to print it out.
    # NOTE: Whether to show this should be a config option in the future.
    if record.exc_info:
        console.print(f" {record.exc_info}")

    # NOTE: It could make a good customization option in the future to
    # switch between RichHandler and my own Text-based formatting


def message_colorizer(message: str) -> Text:

    richtxt = Text(message)

    # Colorize the word 'True' in the message, if it exists:
    for match in re.finditer(r"(True)", message):
        richtxt.stylize(Style(color="blue", bold=True, italic=True), match.start(), match.end())

    # Colorize the word 'False' in the message, if it exists:
    for match in re.finditer(r"(False)", message):
        richtxt.stylize(
            Style(color="bright_red", bold=True, italic=True), match.start(), match.end()
        )

    # Look for any POSIX-style file paths in the message:
    for match in re.finditer(r"(/[^/ ]+)", message):
        richtxt.stylize(Style(color="yellow", italic=True), match.start(), match.end())

    return richtxt


def main() -> None:

    host = "localhost"  #! These should be CLI options in the future
    port = logging.handlers.DEFAULT_TCP_LOGGING_PORT  # python default is 9020

    with LogRecordServer((host, port), LogRecordHandler) as server:
        console.print("[cyan]EZ Log Console initialized.")
        console.print(f"Listening on {host}:{port}")
        server.serve_forever()


def run() -> None:

    try:
        main()
    except KeyboardInterrupt:
        console.print("[bright_red]  [Quitting EZ Log Console]")
        sys.exit(0)
    except Exception as e:
        if isinstance(e, OSError) and e.errno == errno.EADDRINUSE:
            console.print(
                f"[bright_red]Port {9020} is already in use. Either close "
                "that program or choose a different port."
            )
            sys.exit(1)

        console.print("[bright_red]ERROR WITH CONSOLE ITSELF")
        console.print_exception(word_wrap=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
