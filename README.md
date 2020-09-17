# Liturgi PDF to EasyWorship-ready Format Converter

## Requirements

1. Python 3.6
2. Packages
    ```shell script
    pip install -r requirements.txt    
    ```
   
## Run Script

1. Put liturgi files (`.pdf` only) inside `input/`
2. Open the `.bat` files (`run_convert.bat` or `run_convert_short.bat` or `run_convert_long.bat`)  
    As this script automatically separate too long lines into several lines. `run_convert_short.bat` will separate the
    too-long-line into shorter lines, so is its long-version (`run_convert_long.bat`).
   
   OR run this command in terminal:
    ```shell script
    python parse_pdf.py
    ```
3. Resulting files will be inside `output/`

## More Usage
Run this command in terminal:
```shell script
python parse_pdf.py -h
```

This will show all available arguments:
```text
usage: parse_pdf.py [-h] [-id INPUT_DIR] [-od OUTPUT_DIR] [-d]
                    [-m MAX_CHAR_PER_LINE]

optional arguments:
  -h, --help            show this help message and exit
  -id INPUT_DIR, --input_dir INPUT_DIR
  -od OUTPUT_DIR, --output_dir OUTPUT_DIR
  -d, --debug
  -m MAX_CHAR_PER_LINE, --max_char_per_line MAX_CHAR_PER_LINE
```

## Author

Ferdiant Joshua M.
