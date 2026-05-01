#!/usr/bin/env python3
import argparse
import random
import string
import sys
import os
import re
from itertools import product
from playwright.sync_api import sync_playwright

def parse_length(val):
    val = val.strip()

    # Número fijo
    if re.match(r'^\d+$', val):
        n = int(val)
        return lambda: n

    conditions = []
    for part in val.split('&'):
        part = part.strip()
        m = re.match(r'^([<>]=?|==)(\d+)$', part)
        if not m:
            raise ValueError(f"Error: unrecognized length condition: '{part}'")
        op, num = m.group(1), int(m.group(2))
        conditions.append((op, num))

    lo, hi = 1, 256
    for op, num in conditions:
        if op == '>':   lo = max(lo, num + 1)
        elif op == '>=': lo = max(lo, num)
        elif op == '<':  hi = min(hi, num - 1)
        elif op == '<=': hi = min(hi, num)
        elif op == '==': lo = hi = num

    if lo > hi:
        raise ValueError(f"Error: length conditions: range [{lo}, {hi}]")

    return lambda: random.randint(lo, hi)

MODOS = {
    'alpha':       string.ascii_letters,
    'lower':       string.ascii_lowercase,
    'upper':       string.ascii_uppercase,
    'num':         string.digits,
    'alnum':       string.ascii_letters + string.digits,
    'lower+num':   string.ascii_lowercase + string.digits,
    'upper+num':   string.ascii_uppercase + string.digits,
    'hex':         '0123456789abcdef',
    'HEX':         '0123456789ABCDEF',
    'punct':       string.punctuation,
    'printable':   string.printable.strip(),
    'urlsafe':     string.ascii_letters + string.digits + '-_',
}

def get_charset(mode):
    if mode in MODOS:
        return MODOS[mode]
    charset = ''
    for part in mode.split('+'):
        if part in MODOS:
            charset += MODOS[part]
        else:
            raise ValueError(
                f"Error: Mode '{part}' not recognized.\n"
                f"Available modes: {', '.join(MODOS.keys())}"
            )
    return ''.join(sorted(set(charset)))

def load_wordlist(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: wordlist not found: '{filepath}'", file=sys.stderr)
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
        words = [line.strip() for line in fh if line.strip()]
    if not words:
        print(f"Error: wordlist '{filepath}' is empty.", file=sys.stderr)
        sys.exit(1)
    return words

def screenshot(page, url, out_dir, filename):
    out_path = os.path.join(out_dir, filename)
    try:
        page.goto(url, timeout=8000)
        page.screenshot(path=out_path, full_page=True)
        print(f"  ✓  {url}  →  {out_path}")
        return True
    except Exception as e:
        print(f"  ✗  {url}  —  {e}")
        return False

def run_file_mode(filepath, out_dir):
    if not os.path.isfile(filepath):
        print(f"Error: file not found: '{filepath}'", file=sys.stderr)
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as fh:
        urls = [line.strip() for line in fh if line.strip()]

    if not urls:
        print("Error: The file is empty or does not contain URLs.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{len(urls)} loaded URLs from '{filepath}'")
    print(f"Output → {os.path.abspath(out_dir)}\n")
    os.makedirs(out_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        for i, url in enumerate(urls, 1):
            safe_name = re.sub(r'[^\w.-]', '_', url)[:100]
            fname = f"{i:04d}_{safe_name}.png"
            screenshot(page, url, out_dir, fname)

        browser.close()

    print(f"\n✔  Finished. {len(urls)} processed URLs.")

def run_wordlist_mode(prefix, suffix, words, count, out_dir):
    infinite = (count == 0)
    total    = len(words)
    label    = "∞ (loop)" if infinite else str(min(count, total))

    print(f"\n  Wordlist mode")
    print(f"    Prefix      : {prefix!r}")
    print(f"    Suffix      : {suffix!r}")
    print(f"    Words       : {total} in the list")
    print(f"    Iterations  : {label}")
    print(f"    Output      : {os.path.abspath(out_dir)}\n")
    os.makedirs(out_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        done = 0
        try:
            idx = 0
            while True:
                word = words[idx % total]
                idx += 1
                url  = prefix + word + suffix
                safe = re.sub(r'[^\w.-]', '_', word)[:80]
                fname = f"{done+1:05d}_{safe}.png"
                print(f"[{done+1}{'/' + str(min(count, total)) if not infinite else ''}]  {url}")
                screenshot(page, url, out_dir, fname)
                done += 1

                if not infinite and done >= count:
                    break
                if not infinite and idx >= total:
                    break

        except KeyboardInterrupt:
            print("\n⏹  Interrupted by user")
        finally:
            browser.close()

    print(f"\n✔  {done} words processed.")

def run_gen_mode(prefix, suffix, length_fn, charset, count, out_dir):
    infinite = (count == 0)
    label    = "∞" if infinite else str(count)

    print(f"\n🔀  Generation mode")
    print(f"    Prefix      : {prefix!r}")
    print(f"    Suffix      : {suffix!r}")
    print(f"    Charset     : {len(charset)} chars")
    print(f"    Iterations  : {label}")
    print(f"    Output      : {os.path.abspath(out_dir)}\n")
    os.makedirs(out_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        i = 0
        try:
            while infinite or i < count:
                length = length_fn()
                segment = ''.join(random.choice(charset) for _ in range(length))
                url     = prefix + segment + suffix
                fname   = f"{segment}.png"
                print(f"[{i+1}{'/' + str(count) if not infinite else ''}]  {url}")
                screenshot(page, url, out_dir, fname)
                i += 1
        except KeyboardInterrupt:
            print("\n⏹  Interrupted by user.")
        finally:
            browser.close()

    print(f"\n✔  {i} processed combinations.")

HELP_TEXT = """
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
"""

def main():
    if '-h' in sys.argv or '--help' in sys.argv:
        print(HELP_TEXT)
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-s', dest='prefix',  default=None)
    parser.add_argument('-e', dest='suffix',  default=None)
    parser.add_argument('-l', dest='length',  default=None)
    parser.add_argument('-m', dest='mode',    default='alnum')
    parser.add_argument('-c', dest='count',   default=None, type=int)
    parser.add_argument('-f', dest='file',    default=None)
    parser.add_argument('-o', dest='out_dir', default='./')

    args = parser.parse_args()

    # ── Modo archivo ──────────────────────────────────────────────────────
    if args.file:
        incompatible = [('-s', args.prefix), ('-e', args.suffix),
                        ('-l', args.length), ('-m', args.mode if args.mode != 'alnum' else None),
                        ('-c', args.count)]
        used = [flag for flag, val in incompatible if val is not None]
        if used:
            print(f"Error: -f no es compatible con: {', '.join(used)}", file=sys.stderr)
            sys.exit(1)
        run_file_mode(args.file, args.out_dir)
        return

    # ── Modo generación / wordlist ────────────────────────────────────────
    is_wordlist = args.mode.endswith('.txt') or (
        os.sep in args.mode or args.mode.startswith('./') or args.mode.startswith('../')
    )

    errors = []
    if args.prefix is None: errors.append("-s (prefijo) es obligatorio")
    if args.count  is None: errors.append("-c (cantidad) es obligatorio")
    # -l solo es obligatorio en modo charset aleatorio
    if not is_wordlist and args.length is None:
        errors.append("-l (length) is mandatory in charset mode")
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        print("Use -h for help.", file=sys.stderr)
        sys.exit(1)

    suffix = args.suffix if args.suffix is not None else ''

    if args.count < 0:
        print("Error: -c must be 0 (∞) or any other natural number (ℕ).", file=sys.stderr)
        sys.exit(1)

    # ── Rama wordlist ─────────────────────────────────────────────────────
    if is_wordlist:
        words = load_wordlist(args.mode)
        run_wordlist_mode(
            prefix  = args.prefix,
            suffix  = suffix,
            words   = words,
            count   = args.count,
            out_dir = args.out_dir,
        )
        return

    # ── Rama charset aleatorio ────────────────────────────────────────────
    try:
        length_fn = parse_length(args.length)
    except ValueError as e:
        print(f"Error in -l: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        charset = get_charset(args.mode)
    except ValueError as e:
        print(f"Error in -m: {e}", file=sys.stderr)
        sys.exit(1)

    run_gen_mode(
        prefix    = args.prefix,
        suffix    = suffix,
        length_fn = length_fn,
        charset   = charset,
        count     = args.count,
        out_dir   = args.out_dir,
    )

if __name__ == '__main__':
    main()
