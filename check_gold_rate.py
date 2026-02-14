import os
import re
from playwright.sync_api import sync_playwright
import requests

def send_telegram_message(message):
    """Send a message to Telegram"""
    bot_token = os.environ.get('GOLD_BOT_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("Error: Telegram credentials not found in environment variables")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram message sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        return False

def check_gold_rate():
    """Scrape gold rate from Khazana Jewellery website"""
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to the website
            print("Navigating to Khazana Jewellery website...")
            page.goto("https://www.khazanajewellery.com/", wait_until="networkidle")
            
            # Take a screenshot for debugging (optional)
            page.screenshot(path="before_click.png")
            print("Screenshot saved: before_click.png")
            
            # FIXED: Click on the "Today's Rate" element to open the dropdown
            # Wait for the clickable element first
            print("Waiting for 'Today's Rate' element...")
            rate_button = page.wait_for_selector("text=Today's Rate", timeout=10000)
            
            # Click to open the dropdown
            print("Clicking on 'Today's Rate' to open dropdown...")
            rate_button.click()
            
            # Now wait for the dropdown menu to appear
            print("Waiting for dropdown menu...")
            page.wait_for_selector("#dropdown-menu", timeout=10000)
            
            # Take another screenshot after dropdown appears
            page.screenshot(path="after_click.png")
            print("Screenshot saved: after_click.png")
            
            # Extract all gold rates from the dropdown
            dropdown_items = page.query_selector_all("#dropdown-menu .dropdown-item")
            
            if not dropdown_items:
                print("No dropdown items found!")
                browser.close()
                return
            
            # Parse and format the rates
            rates_message = "🏆 <b>Today's Gold & Silver Rates</b> 🏆\n\n"
            
            for item in dropdown_items:
                text = item.inner_text().strip()
                
                # Extract price information using regex
                if "Gold Price" in text:
                    match = re.search(r'Gold Price (\d+KT)/1g (\d+)', text)
                    if match:
                        karat = match.group(1)
                        price = match.group(2)
                        rates_message += f"💛 <b>{karat} Gold:</b> ₹{price}/gram\n"
                
                elif "Silver Price" in text:
                    match = re.search(r'Silver Price (\d+)', text)
                    if match:
                        price = match.group(1)
                        rates_message += f"⚪ <b>Silver:</b> ₹{price}/gram\n"
            
            rates_message += f"\n📅 <i>Updated: {page.evaluate('new Date().toLocaleString()')}</i>"
            rates_message += "\n🔗 <a href='https://www.khazanajewellery.com/'>Visit Website</a>"
            
            print("\n" + "="*50)
            print(rates_message)
            print("="*50 + "\n")
            
            # Send to Telegram
            send_telegram_message(rates_message)
            
        except Exception as e:
            error_message = f"❌ <b>Error checking gold rates:</b>\n{str(e)}"
            print(f"Error: {e}")
            
            # Take error screenshot for debugging
            try:
                page.screenshot(path="error_screenshot.png")
                print("Error screenshot saved: error_screenshot.png")
            except:
                pass
            
            send_telegram_message(error_message)
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    check_gold_rate()
