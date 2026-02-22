"""Sender/Handler module for Ed's EZ Log Console - The cross-platform log console.
This class is a child of the standard library SocketHandler.

For python development, add this JsonSocketHandler as a handler for the standard library
logger. It will send JSON messages to the EZ Log Console receiver.  The default 
settings are configured for local development.
"""

import logging
import logging.handlers as handlers
import json
import struct


class JsonSocketHandler(handlers.SocketHandler):

    def __init__(self, host: str = "localhost", port: int | None = handlers.DEFAULT_TCP_LOGGING_PORT):
        """Initializes the handler with a specific host address and port. Default host
        is 'localhost' and default port is 9020.

        When the attribute *closeOnError* is set to True - if a socket error
        occurs, the socket is silently closed and then reopened on the next
        logging call.
        """
        super().__init__(host, port)

    # The original method is called makePickle. We need to override it.
    # Note that this new version does not pickle the object, we're converting it
    # to a dictionary and then encoding it to JSON. It just happens that this
    # is the best shortcut to build a JSON Socket Handler. Otherwise recreating
    # a similar class would be much more work.
    def makePickle(self, record):
        """OVERRIDE by JsonSocketHandler. This does NOT pickle the record.
        It converts it to a dictionary and then encodes it to JSON."""

        # Convert the LogRecord to a dictionary
        data = record.__dict__.copy()
        
        # 2. Handle the Exception/Traceback safely
        if record.exc_info:
            # If the record has an exception, we use the formatter to 
            # turn the traceback object into a JSON-friendly string.
            formatter = self.formatter if self.formatter else logging.Formatter()

            data['exc_info'] = formatter.formatException(record.exc_info)
            
        # 3. Clean up other non-serializable fields (optional but safe)
        # Some records contain objects that JSON hates. We ensure 'msg' is a string.
        data['msg'] = record.getMessage()

        # 4. Remove args from the dictionary (optional but safe)
        # We want to remove args because once getMessage() has been, called the args 
        # are already baked into msg, so they're redundant and potentially 
        # carry non-serializable objects.
        data.pop('args', None)

        # Encode to JSON and then to bytes    
        try:
            s = json.dumps(data).encode('utf-8')
        except Exception as e:
            # This could happen if there was anything still in the record's
            # attributes that wasn't serializable.
            e.add_note("Failure in JsonSocketHandler to encode record to JSON.")
            raise e
        
        # Prefix with 4-byte length (Big-Endian) just like the original
        return struct.pack(">L", len(s)) + s
