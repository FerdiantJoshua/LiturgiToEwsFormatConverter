from enum import Enum
import os
import json
import logging
from typing import Union, List, Optional

from environs import Env
from fastapi import FastAPI, Request, status, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator
from starlette.responses import JSONResponse, FileResponse

from logging_config import ROOT_MODULE_NAME
from parse_pdf import MAX_CHAR_PER_LINE
from .config import API_CONFIG
from .converter_wrapper import ConverterWrapper

logger = logging.getLogger(f'{ROOT_MODULE_NAME}.{__name__}')

class TextRequest(BaseModel):
    text: str

    @validator('text')
    def error_on_blank_text(cls, val):
        if not val:
            raise ValueError('empty string in \'text\' is not an allowed value')
        return val

class PostprocessRequest(TextRequest):
    is_formatted: bool = False


def create_app(debug: bool = False):
    converter_wrapper = ConverterWrapper(debug)

    app = FastAPI(
        title='Liturgi Format Converter API',
        description='An API which serves iiturgi format conversions.',
        version='0.1.0'
    )
    app.mount("/static/", StaticFiles(directory="api/static"), name="static")

    @app.get('/')
    async def index(request: Request):
        return FileResponse('api/static/index.html')

    @app.post('/convert')
    async def convert(input_file: UploadFile = File(...), max_char_per_line: Optional[int] = Form(MAX_CHAR_PER_LINE)):
        logger.debug('Filename: "%s". Max char per line: "%d"', input_file.filename, max_char_per_line)
        input_file.file.filename = input_file.filename
        conversion_result = converter_wrapper.convert(input_file.file, max_char_per_line)

        response = JSONResponse(
            conversion_result,
            status_code=status.HTTP_200_OK
        )
        return response

    @app.post('/format-text')
    async def format_text(request_body: TextRequest):
        formatted = converter_wrapper.format_text_in_html(request_body.text)
        response = JSONResponse(
            formatted,
            status_code=status.HTTP_200_OK
        )
        return response

    @app.post('/postprocess')
    async def postprocess(request_body: PostprocessRequest):
        postprocessed = converter_wrapper.postprocess(request_body.text, request_body.is_formatted)
        response = JSONResponse(
            postprocessed,
            status_code=status.HTTP_200_OK
        )
        return response

    @app.get('/reload-logging-config')
    async def reload_logging_config():
        env = Env()
        env.read_env(override=True)
        log_level = env.log_level('LOG_LEVEL', logging.INFO)
        logging.root.setLevel(log_level)
        converter_wrapper.debug = log_level==logging.DEBUG
        return {'log_level': logging.getLevelName(logging.root.level)}

    @app.get('/health')
    def health():
        return 'OK'

    return app
