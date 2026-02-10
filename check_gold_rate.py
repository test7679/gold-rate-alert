import os
import json
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime
import pytz

BOT_TOKEN = os.environ["GOLD_BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

RATE_FILE = "last_gold_rate.json"
IST = pytz.timezone("Asia/Kolkata")


def send_alert(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()


def get_last_rate():
    if os.path.exists(RATE_FILE):
        with open(RATE_FILE, "r") as f:
            return json.load(f).get("rate")
    return None


def save_rate(rate):
    with open(RATE_FILE, "w") as f:
        json.dump({"rate": rate}, f)


def check_gold_rate():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            "https://www.khazanajewellery.com/",
            wait_until="domcontentloaded",
            timeout=60000
        )


        page.wait_for_timeout(5000)

        # ⚠️ Selector may change – adjust if needed
        rate_text = page.locator("text=₹").first.inner_text()
        rate = rate_text.strip()

        browser.close()

    last_rate = get_last_rate()
    now_ist = datetime.now(IST).strftime("%d-%m-%Y %I:%M %p")

    if last_rate != rate:
        save_rate(rate)
        send_alert(
            f"💰 GOLD RATE UPDATED\n\n"
            f"New Rate: {rate}\n"
            f"Time (IST): {now_ist}\n\n"
            f"https://www.khazanajewellery.com/"
        )
    else:
        print("No change in gold rate")


if __name__ == "__main__":
    try:
        check_gold_rate()
    except Exception as e:
        send_alert(f"❌ GOLD BOT ERROR:\n{str(e)}")
        raise
