from enum import Enum
import os
import json
import logging
from typing import Union, List, Optional

from environs import Env
from flask import Flask, jsonify, request, send_from_directory

from logging_config import ROOT_MODULE_NAME
from parse_pdf import MAX_CHAR_PER_LINE
from .config import API_CONFIG
from .converter_wrapper import ConverterWrapper

logger = logging.getLogger(f'{ROOT_MODULE_NAME}.{__name__}')


def create_app(debug: bool = False):
    converter_wrapper = ConverterWrapper(debug)

    app = Flask(__name__,
                static_url_path='/static',
                static_folder='static')

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/convert', methods=['POST'])
    def convert():
        input_file = request.files['input_file']
        max_char_per_line = request.form.get('max_char_per_line', MAX_CHAR_PER_LINE)
        logger.debug('Filename: "%s". Max char per line: "%d"', input_file.filename, max_char_per_line)
        conversion_result = converter_wrapper.convert(input_file, max_char_per_line)

        response = jsonify(conversion_result)
        return response

    @app.route('/format-text', methods=['POST'])
    def format_text():
        body = request.json
        formatted = converter_wrapper.format_text_in_html(body.get('text', ''))
        response = jsonify(formatted)
        return response

    @app.route('/postprocess', methods=['POST'])
    def postprocess():
        body = request.json
        postprocessed = converter_wrapper.postprocess(body.get('text', ''), body.get('is_formatted', False))
        response = jsonify(postprocessed)
        return response

    @app.route('/reload-logging-config')
    def reload_logging_config():
        env = Env()
        env.read_env(override=True)
        log_level = env.log_level('LOG_LEVEL', logging.INFO)
        logging.root.setLevel(log_level)
        converter_wrapper.debug = log_level==logging.DEBUG
        return jsonify({'log_level': logging.getLevelName(logging.root.level)})

    @app.route('/health')
    def health():
        return 'OK'

    return app
