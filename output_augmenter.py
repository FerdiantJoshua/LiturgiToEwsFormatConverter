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

# if __name__ == '__main__':
#     with open('output/Tata_Ibadah_Kristus_Raja_2021,_21_Nov_-_(FINAL)_cleaned.txt', 'r') as f_in:
#         lines = f_in.read()
#     lines = postprocess_text(lines)
#     with open('result.txt', 'w') as f_out:
#         f_out.write('\n'.join(lines))


# class Line:
#     def __init__(self, text: str = '', meta: [str] = None, slide_header: str = DEFAULT_SLIDE_HEADER):
#         self.text = text
#         self.meta = [] if meta is None else meta
#         self.slide_header = slide_header

#     def __getitem__(self, key):
#         return getattr(self, key)

#     def __setitem__(self, key, value):
#         setattr(self, key, value)

#     def __str__(self):
#         return f'Text="{self.text}", Meta="{self.meta}"'
