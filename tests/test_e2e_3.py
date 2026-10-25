import requests
import json
import codecs
import sys

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def test_e2e_3():
    print("Testing E2E-3: Admin workflow and user visibility...")
    # 1. Admin login
    r_adm = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@voyantra.com", "password": "admin123"})
    admin_tok = r_adm.json().get("access_token")
    assert admin_tok, "Admin login failed"

    # 2. Admin edits a festival
    f_list = requests.get(f"{BASE_URL}/festivals?city=Pondicherry").json()
    fest_id = f_list[0]["id"]
    updated_name = f_list[0]["name"] + " (Special Edition)"
    r_put = requests.put(
        f"{BASE_URL}/festivals/{fest_id}",
        json={"name": updated_name},
        headers={"Authorization": f"Bearer {admin_tok}"}
    )
    print("Festival update status:", r_put.status_code, "Updated name:", r_put.json().get("name"))
    assert r_put.status_code == 200

    # 3. User verifies updated festival
    f_user_list = requests.get(f"{BASE_URL}/festivals?city=Pondicherry").json()
    match = next((f for f in f_user_list if f["id"] == fest_id), None)
    print("User sees updated festival:", match["name"])
    assert match["name"] == updated_name, "User did not see updated festival"

    # Restore festival name
    original_name = f_list[0]["name"]
    requests.put(
        f"{BASE_URL}/festivals/{fest_id}",
        json={"name": original_name},
        headers={"Authorization": f"Bearer {admin_tok}"}
    )
    print("E2E-3 PASS!")

if __name__ == '__main__':
    test_e2e_3()
