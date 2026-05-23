import argparse
import sys
from playwright.sync_api import sync_playwright
import random
import string

def RUN(start, suffix):
    # This is the base script used in the tool
    with sync_playwright() as p:
        for i in range(15000, 200000): # set the number of pages to capture
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            combo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            route = start + combo + suffix
            print(route)
            page.goto(route)
            page.screenshot(path="./" + str(i) + ".png", full_page=True)
            browser.close()
            i += 1

HELP_TEXT = """
─────────────────────────────────────────────────────────────────────────────────────
  -  START        Start of the URL (before the variable section)
  -  SUFFIX       End of the URL (after the variable section)
  -h, --help      Show this help message.

  Usage example:  python3 PoC.py "https://example.com/" ".zip"
─────────────────────────────────────────────────────────────────────────────────────
"""

def main():
    if '-h' in sys.argv or '--help' in sys.argv:
            print(HELP_TEXT)
            sys.exit(0)

    parser = argparse.ArgumentParser()

    parser.add_argument("start")
    parser.add_argument("suffix")

    args = parser.parse_args()

    print(args.start)
    print(args.suffix)
    
    RUN(args.start, args.suffix)