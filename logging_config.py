import logging
import os
import sys

from environs import Env

import api as api_module


env = Env()
env.read_env()

LOG_LEVEL = env.log_level('LOG_LEVEL', logging.INFO)
LOG_API_DIR = 'log'
ROOT_MODULE_NAME = 'liturgi_format_converter'
API_MODULE_NAME = f'{ROOT_MODULE_NAME}.{api_module.__name__}'

logging.basicConfig(level=LOG_LEVEL, stream=sys.stdout)
logging.debug(f'ROOT_MODULE_NAME is: {ROOT_MODULE_NAME}')
logging.debug(f'API_LOGGER_NAME is: {API_MODULE_NAME}')

os.makedirs(LOG_API_DIR, exist_ok=True)
LOGGING_CONFIG = dict(
    version = 1,
    disable_existing_loggers = False,
    root={'level': LOG_LEVEL, 'handlers': []},
    loggers = {
        ROOT_MODULE_NAME: {
            'handlers': ['console_handler', 'time_rotating_file_handler_root']
        },
        API_MODULE_NAME: {
            'handlers': ['console_handler', 'time_rotating_file_handler_api'],
            'propagate': False
        },
        'pdfminer': {
            'level': logging.ERROR
        }
    },
    handlers = {
        'console_handler': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'time_rotating_file_handler_root': {
            'formatter': 'default',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': f'./{LOG_API_DIR}/log_main',
            'encoding': 'utf-8',
            'when': 'midnight',
            'backupCount': 30
        },
        'time_rotating_file_handler_api': {
            'formatter': 'default',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': f'./{LOG_API_DIR}/log_api',
            'encoding': 'utf-8',
            'when': 'midnight',
            'backupCount': 30
        },
    },
    formatters = {
        'default': {
            'format': '%(asctime)s [%(levelname)s - %(name)s - %(filename)s:%(lineno)s] > %(message)s'
        },
    },
)
