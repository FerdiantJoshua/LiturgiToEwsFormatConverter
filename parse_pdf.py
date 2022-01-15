import argparse
import logging
from logging.config import dictConfig
import os
import re
import sys

from unidecode import unidecode
from pdfminer.high_level import extract_text

from logging_config import ROOT_MODULE_NAME, LOGGING_CONFIG


date_regex = re.compile(r'[A-Z]{4,6},\s+\d{1,2}\s+[A-Z]{3,10}\s+\d{4}')
footer_regex = re.compile(r'^Liturgi (?:[A-Z][a-zA-Z,_]+\s+)+\d{1,2}\s+\w+\s+20\d\d')
_heading_1_regex_1 = re.compile(r'[IVX0-9]{1,5}\.\s+([A-Z ]{5,30})')
_heading_1_regex_2 = re.compile(r'[IVX0-9]{1,5}\.\s+([A-Za-z ]{5,30})')
heading_1_regex_opts = [_heading_1_regex_1, _heading_1_regex_2]
heading_2_regex = re.compile(r'([A-Z., ]{5,30})')
heading_3_regex = re.compile(r'([A-Z.,\'"\- ]{5,50})')
song_indicator_regex = re.compile(r'(?:\d{1,2}\.\s+)?NYANYIAN\s+(?:(?:UMAT)|[A-Z]+)')
cong_inst_regex = re.compile(r'(?:\(duduk\))|(?:\(berdiri\))')
cong_inst_addt_regex = re.compile(r'\([a-zA-Z,.\- ]{3,200}\)')
conv_start_regex = re.compile(r'^[A-Z][0-9a-zA-Z., ]{1,10}: ')
cut_conv_start_name_regex = re.compile(r'^[A-Z][0-9a-zA-Z., ]{0,10}')
cut_conv_start_colon_regex = re.compile(r'^: ')
repeated_char_all_detect_regex = re.compile(r'(?:(.)\1{1}){3,}')
repeated_char_replace_regex = re.compile(r'((.)\2{1})')
META = {
    'DATE': 'date',
    'TITLE': 'title',
    'HEAD1': 'heading_1',
    'HEAD2': 'heading_2',
    'HEAD3': 'heading_3',
    'SONG': 'song',
    'CONG_INST': 'congregate_instruction',
    'CONG_INST_ADDT': 'congregate_instruction_additional',
    'CONV_START': 'conversation_start',
    'CUT_CONV_START_NAME': 'cut_conversation_start_name',
    'CUT_CONV_START_COLON': 'cut_conversation_start_colon',
    'BODY': 'body'
}
MAX_CHAR_PER_LINE = 70
END_LINE_TOLERANCE = 5

if __name__ == '__main__':
    dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(f'{ROOT_MODULE_NAME}.{__name__}')


replacement_regex = re.compile(r' {2,99}')
def preprocess(text):
    return re.sub(replacement_regex, r' ', unidecode(text.strip()))


def _window_sentence(sentence, max_char_per_line=MAX_CHAR_PER_LINE) -> str:
    punctuations = '.,!?;'
    char_count = 0
    result = ''
    i = 0
    while i < len(sentence):
        char_count += 1
        char = sentence[i]
        result += char
        if char in punctuations and char_count >= max_char_per_line and i < len(sentence) - END_LINE_TOLERANCE:
            result += '\n\n'
            char_count = 0
            i += 1 if sentence[i+1] == ' ' else 0
        i += 1
    return result


def _prettify_result(data: list, max_char_per_line: int = MAX_CHAR_PER_LINE, with_meta : bool = False) -> [str]:
    buffer_out = []
    for i in range(len(data)):
        datum = data[i]
        prev = data[i-1]
        prev_2 = data[i-2]
        formatted = datum["text"]
        logger.debug(formatted  + (f'\t\t<===>\t\t{",".join(datum["meta"])}' if with_meta else ''))
        if META['TITLE'] in datum['meta'] or META['CONG_INST_ADDT'] in datum['meta']:
            buffer_out.append(formatted)
        elif META['SONG'] in datum['meta']:
            if not META['SONG'] in prev['meta']:
                buffer_out.append('\n' + formatted)
            elif META['BODY'] in datum['meta']:
                buffer_out.append(formatted)
        elif META['HEAD1'] in datum['meta'] or META['HEAD2'] in datum['meta'] or META['HEAD3'] in datum['meta']:
            buffer_out.append('\n' + formatted)
        elif META['CONG_INST'] in datum['meta']:
            # SWAP INSTRUCTION WITH HEADING
            if META['HEAD1'] not in prev['meta'] and META['HEAD2'] not in prev['meta'] and META['HEAD3'] not in prev['meta']:
                data[i], data[i - 1] = data[i - 1], data[i]
                buffer_out.insert(len(buffer_out) - 1, formatted)
                logger.debug(f'swapped: """{buffer_out[-2]}""", """{buffer_out[-1]}"""')
            else:
                buffer_out.append(formatted)
        elif META['CONV_START'] in datum['meta'] or META['CUT_CONV_START_NAME'] in datum['meta']:
            buffer_out.append('\n' + formatted)
        elif META['CUT_CONV_START_COLON'] in datum['meta']:
            if META['CUT_CONV_START_NAME'] in prev['meta']:
                buffer_out[len(buffer_out) - 1] += ' ' + formatted
            elif META['CUT_CONV_START_NAME'] in prev_2['meta']:
                buffer_out[len(buffer_out) - 2] += ' ' + formatted
            else:
                buffer_out.append(formatted)
        elif META['BODY'] in datum['meta']:
            if datum['meta'] == prev['meta'] or META['CONV_START'] in prev['meta'] or META['CUT_CONV_START_NAME'] in prev['meta'] or META['CUT_CONV_START_COLON'] in prev['meta']:
                buffer_out[len(buffer_out) - 1] += ' ' + formatted
            else:
                buffer_out.append('\n' + formatted)

    prettified = []
    for buffer in buffer_out:
        prettified.append(_window_sentence(buffer, max_char_per_line))
    return prettified


def parse_converted_pdf(texts: str, max_char_per_line: int = MAX_CHAR_PER_LINE, debug: bool = False) -> str:
    lines = texts.split('\n')

    is_first_heading_1_found = False
    regex_opt_idx = 0
    while not is_first_heading_1_found and regex_opt_idx < len(heading_1_regex_opts):
        data = []
        is_reading_song = False
        for line_ in lines:
            text = preprocess(line_)
            line = {'text': text, 'meta': []}
            if (text != '') and not re.match(footer_regex, text):
                line['text'] = text

                # ========== DATE ==========
                if re.fullmatch(date_regex, text):
                    line['meta'].append(META['DATE'])
                    date = text.replace(' ', '_').lower()

                # ========== HEADING/BODY LEVEL ==========
                if re.fullmatch(heading_1_regex_opts[regex_opt_idx], text):
                    line['meta'].append(META['HEAD1'])
                    is_first_heading_1_found = True
                    is_reading_song = False
                elif not is_first_heading_1_found:
                    line['meta'].append(META['TITLE'])
                elif re.fullmatch(heading_2_regex, text):
                    line['meta'].append(META['HEAD2'])
                    is_reading_song = False
                elif re.fullmatch(heading_3_regex, text):
                    line['meta'].append(META['HEAD3'])
                else:
                    line['meta'].append(META['BODY'])

                # ========== TITLE REPEATED CHAR CORRECTION ==========
                if META['TITLE'] in line['meta'] and re.match(repeated_char_all_detect_regex, text):
                    line['text'] = re.sub(repeated_char_replace_regex, r'\2', text)
                    logger.debug(f'Replaced repeated characters: {text} -> {line["text"]}')

                # ========== CONGREGATION INSTRUCTION ==========
                if re.fullmatch(cong_inst_regex, text):
                    line['meta'].append(META['CONG_INST'])
                elif re.fullmatch(cong_inst_addt_regex, text):
                    line['meta'].append(META['CONG_INST_ADDT'])

                # ========== SONG ==========
                if re.match(song_indicator_regex, text):
                    is_reading_song = True
                elif is_reading_song and META['CONG_INST'] not in line['meta']:
                    line['meta'].append(META['SONG'])

                # ========== CONVERSATION START (SOMETIMES GET CUT) ==========
                if 'song' not in line['meta'] and 'body' in line['meta'] and len(line['meta']) == 1:
                    if re.match(conv_start_regex, text):
                        line['meta'].append(META['CONV_START'])
                    elif re.fullmatch(cut_conv_start_name_regex, text):
                        line['meta'].append(META['CUT_CONV_START_NAME'])
                    elif re.match(cut_conv_start_colon_regex, text):
                        line['meta'].append(META['CUT_CONV_START_COLON'])

                # heading1 and song heading are sometimes swapped
                if META['HEAD1'] in line['meta'] and META['SONG'] in data[-1]['meta'] and META['BODY'] not in data[-1]['meta']:
                    data.insert(len(data) - 1, line)
                    is_reading_song = True
                    logger.debug(f'swapped: """{data[-2]["text"]}""", """{data[-1]["text"]}"""')
                else:
                    data.append(line)

        if not is_first_heading_1_found:
            regex_opt_idx += 1
            logger.info(f'Heading 1 was not found. Retrying with another heading_1_regex (opt {regex_opt_idx + 1})')

    return '\n'.join(_prettify_result(data, max_char_per_line, debug))


def extract_pdf_text(input_path) -> str:
    input_path = os.path.normpath(input_path)
    return extract_text(input_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-id', '--input_dir', default='input')
    parser.add_argument('-od', '--output_dir', default='output')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-m', '--max_char_per_line', type=int, default=MAX_CHAR_PER_LINE)
    args = parser.parse_args()

    if args.debug: 
        logger.setLevel(logging.DEBUG)

    os.makedirs('input/', exist_ok=True)
    os.makedirs('output/', exist_ok=True)

    success_count = 0
    error_count = 0
    skipped_count = 0
    path, _, files = next(os.walk(args.input_dir))
    logger.info(f'Found {len(files)} files inside {args.input_dir}')
    for file in files:
        name, ext = os.path.splitext(file)
        name = name.replace(' ', '_')
        input_path = f'{path}/{file}/'
        output_path = f'{args.output_dir}/{name}_cleaned.txt'
        logger.debug(f'\n========== {output_path} ==========')
        logger.info(f'Converting {file}')
        if ext == '.pdf':
            try:
                converted = extract_pdf_text(input_path)
                parsed = parse_converted_pdf(converted, args.max_char_per_line, args.debug)
                with open(output_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(parsed)
                logger.info(f'Successfully convert {args.input_dir}/{file} to {output_path}')
                success_count += 1
            except Exception as err:
                logger.exception(err)
                logger.error(f'Unable to convert {args.input_dir}/{file}!')
                error_count += 1
        else:
            logger.info(f'Skipping {file} as it is not a pdf file.')
            skipped_count += 1
    logger.info(
        f'\nSummary:\n\tSuccessful conversion(s):\t{success_count}\n\tFailed conversion(s):\t\t{error_count}\n\tSkipped conversion(s):\t\t{skipped_count}'
    )
    logger.debug('<<<<<<<<<<<<<<<<<<<< END OF LOG >>>>>>>>>>>>>>>>>>>>\n')
