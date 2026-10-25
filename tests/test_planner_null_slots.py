import sys
import codecs
import json
import socket
import urllib.request
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")

def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except Exception:
        return False

def test_planner_null_slots():
    print("=" * 70)
    print("PLAYWRIGHT E2E: PLANNER NULL-SLOT OPTIMIZATION & ROBUSTNESS TEST")
    print("=" * 70)

    backend_live = is_port_open("127.0.0.1", 8000)
    frontend_live = is_port_open("127.0.0.1", 5173)

    if not backend_live or not frontend_live:
        print(f"[STATUS] Backend on 127.0.0.1:8000: {'RUNNING' if backend_live else 'NOT RUNNING'}")
        print(f"[STATUS] Frontend on 127.0.0.1:5173: {'RUNNING' if frontend_live else 'NOT RUNNING'}")
        print("ERROR: Required servers are not running. TEST NOT RUN.")
        sys.exit(2)

    page_errors = []
    console_errors = []

    mock_itinerary_response = {
        "itinerary_title": "Custom Plan: Null Slot Robustness Test",
        "feasibility_status": "100% Feasible",
        "has_unavailability_warning": False,
        "unavailability_notice": None,
        "summary": "Custom 1-day plan with morning slot intentionally set to null.",
        "days": [
            {
                "day_number": 1,
                "theme": "Coastal Heritage Day (Null Morning Slot)",
                "morning": None,
                "afternoon": {
                    "place_name": "Auroville & Matrimandir",
                    "activity_note": "Afternoon meditation and township visit.",
                    "est_time": "12:30 PM - 3:30 PM"
                },
                "evening": {
                    "place_name": "Promenade Beach (Rock Beach)",
                    "activity_note": "Sunset walk along the seafront.",
                    "est_time": "5:00 PM - 8:00 PM"
                }
            }
        ],
        "total_estimated_budget_inr": 0,
        "belief_and_etiquette_advisory": "Observe local decorum.",
        "travel_tips": ["Carry water and comfortable walking shoes."],
        "source": "fallback",
        "fallback_reason": "no_api_key"
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            permissions=["geolocation"],
            viewport={"width": 1280, "height": 900}
        )
        page = context.new_page()

        page.on("pageerror", lambda err: page_errors.append(str(err)))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # Intercept itinerary generation API call to return mocked null-slot response
        def handle_generate(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "city_id": "pondicherry",
                    "query_text": "Test null slots in Day 1",
                    "retrieved_places_count": 2,
                    "available_alternatives": [],
                    "itinerary": mock_itinerary_response
                })
            )

        page.route("**/recommendations/generate-itinerary", handle_generate)

        # Step 1: Open app
        print("\n[Step 1] Loading Voyantra app...")
        page.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        # Handle city selector modal if visible
        proceed_btn = page.locator("button:has-text('Proceed with Pondicherry')")
        if proceed_btn.is_visible():
            proceed_btn.click()
            page.wait_for_timeout(500)

        # Step 2: Navigate to AI Trip Planner tab
        print("[Step 2] Navigating to AI Trip Planner tab...")
        planner_nav = page.locator("button:has-text('AI Trip Planner'), button:has-text('Trip Basket')").first
        if planner_nav.is_visible():
            planner_nav.click()
            page.wait_for_timeout(600)

        # Step 3: Trigger Generate Itinerary
        print("[Step 3] Generating mocked itinerary with null morning slot...")
        prompt_area = page.locator("textarea").first
        if prompt_area.is_visible():
            prompt_area.fill("Test null slots in Day 1")
            page.wait_for_timeout(300)

        gen_btn = page.locator("button:has-text('Generate AI Itinerary')")
        if gen_btn.is_visible():
            gen_btn.click()
            page.wait_for_selector("text=Drag & Drop Interactive Plan", timeout=15000)
            print("-> Mocked itinerary rendered with null morning slot.")

        # Step 4: Click Optimize Route & Order on Day 1
        print("[Step 4] Clicking '⚡ Optimize Route & Order' on Day 1...")
        opt_btn = page.locator("button:has-text('Optimize Route & Order')").first
        assert opt_btn.is_visible(), "Optimize button not visible on Day 1"
        opt_btn.click()

        # Wait for optimization response to complete
        page.wait_for_selector("text=Optimized Sequence:", timeout=30000)
        print("-> Optimization completed without crashing.")

        # Step 5: Assert no page errors
        print("\n[Step 5] Verifying console and page errors...")
        print(f"Page errors caught: {len(page_errors)}")
        if page_errors:
            for pe in page_errors:
                print(f"  ERROR: {pe}")

        assert len(page_errors) == 0, f"Page errors occurred during null-slot optimization: {page_errors}"
        print("-> PASS: No unhandled page errors or TypeErrors during null-slot optimization.")

        browser.close()

    print("\n" + "=" * 70)
    print("ALL PLANNER NULL-SLOT TESTS PASSED (1/1)")
    print("=" * 70)

if __name__ == "__main__":
    test_planner_null_slots()
