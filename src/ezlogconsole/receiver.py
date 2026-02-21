"""Receiver module for Ed's EZ Log Console - The cross-platform log console.
This server/receiver just takes JSON on a TCP socket, so it can have messages
sent to it from any process that can reach it. The default settings are
configured for local development.

For other python apps, you can add this library and import the `JsonSocketHandler` 
class from the `sender` module. Or just copy it. It's 12 lines of code, not including 
the comments and imports."""

# Standard library
# from __future__ import annotations
from typing import Any
import logging
import logging.handlers
import socketserver
import struct
from datetime import datetime
import sys
import os
import threading
import json

# Rich
from rich.rule import Rule
from rich.console import Console
from rich.text import Text, Span
from rich.segment import Segment
from rich.logging import RichHandler


LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "cyan",
    logging.INFO: "green",
    logging.WARNING: "yellow",
    logging.ERROR: "red",
    logging.CRITICAL: "bold red",
}

# Create a lock to keep the shared set safe
set_lock = threading.Lock()

# Create the rich console
console = Console()


class LogRecordHandler(socketserver.StreamRequestHandler):
    # Since we pass this into the LogRecordServer in the main function
    # below, which is a ThreadingTCPServer, the TCP Server creates a new
    # LogRecordHandler instance for each client connection in its own thread.
    # So keep in mind that connections can't share data through this class
    # unless you were to store it as a class attribute. But that's not
    # a good idea here 
        
    def handle(self) -> None:

        # The self.client_address attribute is typed as `Any` by the logging lib.
        # So trying to be more specific here has no effect on the type checker.
        self.active_senders: dict[Any, str | None] | None = getattr( 
            self.server, "active_senders", None
        )
        if self.active_senders is None:
            console.print(
                "[bright_red]FATAL ERROR: Could not find `active_senders` attribute "
                "on the server object. This LogRecordHandler is designed to work "
                "with the LogRecordServer class, so if you're seeing this error, "
                "you must have used it with a different server class. Ensure "
                "your duck typing matches what is expected."
            )
            os._exit(1)

        while True:
            try:
                # 1. Every TCP packet that Python's SocketHandler sends over the wire is
                # prefixed with a 4-byte header that encodes the length of the payload 
                # that follows. So before you can read the packet, you need 
                # to read those 4 bytes first to know how much is coming next. 
                # rfile.read(4) blocks until all 4 bytes arrive or the connection drops.
                chunk = self.rfile.read(4)

                # If the length is less than 4 bytes, it means the connection has been 
                # closed. In that case, we can just break out of the loop.                
                if len(chunk) < 4:
                    if self.client_address in self.active_senders:
                        console.print(
                            f"[blue]{self.active_senders[self.client_address]} "
                            f"{self.client_address} disconnected."
                        )
                        with set_lock:
                            del self.active_senders[self.client_address]
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
                # Connection was closed
                console.print(f"[blue]{self.client_address} disconnected.")
                break 
            except Exception as e:
                console.print(f"[bright_red]Error reading data-stream: {e}")
                break
                
            try:
                # 4. Decode and Process
                log_dict = json.loads(data.decode('utf-8'))
                record = logging.makeLogRecord(log_dict)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                console.print(f"[bright_red]Error decoding JSON: {e}")
                # For JSON decoding errors, we just skip and continue
                continue

            # check known senders
            if self.client_address not in self.active_senders:
                with set_lock:
                    self.active_senders[self.client_address] = record.processName
                console.print(Rule(characters="- - "))
                console.print(
                    f"[green]{record.processName} {self.client_address} connected."
                ) 

            # aaaand print it
            print_record(record)


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

    # for future upgrades to formatting the message:
    # message = record.getMessage()

    line.append(record.getMessage())
    line.append(f"  ({record.filename}:{record.lineno})", style="grey23 italic")
    console.print(line)

    # NOTE: This would make a good customization option in the future
    # (eg. switch between RichHandler and my own Text-based formatting)

class LogRecordServer(socketserver.ThreadingTCPServer):
    # Allow reusing the port immediately after the server stops
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        # This is the only change from the original class.
        # We need to keep track of the active senders.
        self.active_senders = {}

        super().__init__(server_address, RequestHandlerClass)


def main():

    host = "localhost"  #! This could be an option in the future
    port = logging.handlers.DEFAULT_TCP_LOGGING_PORT  # python default is 9020

    with LogRecordServer((host, port), LogRecordHandler) as server:
        console.print(f"[cyan]EZ Log Console initialized.")
        console.print(f"[dim]Listening on {host}:{port}[/dim]")
        server.serve_forever()

def run():

    try:
        main()
    except KeyboardInterrupt:
        console.print("bright_red]  [Quitting EZ Log Console]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bright_red]ERROR WITH CONSOLE ITSELF")
        console.print_exception(word_wrap=True)
        sys.exit(1)

if __name__ == "__main__":
    run()