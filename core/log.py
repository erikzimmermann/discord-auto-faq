import logging
import sys

logger: logging.Logger = logging.getLogger('nextcord')


class LoggingFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def load_logging_handlers() -> None:
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a')
    handler.setFormatter(LoggingFormatter())
    logger.addHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(LoggingFormatter())
    logger.addHandler(handler)


def combine(message: str, args: [object]) -> str:
    if args and len(args) > 0:
        for arg in args:
            message += " " + str(arg)
    return message


def info(message: str, *args) -> None:
    logger.info(combine(message, args))


def warning(message: str, *args) -> None:
    logger.warning(combine(message, args))


def error(message: str, *args) -> None:
    logger.error(combine(message, args))


def critical(message: str, *args) -> None:
    logger.critical(combine(message, args))
