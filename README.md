# EZLogConsole

[![badge](https://img.shields.io/pypi/v/ezlogconsole)](https://pypi.org/project/ezlogconsole/)
[![badge](https://img.shields.io/github/v/release/edward-jazzhands/ezlogconsole)](https://github.com/edward-jazzhands/ezlogconsole/releases/latest)
[![badge](https://img.shields.io/badge/Requires_Python->=3.11-blue&logo=python)](https://python.org)
[![badge](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit)

An ultra-simple, modern, and JSON-based logging console with an included logging handler for the standard library's `logging` module. You can also just copy paste the code for the logging handler if you don't want to add it as a project dependency. Either way, it'll connect the standard library logger to the console, and pretty-print the logs in a nice, readable format.

This first alpha release is only designed with python log records in mind, but under the hood its just a simple TCP server that decodes JSON and prints it to the console. This means any process from any language can send logs to the console. This will be better supported in the future.

## Reason for this project

The typical examples shown of building a local, socket-based logging receiver by the official python docs and most beginner tutorials, demonstrate usage of the standard library's 'SocketHandler' class. This is a useful class, however it uses 'pickling' to send log records as serialized python objects over a socket.

This was great when it was first invented in 2001, but it's not really a good idea to use pickling for logging. Mostly because it's an attack vector for remote code execution. Even for local logging, it's generally considered bad practice to use pickling.

The modern way to send log records over a socket is to use JSON. This is a much more secure way to send log records, and it's also more universal and portable. But the standard library's logging module doesn't have a built in JSON-based handler. So you would first need to write a JSON logging handler, and add it to your logging configuration. Then you also have to build yourself a socket handler class that uses the JSON handler instead of the default one, for passing into the TCPServer class from the `socketserver` module.

Then also factor in using the Rich library for formatting the log records with colors and other things, and the Click library for adding CLI options to the console. It becomes quite a lot of work just to build yourself a modern safe logging receiver console.

I also wanted something that integrates with the standard library's logging module. So put it al together, and you've got EZLogConsole.

## Install as tool

Use either [UV](https://github.com/astral-sh/uv) or [PipX](https://pipx.pypa.io/)

```sh
uv tool install ezlogconsole
```

```sh
pipx install ezlogconsole
```

## Install into project/venv

```sh
pip install ezlogconsole
```

Or, with UV:

```sh
uv add ezlogconsole
```

## Quick Start

**Logging Handler**

```python
from ezlogconsole import JsonSocketHandler

# Create a handler
handler = JsonSocketHandler()

# Add it to the logger
logger = logging.getLogger()
logger.addHandler(handler)

# The handler doesn't need a formatter since we are using JSON

# Now the EZ console is a receiver for your logs
logger.info("Hello, world!")
```

**Logging Receiver**

After you've installed the EZLogConsole as a tool using either UV or PipX, you can run it from the command line:

```sh
ezlogconsole
```

This will start the EZLogConsole receiver on the default port (9020). 

You can change the port by passing a different port number:

```sh
ezlogconsole --port 9021
```

For more options on both the console and the handler, see the docs.

## Documentation

Full docs: [**Click here**](https://edward-jazzhands.github.io/libraries/ezlogconsole/docs/)

---

## License

MIT License. See [LICENSE](LICENSE) for details.
