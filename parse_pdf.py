import argparse
import json
import os
import re
import sys

from unidecode import unidecode


date_regex = re.compile(r'[A-Z]{4,6},\s+\d{1,2}\s+[A-Z]{3,10}\s+\d{4}')
footer_regex = re.compile(r'Liturgi \w+\s+\d{1,2}\s+\w+\s+20\d\d')
heading_1_regex = re.compile(r'[IVX]{1,5}\.\s+[A-Z ]{5,30}')
heading_2_regex = re.compile(r'[A-Z., ]{5,30}')
heading_3_regex = re.compile(r'[A-Z.," ]{5,50}')
song_indicator_regex = re.compile(r'NYANYIAN\s+(?:(?:UMAT)|[A-Z]+)')
song_inst_regex = re.compile(r'(?:\w{2,3}\s+=\s+\w{1,2})|(?:\d{1,3}\s+ketuk)')
cong_inst_regex = re.compile(r'(?:\(duduk\))|(?:\(berdiri\))')
cong_inst_addt_regex = re.compile(r'\([a-zA-Z,.\- ]{3,200}\)')
conv_start_regex = re.compile(r'^[0-9a-zA-Z., ]{1,10}: ')
cut_conv_start_name_regex = re.compile(r'^[A-Z][0-9a-zA-Z., ]{1,10}')
cut_conv_start_colon_regex = re.compile(r'^: ')
META = {
    'DATE': 'date',
    'TITLE': 'title',
    'HEAD1': 'heading_1',
    'HEAD2': 'heading_2',
    'HEAD3': 'heading_3',
    'SONG': 'song',
    'SONG_INFO': 'song_info',
    'SONG_INST': 'song_instruction',
    'CONG_INST': 'congregate_instruction',
    'CONG_INST_ADDT': 'congregate_instruction_additional',
    'CONV_START': 'conversation_start',
    'CUT_CONV_START_NAME': 'cut_conversation_start_name',
    'CUT_CONV_START_COLON': 'cut_conversation_start_colon',
    'BODY': 'body'
}
TEMP_DIR = 'temp/'
MAX_CHAR_PER_LINE = 70
END_LINE_TOLERANCE = 5


class PdfMinerException(Exception):
    pass


replacement_regex = re.compile(r' {2,99}')
def preprocess(text):
    return re.sub(replacement_regex, r' ', unidecode(text.strip()))


def _window_sentence(sentence, max_char_per_line=MAX_CHAR_PER_LINE):
    punctuations = '.,!?'
    char_count = 0
    result = ''
    for i in range(len(sentence)):
        char_count += 1
        char = sentence[i]
        result += char
        if char in punctuations and char_count >= max_char_per_line and i < len(sentence) - END_LINE_TOLERANCE:
            result += '\n'
            char_count = 0
    return result


def print_format(data: list, max_char_per_line: bool, with_meta:bool=False, print_target=sys.stdout) -> None:
    buffer_out = []
    for i in range(len(data)):
        datum = data[i]
        prev = data[i-1]
        prev_2 = data[i-2]
        formatted = datum["text"] + (f'\t\t<===>\t\t{",".join(datum["meta"])}' if with_meta else '')
        # print(formatted)
        if META['TITLE'] in datum['meta'] or META['CONG_INST_ADDT'] in datum['meta']:
            buffer_out.append(formatted)
        elif META['SONG'] in datum['meta']:
            if META['HEAD3'] in datum['meta']:
                buffer_out.append('\nIntro\n' + formatted)
            elif META['HEAD2'] in datum['meta']:
                buffer_out.append('\n' + formatted)
            elif META['BODY'] in datum['meta']:
                buffer_out.append(formatted)
        elif META['HEAD1'] in datum['meta'] or META['HEAD2'] in datum['meta'] or META['HEAD3'] in datum['meta']:
            buffer_out.append('\n' + formatted)
        elif META['CONG_INST'] in datum['meta']:
            if META['HEAD1'] not in prev['meta'] and META['HEAD2'] not in prev['meta'] and META['HEAD3'] not in prev['meta']:
                data[i], data[i-1] = data[i-1], data[i]
                # print(f'swapped: {datum}, {prev}')
                buffer_out.insert(len(buffer_out) - 1, formatted)
            else:
                buffer_out.append(formatted)
        elif META['SONG_INFO'] in datum['meta']:
            buffer_out[len(buffer_out) - 1] += ' ' + formatted
        elif META['SONG_INST'] in datum['meta']:
            if META['SONG_INST'] in prev['meta']:
                buffer_out[len(buffer_out) - 1] += ' ' + formatted
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

    for buffer in buffer_out:
        print(_window_sentence(buffer, max_char_per_line), file=print_target)


def parse_converted_pdf(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()

    is_first_heading_1_found = False
    is_finding_song_info = False
    is_reading_song = False
    for line_ in lines:
        text = preprocess(line_)
        line = {'text': text, 'meta': []}
        if text != '' and not re.match(footer_regex, text):
            line['text'] = text

            # ========== DATE ==========
            if re.fullmatch(date_regex, text):
                line['meta'].append(META['DATE'])
                date = text.replace(' ', '_').lower()

            # ========== HEADING/BODY LEVEL ==========
            if re.fullmatch(heading_1_regex, text):
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

            # ========== CONGREGATION INSTRUCTION ==========
            if re.fullmatch(cong_inst_regex, text):
                line['meta'].append(META['CONG_INST'])
            elif re.fullmatch(cong_inst_addt_regex, text):
                line['meta'].append(META['CONG_INST_ADDT'])

            # ========== SONG ==========
            if re.match(song_indicator_regex, text):
                line['meta'].append(META['SONG'])
                is_finding_song_info = True
                is_reading_song = True
            elif re.match(song_inst_regex, text):
                line['meta'].append(META['SONG_INST'])
                is_finding_song_info = False
            elif is_finding_song_info and META['HEAD3'] not in line['meta'] and META['CONG_INST_ADDT'] not in line['meta']:
                line['meta'].append(META['SONG_INFO'])
            elif is_reading_song:
                line['meta'].append(META['SONG'])

            # ========== CONVERSATION START (SOMETIMES GET CUT) ==========
            if 'body' in line['meta'] and len(line['meta']) == 1:
                if re.match(conv_start_regex, text):
                    line['meta'].append(META['CONV_START'])
                elif re.fullmatch(cut_conv_start_name_regex, text):
                    line['meta'].append(META['CUT_CONV_START_NAME'])
                elif re.match(cut_conv_start_colon_regex, text):
                    line['meta'].append(META['CUT_CONV_START_COLON'])

            data.append(line)

    with open(output_path, 'w') as f_out:
        print_format(data, args. max_char_per_line, args.debug, f_out)


def convert_pdf_to_txt(input_path, output_path):
    input_path = os.path.normpath(input_path)
    output_path = os.path.normpath(output_path)
    #print(f'python pdf2txt.py -o {output_path} "{input_path}"')
    exit_code = os.system(f'python pdf2txt.py -o "{output_path}" "{input_path}"')
    if exit_code != 0:
        raise PdfMinerException(f'PdfMiner exit_code is {exit_code}! Exiting..')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-id', '--input_dir', default='input')
    parser.add_argument('-od', '--output_dir', default='output')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-m', '--max_char_per_line', type=int, default=MAX_CHAR_PER_LINE)
    args = parser.parse_args()

    os.makedirs('input/', exist_ok=True)
    os.makedirs('output/', exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    data = []
    songs = []
    headings = []
    path, _, files = next(os.walk(args.input_dir))
    print(f'Found {len(files)} files inside {args.input_dir}')
    for file in files:
        print(f'Converting {file}')
        name, ext = os.path.splitext(file)
        name = name.replace(' ', '_')
        input_path = f'{path}/{file}/'
        temp_path = f'{TEMP_DIR}/{name}_temp.txt'
        output_path = f'{args.output_dir}/{name}_cleaned.txt'
        if ext == '.pdf':
            convert_pdf_to_txt(input_path, temp_path)
            parse_converted_pdf(temp_path, output_path)
            print(f'Successfully convert {args.input_dir}/{file} to {output_path}')
        else:
            print(f'Skipping {file} as it is not a pdf file.')
