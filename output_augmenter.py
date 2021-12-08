import re

from parse_pdf import heading_1_regex_opts, heading_2_regex, heading_3_regex


DEFAULT_ADDITIONAL_SEPARATOR = '[===]'
DEFAULT_SLIDE_HEADER = 'Kebaktian'
DEFAULT_SLIDE_HEADER_TAG = 'sht'
ALL_HEADING_REGEX = [*heading_1_regex_opts, heading_2_regex, heading_3_regex]

def _format_slide_header(slide_header:str, slide_header_tag:str) -> str:
    return f'{{{slide_header_tag}}}{slide_header}{{/{slide_header_tag}}}'

def _print_slide_separator(additional_separator: str = '', slide_header: str = '', slide_header_tag: str = '') -> str:
    return additional_separator if not slide_header or not slide_header_tag else \
        f'{additional_separator}\n{_format_slide_header(slide_header, slide_header_tag)}'

def postprocess_text(text: str, additional_separator: str = DEFAULT_ADDITIONAL_SEPARATOR, slide_header_tag: str = DEFAULT_SLIDE_HEADER_TAG) -> str:
    lines = text.split('\n')

    current_slide_header = DEFAULT_SLIDE_HEADER
    prev_line_is_separator = False
    for i in range(len(lines)):
        if lines[i] == '':
            lines[i] = _print_slide_separator(additional_separator, current_slide_header, slide_header_tag)
            prev_line_is_separator = True
            continue

        for regex in ALL_HEADING_REGEX:
            match_object = re.fullmatch(regex, lines[i])
            if match_object:
                current_slide_header = match_object.group(1)
                if prev_line_is_separator:
                    print('\t' + lines[i-1])
                    lines[i-1] = _print_slide_separator(additional_separator, current_slide_header, slide_header_tag)
                    prev_line_is_separator = False
                break
    
    return '\n'.join(lines)
