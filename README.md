# EZPubSub

[![badge](https://img.shields.io/pypi/v/ezlogconsole)](https://pypi.org/project/ezlogconsole/)
[![badge](https://img.shields.io/github/v/release/edward-jazzhands/ezlogconsole)](https://github.com/edward-jazzhands/ezlogconsole/releases/latest)
[![badge](https://img.shields.io/badge/Requires_Python->=3.11-blue&logo=python)](https://python.org)
[![badge](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit)

An ultra-simple, modern, and JSON-based logging console with an included logging handler for the standard library's `logging` module. You can also just copy paste the code for the logging handler if you don't want to add it as a project dependency. Either way, it'll connect the standard library logger to the console, and pretty-print the logs in a nice, readable format.

This first alpha release is only designed with python log records in mind, but under the hood its just a simple TCP server that decodes JSON and prints it to the console. This means any process from any language can send logs to the console. This will be better supported in the future.

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
