import sys
import codecs
import time
import requests
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

def test_phase5_ui():
    print("=" * 70)
    print("PLAYWRIGHT E2E: PHASE 5 LIVE FOOTFALL REPORTING & GEOFENCE MODAL UI")
    print("=" * 70)

    # Fetch a place in Pondicherry from backend
    res = requests.get("http://127.0.0.1:8000/api/v1/places?city_id=pondicherry")
    assert res.status_code == 200, "Backend /places endpoint failed"
    places = res.json()
    assert len(places) > 0, "No places found"
    first_place = places[0]
    p_id = first_place["id"]
    p_name = first_place["name"]
    p_lat = first_place["coordinates"]["lat"]
    p_lng = first_place["coordinates"]["lng"]
    print(f"Target destination for UI test: {p_name} ({p_id}) at ({p_lat}, {p_lng})")

    # Clean existing reports for this place to reset rate limits
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=500)
    db = client["voyantra_db"]
    db["crowd_reports"].delete_many({})
    db["feature_snapshots"].delete_many({})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Grant geolocation permission
        context = browser.new_context(
            permissions=["geolocation"],
            viewport={"width": 1280, "height": 900}
        )
        page = context.new_page()
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]:", msg.text))
        page.on("pageerror", lambda err: print(f"PAGEERROR:", err))

        # Step 1: Open app
        print("\n[Step 1] Loading Voyantra app...")
        page.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Handle city selector modal if visible
        proceed_btn = page.locator("button:has-text('Proceed with Pondicherry')")
        if proceed_btn.is_visible():
            proceed_btn.click()
            page.wait_for_timeout(500)

        # Step 2: Ensure we are on Destinations page
        print("[Step 2] Locating crowd badges on destination cards...")
        dest_nav = page.locator("button:has-text('Destinations')").first
        if dest_nav.is_visible():
            dest_nav.click()
            page.wait_for_timeout(500)

        # Locate first crowd badge button
        crowd_badges = page.locator("button:has-text('Crowd'), button:has-text('Serene'), button:has-text('Moderate'), button:has-text('Bustling'), button:has-text('Surge')")
        badge_count = crowd_badges.count()
        print(f"Found {badge_count} crowd badges on screen.")
        assert badge_count > 0, "No crowd badges rendered on destination cards"

        # Click the first badge to open popover
        print("[Step 3] Clicking crowd badge to open Analytics Popover...")
        badge_elem = crowd_badges.first
        badge_elem.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        badge_elem.click()
        page.wait_for_timeout(1000)

        # Verify Popover content
        popover_header = page.locator("text=Crowd Density Intelligence")
        assert popover_header.is_visible(), "Popover failed to open or header missing"
        print("-> Popover successfully opened with header 'Crowd Density Intelligence'")

        provenance = page.locator("text=Seasonality:")
        assert provenance.is_visible(), "Data provenance footer missing in popover"
        print(f"-> Provenance verified: {provenance.text_content()}")

        # Step 4: Click 'Report Live Footfall'
        print("\n[Step 4] Opening Live Footfall Reporting Modal...")
        report_btn = page.locator("button:has-text('Report Live Footfall')")
        print("report_btn count:", report_btn.count())
        assert report_btn.is_visible(), "'Report Live Footfall' button not found"
        report_btn.click(force=True)
        page.wait_for_timeout(1000)

        # Print all visible h3 elements or dialogs
        h3_texts = [page.locator("h3").nth(i).text_content() for i in range(page.locator("h3").count())]
        print("Visible h3s on page:", h3_texts)
        modal_title = page.locator("h3:has-text('Report Live Footfall')")
        assert modal_title.is_visible(), "Modal title not visible"
        print("-> Live Footfall Reporting Modal successfully rendered.")

        # Step 5: Test Geofence Rejection (> 200m away)
        print("\n[Step 5] Simulating user location > 200m away (5km offset)...")
        context.set_geolocation({"latitude": p_lat + 0.05, "longitude": p_lng + 0.05})
        submit_btn = page.locator("button:has-text('Verify Location & Submit')")
        assert submit_btn.is_visible(), "Submit button not visible in modal"
        submit_btn.click()
        page.wait_for_timeout(1500)

        # Check for rejection alert
        error_banner = page.locator("text=Verification Notice:")
        assert error_banner.is_visible(), "Expected Geofence rejection banner"
        error_text = page.locator("text=Verification failed").first.text_content()
        print(f"-> Geofence rejection caught properly: {error_text}")

        # Step 6: Test Geofence Acceptance (on-site <= 200m)
        modal_place_name = page.locator("h3:has-text('Report Live Footfall') + p").text_content().strip()
        matched = next((p for p in places if p["name"].strip() == modal_place_name), None)
        assert matched is not None, f"Could not find matched place in backend for: {modal_place_name}"
        real_id = matched["id"]
        real_lat = matched["coordinates"]["lat"]
        real_lng = matched["coordinates"]["lng"]

        # Clear reports for this place so cooldown doesn't block
        db["crowd_reports"].delete_many({"place_id": real_id})
        db["feature_snapshots"].delete_many({"place_id": real_id})

        print(f"\n[Step 6] Simulating on-site user presence for '{modal_place_name}' at ({real_lat}, {real_lng})...")
        context.set_geolocation({"latitude": real_lat, "longitude": real_lng})
        
        # Select 'Bustling & Busy' crowd option
        bustling_option = page.locator("button:has-text('Bustling & Busy')")
        if bustling_option.is_visible():
            bustling_option.click()
            print("-> Selected 'Bustling & Busy' (75% footfall)")

        submit_btn.click()

        # Check for success notification immediately while modal is still open (auto-closes in 1.8s)
        success_banner = page.wait_for_selector(".bg-emerald-50", timeout=5000)
        assert success_banner is not None, "Expected success confirmation in modal"
        print(f"-> Success banner confirmed: {success_banner.text_content()}")

        # Step 7: Wait for modal to auto-close and check live status in popover
        print("\n[Step 7] Waiting for modal to auto-close and checking updated live crowd confidence badge...")
        page.wait_for_timeout(2500)
        live_badge = page.locator("text=CONFIDENCE")
        if live_badge.is_visible():
            print(f"-> Live confidence indicator: {live_badge.text_content()}")

        browser.close()
        print("\n" + "=" * 70)
        print("PHASE 5 E2E UI TEST PASSED WITH 100% SUCCESS!")
        print("=" * 70)

if __name__ == "__main__":
    test_phase5_ui()
