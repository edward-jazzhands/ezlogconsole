import logging
from time import sleep
from random import random
from ezlogconsole import JsonSocketHandler

handler = JsonSocketHandler()

logger = logging.getLogger("my-program")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
sleep(random())
logger.debug("My Program starting...")

logger.debug("Loading configuration from /home/zara/.config/my-program/config.toml")
sleep(random())
logger.info("Configuration loaded successfully")

logger.debug("debug_mode = True")
logger.debug("dry_run = False")
logger.debug("verbose = True")
sleep(random())
logger.info("Resolved data directory: /home/zara/.local/share/my-program/data")
logger.info("Resolved cache directory: /tmp/my-program/cache")
logger.debug("Cache directory exists = True")
logger.debug("Data directory exists = False — creating...")
sleep(random())
logger.info("Created missing data directory at /home/zara/.local/share/my-program/data")

logger.info("Connecting to database at /home/zara/.local/share/my-program/data/app.db")
logger.debug("use_wal_mode = True")
logger.debug("connection_timeout = 5.0")
sleep(random())
logger.info("Database connection established")

logger.debug("Plugin directory: /home/zara/.config/my-program/plugins")
logger.debug("Plugin directory exists = True")
logger.info("Discovered 3 plugins: ['analytics.so', 'notifier.so', 'exporter.so']")
logger.debug("Loading plugin: /home/zara/.config/my-program/plugins/analytics.so")
sleep(random())
logger.debug("Loading plugin: /home/zara/.config/my-program/plugins/notifier.so")
logger.warning("Plugin notifier.so requests elevated permissions — user consent required")
logger.debug("user_consented = True")
logger.debug("Loading plugin: /home/zara/.config/my-program/plugins/exporter.so")
sleep(random())
logger.info("All plugins loaded successfully")

logger.debug("output_path = /home/zara/Documents/my-program/output")
logger.debug("overwrite_existing = False")
logger.debug("compress_output = True")
sleep(random())
logger.info("Startup complete — ready to rock 🎸")