import json
import os
import shutil
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

# কনফিগারেশন
TARGET_URL = "https://toffeelive.com/en/watch/Xi_Ga5oBNnOkwJLWkhKP"
COOKIE_NAME = "Edge-Cache-Cookie"
MAX_RETRIES = 30 
INPUT_FILE = "template/Template.json"
OUTPUT_DIR = "public"

def get_fresh_cookie():
    captured_data = None
    with sync_playwright() as p:
        # গিটহাবের জন্য headless=False থাকবে কিন্তু xvfb দিয়ে রান হবে
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def capture(request=None, response=None):
            nonlocal captured_data
            # Request/Response বা Browser Store থেকে কুকি চেক
            for c in context.cookies():
                if c['name'] == COOKIE_NAME and c['value']:
                    captured_data = {"name": c['name'], "value": c['value'], "full": f"{c['name']}={c['value']}"}
                    return True
            return False

        page.on("request", lambda req: capture())
        
        try:
            print(f"🌐 Opening: {TARGET_URL}")
            page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
            
            for attempt in range(1, MAX_RETRIES + 1):
                if capture(): break
                print(f"⏳ Attempt {attempt}: Clicking to trigger cookie...")
                page.mouse.click(random.randint(100, 500), random.randint(100, 500))
                page.wait_for_timeout(3000)
                
        except Exception as e:
            print(f"⚠️ Error during capture: {e}")
        finally:
            browser.close()
    return captured_data

def run():
    print("\n🚀 STARTING TOFFEE COOKIE SYNC (REAL BROWSER MODE)")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ১. টেমপ্লেট লোড করা
    if not os.path.exists(INPUT_FILE):
        print(f"❌ {INPUT_FILE} পাওয়া যায়নি!")
        return
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        template_data = json.load(f)

    # ২. নতুন কুকি সংগ্রহ
    cookie_info = get_fresh_cookie()
    if not cookie_info:
        print("❌ কুকি ক্যাপচার করা যায়নি!")
        return

    print(f"✅ কুকি পাওয়া গেছে: {cookie_info['value'][:30]}...")

    # ৩. ডাটা আপডেট করা
    updated_data = json.loads(json.dumps(template_data))
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    
    m3u = "#EXTM3U\n"
    for ch in updated_data.get("channels", []):
        if "headers" in ch:
            ch["headers"]["cookie"] = cookie_info["full"]
            ch["headers"]["user-agent"] = user_agent
        
        # M3U জেনারেট করা
        name = ch.get("name", "Unknown")
        logo = ch.get("logo", "")
        link = ch.get("link", "")
        m3u += f'#EXTINF:-1 tvg-logo="{logo}", {name}\n'
        m3u += f'#EXTVLCOPT:http-user-agent={user_agent}\n'
        m3u += f'#EXTHTTP:{{"cookie":"{cookie_info["full"]}"}}\n'
        m3u += f'{link}\n\n'

    updated_data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ৪. ফাইল সেভ করা
    with open(os.path.join(OUTPUT_DIR, "toffee_channels.json"), "w") as f:
        json.dump(updated_data, f, indent=4)
    with open(os.path.join(OUTPUT_DIR, "Toffee_playlist.m3u8"), "w") as f:
        f.write(m3u)

    print(f"✅ সফলভাবে {OUTPUT_DIR} ফোল্ডারে ফাইল সেভ হয়েছে।")

if __name__ == "__main__":
    run()
