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
    """Scrape gold rate from Khazana Jewellery website - Ultra Robust Version"""
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        
        # Create context with realistic settings
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            # Navigate to the website - be very patient
            print("Navigating to Khazana Jewellery website...")
            
            # Try simplest possible load
            page.goto("https://www.khazanajewellery.com/", timeout=90000)
            print("Initial page load complete")
            
            # Give it plenty of time to render
            print("Waiting for page to fully render...")
            page.wait_for_timeout(5000)
            
            # Take screenshot
            page.screenshot(path="page_state.png", full_page=True)
            print("Screenshot saved: page_state.png")
            
            # Get the ENTIRE page content
            print("Extracting page content...")
            page_content = page.content()
            
            # Also try to get any visible text
            body_text = page.evaluate("() => document.body.innerText")
            
            print(f"Page content length: {len(page_content)} characters")
            print(f"Body text length: {len(body_text)} characters")
            
            # METHOD 1: Parse from HTML content directly
            print("\n--- Attempting Method 1: Parse HTML content ---")
            rates_found = {}
            
            # Look for all gold rate patterns in the HTML
            gold_patterns = [
                r'Gold Price (\d+KT)/1g (\d+)',  # Standard format
                r'(\d+KT).*?(\d{5})',             # Flexible format
                r'dropdown_title[^>]*>([^<]*Gold Price[^<]*)',  # From dropdown title
            ]
            
            for pattern in gold_patterns:
                matches = re.finditer(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    try:
                        if len(match.groups()) >= 2:
                            karat = match.group(1)
                            price = match.group(2)
                            if karat and price and price.isdigit():
                                rates_found[karat] = price
                                print(f"  Found: {karat} = ₹{price}")
                    except:
                        pass
            
            # Look for silver price
            silver_patterns = [
                r'Silver Price (\d+)',
                r'Silver.*?(\d{3})',
            ]
            
            for pattern in silver_patterns:
                matches = re.finditer(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    try:
                        price = match.group(1)
                        if price and price.isdigit():
                            rates_found['Silver'] = price
                            print(f"  Found: Silver = ₹{price}")
                            break
                    except:
                        pass
                if 'Silver' in rates_found:
                    break
            
            # METHOD 2: If HTML parsing found nothing, try visible text
            if not rates_found:
                print("\n--- Attempting Method 2: Parse visible text ---")
                
                for pattern in gold_patterns:
                    matches = re.finditer(pattern, body_text, re.IGNORECASE)
                    for match in matches:
                        try:
                            if len(match.groups()) >= 2:
                                karat = match.group(1)
                                price = match.group(2)
                                if karat and price and price.isdigit():
                                    rates_found[karat] = price
                                    print(f"  Found: {karat} = ₹{price}")
                        except:
                            pass
                
                for pattern in silver_patterns:
                    matches = re.finditer(pattern, body_text, re.IGNORECASE)
                    for match in matches:
                        try:
                            price = match.group(1)
                            if price and price.isdigit():
                                rates_found['Silver'] = price
                                print(f"  Found: Silver = ₹{price}")
                                break
                        except:
                            pass
                    if 'Silver' in rates_found:
                        break
            
            # METHOD 3: Try JavaScript evaluation as last resort
            if not rates_found:
                print("\n--- Attempting Method 3: JavaScript evaluation ---")
                try:
                    # Try to find elements using JavaScript
                    js_content = page.evaluate("""
                        () => {
                            const results = [];
                            
                            // Look for dropdown items
                            const dropdownItems = document.querySelectorAll('#dropdown-menu li a');
                            dropdownItems.forEach(item => results.push(item.innerText));
                            
                            // Look for dropdown title
                            const title = document.querySelector('#dropdown_title');
                            if (title) results.push(title.innerText);
                            
                            // Look for any text containing "Gold Price" or "Silver Price"
                            const allText = document.body.innerText;
                            const lines = allText.split('\\n');
                            lines.forEach(line => {
                                if (line.includes('Gold Price') || line.includes('Silver Price')) {
                                    results.push(line);
                                }
                            });
                            
                            return results;
                        }
                    """)
                    
                    print(f"JavaScript found {len(js_content)} text items")
                    
                    for text in js_content:
                        print(f"  Checking: {text}")
                        
                        # Parse gold rates
                        gold_match = re.search(r'Gold Price (\d+KT)/1g (\d+)', text)
                        if gold_match:
                            karat = gold_match.group(1)
                            price = gold_match.group(2)
                            rates_found[karat] = price
                            print(f"    -> Extracted: {karat} = ₹{price}")
                        
                        # Parse silver rate
                        silver_match = re.search(r'Silver Price (\d+)', text)
                        if silver_match:
                            price = silver_match.group(1)
                            rates_found['Silver'] = price
                            print(f"    -> Extracted: Silver = ₹{price}")
                    
                except Exception as js_error:
                    print(f"JavaScript method failed: {js_error}")
            
            # Build message from whatever we found
            if rates_found:
                print("\n" + "="*60)
                print("SUCCESS! Found rates:")
                
                rates_message = "🏆 <b>Today's Gold & Silver Rates</b> 🏆\n\n"
                
                # Add gold rates
                for karat in ['22KT', '24KT', '18KT']:
                    if karat in rates_found:
                        rates_message += f"💛 <b>{karat} Gold:</b> ₹{rates_found[karat]}/gram\n"
                
                # Add silver rate
                if 'Silver' in rates_found:
                    rates_message += f"⚪ <b>Silver:</b> ₹{rates_found['Silver']}/gram\n"
                
                rates_message += "\n📅 <i>Source: Khazana Jewellery</i>"
                rates_message += "\n🔗 <a href='https://www.khazanajewellery.com/'>Visit Website</a>"
                
                print(rates_message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<a href=\'https://www.khazanajewellery.com/\'>', '').replace('</a>', ''))
                print("="*60 + "\n")
                
                send_telegram_message(rates_message)
            else:
                # Save HTML for debugging
                with open('page_content.html', 'w', encoding='utf-8') as f:
                    f.write(page_content)
                print("Saved page content to page_content.html for debugging")
                
                with open('body_text.txt', 'w', encoding='utf-8') as f:
                    f.write(body_text)
                print("Saved body text to body_text.txt for debugging")
                
                raise Exception("Could not find any gold/silver rates on the page. Check debug files.")
            
        except Exception as e:
            error_message = f"❌ <b>Error checking gold rates:</b>\n\n{str(e)[:500]}"
            print(f"\n{'='*60}")
            print(f"ERROR: {e}")
            print(f"{'='*60}\n")
            
            # Take error screenshot
            try:
                page.screenshot(path="error_screenshot.png", full_page=True)
                print("Error screenshot saved: error_screenshot.png")
            except:
                pass
            
            send_telegram_message(error_message)
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    check_gold_rate()
