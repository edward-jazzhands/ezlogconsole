# EZLogConsole

<img alt="preview" src="https://edward-jazzhands.github.io/assets/ezlogconsole/screenshot1.png" />

[![badge](https://img.shields.io/pypi/v/ezlogconsole)](https://pypi.org/project/ezlogconsole/)
[![badge](https://img.shields.io/github/v/release/edward-jazzhands/ezlogconsole)](https://github.com/edward-jazzhands/ezlogconsole/releases/latest)
[![badge](https://img.shields.io/badge/Requires_Python->=3.11-blue&logo=python)](https://python.org)
[![badge](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit)

An ultra-simple, modern, and JSON-based logging console with an included logging handler for the Python standard library's `logging` module, and console built with the [Rich](https://github.com/Textualize/rich) library.

This first alpha release is only designed with python log records in mind, but under the hood its just a simple TCP server that decodes JSON and prints it to the console. This means any process from any language can send logs to the console. This will be better supported in the future.

You can also just copy paste the code for the logging handler if you don't want to add it as a project dependency. Either way, it'll connect the standard library logger to the console, and pretty-print the logs in a nice, readable format.

## Reason for this project

The typical examples shown of building a local, socket-based logging receiver by the official python docs and most beginner tutorials, demonstrate usage of the standard library's 'SocketHandler' class. This is a useful class, however it uses 'pickling' to send log records as serialized python objects over a socket.

This was great when it was first invented in 2001, but it's not really a good idea to use pickling for logging. Mostly because it's an attack vector for remote code execution. Even for local logging, it's generally considered bad practice to use pickling.

The modern way to send log records over a socket is to use JSON. This is a much more secure way to send log records, and it's also more universal and portable. But the standard library's logging module doesn't have a built in JSON-based handler. So you would first need to write a JSON logging handler, and add it to your logging configuration. Then you also have to build yourself a socket handler class that uses the JSON handler instead of the default one, for passing into the TCPServer class from the `socketserver` module.

Then also factor in using the Rich library for formatting the log records with colors and other things, and the Click library for adding CLI options to the console. It should also be installable as a tool with either UV or PipX. You put it all together, and it becomes quite a lot of work just to build yourself a modern safe logging receiver console.

I did this once, and I said "This should be a library so I don't have to do this again." And thus, EZLogConsole was born.

## Installation

### Requirements

- UV or pipX to install as a global tool
- Python 3.11 or higher needed if adding into a project

### As a tool

Use either [UV](https://github.com/astral-sh/uv) or [PipX](https://pipx.pypa.io/)

```sh
uv tool install ezlogconsole
```

```sh
pipx install ezlogconsole
```

### Into project/venv

```sh
pip install ezlogconsole
```

Or, with UV:

```sh
uv add ezlogconsole
```

## Documentation

### Logging Handler

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

The handler can also take `host` and `port` arguments. The default host is `localhost` and the default port is `9020`. You can change these by passing different values to the handler:

```python
handler = JsonSocketHandler(host="192.168.1.100", port=9021)
```

The handler is a child of the standard library SocketHandler. The code is quite short, so you can easily copy paste it into your project in order to avoid adding ezlogconsole as a dependency. You can view the code [here](https://github.com/edward-jazzhands/ezlogconsole/blob/main/src/ezlogconsole/sender.py).

### Logging Receiver

After you've installed the EZLogConsole either as a tool or into your project environment (assuming the environment is activated), you can run it from the command line:

```sh
ezlogconsole
```

If you've installed into the local environment using UV, you'd generally not be activating the python environment, but instead run it with:

```sh
uv run ezlogconsole
```

This will start the EZLogConsole receiver on the default port (9020). 

#### CLI Options

- **--host** or **-h** - Host to listen on. Default is `localhost`.
- **--port** or **-p** - Port to listen on. Default is `9020`.
- **--max-bytes** or **-m** - Maximum bytes to read per log message. Default is `10000`.
- **--rich-handler** or **-r** - Use standard RichHandler instead of my own skinny-console formatter. Default is `False`.
- **--exceptions** or **-e** - Show full exception tracebacks in log messages. Default is `False`.

You can change the port by passing a different port number:

```sh
ezlogconsole --port 9021
```

The host address defaults to `localhost`.   
You can also specify a different host address:

```sh
ezlogconsole --host 192.168.1.100
```

You can set the max bytes to read per log message. The default is `10000` (10kb) which should be enough for most log messages (This is a safety feature). But you can change it if you need to:

```sh
ezlogconsole --max-bytes 20000
```

The Rich library, which provides the console itself, also provides a logging handler for printing log messages to the console. It uses tables, and looks better if the terminal is fairly wide. You can use this handler instead of the default one by passing the `--rich-handler` flag:

```sh
ezlogconsole --rich-handler
```

And finally, you can show full exception tracebacks in log messages that have an exception attached:

```sh
ezlogconsole --exceptions
```

## Future Plans

- Document the JSON format for log messages so that other languages can send logs to the console.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
