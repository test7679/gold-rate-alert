import os
import requests
from playwright.sync_api import sync_playwright

GOLD_BOT_TOKEN = os.environ["GOLD_BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

RATE_FILE = "last_rate.txt"
KHAZANA_URL = "https://www.khazanajewellery.com/"


def send_alert(message: str):
    url = f"https://api.telegram.org/bot{GOLD_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()


def read_last_rate():
    if not os.path.exists(RATE_FILE):
        return None
    with open(RATE_FILE, "r") as f:
        return f.read().strip()


def write_last_rate(rate: str):
    with open(RATE_FILE, "w") as f:
        f.write(rate)


def get_current_gold_rate():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(KHAZANA_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        # ⚠️ Selector may change — verified common pattern
        rate_text = page.locator("text=/Gold Rate/i").first.inner_text()

        browser.close()
        return rate_text.strip()


def check_gold_rate():
    current_rate = get_current_gold_rate()
    last_rate = read_last_rate()

    print("Last rate:", last_rate)
    print("Current rate:", current_rate)

    if last_rate != current_rate:
        send_alert(
            "💰 Khazana Gold Rate Updated!\n\n"
            f"New Rate:\n{current_rate}\n\n"
            f"Website:\n{KHAZANA_URL}"
        )
        write_last_rate(current_rate)
    else:
        print("Gold rate unchanged")


if __name__ == "__main__":
    check_gold_rate()
