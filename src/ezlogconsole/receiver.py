"Receiver module for Ed's EZ Log Console"

import logging
import logging.handlers
import pickle
import socketserver
import struct
from datetime import datetime
import sys

from rich.rule import Rule
from rich.console import Console
from rich.text import Text
from rich.logging import RichHandler

console = Console()

LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "cyan",
    logging.INFO: "green",
    logging.WARNING: "yellow",
    logging.ERROR: "red",
    logging.CRITICAL: "bold red",
}


class LogRecordHandler(socketserver.StreamRequestHandler):

    known_senders = set()

    def handle(self) -> None:

        while True:

            # Every log record that Python's SocketHandler sends over the wire is 
            # prefixed with a 4-byte header that encodes the length of the payload 
            # that follows. So before you can read the actual log data, you need 
            # to read those 4 bytes first to know how much is coming next. 
            # rfile.read(4) blocks until all 4 bytes arrive or the connection drops.
            chunk = self.rfile.read(4)

            # If the length is less than 4 bytes, it means the connection has been 
            # closed. In that case, we can just break out of the loop.
            if len(chunk) < 4:
                break

            # This converts those 4 raw bytes into a Python integer. The format 
            # string ">L" means big-endian (>) unsigned long (L), which is the format 
            # Python's SocketHandler uses when it writes the length prefix on the sender 
            # side. struct.unpack always returns a tuple even when there's one 
            # value, so [0] just pulls out that single integer.
            length = struct.unpack(">L", chunk)[0]

            # Now we read the length that was specified in the header.
            data = self.rfile.read(length)

            # Since we know the data is a serialized LogRecord, we now
            # can deserialize it. pickle.loads(data) deserializes those bytes 
            # back into a Python dictionary of the log record's attributes 
            # (things like levelno, msg, name, created, etc.). Then 
            # logging.makeLogRecord() is designed to take a dictionary of
            # these attributes and turn it into a LogRecord object.
            record = logging.makeLogRecord(pickle.loads(data))

            # check known senders
            if self.client_address not in self.known_senders:
                self.known_senders.add(self.client_address)
                console.print(Rule())
                console.print(f"[cyan]New sender detected: {self.client_address}[/cyan]")

            # TO USE SENTINEL LOGS:
            # 1) Create a log record with level number 0.
            # 2) Set the record.name to either "connect" or "disconnect".
            # 3) Set the record.processName to the name of the sending program.
            # 4) Send it.
            if record.levelno == 0:
                # This is a sentinel record. We check the name to see
                # what type of sentinel it is.
                if record.name == "connect":
                    console.print(f"[green]'{record.processName}' ({self.client_address}) has connected.")
                    console.print(Rule(characters="- - "))
                elif record.name == "disconnect":
                    console.print(f"[blue]{record.processName} ({self.client_address}) disconnected.")
                continue

            # aaaand print it
            self.print_record(record)

    def print_record(self, record: logging.LogRecord) -> None:

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

        # My code below is designed to look good on skinny consoles:

        color = LEVEL_COLORS.get(record.levelno, "white")
        line = Text() 
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        line.append(f"{ts} ", style="dim")
        line.append(f"[{record.levelname}] ", style=color)
        line.append(record.getMessage())
        line.append(f"  ({record.filename}:{record.lineno})", style="grey23 italic")
        console.print(line)

        # NOTE: This would make a good customization option in the future
        # (eg. switch between RichHandler and my own Text-based formatting)

class LogRecordServer(socketserver.ThreadingTCPServer):
    # Allow reusing the port immediately after the server stops
    allow_reuse_address = True

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
        console.print("[red]  [Quitting EZ Log Console]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]ERROR WITH CONSOLE ITSELF")
        console.print_exception()
        sys.exit(1)

if __name__ == "__main__":
    run()