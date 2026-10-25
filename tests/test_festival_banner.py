from playwright.sync_api import sync_playwright

def test_banner():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            geolocation={"latitude": 11.9416, "longitude": 79.8083},
            permissions=["geolocation"]
        )
        page = context.new_page()
        page.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        # Check if banner is present for active festivals
        banner = page.locator("text=Phase 3: Festival Advisory")
        print("Banner visible currently:", banner.is_visible())
        context.close()
        browser.close()

if __name__ == '__main__':
    test_banner()
