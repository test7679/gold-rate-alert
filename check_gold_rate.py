import os
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime
import pytz

BOT_TOKEN = os.environ["GOLD_BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

IST = pytz.timezone("Asia/Kolkata")


def send_alert(message: str):
    # Telegram-safe (no markdown to avoid 400 errors)
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

        # Allow JS to render dropdown HTML
        page.wait_for_timeout(8000)

        # ✅ READ DROPDOWN CONTENT DIRECTLY (NO CLICK)
        dropdown_text = page.locator("#dropdown-menu").inner_text().strip()

        browser.close()

    now_ist = datetime.now(IST).strftime("%d-%m-%Y %I:%M %p")

    if not dropdown_text:
        send_alert(
            "⚠️ KHZANA METAL RATES\n\n"
            "Dropdown found but empty.\n"
            f"Time (IST): {now_ist}"
        )
        return

    lines = [line.strip() for line in dropdown_text.splitlines() if line.strip()]

    message = (
        "💰 KHZANA METAL RATES\n\n"
        + "\n".join(f"• {line}" for line in lines)
        + f"\n\n🕰 Time (IST): {now_ist}\n"
        + "🔗 https://www.khazanajewellery.com/"
    )

    send_alert(message)


if __name__ == "__main__":
    try:
        check_gold_rate()
    except Exception as e:
        # Always safe message
        send_alert(f"GOLD BOT ERROR:\n{str(e)}")
        raise
