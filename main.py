import os
import logging
from logging.config import dictConfig
import tkinter as tk
from tkinter import filedialog, scrolledtext

from logging_config import ROOT_MODULE_NAME, LOGGING_CONFIG, LOG_LEVEL
from output_augmenter import postprocess_text
from parse_pdf import MAX_CHAR_PER_LINE, extract_pdf_text, parse_converted_pdf

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(f'{ROOT_MODULE_NAME}.{__name__}')

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='y')
        self.master.title('Liturgi Converter: PDF to TXT in EWS Format')
        self.master.geometry('1366x768')
        self.master.maxsize(1366, 768)

        self.rowconfigure(4, weight=1)

        self.create_widgets()

    def create_widgets(self):
        self.btn_dialog_open_file = tk.Button(
            self,
            text='Open a Liturgi file (.pdf)',
            command=self.open_file
        )
        self.btn_dialog_open_file.grid(row=1, column=0, pady=(16,0))

        self.lbl_chosen_file = tk.Label(
            self,
            text='No file has been opened',
            font=('Arial', 8),
            wraplength='480p'
        )
        self.lbl_chosen_file.grid(row=2, column=0, pady=(0,16))

        self.lbl_max_char_per_line = tk.Label(self, text='Max char per line: ')
        self.lbl_max_char_per_line.grid(row=3, column=0)
        self.txt_max_char_per_line = tk.Entry(self, width=20)
        self.txt_max_char_per_line.insert(-1, MAX_CHAR_PER_LINE)
        self.txt_max_char_per_line.grid(row=4, column=0, pady=(0,8))

        self.convert = tk.Button(
            self,
            text='Convert to EWS Format',
            command=self.convert_to_ews_format
        )
        self.convert.grid(row=5, column=0)
        
        self.lbl_error = tk.Label(self, text='', foreground='red')
        self.lbl_error.grid(row=6, column=0)

        self.txt_result = scrolledtext.ScrolledText(self, height=25)
        self.txt_result.grid(row=7, column=0, pady=(0,16))

        self.copy = tk.Button(
            self,
            text='Copy result to clipboard',
            command=lambda: self.copy_result(self.txt_result)
        )
        self.copy.grid(row=8, column=0, pady=(0,16))

        self.txt_result_postprocessed = scrolledtext.ScrolledText(self, height=25)
        self.txt_result_postprocessed.grid(row=7, column=1, pady=(0,16))

        self.postprocess = tk.Button(
            self,
            text='Postprocess',
            command=self.postprocess
        )
        self.postprocess.grid(row=8, column=1)

        self.copy_postprocessed = tk.Button(
            self,
            text='Copy result to clipboard',
            command=lambda: self.copy_result(self.txt_result_postprocessed)
        )
        self.copy_postprocessed.grid(row=9, column=1, pady=(0,16))

    def open_file(self):
        filepath = filedialog.askopenfilename(
            initialdir = './',
            title = 'Select a File',
            filetypes = (('PDF files', '*.pdf*'), ('All files', '*.*'))
        )
        self.lbl_chosen_file.configure(text=filepath)

        return filepath

    def convert_to_ews_format(self):
        filepath = self.lbl_chosen_file['text']
        _, ext = os.path.splitext(filepath)
        if ext == '.pdf':
            try:
                self.txt_result.delete('1.0', tk.END)

                max_char_per_line = self.txt_max_char_per_line.get() or 0
                converted = extract_pdf_text(filepath)
                parsed = parse_converted_pdf(converted, int(max_char_per_line), LOG_LEVEL == logging.DEBUG)

                self.txt_result.insert('end', parsed)
                msg = f'Successfully convert {filepath}'
                self.lbl_error.configure(text='')
                logger.info(msg)
            except Exception as err:
                msg = f'Unable to convert {filepath}! Detail: {err}'
                self.lbl_error.configure(text=msg)
                logger.error(msg)

    def postprocess(self):
        try:
            self.txt_result_postprocessed.delete('1.0', tk.END)
            text = self.txt_result.get('1.0', tk.END)
            postprocessed = postprocess_text(text)
            self.txt_result_postprocessed.insert('end', postprocessed)
            msg = f'Successfully postprocess text!'
            self.lbl_error.configure(text='')
            logger.info(msg)
        except Exception as err:
            msg = f'Unable to postprocess! Detail: {err}'
            self.lbl_error.configure(text=msg)
            logger.error(msg)

    def copy_result(self, textbox):
        self.clipboard_clear()
        self.clipboard_append(textbox.get("1.0",'end-1c'))

logger.info('Running in GUI mode..')
root = tk.Tk()
root.state('zoomed')
app = Application(master=root)
app.mainloop()
