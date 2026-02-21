import logging
import logging.handlers

def setup_logging() -> None:
    
    handler = logging.handlers.SocketHandler(
        "localhost",
        logging.handlers.DEFAULT_TCP_LOGGING_PORT,  # 9020
    )
    logging.basicConfig(level=logging.DEBUG, handlers=[handler])


if __name__ == "__main__":
    setup_logging()
    log = logging.getLogger("myapp")

    log.debug("Starting up")
    log.info("Everything is fine")
    log.warning("Something looks off")
    log.error("Something broke")