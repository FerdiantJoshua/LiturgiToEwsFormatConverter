import logging
from logging.config import dictConfig

import uvicorn

from logging_config import LOGGING_CONFIG, LOG_LEVEL
from api.main import create_app
from api.config import API_CONFIG

dictConfig(LOGGING_CONFIG)

liturgi_format_converter_api = create_app(LOG_LEVEL==logging.DEBUG)


if __name__ == '__main__':
    uvicorn.run(liturgi_format_converter_api, host=API_CONFIG['hostname'], port=API_CONFIG['port'])
