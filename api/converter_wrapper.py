import io
import json
import logging
from tempfile import SpooledTemporaryFile
from typing import List, Optional

from pdfminer.high_level import extract_text

from logging_config import ROOT_MODULE_NAME
from output_augmenter import postprocess_text
from parse_pdf import MAX_CHAR_PER_LINE, parse_converted_pdf


logger = logging.getLogger(f'{ROOT_MODULE_NAME}.{__name__}')

class ConverterWrapper:
    def __init__(self):
        pass

    def convert(self, input_file: SpooledTemporaryFile, max_char_per_line: int = MAX_CHAR_PER_LINE, debug: bool = False) -> dict:
        result = ''
        input_file.seek(0, io.SEEK_END)
        if input_file.tell() > 0:
            try:
                converted = extract_text(input_file)
                result = parse_converted_pdf(converted, int(max_char_per_line), debug)

                msg = f'Successfully convert "{input_file.filename}!"'
                logger.info(msg)
            except Exception as err:
                msg = f'Unable to convert "{input_file.filename}"! Detail: {err}'
                logger.error(msg)

        result = {'result': result}
        return result

    def postprocess(self, text: str) -> str:
        result = ''
        try:
            result = postprocess_text(text)
            msg = f'Successfully postprocess text!'
            logger.info(msg)
        except Exception as err:
            msg = f'Unable to postprocess! Detail: {err}'
            logger.error(msg)

        result = {'result': result}
        return result
