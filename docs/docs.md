# EZLogConsole<br>Documentation and Guide

## Requirements

- Python 3.11 or higher if adding into a project
- UV or pipX to install as a global tool

## Installation into project

```sh
pip install ezlogconsole
```

Or, with [UV](https://github.com/astral-sh/uv):

```sh
uv add ezlogconsole
```

## Install as tool

Use either UV or PipX

```sh
uv tool install ezlogconsole
```

```sh
pipx install ezlogconsole
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

After you've installed the EZLogConsole either as a tool or into your project environment, you can run it from the command line:

```sh
ezlogconsole
```

This assumes you've activated the environment. If you've installed into the local environment using UV, you'd generally run it with:

```sh
uv run ezlogconsole
```

This will start the EZLogConsole receiver on the default port (9020). 

You can change the port by passing a different port number:

```sh
ezlogconsole --port 9021
```

The host address defaults to `localhost`.   
You can also specify a different host address:

```sh
ezlogconsole --host 192.168.1.100
```