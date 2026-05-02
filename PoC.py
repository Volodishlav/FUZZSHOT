from playwright.sync_api import sync_playwright
import random
import string

# This is the base script used in the tool
with sync_playwright() as p:
    for i in range(15000, 200000): # set the number of pages to capture
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        combo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        route = "https://example.com/" + combo + ".zip" # modify this
        print(route)
        page.goto(route)
        page.screenshot(path="./" + str(i) + ".png", full_page=True)
        browser.close()
        i = i+
