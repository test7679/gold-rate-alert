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
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
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

        # Allow JS to render price banner
        page.wait_for_timeout(6000)

        # ✅ This text is ALWAYS present when rates load
        page.wait_for_selector("text=Today's Rate", timeout=60000)

        # Collect all visible rate entries
        rate_elements = page.locator(
            "li a:text('Gold Price'), li a:text('Silver Price')"
        ).all_inner_texts()

        browser.close()

    if not rate_elements:
        return  # silent if site fails

    now_ist = datetime.now(IST).strftime("%d-%m-%Y %I:%M %p")

    message_lines = []
    for rate in rate_elements:
        message_lines.append(f"• {rate}")

    message = (
        "💰 KHZANA METAL RATES\n\n"
        + "\n".join(message_lines)
        + f"\n\n🕰 Time (IST): {now_ist}\n"
        + "🔗 https://www.khazanajewellery.com/"
    )

    send_alert(message)


if __name__ == "__main__":
    check_gold_rate()
