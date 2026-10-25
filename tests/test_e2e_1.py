import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from playwright.sync_api import sync_playwright
import uuid

def test_e2e_1():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Mock GPS at Pondicherry (11.9416, 79.8083)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            geolocation={"latitude": 11.9416, "longitude": 79.8083},
            permissions=["geolocation"]
        )
        page = context.new_page()
        
        console_errors = []
        failed_requests = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ['error', 'warning'] else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url} -> {req.failure}"))
        
        # 1. Load app
        page.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        
        # 2. Register new user
        login_btn = page.locator("button:has-text('Sign In')")
        if login_btn.is_visible():
            login_btn.click()
            page.wait_for_timeout(500)
            
            reg_tab = page.locator("button:has-text('Create Traveler Account')")
            if reg_tab.is_visible():
                reg_tab.click()
                page.wait_for_timeout(300)
                
            test_email = f"e2e_user_{uuid.uuid4().hex[:6]}@voyantra.com"
            page.locator("input[placeholder*='Full Name']").fill("E2E Traveler")
            page.locator("input[placeholder*='name@example.com']").fill(test_email)
            page.locator("input[placeholder*='password']").fill("secret123")
            page.locator("button:has-text('Complete Registration')").click()
            page.wait_for_timeout(1000)
            print(f"Registered user: {test_email}")
            
        # 3. GPS detects Pondicherry
        notice = page.locator("header div:has-text('Detected Location')")
        print("GPS Notice visible:", notice.is_visible(), notice.inner_text() if notice.is_visible() else "")
        
        # 4. Set preferences in Profile / Preferences page
        pref_tab = page.locator("button:has-text('My Preferences')")
        pref_tab.click()
        page.wait_for_timeout(800)
        
        # Select age group: 41-60 yrs (Family & Group Travel) for age 55
        family_pill = page.locator("button:has-text('41 - 60 yrs')")
        if family_pill.is_visible():
            family_pill.click()
            page.wait_for_timeout(300)
            print("Selected Age Group: 41-60 (Family)")
            
        # Select dietary: Pure Veg & Jain
        veg_pill = page.locator("button:has-text('Pure Veg & Jain')")
        if veg_pill.is_visible():
            veg_pill.click()
            page.wait_for_timeout(300)
            print("Selected Dietary: Pure Veg & Jain")
            
        # Select budget: Moderate
        mod_pill = page.locator("button:has-text('Moderate')")
        if mod_pill.is_visible():
            mod_pill.click()
            page.wait_for_timeout(300)
            print("Selected Budget: Moderate")
            
        # 5. Go to AI Planner
        page.locator("button:has-text('Personalized Planner')").click()
        page.wait_for_timeout(1000)
        
        # Fill in custom travel prompt
        prompt = "2-day trip to Pondicherry, pure vegetarian, medium budget, love beaches and heritage walks"
        page.locator("textarea").fill(prompt)
        page.wait_for_timeout(300)
        
        # Click Generate AI Itinerary
        gen_btn = page.locator("button:has-text('Generate AI Itinerary')")
        print("Generate button enabled:", gen_btn.is_enabled())
        gen_btn.click()
        
        # Wait for itinerary to generate
        page.wait_for_selector("text=Drag & Drop Interactive Plan", timeout=45000)
        print("AI Itinerary generated successfully!")
        
        # Check generated days
        days = page.locator("h3:has-text('Day 1'), h3:has-text('Day 2')").all_inner_texts()
        print("Generated Day titles:", days)
        
        # Check Chat Refinement panel
        chat_box = page.locator("input[placeholder*='Type your second prompt']")
        print("Refinement chat input visible:", chat_box.is_visible())
        
        # 6. Check crowd badge on Explore
        page.locator("button:has-text('Explore Places')").click()
        page.wait_for_timeout(800)
        crowd_badge = page.locator("button[title*='Crowd Analytics']").first
        crowd_badge.click()
        page.wait_for_timeout(800)
        print("Crowd popover open:", page.locator("text=Crowd Density Analytics").is_visible())
        page.mouse.click(10, 10)
        page.wait_for_timeout(500)
        
        print("\nConsole errors/warnings:", len(console_errors), console_errors[:5])
        print("Failed network requests:", len(failed_requests), failed_requests)
        
        context.close()
        browser.close()

if __name__ == '__main__':
    test_e2e_1()
