from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.goto('http://127.0.0.1:5173/', wait_until="domcontentloaded")
        
        proceed = page.locator("button:has-text('Proceed with Pondicherry')")
        if proceed.is_visible():
            proceed.click()
            page.wait_for_timeout(500)
            
        page.locator("button:has-text('Trip Basket')").click()
        page.wait_for_timeout(500)
        
        # Clear basket if any
        clear_btn = page.locator("button:has-text('Clear')")
        if clear_btn.is_visible():
            clear_btn.click()
            page.wait_for_timeout(500)
            
        # Back to Explore Places
        page.locator("button:has-text('Explore Places')").click()
        page.wait_for_timeout(500)
        
        # Add Cafe des Arts (Rs 450, 60 mins)
        cafe_card = page.locator("h3:has-text('Cafe des Arts')").locator("xpath=ancestor::div[contains(@class, 'rounded-2xl')]")
        cafe_card.locator("button:has-text('Add to Trip')").click()
        page.wait_for_timeout(400)
        
        # Add Paradise Beach (Rs 350, 180 mins)
        paradise_card = page.locator("h3:has-text('Paradise Beach')").locator("xpath=ancestor::div[contains(@class, 'rounded-2xl')]")
        paradise_card.locator("button:has-text('Add to Trip')").click()
        page.wait_for_timeout(400)
        
        # Open Trip Basket
        page.locator("button:has-text('Trip Basket')").click()
        page.wait_for_timeout(800)
        
        # Total cost container
        stat_box = page.locator("text=Total Activity Cost").locator("xpath=..")
        print("Total Activity Cost box with 2 places (450 + 350 = 800):")
        print(stat_box.inner_text().encode('ascii', 'replace').decode('ascii'))
        
        # List of items in basket
        items = page.locator("div.truncate").all_inner_texts()
        print("Items listed in basket:", [it.encode('ascii', 'replace').decode('ascii') for it in items])
        
        # Remove first item
        trash_btn = page.locator("button[title='Remove']").first
        trash_btn.click()
        page.wait_for_timeout(500)
        
        print("\nTotal Activity Cost box after removing 1 item (350 remaining):")
        print(stat_box.inner_text().encode('ascii', 'replace').decode('ascii'))
        print("Items listed in basket after deletion:", [it.encode('ascii', 'replace').decode('ascii') for it in page.locator("div.truncate").all_inner_texts()])
        
        browser.close()

if __name__ == '__main__':
    inspect()
