import os
import tkinter as tk
from tkinter import filedialog, scrolledtext

from logger import Logger
from parse_pdf import extract_pdf_text, parse_converted_pdf


logger = Logger().get_logger()

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='y')
        self.master.title('Liturgi Converter: PDF to TXT in EWS Format')
        self.master.geometry('800x600')
        self.master.maxsize(800, 600)

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

        self.convert = tk.Button(
            self,
            text='Convert to EWS Format',
            command=self.convert_to_ews_format
        )
        self.convert.grid(row=3, column=0)
        
        self.lbl_error = tk.Label(self, text='', foreground='red')
        self.lbl_error.grid(row=4, column=0)

        self.txt_result = scrolledtext.ScrolledText(self, height=25)
        self.txt_result.grid(row=5, column=0, pady=(0,16))

        self.convert = tk.Button(
            self,
            text='Copy result to clipboard',
            command=self.copy_result
        )
        self.convert.grid(row=6, column=0, pady=(0,16))

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
                converted = extract_pdf_text(filepath)
                parsed = parse_converted_pdf(converted)
                self.txt_result.insert('end', parsed)
                msg = f'Successfully convert {filepath}'
                self.lbl_error.configure(text='')
                logger.info(msg)
            except Exception as err:
                msg = f'Unable to convert {filepath}! Detail: {err}'
                self.lbl_error.configure(text=msg)
                logger.error(msg)

    def copy_result(self):
        self.clipboard_clear()
        self.clipboard_append(self.txt_result.get("1.0",'end-1c'))

logger.info('Running in GUI mode..')
root = tk.Tk()
app = Application(master=root)
app.mainloop()
