import os
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_telegram_message(message):
    """Send a message to Telegram"""
    bot_token = os.environ.get('GOLD_BOT_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("Error: GOLD_BOT_TOKEN or CHAT_ID not set in environment variables")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Message sent successfully to Telegram")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        return False

def check_gold_rate():
    """Scrape gold rate and send to Telegram"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        print("Fetching gold rates from Khazana Jewellery...")
        response = requests.get('https://www.khazanajewellery.com/', 
                               headers=headers, 
                               timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rates_found = {}
        
        # Look in dropdown menu items
        dropdown_items = soup.select('#dropdown-menu li a')
        
        if dropdown_items:
            for item in dropdown_items:
                text = item.get_text(strip=True)
                
                gold_match = re.search(r'Gold Price (\d+KT)/1g (\d+)', text)
                if gold_match:
                    rates_found[gold_match.group(1)] = gold_match.group(2)
                
                silver_match = re.search(r'Silver Price (\d+)', text)
                if silver_match:
                    rates_found['Silver'] = silver_match.group(1)
        
        # Fallback: Look in dropdown title
        if not rates_found:
            dropdown_title = soup.select_one('#dropdown_title')
            if dropdown_title:
                text = dropdown_title.get_text(strip=True)
                gold_match = re.search(r'Gold Price (\d+KT)/1g (\d+)', text)
                if gold_match:
                    rates_found[gold_match.group(1)] = gold_match.group(2)
        
        # Fallback: Search entire HTML
        if not rates_found:
            gold_matches = re.finditer(r'Gold Price (\d+KT)/1g (\d+)', response.text)
            for match in gold_matches:
                rates_found[match.group(1)] = match.group(2)
            
            silver_match = re.search(r'Silver Price (\d+)', response.text)
            if silver_match:
                rates_found['Silver'] = silver_match.group(1)
        
        # Only send message if we found rates
        if rates_found:
            message = "🏆 <b>Today's Gold & Silver Rates</b> 🏆\n\n"
            
            for karat in ['22KT', '24KT', '18KT']:
                if karat in rates_found:
                    message += f"💛 <b>{karat} Gold:</b> ₹{rates_found[karat]}/gram\n"
            
            if 'Silver' in rates_found:
                message += f"⚪ <b>Silver:</b> ₹{rates_found['Silver']}/gram\n"
            
            message += "\n📅 <i>Source: Khazana Jewellery</i>"
            
            send_telegram_message(message)
            print(f"Found rates: {rates_found}")
        else:
            print("No gold rates found on the website")
    
    except Exception as e:
        print(f"Error checking gold rate: {e}")

if __name__ == "__main__":
    check_gold_rate()
