from playwright.sync_api import sync_playwright

def test_crowd_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.goto('http://127.0.0.1:5173/', wait_until="domcontentloaded")
        
        # Proceed with Pondicherry
        proceed = page.locator("button:has-text('Proceed with Pondicherry')")
        if proceed.is_visible():
            proceed.click()
            page.wait_for_timeout(500)
            
        # 1. Find CrowdBadge buttons
        # e.g. text "Moderate Crowd", "Bustling / High Footfall", "Serene / Low Crowd"
        badge = page.locator("button[title*='Crowd Analytics']").first
        print("Found CrowdBadge button. Visible:", badge.is_visible())
        badge.click()
        page.wait_for_timeout(1000)
        
        # 2. Check Popover
        popover = page.locator("text=Crowd Density Analytics")
        print("Popover visible on click:", popover.is_visible())
        
        progress_bar = page.locator("text=Dynamic Density Index:")
        print("Progress bar header visible:", progress_bar.is_visible())
        
        quiet_win = page.locator("text=Best Visiting Window:")
        print("Quiet window visible:", quiet_win.is_visible(), quiet_win.inner_text() if quiet_win.is_visible() else "")
        
        drivers = page.locator("text=Crowd Drivers:")
        print("Drivers visible:", drivers.is_visible())
        
        chart = page.locator("text=Hourly Crowd Curve")
        print("Hourly curve chart visible:", chart.is_visible())
        
        # 3. Test Esc key press
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        print("Popover visible after pressing Escape:", popover.is_visible())
        
        # 4. Test outside click
        page.mouse.click(10, 10)
        page.wait_for_timeout(500)
        print("Popover visible after clicking outside (10, 10):", popover.is_visible())
        
        # 5. Check badge colors
        all_badges = page.locator("button[title*='Crowd Analytics']").all()
        print(f"Total crowd badges found: {len(all_badges)}")
        for i, b in enumerate(all_badges[:4]):
            cls = b.get_attribute("class")
            txt = b.inner_text().strip()
            print(f"  Badge {i}: text='{txt}' class='{cls}'")
            
        browser.close()

if __name__ == '__main__':
    test_crowd_ui()
