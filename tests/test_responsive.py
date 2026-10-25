from playwright.sync_api import sync_playwright

def test_responsive():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. Desktop: 1440px
        p_desktop = browser.new_page(viewport={"width": 1440, "height": 900})
        p_desktop.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        proceed_d = p_desktop.locator("button:has-text('Proceed with Pondicherry')")
        if proceed_d.is_visible():
            proceed_d.click()
            p_desktop.wait_for_timeout(500)
            
        # Check desktop navbar links
        desktop_nav = p_desktop.locator("nav.hidden.md\\:flex")
        print("Desktop 1440px: Desktop Nav visible:", desktop_nav.is_visible())
        
        # Check crowd popover on desktop
        badge_d = p_desktop.locator("button[title*='Crowd Analytics']").first
        badge_d.click()
        p_desktop.wait_for_timeout(500)
        popover_d = p_desktop.locator("text=Crowd Density Analytics")
        print("Desktop 1440px: Crowd Popover visible:", popover_d.is_visible())
        
        # 2. Mobile: 375px
        p_mobile = browser.new_page(viewport={"width": 375, "height": 667})
        p_mobile.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        proceed_m = p_mobile.locator("button:has-text('Proceed with Pondicherry')")
        if proceed_m.is_visible():
            proceed_m.click()
            p_mobile.wait_for_timeout(500)
            
        # Check mobile bottom tab bar
        mobile_bar = p_mobile.locator("div.md\\:hidden.flex.border-t")
        print("Mobile 375px: Mobile Tab Bar visible:", mobile_bar.is_visible())
        
        # Check crowd badge and popover on mobile
        badge_m = p_mobile.locator("button[title*='Crowd Analytics']").first
        badge_m.click()
        p_mobile.wait_for_timeout(500)
        popover_m = p_mobile.locator("text=Crowd Density Analytics")
        print("Mobile 375px: Crowd Popover visible:", popover_m.is_visible())
        
        # Check popover width and bounding box on mobile
        box_m = popover_m.bounding_box()
        print("Mobile 375px: Popover bounding box:", box_m)
        fits_screen = box_m['x'] >= 0 and (box_m['x'] + box_m['width']) <= 375
        print(f"Mobile 375px: Popover fits within 375px width?: {fits_screen} (right edge: {box_m['x'] + box_m['width']}px)")
        
        # Go to Planner tab on mobile
        # Click Planner in mobile bar
        planner_tab_btn = p_mobile.locator("div.md\\:hidden button:has-text('Personalized')").or_(p_mobile.locator("div.md\\:hidden button:has-text('Planner')")).first
        planner_tab_btn.click()
        p_mobile.wait_for_timeout(500)
        
        # Check Planner page on mobile
        planner_title = p_mobile.locator("h1:has-text('Personalized AI Trip Planner')")
        print("Mobile 375px: Planner Page visible:", planner_title.is_visible())
        
        # Check Drag & Drop card touch/drag readiness on mobile
        # In mobile touch devices, HTML5 Drag & Drop API (draggable=true) does NOT trigger natively on touch without touch polyfill!
        print("Mobile 375px: Drag-and-drop HTML5 attribute note: Native HTML5 Drag & Drop does not support touch events on mobile without touch polyfills.")

        browser.close()

if __name__ == '__main__':
    test_responsive()
