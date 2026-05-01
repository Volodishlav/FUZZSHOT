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
    """
    Parsea el flag -l. Puede ser:
      - Un número entero fijo: "5"
      - Una expresión con condiciones: "<=6&>2"
    Devuelve una función que genera una longitud válida aleatoria,
    o siempre el mismo número si es fijo.
    """
    val = val.strip()

    # Número fijo
    if re.match(r'^\d+$', val):
        n = int(val)
        return lambda: n

    # Expresión tipo "<=6&>2" — parsear condiciones
    conditions = []
    for part in val.split('&'):
        part = part.strip()
        m = re.match(r'^([<>]=?|==)(\d+)$', part)
        if not m:
            raise ValueError(f"Condición de longitud no reconocida: '{part}'")
        op, num = m.group(1), int(m.group(2))
        conditions.append((op, num))

    # Determinar rango válido
    lo, hi = 1, 256
    for op, num in conditions:
        if op == '>':   lo = max(lo, num + 1)
        elif op == '>=': lo = max(lo, num)
        elif op == '<':  hi = min(hi, num - 1)
        elif op == '<=': hi = min(hi, num)
        elif op == '==': lo = hi = num

    if lo > hi:
        raise ValueError(f"Condiciones de longitud imposibles: rango [{lo}, {hi}]")

    return lambda: random.randint(lo, hi)

# ── Charset según modo ────────────────────────────────────────────────────

MODOS = {
    'alpha':       string.ascii_letters,
    'lower':       string.ascii_lowercase,
    'upper':       string.ascii_uppercase,
    'num':      string.digits,
    'alnum':       string.ascii_letters + string.digits,
    'lower+num': string.ascii_lowercase + string.digits,
    'upper+num': string.ascii_uppercase + string.digits,
    'hex':         '0123456789abcdef',
    'HEX':         '0123456789ABCDEF',
    'punct':       string.punctuation,
    'printable':   string.printable.strip(),
    'urlsafe':     string.ascii_letters + string.digits + '-_',
}

def get_charset(mode):
    if mode in MODOS:
        return MODOS[mode]
    # Permitir combinaciones con '+': ej. "lower+digits+punct"
    charset = ''
    for part in mode.split('+'):
        if part in MODOS:
            charset += MODOS[part]
        else:
            raise ValueError(
                f"Modo '{part}' no reconocido.\n"
                f"Modos disponibles: {', '.join(MODOS.keys())}"
            )
    return ''.join(sorted(set(charset)))

def load_wordlist(filepath):
    """Carga un .txt y devuelve lista de palabras (una por línea, sin blancos)."""
    if not os.path.isfile(filepath):
        print(f"Error: no se encontró la wordlist '{filepath}'", file=sys.stderr)
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
        words = [line.strip() for line in fh if line.strip()]
    if not words:
        print(f"Error: la wordlist '{filepath}' está vacía.", file=sys.stderr)
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
        print(f"Error: no se encontró el archivo '{filepath}'", file=sys.stderr)
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as fh:
        urls = [line.strip() for line in fh if line.strip()]

    if not urls:
        print("El archivo está vacío o no contiene URLs.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{len(urls)} URLs cargadas desde '{filepath}'")
    print(f"Salida → {os.path.abspath(out_dir)}\n")
    os.makedirs(out_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        for i, url in enumerate(urls, 1):
            safe_name = re.sub(r'[^\w.-]', '_', url)[:100]
            fname = f"{i:04d}_{safe_name}.png"
            screenshot(page, url, out_dir, fname)

        browser.close()

    print(f"\n✔  Terminado. {len(urls)} URLs procesadas.")

def run_wordlist_mode(prefix, suffix, words, count, out_dir):
    infinite = (count == 0)
    total    = len(words)
    label    = "∞ (bucle)" if infinite else str(min(count, total))

    print(f"\n  Modo wordlist")
    print(f"    Prefijo  : {prefix!r}")
    print(f"    Sufijo   : {suffix!r}")
    print(f"    Palabras : {total} en la lista")
    print(f"    Cantidad : {label}")
    print(f"    Salida   → {os.path.abspath(out_dir)}\n")
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
            print("\n⏹  Interrumpido por el usuario.")
        finally:
            browser.close()

    print(f"\n✔  {done} palabras procesadas.")

def run_gen_mode(prefix, suffix, length_fn, charset, count, out_dir):
    infinite = (count == 0)
    label    = "∞" if infinite else str(count)

    print(f"\n🔀  Modo generación")
    print(f"    Prefijo  : {prefix!r}")
    print(f"    Sufijo   : {suffix!r}")
    print(f"    Charset  : {len(charset)} chars")
    print(f"    Cantidad : {label}")
    print(f"    Salida   → {os.path.abspath(out_dir)}\n")
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
            print("\n⏹  Interrumpido por el usuario.")
        finally:
            browser.close()

    print(f"\n✔  {i} combinaciones procesadas.")

HELP_TEXT = """
─────────────────────────────────────────────────────────────────────────────────────
  -s PREFIX       Primera parte de la URL (antes de la sección variable)
  -e SUFFIX       Segunda parte de la URL (después de la sección variable)
  -l LENGTH       Longitud de la sección generada.
                    Número fijo:     -l 5
                    Con condiciones: -l "<=6&>2"  (operadores: < > <= >= ==)
                    Se pueden encadenar con &.
  -m MODE/FILE    Charset o ruta a wordlist:
                      alpha        a-z A-Z
                      lower        a-z
                      upper        A-Z
                      num          0-9
                      alnum        a-z A-Z 0-9  (por defecto)
                      lower+num    a-z 0-9
                      upper+num    A-Z 0-9
                      hex          0-9 a-f
                      HEX          0-9 A-F
                      urlsafe      a-z A-Z 0-9 - _
                      printable    todos los caracteres imprimibles
                  Wordlist: pasa la ruta a un .txt (una palabra por línea).
                      El programa probará cada palabra en orden en vez de generar
                      combinaciones aleatorias. Con -c 0 recorre en bucle infinito.
  -c COUNT        Número de iteraciones. 0 = infinito (Ctrl+C para parar).
                      En modo wordlist finito se limita también al tamaño de la lista.
  -f FILE         Ruta a un .txt con una URL/IP por línea.
  -o DIR          Directorio de salida para las capturas (por defecto: ./)
  -h, --help      Muestra esta ayuda.
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
        errors.append("-l (longitud) es obligatorio en modo charset")
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        print("Usa -h para ver la ayuda.", file=sys.stderr)
        sys.exit(1)

    suffix = args.suffix if args.suffix is not None else ''

    if args.count < 0:
        print("Error: -c debe ser 0 (infinito) o un número positivo.", file=sys.stderr)
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
        print(f"Error en -l: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        charset = get_charset(args.mode)
    except ValueError as e:
        print(f"Error en -m: {e}", file=sys.stderr)
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
