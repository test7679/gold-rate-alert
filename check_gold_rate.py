def check_gold_rate():
    from playwright.sync_api import sync_playwright
    from datetime import datetime
    import pytz

    IST = pytz.timezone("Asia/Kolkata")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            "https://www.khazanajewellery.com/",
            wait_until="networkidle",
            timeout=60000
        )

        # ✅ Wait for ANY gold text (most reliable signal)
        page.wait_for_selector("text=Gold Price", timeout=60000)

        # ✅ Collect all dropdown-like values safely
        rates = page.locator("li a").all_inner_texts()

        browser.close()

    metal_rates = [
        r.strip()
        for r in rates
        if "Gold Price" in r or "Silver Price" in r
    ]

    now_ist = datetime.now(IST).strftime("%d-%m-%Y %I:%M %p")

    if not metal_rates:
        send_alert(
            "⚠️ KHZANA METAL RATES\n\n"
            "No rates detected.\n"
            f"Time (IST): {now_ist}"
        )
        return

    message = (
        "💰 KHZANA METAL RATES\n\n"
        + "\n".join(f"• {rate}" for rate in metal_rates)
        + f"\n\n🕰 Time (IST): {now_ist}\n"
        + "🔗 https://www.khazanajewellery.com/"
    )

    send_alert(message)
