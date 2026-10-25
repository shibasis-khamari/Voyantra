import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from playwright.sync_api import sync_playwright

def test_gps_cases():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 4.7: Geolocation denied
        context7 = browser.new_context(
            permissions=[]
        )
        page7 = context7.new_page()
        page7.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page7.wait_for_timeout(1000)
        modal_vis7 = page7.locator("text=Choose Your Destination").is_visible() or page7.locator("text=Location Permission Needed").is_visible()
        print(f"4.7 Permission denied: modal_visible={modal_vis7}")
        
        # 4.8: Modal manual selection
        chennai_opt = page7.locator("button:has-text('Chennai')").first
        if chennai_opt.is_visible():
            chennai_opt.click()
            page7.wait_for_timeout(300)
            proceed_btn = page7.locator("button:has-text('Proceed with Chennai')")
            if proceed_btn.is_visible():
                proceed_btn.click()
                page7.wait_for_timeout(800)
        
        city_sel8 = page7.locator("select").first.input_value()
        has_marina = page7.locator("h3:has-text('Marina Beach')").is_visible()
        print(f"4.8 Manual selection of Chennai: selectedCity={city_sel8}, Marina Beach visible={has_marina}")

        # 4.9: GPS button in Navbar re-triggers detection
        gps_btn = page7.locator("button[title*='GPS']")
        gps_btn.click()
        page7.wait_for_timeout(800)
        modal_vis9 = page7.locator("text=Location Permission Needed").is_visible() or page7.locator("text=Choose Your Destination").is_visible()
        print(f"4.9 GPS button re-trigger: modal_visible={modal_vis9}")

        # 4.10: Stale data check
        page7.locator("select").first.select_option("pondicherry")
        page7.wait_for_timeout(800)
        chennai_cards_in_pondy = page7.locator("h3:has-text('Marina Beach')").count()
        pondy_cards_in_pondy = page7.locator("h3:has-text('Promenade Beach')").count()
        
        page7.locator("select").first.select_option("chennai")
        page7.wait_for_timeout(800)
        chennai_cards_in_chennai = page7.locator("h3:has-text('Marina Beach')").count()
        pondy_cards_in_chennai = page7.locator("h3:has-text('Promenade Beach')").count()
        print(f"4.10 Stale data check:")
        print(f"  In Pondicherry view: Promenade={pondy_cards_in_pondy}, Marina={chennai_cards_in_pondy}")
        print(f"  In Chennai view: Marina={chennai_cards_in_chennai}, Promenade={pondy_cards_in_chennai}")

        context7.close()
        browser.close()

if __name__ == '__main__':
    test_gps_cases()
