from playwright.sync_api import sync_playwright

def test_basket_estimator():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        
        # Navigate to app
        page.goto('http://127.0.0.1:5173/', wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        
        # If Proceed with Pondicherry is visible, click it
        proceed_btn = page.locator("button:has-text('Proceed with Pondicherry')")
        if proceed_btn.is_visible():
            proceed_btn.click()
            page.wait_for_timeout(500)
            
        print("Page title:", page.title())
        
        # Find place cards and click "Add to Trip"
        add_btns = page.locator("button:has-text('Add to Trip')")
        count = add_btns.count()
        print(f"Found {count} 'Add to Trip' buttons.")
        
        if count >= 2:
            # Click first place card
            add_btns.nth(0).click()
            page.wait_for_timeout(300)
            # Click second place card
            add_btns.nth(0).click()
            page.wait_for_timeout(300)
            print("Clicked to add 2 places to trip.")
            
        # Click "Trip Basket" button in Navbar
        basket_nav = page.locator("button:has-text('Trip Basket')")
        basket_nav.click()
        page.wait_for_timeout(1000)
        
        # Verify Basket section on Planner page
        basket_title = page.locator("h3:has-text('Your Trip Basket')")
        print("Basket Title visible:", basket_title.is_visible())
        assert basket_title.is_visible(), "Your Trip Basket failed to open!"
        
        # Verify Total Activity Cost stat
        cost_stat = page.locator("text=Total Activity Cost")
        print("Total Activity Cost visible:", cost_stat.is_visible())
        assert cost_stat.is_visible(), "Total Activity Cost label missing!"
        
        # Verify Est. Time Needed stat
        time_stat = page.locator("text=Est. Time Needed")
        print("Est. Time Needed visible:", time_stat.is_visible())
        assert time_stat.is_visible(), "Est. Time Needed label missing!"
        
        print("SUCCESS: Trip Basket Estimator correctly loads and calculates costs.")
        browser.close()

if __name__ == '__main__':
    test_basket_estimator()
