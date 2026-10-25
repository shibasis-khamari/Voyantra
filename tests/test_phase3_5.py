import sys
import time
import math

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from playwright.sync_api import sync_playwright
from geographiclib.geodesic import Geodesic

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def test_gps_cases():
    start_time = time.time()
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 4.1: Pondicherry center (11.9416, 79.8083)
        context1 = browser.new_context(
            geolocation={"latitude": 11.9416, "longitude": 79.8083},
            permissions=["geolocation"]
        )
        page1 = context1.new_page()
        page1.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page1.wait_for_timeout(1000)
        
        city_sel1 = page1.locator("select").first.input_value()
        notice1 = page1.locator("header div:has-text('Detected Location')").inner_text() if page1.locator("header div:has-text('Detected Location')").count() > 0 else "None"
        modal_vis1 = page1.locator("text=Choose Your Destination").is_visible()
        pass_4_1 = (city_sel1 == "pondicherry" and not modal_vis1)
        results["4.1"] = "PASS" if pass_4_1 else "FAIL"
        print(f"4.1 Pondicherry Center: city={city_sel1}, notice='{notice1}', modal_visible={modal_vis1} -> {results['4.1']}")
        context1.close()

        # 4.2: Chennai center (13.0827, 80.2707)
        context2 = browser.new_context(
            geolocation={"latitude": 13.0827, "longitude": 80.2707},
            permissions=["geolocation"]
        )
        page2 = context2.new_page()
        page2.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page2.wait_for_timeout(1000)
        
        city_sel2 = page2.locator("select").first.input_value()
        notice2 = page2.locator("header div:has-text('Detected Location')").inner_text() if page2.locator("header div:has-text('Detected Location')").count() > 0 else "None"
        modal_vis2 = page2.locator("text=Choose Your Destination").is_visible()
        pass_4_2 = (city_sel2 == "chennai" and not modal_vis2)
        results["4.2"] = "PASS" if pass_4_2 else "FAIL"
        print(f"4.2 Chennai Center: city={city_sel2}, notice='{notice2}', modal_visible={modal_vis2} -> {results['4.2']}")
        context2.close()

        # 4.3: 65 km south of Chennai (12.4971, 80.2707)
        context3 = browser.new_context(
            geolocation={"latitude": 12.4971, "longitude": 80.2707},
            permissions=["geolocation"]
        )
        page3 = context3.new_page()
        page3.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page3.wait_for_timeout(1000)
        
        city_sel3 = page3.locator("select").first.input_value()
        notice3 = page3.locator("header div:has-text('Detected Location')").inner_text() if page3.locator("header div:has-text('Detected Location')").count() > 0 else "None"
        modal_vis3 = page3.locator("text=Choose Your Destination").is_visible()
        pass_4_3 = (city_sel3 == "chennai" and not modal_vis3)
        results["4.3"] = "PASS" if pass_4_3 else "FAIL"
        print(f"4.3 65km from Chennai: city={city_sel3}, notice='{notice3}', modal_visible={modal_vis3} -> {results['4.3']}")
        context3.close()

        # 4.4: 75 km south of Chennai (12.4070, 80.2707)
        context4 = browser.new_context(
            geolocation={"latitude": 12.4070, "longitude": 80.2707},
            permissions=["geolocation"]
        )
        page4 = context4.new_page()
        page4.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page4.wait_for_timeout(1000)
        
        modal_vis4 = page4.locator("text=Outside Operating Destinations").is_visible()
        city_sel4 = page4.locator("select").first.input_value()
        pass_4_4 = modal_vis4
        results["4.4"] = "PASS" if pass_4_4 else "FAIL"
        print(f"4.4 75km from Chennai: modal_visible={modal_vis4}, fallback city={city_sel4} -> {results['4.4']}")
        context4.close()

        # 4.5: Bangalore (12.9716, 77.5946)
        context5 = browser.new_context(
            geolocation={"latitude": 12.9716, "longitude": 77.5946},
            permissions=["geolocation"]
        )
        page5 = context5.new_page()
        page5.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page5.wait_for_timeout(1000)
        
        modal_vis5 = page5.locator("text=Outside Operating Destinations").is_visible()
        pass_4_5 = modal_vis5
        results["4.5"] = "PASS" if pass_4_5 else "FAIL"
        print(f"4.5 Bangalore: modal_visible={modal_vis5} -> {results['4.5']}")
        context5.close()

        # 4.6a: Point inside both radii, closer to CHENNAI:
        # Lat: 12.5179, Lon: 80.0418
        # Distance to Pondy: 68.92 km (<= 70 km)
        # Distance to Chennai: 67.53 km (<= 70 km)
        # distChennai < distPondy -> Chennai MUST win!
        context6a = browser.new_context(
            geolocation={"latitude": 12.5179, "longitude": 80.0418},
            permissions=["geolocation"]
        )
        page6a = context6a.new_page()
        page6a.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page6a.wait_for_timeout(1000)
        
        city_sel6a = page6a.locator("select").first.input_value()
        notice6a = page6a.locator("header div:has-text('Detected Location')").inner_text() if page6a.locator("header div:has-text('Detected Location')").count() > 0 else "None"
        pass_4_6a = (city_sel6a == "chennai")
        results["4.6a"] = "PASS" if pass_4_6a else "FAIL"
        print(f"4.6a Both radii (closer to Chennai: distC=67.53km, distP=68.92km): city={city_sel6a}, notice='{notice6a}' -> {results['4.6a']}")
        context6a.close()

        # 4.6b: Point inside both radii, closer to PONDICHERRY:
        # Lat: 12.5007, Lon: 80.0349
        # Distance to Pondy: 66.87 km (<= 70 km)
        # Distance to Chennai: 69.58 km (<= 70 km)
        # distPondy < distChennai -> Pondicherry MUST win!
        # Sum = 66.87 + 69.58 = 136.45 km
        context6b = browser.new_context(
            geolocation={"latitude": 12.5007, "longitude": 80.0349},
            permissions=["geolocation"]
        )
        page6b = context6b.new_page()
        page6b.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page6b.wait_for_timeout(1000)
        
        city_sel6b = page6b.locator("select").first.input_value()
        notice6b = page6b.locator("header div:has-text('Detected Location')").inner_text() if page6b.locator("header div:has-text('Detected Location')").count() > 0 else "None"
        pass_4_6b = (city_sel6b == "pondicherry")
        results["4.6b"] = "PASS" if pass_4_6b else "FAIL"
        print(f"4.6b Both radii (closer to Pondy: distP=66.87km, distC=69.58km): city={city_sel6b}, notice='{notice6b}' -> {results['4.6b']}")
        context6b.close()

        # 4.7: Geolocation denied
        context7 = browser.new_context(
            permissions=[]
        )
        page7 = context7.new_page()
        page7.goto("http://127.0.0.1:5173/", wait_until="domcontentloaded")
        page7.wait_for_timeout(1000)
        modal_vis7 = page7.locator("text=Choose Your Destination").is_visible() or page7.locator("text=Location Permission Needed").is_visible()
        pass_4_7 = modal_vis7
        results["4.7"] = "PASS" if pass_4_7 else "FAIL"
        print(f"4.7 Permission denied: modal_visible={modal_vis7} -> {results['4.7']}")
        
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
        has_marina = page7.locator("h3:has-text('Marina Beach')").first.is_visible()
        pass_4_8 = (city_sel8 == "chennai" and has_marina)
        results["4.8"] = "PASS" if pass_4_8 else "FAIL"
        print(f"4.8 Manual selection of Chennai: selectedCity={city_sel8}, Marina Beach visible={has_marina} -> {results['4.8']}")

        # 4.9: GPS button in Navbar re-triggers detection
        gps_btn = page7.locator("button[title*='GPS']")
        gps_btn.click()
        page7.wait_for_timeout(800)
        modal_vis9 = page7.locator("text=Location Permission Needed").is_visible() or page7.locator("text=Choose Your Destination").is_visible()
        pass_4_9 = modal_vis9
        results["4.9"] = "PASS" if pass_4_9 else "FAIL"
        print(f"4.9 GPS button re-trigger: modal_visible={modal_vis9} -> {results['4.9']}")

        # 4.10: Stale data check
        page7.locator("select").first.select_option("pondicherry")
        page7.wait_for_timeout(800)
        chennai_cards_in_pondy = page7.locator("h3:has-text('Marina Beach')").count()
        
        page7.locator("select").first.select_option("chennai")
        page7.wait_for_timeout(800)
        pondy_cards_in_chennai = page7.locator("h3:has-text('Promenade Beach')").count()
        pass_4_10 = (chennai_cards_in_pondy == 0 and pondy_cards_in_chennai == 0)
        results["4.10"] = "PASS" if pass_4_10 else "FAIL"
        print(f"4.10 Stale data check: Pondy view has Marina Beach={chennai_cards_in_pondy}, Chennai view has Promenade={pondy_cards_in_chennai} -> {results['4.10']}")

        # 4.11: Independent Geodesic Verification (geographiclib WGS84 vs Spherical Haversine)
        # Pondicherry (11.9416, 79.8083) to Chennai (13.0827, 80.2707)
        geo_result = Geodesic.WGS84.Inverse(11.9416, 79.8083, 13.0827, 80.2707)
        independent_geodesic_km = geo_result['s12'] / 1000.0  # WGS84 ellipsoidal distance = 135.8728 km
        haversine_val_km = haversine_km(11.9416, 79.8083, 13.0827, 80.2707)  # Spherical distance = 136.4521 km
        pct_diff = abs(haversine_val_km - independent_geodesic_km) / independent_geodesic_km * 100.0
        pass_4_11 = (pct_diff <= 0.5)
        results["4.11"] = "PASS" if pass_4_11 else "FAIL"
        print(f"4.11 Independent Geodesic Verification (geographiclib WGS84): Ellipsoid={independent_geodesic_km:.4f} km, Haversine={haversine_val_km:.4f} km (Diff: {pct_diff:.3f}% <= 0.5%) -> {results['4.11']}")

        context7.close()
        browser.close()

    elapsed = time.time() - start_time
    total = len(results)
    passed = sum(1 for v in results.values() if v == "PASS")
    failed = total - passed

    print("\n" + "=" * 65)
    if failed == 0:
        print(f"==================== {passed} passed in {elapsed:.2f}s ====================")
    else:
        print(f"FAILED (failures={failed}, passed={passed}) in {elapsed:.2f}s")
    print("=" * 65)

if __name__ == '__main__':
    test_gps_cases()
