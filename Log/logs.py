import logging
from colorlog import ColoredFormatter


class Logs:
    """
    Class for managing logs with colored formatting.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def Returnlog(name: str, function_name: str = "") -> logging.Logger:
        """
        Configures and returns a logger with colored formatting.

        Args:
        -----
        name : str
            Name of the logger.
        function_name : str, optional
            Name of the function associated with the logger. Default is an empty string.

        Returns:
        --------
        logging.Logger
            Configured logger object.
        """
        log = logging.getLogger(name + " -> " + function_name)
        log.setLevel(logging.DEBUG)

        # Check if the logger already has handlers to avoid duplicating logs
        if not log.hasHandlers():
            LOG_COLORS = {
                "DEBUG": "white",
                "INFO": "green",
                "ERROR": "red",
                "WARNING": "blue",
            }

            formatter = ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(filename)s - %(log_color)s%(levelname)-8s: %(log_color)s%(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors=LOG_COLORS,
                reset=True,
                style="%",
            )

            file_handler = logging.FileHandler(".\\Log\\log_app.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)

            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.DEBUG)
            stream_handler.setFormatter(formatter)

            log.addHandler(file_handler)
            log.addHandler(stream_handler)

        return log
