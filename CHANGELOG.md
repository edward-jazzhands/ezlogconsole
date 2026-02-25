# ezlogconsole Changelog

## [0.2.0] 2026-02-24

- Added click CLI. Now possible to set the following config options:
  - host (default: localhost)
  - port (default: 9020)
  - max_bytes (default: 10000)
  - rich_handler (default: False)
  - exceptions (default: False)
- Changed using 'name' attribute of LogRecord to identify senders
  instead of 'processName'.
- Added port already in use error check.

**Developers:**
- Added type hints, now passes mypy and basedpyright in strict mode.
- Added unit tests, confirmed passing Nox for python 3.11 and 3.14.


## [0.1.0] 2026-02-21

- Initial release
