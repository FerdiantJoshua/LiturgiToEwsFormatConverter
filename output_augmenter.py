import html
import re

from bs4 import BeautifulSoup, Tag

from parse_pdf import heading_1_regex_opts, heading_2_regex, heading_3_regex, cong_inst_regex


DEFAULT_ADDITIONAL_SEPARATOR = '[===]'
DEFAULT_SLIDE_HEADER = 'Kebaktian'
DEFAULT_SLIDE_HEADER_TAG = 'sht'
DEFAULT_CONGREGATION_INSTRUCTION_TAG = 'ci'
KJ_NKB_PKJ_REGEX = re.compile(r'^((?:(?:KJ)|(?:NKB)|(?:PKJ)|(?:KK)) ?[\d\w]+ ?: ?\d?.*)')
ALL_HEADING_REGEX = [*heading_1_regex_opts, heading_2_regex, heading_3_regex, KJ_NKB_PKJ_REGEX]

DEFAULT_HTML_TAGS_MAPPING = {
    'h1': DEFAULT_SLIDE_HEADER_TAG,
    'h2': DEFAULT_CONGREGATION_INSTRUCTION_TAG,
    'em': 'it',
    'sup': 'su',
    'sub': 'sb',
    'strong': 'st'
}
COLOR_TO_EL_NAME_MAPPING = {
    'white': 'w',
    'red': 'r',
    'blue': 'bl',
    'yellow': 'y',
    'green': 'g',
    'pink': 'pk',
    'orange': 'o',
    'purple': 'pp'
}
COLOR_CSS_ATTR_NAME = 'color: '

FONT_SIZE_ATTR_PREFIX = 'ql-size-'
FONT_SIZE_TO_EL_NAME_MAPPING = {
    'small': 'sm',
    'large': 'lg'
}

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
            formatted_slide_header = _format_text(current_slide_header, slide_header_tag)
            lines[i] = f'{formatted_slide_header}' if match_object else f'{formatted_slide_header}\n{lines[i]}'
            prev_line_is_separator = False
    
    return '\n'.join(lines)

def format_text_in_html(text: str) -> str:
    lines = text.split('\n')
    if lines[-1] == '':
        lines = lines[:-1]

    for i in range(len(lines)):
        if lines[i] == '':
            lines[i] = '<br>'

        for regex in ALL_HEADING_REGEX:
            match_object = re.fullmatch(regex, lines[i])
            if match_object:
                slide_header = _format_text(match_object.group(1), 'h1', in_html=True)
                lines[i] = slide_header
                break

        if not match_object:
            match_object = re.fullmatch(cong_inst_regex, lines[i])
            if match_object:
                congregation_instruction = _format_text(match_object.group(1), 'h2', in_html=True)
                lines[i] = congregation_instruction
            else:
                lines[i] = _format_text(lines[i], 'p', in_html=True)

    return ''.join(lines)

def postprocess_formatted_text(text: str, additional_separator: str = DEFAULT_ADDITIONAL_SEPARATOR, slide_header_tag: str = DEFAULT_SLIDE_HEADER_TAG) -> str:
    lines = _convert_format_from_html(text, slide_header_tag)
    
    current_formatted_slide_header = _format_text(DEFAULT_SLIDE_HEADER, slide_header_tag)
    prev_line_is_separator = True
    current_line_is_header = False
    for i in range(len(lines)):
        if lines[i] == '':
            lines[i] = additional_separator
            prev_line_is_separator = True
            continue

        current_line_is_header = lines[i].startswith(f'{{{slide_header_tag}}}')
        if current_line_is_header:
            current_formatted_slide_header = lines[i]

        if prev_line_is_separator:
            if not current_line_is_header:
                lines[i] = f'{current_formatted_slide_header}\n{lines[i]}'
            prev_line_is_separator = False
    
    return '\n'.join(lines)

def _convert_format_from_html(text: str, slide_header_tag: str) -> [str]:
    html_tags_mapping = DEFAULT_HTML_TAGS_MAPPING.copy()
    html_tags_mapping['h1'] = slide_header_tag

    html_br_tag = re.compile(r'<br/?>')

    result = []

    soup = BeautifulSoup(text, 'html.parser')
    for tag, replacement in html_tags_mapping.items():
        elements = soup.find_all(tag)
        for element in elements:
            el_style = element.get('style')
            el_class = element.get('class')
            if el_style is None and el_class is None:
                element.name = replacement
            else:
                if el_style is not None:
                    span_style = soup.new_tag('span', attrs={'style':el_style})
                    element.wrap(span_style)
                if el_class is not None:
                    span_class = soup.new_tag('span', attrs={'class':el_class})
                    element.wrap(span_class)
                element.wrap(soup.new_tag(replacement))
                element.unwrap()

    spans = soup.find_all('span')
    for span in spans:
        _convert_html_color_style(span)
        _convert_html_font_size_class(span)

    for tag in soup.contents:
        content = str(tag) if tag.name != 'p' else ''.join(str(s) for s in tag)
        content = re.sub(html_br_tag, '', content)
        mapping_table = content.maketrans('<>', '{}')
        converted = content.translate(mapping_table)
        result.extend(html.unescape(converted).split('\n\n'))

    return result

def _convert_html_color_style(tag: Tag):
    tag_style = tag.get('style')
    if isinstance(tag_style, str):
        if tag_style.startswith(COLOR_CSS_ATTR_NAME):
            color = tag_style[len(COLOR_CSS_ATTR_NAME):-1]
            tag.name = COLOR_TO_EL_NAME_MAPPING[color]
        del tag['style']

def _convert_html_font_size_class(tag: Tag):
    tag_class = tag.get('class')
    if isinstance(tag_class, list) and len(tag_class) > 0:
        if tag_class[0].startswith(FONT_SIZE_ATTR_PREFIX):
            size = tag_class[0][len(FONT_SIZE_ATTR_PREFIX):]
            tag.name = FONT_SIZE_TO_EL_NAME_MAPPING[size]
        del tag['class']

def _format_text(text:str, tag:str, in_html: bool = False) -> str:
    if not in_html:
        return f'{{{tag}}}{text}{{/{tag}}}'
    else:
        return f'<{tag}>{text}</{tag}>'
