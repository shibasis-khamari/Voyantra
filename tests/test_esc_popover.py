from playwright.sync_api import sync_playwright

def test_esc():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            geolocation={"latitude": 11.9416, "longitude": 79.8083},
            permissions=["geolocation"]
        )
        page = context.new_page()
        page.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        # Click the first crowd badge
        badge_btn = page.locator("button[title*='Crowd Analytics']").first
        badge_btn.click()
        page.wait_for_timeout(500)

        popover = page.locator("text=Crowd Density Analytics")
        is_open = popover.is_visible()
        print(f"Popover open after click: {is_open}")

        # Press Escape key
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        is_closed = not popover.is_visible()
        print(f"Popover closed after Escape: {is_closed}")
        context.close()
        browser.close()

        assert is_open and is_closed, "Esc key test failed"
        print("TEST 3.13 ESC KEY PASS!")

if __name__ == '__main__':
    test_esc()
