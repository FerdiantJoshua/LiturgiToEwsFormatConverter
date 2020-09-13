# Liturgi PDF to EasyWorship-ready Format Converter

## Requirements

1. Python 3.6
2. Packages
    ```shell script
    pip install -r requirements.txt    
    ```
   
## Run Script

1. Put liturgi files (`.pdf` only) inside `input/`
2. Run open the `.bat` files (`run_convert.bat` or `run_convert_short.bat` or `run_convert_long.bat`)  
    As this script automatically separate too long lines into several lines. `run_convert_short.bat` will separate the
    too-long-line into shorter lines, so is its long-version (`run_convert_long.bat`).
   
   OR
    ```shell script
    python parse_pdf.py
    ```
3. Resulting files will be inside `output/`

## Author

Ferdiant Joshua M.
