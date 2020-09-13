# REFERENCE: https://gist.github.com/huklee/cea20761dd05da7c39120084f52fcc7c
import datetime
import logging
import os


class SingletonType(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Logger(object, metaclass=SingletonType):
    _logger = None

    def __init__(self, log_level=logging.INFO):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s - %(filename)s:%(lineno)s] > %(message)s')

        now = datetime.datetime.now()
        dirname = "./log"

        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        fileHandler = logging.FileHandler(dirname + "/log_" + now.strftime("%Y-%m-%d") + ".log")

        streamHandler = logging.StreamHandler()

        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)

        self._logger.addHandler(fileHandler)
        self._logger.addHandler(streamHandler)

        self._logger.debug("Generating new logger instance")

    def get_logger(self):
        return self._logger
