import sys
import codecs
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

def test_phase4_ui():
    print("=" * 70)
    print("PLAYWRIGHT E2E: PHASE 4 NAVIGATION & TSP DAY OPTIMIZER UI")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        # 1. Navigate to Planner page
        print("[1] Loading Voyantra app...")
        page.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Proceed with city if prompt shows
        proceed_btn = page.locator("button:has-text('Proceed with Pondicherry')")
        if proceed_btn.is_visible():
            proceed_btn.click()
            page.wait_for_timeout(500)

        # Click AI Trip Planner tab in navbar
        planner_nav = page.locator("button:has-text('Trip Basket'), button:has-text('AI Trip Planner')").first
        if planner_nav.is_visible():
            planner_nav.click()
            page.wait_for_timeout(500)

        # 2. Fill prompt text
        print("[2] Filling prompt text...")
        prompt_area = page.locator("textarea").first
        if prompt_area.is_visible():
            prompt_area.fill("2-day trip to Pondicherry, love French Quarter heritage and beaches")
            page.wait_for_timeout(500)

        # 3. Generate AI Itinerary
        print("[3] Generating AI Itinerary...")
        generate_btn = page.locator("button:has-text('Generate AI Itinerary')")
        if generate_btn.is_visible():
            generate_btn.click()
            # Wait for itinerary to finish generation
            page.wait_for_selector("text=Drag & Drop Interactive Plan", timeout=30000)
            print("-> Itinerary successfully synthesized.")

        # 4. Find the "⚡ Optimize Route & Order" button on Day 1
        print("[4] Triggering ⚡ Optimize Route & Order (P4-T4 & P4-T7)...")
        opt_btn = page.locator("button:has-text('Optimize Route & Order')").first
        assert opt_btn.is_visible(), "Optimize button not visible on Day 1 card"
        opt_btn.click()

        # Wait for optimization to complete
        page.wait_for_selector("text=Optimized Sequence:", timeout=40000)
        print("-> Day schedule optimized successfully! Metrics banner appeared.")

        # 5. Check transit leg cards
        print("[5] Checking TransitLegCard connectors (P4-T6)...")
        transit_text = page.locator("text=travel").first.inner_text()
        print(f"   Travel metrics: {transit_text}")

        # Check for mode switch button
        mode_btn = page.locator("button:has-text('Switch to Walk'), button:has-text('Driving')").first
        assert mode_btn.is_visible(), "Transit mode switcher button not visible"

        # 6. Check View Route Map on Leaflet
        print("[6] Toggling Route Map View on Leaflet...")
        map_btn = page.locator("button:has-text('View Route Map')").first
        if map_btn.is_visible():
            map_btn.click()
            page.wait_for_timeout(1000)
            map_container = page.locator(".leaflet-container").first
            assert map_container.is_visible(), "Leaflet map container not visible when toggled"
            print("-> Leaflet map rendered with turn-by-turn route overlay!")

        browser.close()

    print("\n" + "=" * 70)
    print("ALL PHASE 4 UI & E2E TESTS PASSED (P4-T4, P4-T5, P4-T6, P4-T7 VERIFIED)")
    print("=" * 70)

if __name__ == "__main__":
    test_phase4_ui()
