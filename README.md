# FUZZSHOT
A fast URL fuzzer with automated screenshot capture. This is a powerful CLI tool designed for dynamic URL generation and fuzzing. It allows the construction of customizable URL structures using lots of parameters, making it ideal for automation and testing workflows.

## Features
- Highly Configurable: Full control over prefixes, suffixes, and length.
- Flexible Length Logic: Supports fixed values or conditional ranges (e.g. >2&<=6).
- Multiple Charset Modes: From simple alphanumeric sets to printable and hexadecimal characters.
- Wordlist Support: Load custom .txt dictionaries for targeted fuzzing.
- Output-Oriented Design: Built to integrate into workflows involving screenshotting or structured data storage.

## Instalation

```bash
git clone https://github.com/Volodishlav/FUZZSHOT.git
cd FUZZSHOT
```
### Installing dependencies

```bash
pip install -r requirements.txt
```

### Using a Python Virtual Environment (venv)

```bash
python3 -m venv .venv

# Activating it:
source .venv/bin/activate  # Linux
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

## Use

```bash
python3 main.py <parameters>
```

### Flags and parameters

```text
python3 main.py -h
─────────────────────────────────────────────────────────────────────────────────────
  -s PREFIX       Start of the URL (before the variable section)
  -e SUFFIX       End of the URL (after the variable section)
  -l LENGTH       Length of the generated section.
                     Fixed number:    -l 5
                     Conditional:     -l "<=6&>2" (operators: < > <= >= ==)
                     Can be chained using &.
  -m MODE         Charset or path to wordlist:
                      alpha        a-z A-Z
                      lower        a-z
                      upper        A-Z
                      num          0-9
                      alnum        a-z A-Z 0-9  (default)
                      lower+num    a-z 0-9
                      upper+num    A-Z 0-9
                      hex          0-9 a-f
                      HEX          0-9 A-F
                      urlsafe      a-z A-Z 0-9 - _
                      printable    all printable characters
                  Wordlist: Provide the path to a .txt file (one word per line).
                      The program will iterate through the list instead of 
                      generating random combinations. Use -c 0 for infinite loop.
  -c COUNT        Number of iterations. 0 = infinite (Ctrl+C to stop).
                      In finite wordlist mode, it is also limited by list size.
  -f FILE         Path to a .txt file with one URL/IP per line.
  -o DIR          Output directory for screenshots (default: ./)
  -h, --help      Show this help message.
─────────────────────────────────────────────────────────────────────────────────────
```

## Disclaimer

This tool is intended for educational and research purposes only. The author is not responsible for any misuse, damage, or illegal activity caused by the use of this software. Users are solely responsible for ensuring compliance with applicable laws and regulations. The author is not responsible for any misuse, damage, or illegal activity caused by the use of this software.
