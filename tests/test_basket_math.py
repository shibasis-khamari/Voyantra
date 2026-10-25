from playwright.sync_api import sync_playwright

def test_basket_math():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto('http://127.0.0.1:5173/', wait_until="domcontentloaded")
        
        # Proceed with Pondicherry
        proceed_btn = page.locator("button:has-text('Proceed with Pondicherry')")
        if proceed_btn.is_visible():
            proceed_btn.click()
            page.wait_for_timeout(500)
            
        # Go to planner and clear any existing plan
        page.locator("button:has-text('Trip Basket')").click()
        page.wait_for_timeout(500)
        clear_btn = page.locator("button:has-text('Clear All')")
        if clear_btn.is_visible():
            clear_btn.click()
            page.wait_for_timeout(500)
            
        # Back to Explore
        page.locator("button:has-text('Explore Places')").click()
        page.wait_for_timeout(500)
        
        # Find "Cafe des Arts" card and click "Add to Trip" (estimated cost: ₹450)
        cafe_card = page.locator("div:has-text('Cafe des Arts')").filter(has=page.locator("button:has-text('Add to Trip')")).last
        cafe_btn = cafe_card.locator("button:has-text('Add to Trip')")
        cafe_btn.click()
        page.wait_for_timeout(300)
        
        # Find "Paradise Beach" card and click "Add to Trip" (estimated cost: ₹350)
        paradise_card = page.locator("div:has-text('Paradise Beach')").filter(has=page.locator("button:has-text('Add to Trip')")).last
        paradise_btn = paradise_card.locator("button:has-text('Add to Trip')")
        paradise_btn.click()
        page.wait_for_timeout(300)
        
        # Now go to Trip Basket
        page.locator("button:has-text('Trip Basket')").click()
        page.wait_for_timeout(500)
        
        # Check Basket cost
        # Total cost should be 450 + 350 = 800
        basket_text = page.locator(".space-y-4").first.inner_text()
        print("Basket panel text with 2 paid places:\n", basket_text)
        
        # Remove Paradise Beach
        remove_btns = page.locator("button:has(svg.lucide-trash2)")
        print(f"Found {remove_btns.count()} trash/remove buttons.")
        if remove_btns.count() > 0:
            remove_btns.first.click()
            page.wait_for_timeout(500)
            basket_text_after = page.locator(".space-y-4").first.inner_text()
            print("Basket panel text after removing 1 place:\n", basket_text_after)
            
        browser.close()

if __name__ == '__main__':
    test_basket_math()
