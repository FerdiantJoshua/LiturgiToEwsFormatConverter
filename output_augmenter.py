import re

from parse_pdf import heading_1_regex_opts, heading_2_regex, heading_3_regex


DEFAULT_ADDITIONAL_SEPARATOR = '[===]'
DEFAULT_SLIDE_HEADER = 'Kebaktian'
DEFAULT_SLIDE_HEADER_TAG = 'sht'
KJ_NKB_PKJ_REGEX = re.compile(r'^((?:(?:KJ)|(?:NKB)|(?:PKJ)) ?[\d\w]+ ?: ?\d?.*)')
ALL_HEADING_REGEX = [*heading_1_regex_opts, heading_2_regex, heading_3_regex, KJ_NKB_PKJ_REGEX]

def _format_slide_header(slide_header:str, slide_header_tag:str) -> str:
    return f'{{{slide_header_tag}}}{slide_header}{{/{slide_header_tag}}}'

def postprocess_text(text: str, additional_separator: str = DEFAULT_ADDITIONAL_SEPARATOR, slide_header_tag: str = DEFAULT_SLIDE_HEADER_TAG) -> str:
    lines = text.split('\n')

    current_slide_header = DEFAULT_SLIDE_HEADER
    prev_line_is_separator = True
    for i in range(len(lines)):
        if lines[i] == '':
            lines[i] = additional_separator
            prev_line_is_separator = True
            continue

        for regex in ALL_HEADING_REGEX:
            match_object = re.fullmatch(regex, lines[i])
            if match_object:
                current_slide_header = match_object.group(1)
                break

        if prev_line_is_separator:
            slide_header = _format_slide_header(current_slide_header, slide_header_tag)
            lines[i] = f'{slide_header}' if match_object else f'{slide_header}\n{lines[i]}'
            prev_line_is_separator = False
    
    return '\n'.join(lines)
