# dpia-pdf-poc

This is a proof-of-concept that generates a user-fillable PDF form based upon the 'rapportagemodel'
DPIA.

## Usage

For now the tool is a command-line tool.

### Prerequisites
- Python 3.12
- [uv](https://docs.astral.sh/uv/)

### Setup and running
Make sure the prerequisites are installed. To run the script you can run 
```
uv run python main.py [OPTIONS]
```
where the options are as follows:
```
Options:
 -d, --definitions PATH  [required]
 -o, --output PATH       Path to the output PDF file [required]
 --help                  Show this message and exit.
```
The directory `dpia-static` contains an example (the first 2 questions of the DPIA in an intermediate
format).
