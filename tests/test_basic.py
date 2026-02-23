# from typing import TypedDict
import logging.handlers
from ezlogconsole import JsonSocketHandler, LogRecordServer, LogRecordHandler

DEFAULT_HOST = "localhost"  
DEFAULT_PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT 

# with LogRecordServer((host, port), LogRecordHandler) as server: