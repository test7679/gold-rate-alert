import os
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime
import pytz

BOT_TOKEN = os.environ["GOLD_BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

IST = pytz.timezone("Asia/Kolkata")


def send_alert(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()


def check_gold_rate():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page.goto(
            "https://www.khazanajewellery.com/",
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(8000)

        rate_text = page.locator("text=₹").first.inner_text()
        rate = rate_text.strip()

        browser.close()

    now_ist = datetime.now(IST).strftime("%d-%m-%Y %I:%M %p")

    send_alert(
        f"💰 GOLD RATE UPDATE\n\n"
        f"Rate: {rate}\n"
        f"Time (IST): {now_ist}\n\n"
        f"https://www.khazanajewellery.com/"
    )


if __name__ == "__main__":
    try:
        check_gold_rate()
    except Exception as e:
        send_alert(f"❌ GOLD BOT ERROR:\n{str(e)}")
        raise
