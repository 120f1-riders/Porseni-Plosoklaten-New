#!/usr/bin/env python3
"""
Backend test for NEW delta: Peserta verify super_admin-only; POST /users bulk create; 
lomba idcard_image_url; juara gender; backup/restore; 5 required files
"""
import requests
import json
import sys

BASE_URL = "https://porseni-superadmin.preview.emergentagent.com/api"

def test_scenario_1_post_users_bulk_create():
    """
    Scenario 1: POST /api/users (super_admin only, bulk-create)
    - As super_admin, POST /users {name, email:"panitia.futsal", role:"panitia"} (no password) -> expect 200, status:"verified", password_plain:"12345678", NO password hash / token / _id in response.
    - Then POST /api/auth/login {email:"panitia.futsal", password:"12345678"} -> expect 200 with token (this proves auto-verified + default password).
    - POST /users again with SAME email -> expect 400 (duplicate).
    - POST /users as a non-super user (create an admin_madrasah first via POST /users, login as it) -> expect 403.
    """
    print("\n=== SCENARIO 1: POST /users (super_admin only, bulk-create) ===")
    
    # Login as super_admin
    print("\n[1.1] Login as super_admin...")
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": "super@porseni.id", "password": "admin123"})
    assert r.status_code == 200, f"Super admin login failed: {r.status_code} {r.text}"
    super_token = r.json()["token"]
    # Check no password/token leak in login response
    user_obj = r.json().get("user", {})
    assert "password" not in user_obj, "Login response leaked password field"
    assert "password_plain" not in user_obj, "Login response leaked password_plain field"
    assert "token" not in user_obj, "Login response leaked token field"
    assert "_id" not in user_obj, "Login response leaked _id field"
    print("✅ Super admin login OK, no password/token/_id leak in user object")
    
    # Create panitia user via POST /users (no password provided)
    print("\n[1.2] POST /users as super_admin (panitia.futsal, no password)...")
    r = requests.post(f"{BASE_URL}/users", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"name": "Panitia Futsal", "email": "panitia.futsal@porseni.id", "role": "panitia"})
    assert r.status_code == 200, f"POST /users failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["status"] == "verified", f"Expected status=verified, got {data.get('status')}"
    assert data["password_plain"] == "12345678", f"Expected password_plain=12345678, got {data.get('password_plain')}"
    assert "password" not in data, "Response leaked password hash"
    assert "token" not in data, "Response leaked token"
    assert "_id" not in data, "Response leaked _id"
    print(f"✅ POST /users OK: status=verified, password_plain=12345678, no hash/token/_id leak")
    
    # Login with default password
    print("\n[1.3] Login as panitia.futsal with default password 12345678...")
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": "panitia.futsal@porseni.id", "password": "12345678"})
    assert r.status_code == 200, f"Login with default password failed: {r.status_code} {r.text}"
    panitia_token = r.json()["token"]
    print("✅ Login with default password OK (proves auto-verified + default password)")
    
    # Duplicate email -> 400
    print("\n[1.4] POST /users with SAME email (duplicate)...")
    r = requests.post(f"{BASE_URL}/users", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"name": "Duplicate", "email": "panitia.futsal@porseni.id", "role": "panitia"})
    assert r.status_code == 400, f"Expected 400 for duplicate, got {r.status_code}"
    print("✅ Duplicate email rejected with 400")
    
    # Create admin_madrasah, login, try POST /users -> 403
    print("\n[1.5] Create admin_madrasah via POST /users, login, try POST /users -> expect 403...")
    r = requests.post(f"{BASE_URL}/users", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"name": "Admin MI Test", "email": "admin.mi.test@porseni.id", "role": "admin_madrasah", "madrasah_name": "MI Test"})
    assert r.status_code == 200, f"Create admin_madrasah failed: {r.status_code} {r.text}"
    print("✅ admin_madrasah created")
    
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin.mi.test@porseni.id", "password": "12345678"})
    assert r.status_code == 200, f"admin_madrasah login failed: {r.status_code} {r.text}"
    admin_token = r.json()["token"]
    print("✅ admin_madrasah login OK")
    
    r = requests.post(f"{BASE_URL}/users", 
                      headers={"Authorization": f"Bearer {admin_token}"},
                      json={"name": "Another User", "email": "another@porseni.id", "role": "panitia"})
    assert r.status_code == 403, f"Expected 403 for non-super POST /users, got {r.status_code}"
    print("✅ Non-super user POST /users rejected with 403")
    
    print("\n✅ SCENARIO 1 PASSED: POST /users super_admin-only, auto-verified, default password, duplicate rejection, non-super 403")
    return super_token, admin_token


def test_scenario_2_peserta_verify_super_admin_only(super_token, admin_token):
    """
    Scenario 2: PUT /api/peserta/:id/status is SUPER_ADMIN ONLY
    - Create an admin_madrasah user via POST /users {name, email:"mi.test", role:"admin_madrasah", madrasah_name:"MI Test"}; login to get token.
    - As that admin_madrasah, create a lomba? No—only super creates lomba. As super_admin create a lomba (individu). As admin_madrasah POST /peserta {participant_name, gender:"L", lomba_id}. 
    - As admin_madrasah, PUT /peserta/:id/status {status:"verified"} -> expect 403.
    - As super_admin, PUT /peserta/:id/status {status:"verified"} -> expect 200 and status verified.
    """
    print("\n=== SCENARIO 2: PUT /peserta/:id/status is SUPER_ADMIN ONLY ===")
    
    # Create lomba as super_admin
    print("\n[2.1] Create lomba (individu) as super_admin...")
    r = requests.post(f"{BASE_URL}/lomba", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"name": "Test Lomba Individu", "type": "individu"})
    assert r.status_code == 200, f"Create lomba failed: {r.status_code} {r.text}"
    lomba_id = r.json()["id"]
    print(f"✅ Lomba created: {lomba_id}")
    
    # Create peserta as admin_madrasah
    print("\n[2.2] Create peserta as admin_madrasah...")
    r = requests.post(f"{BASE_URL}/peserta", 
                      headers={"Authorization": f"Bearer {admin_token}"},
                      json={"participant_name": "Ahmad Test", "gender": "L", "lomba_id": lomba_id})
    assert r.status_code == 200, f"Create peserta failed: {r.status_code} {r.text}"
    peserta_id = r.json()["id"]
    print(f"✅ Peserta created: {peserta_id}")
    
    # Try PUT /peserta/:id/status as admin_madrasah -> 403
    print("\n[2.3] PUT /peserta/:id/status as admin_madrasah -> expect 403...")
    r = requests.put(f"{BASE_URL}/peserta/{peserta_id}/status", 
                     headers={"Authorization": f"Bearer {admin_token}"},
                     json={"status": "verified"})
    assert r.status_code == 403, f"Expected 403 for admin_madrasah verify, got {r.status_code}"
    print("✅ admin_madrasah PUT /peserta/:id/status rejected with 403")
    
    # PUT /peserta/:id/status as super_admin -> 200
    print("\n[2.4] PUT /peserta/:id/status as super_admin -> expect 200...")
    r = requests.put(f"{BASE_URL}/peserta/{peserta_id}/status", 
                     headers={"Authorization": f"Bearer {super_token}"},
                     json={"status": "verified"})
    assert r.status_code == 200, f"Super admin verify failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["status"] == "verified", f"Expected status=verified, got {data.get('status')}"
    print("✅ super_admin PUT /peserta/:id/status OK, status=verified")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/peserta/{peserta_id}", headers={"Authorization": f"Bearer {super_token}"})
    requests.delete(f"{BASE_URL}/lomba/{lomba_id}", headers={"Authorization": f"Bearer {super_token}"})
    
    print("\n✅ SCENARIO 2 PASSED: PUT /peserta/:id/status is super_admin-only")


def test_scenario_3_lomba_idcard_image_url(super_token):
    """
    Scenario 3: Lomba idcard_image_url
    - As super_admin POST /lomba {name:"IDCARDTEST", type:"individu", idcard_image_url:"/api/files/xyz"} -> expect 200 with idcard_image_url="/api/files/xyz".
    - PUT /lomba/:id {idcard_image_url:"/api/files/abc"} -> expect 200 idcard_image_url updated.
    - GET /lomba includes idcard_image_url. Clean up (DELETE).
    """
    print("\n=== SCENARIO 3: Lomba idcard_image_url ===")
    
    # POST lomba with idcard_image_url
    print("\n[3.1] POST /lomba with idcard_image_url...")
    r = requests.post(f"{BASE_URL}/lomba", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"name": "IDCARDTEST", "type": "individu", "idcard_image_url": "/api/files/xyz"})
    assert r.status_code == 200, f"POST /lomba failed: {r.status_code} {r.text}"
    data = r.json()
    lomba_id = data["id"]
    assert data["idcard_image_url"] == "/api/files/xyz", f"Expected idcard_image_url=/api/files/xyz, got {data.get('idcard_image_url')}"
    print(f"✅ POST /lomba OK: idcard_image_url=/api/files/xyz")
    
    # PUT lomba idcard_image_url
    print("\n[3.2] PUT /lomba/:id {idcard_image_url:'/api/files/abc'}...")
    r = requests.put(f"{BASE_URL}/lomba/{lomba_id}", 
                     headers={"Authorization": f"Bearer {super_token}"},
                     json={"idcard_image_url": "/api/files/abc"})
    assert r.status_code == 200, f"PUT /lomba failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["idcard_image_url"] == "/api/files/abc", f"Expected idcard_image_url=/api/files/abc, got {data.get('idcard_image_url')}"
    print(f"✅ PUT /lomba OK: idcard_image_url updated to /api/files/abc")
    
    # GET /lomba includes idcard_image_url
    print("\n[3.3] GET /lomba includes idcard_image_url...")
    r = requests.get(f"{BASE_URL}/lomba")
    assert r.status_code == 200, f"GET /lomba failed: {r.status_code} {r.text}"
    lomba_list = r.json()
    found = next((l for l in lomba_list if l["id"] == lomba_id), None)
    assert found is not None, "Lomba not found in GET /lomba"
    assert found["idcard_image_url"] == "/api/files/abc", f"Expected idcard_image_url=/api/files/abc in GET, got {found.get('idcard_image_url')}"
    print(f"✅ GET /lomba OK: idcard_image_url=/api/files/abc")
    
    # Cleanup
    print("\n[3.4] DELETE /lomba/:id...")
    r = requests.delete(f"{BASE_URL}/lomba/{lomba_id}", headers={"Authorization": f"Bearer {super_token}"})
    assert r.status_code == 200, f"DELETE /lomba failed: {r.status_code} {r.text}"
    print("✅ Cleanup OK")
    
    print("\n✅ SCENARIO 3 PASSED: Lomba idcard_image_url persists and updates correctly")


def test_scenario_4_juara_gender(super_token, admin_token):
    """
    Scenario 4: Juara gender (upsert by lomba_id+rank+gender)
    - Use an individu lomba; create 2 peserta (one gender L, one gender P). As super_admin verify both is not required for juara POST but do create peserta.
    - POST /juara {lomba_id, rank:"Juara 1", gender:"L", peserta_id:<L peserta>} -> 200.
    - POST /juara {lomba_id, rank:"Juara 1", gender:"P", peserta_id:<P peserta>} -> 200.
    - GET /juara?lomba_id=<id> -> expect 2 docs, one gender L one gender P, both rank "Juara 1".
    - POST /juara again {lomba_id, rank:"Juara 1", gender:"L", peserta_id:<other>} -> GET still returns exactly 2 (upsert replaced the L one, not the P one).
    """
    print("\n=== SCENARIO 4: Juara gender (upsert by lomba_id+rank+gender) ===")
    
    # Create lomba
    print("\n[4.1] Create lomba (individu)...")
    r = requests.post(f"{BASE_URL}/lomba", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"name": "Test Lomba Gender", "type": "individu"})
    assert r.status_code == 200, f"Create lomba failed: {r.status_code} {r.text}"
    lomba_id = r.json()["id"]
    print(f"✅ Lomba created: {lomba_id}")
    
    # Create 2 peserta (L and P)
    print("\n[4.2] Create peserta L...")
    r = requests.post(f"{BASE_URL}/peserta", 
                      headers={"Authorization": f"Bearer {admin_token}"},
                      json={"participant_name": "Ahmad L", "gender": "L", "lomba_id": lomba_id})
    assert r.status_code == 200, f"Create peserta L failed: {r.status_code} {r.text}"
    peserta_L_id = r.json()["id"]
    print(f"✅ Peserta L created: {peserta_L_id}")
    
    print("\n[4.3] Create peserta P...")
    r = requests.post(f"{BASE_URL}/peserta", 
                      headers={"Authorization": f"Bearer {admin_token}"},
                      json={"participant_name": "Siti P", "gender": "P", "lomba_id": lomba_id})
    assert r.status_code == 200, f"Create peserta P failed: {r.status_code} {r.text}"
    peserta_P_id = r.json()["id"]
    print(f"✅ Peserta P created: {peserta_P_id}")
    
    # POST juara L
    print("\n[4.4] POST /juara {rank:'Juara 1', gender:'L', peserta_id:<L>}...")
    r = requests.post(f"{BASE_URL}/juara", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"lomba_id": lomba_id, "rank": "Juara 1", "gender": "L", "peserta_id": peserta_L_id})
    assert r.status_code == 200, f"POST /juara L failed: {r.status_code} {r.text}"
    juara_L_id = r.json()["id"]
    print(f"✅ Juara L created: {juara_L_id}")
    
    # POST juara P
    print("\n[4.5] POST /juara {rank:'Juara 1', gender:'P', peserta_id:<P>}...")
    r = requests.post(f"{BASE_URL}/juara", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"lomba_id": lomba_id, "rank": "Juara 1", "gender": "P", "peserta_id": peserta_P_id})
    assert r.status_code == 200, f"POST /juara P failed: {r.status_code} {r.text}"
    juara_P_id = r.json()["id"]
    print(f"✅ Juara P created: {juara_P_id}")
    
    # GET /juara?lomba_id -> expect 2 docs
    print("\n[4.6] GET /juara?lomba_id=<id> -> expect 2 docs (L and P)...")
    r = requests.get(f"{BASE_URL}/juara?lomba_id={lomba_id}", headers={"Authorization": f"Bearer {super_token}"})
    assert r.status_code == 200, f"GET /juara failed: {r.status_code} {r.text}"
    juara_list = r.json()
    assert len(juara_list) == 2, f"Expected 2 juara, got {len(juara_list)}"
    genders = {j["gender"] for j in juara_list}
    assert genders == {"L", "P"}, f"Expected genders L and P, got {genders}"
    ranks = {j["rank"] for j in juara_list}
    assert ranks == {"Juara 1"}, f"Expected all rank='Juara 1', got {ranks}"
    print(f"✅ GET /juara OK: 2 docs, genders L and P, both rank='Juara 1'")
    
    # Create another peserta L
    print("\n[4.7] Create another peserta L...")
    r = requests.post(f"{BASE_URL}/peserta", 
                      headers={"Authorization": f"Bearer {admin_token}"},
                      json={"participant_name": "Budi L", "gender": "L", "lomba_id": lomba_id})
    assert r.status_code == 200, f"Create peserta L2 failed: {r.status_code} {r.text}"
    peserta_L2_id = r.json()["id"]
    print(f"✅ Peserta L2 created: {peserta_L2_id}")
    
    # POST juara L again (upsert)
    print("\n[4.8] POST /juara again {rank:'Juara 1', gender:'L', peserta_id:<L2>} (upsert)...")
    r = requests.post(f"{BASE_URL}/juara", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"lomba_id": lomba_id, "rank": "Juara 1", "gender": "L", "peserta_id": peserta_L2_id})
    assert r.status_code == 200, f"POST /juara L2 failed: {r.status_code} {r.text}"
    print(f"✅ Juara L upserted")
    
    # GET /juara?lomba_id -> still expect 2 docs (L replaced, P unchanged)
    print("\n[4.9] GET /juara?lomba_id=<id> -> still expect 2 docs (L replaced, P unchanged)...")
    r = requests.get(f"{BASE_URL}/juara?lomba_id={lomba_id}", headers={"Authorization": f"Bearer {super_token}"})
    assert r.status_code == 200, f"GET /juara failed: {r.status_code} {r.text}"
    juara_list = r.json()
    assert len(juara_list) == 2, f"Expected 2 juara after upsert, got {len(juara_list)}"
    genders = {j["gender"] for j in juara_list}
    assert genders == {"L", "P"}, f"Expected genders L and P after upsert, got {genders}"
    # Check L peserta_id is now peserta_L2_id
    juara_L = next((j for j in juara_list if j["gender"] == "L"), None)
    assert juara_L is not None, "Juara L not found after upsert"
    assert juara_L["peserta_id"] == peserta_L2_id, f"Expected peserta_id={peserta_L2_id}, got {juara_L['peserta_id']}"
    print(f"✅ GET /juara OK: still 2 docs, L replaced (peserta_id={peserta_L2_id}), P unchanged")
    
    # Cleanup
    for jid in [j["id"] for j in juara_list]:
        requests.delete(f"{BASE_URL}/juara/{jid}", headers={"Authorization": f"Bearer {super_token}"})
    for pid in [peserta_L_id, peserta_P_id, peserta_L2_id]:
        requests.delete(f"{BASE_URL}/peserta/{pid}", headers={"Authorization": f"Bearer {super_token}"})
    requests.delete(f"{BASE_URL}/lomba/{lomba_id}", headers={"Authorization": f"Bearer {super_token}"})
    
    print("\n✅ SCENARIO 4 PASSED: Juara gender upsert by lomba_id+rank+gender working correctly")


def test_scenario_5_backup_restore(super_token):
    """
    Scenario 5: Backup & Restore
    - GET /api/admin/backup as super_admin -> 200 with body.collections containing keys users, lomba, peserta, hasil, juara, templates, files, settings (arrays).
    - GET /api/admin/backup as non-super (admin_madrasah token) -> 403.
    - POST /api/admin/restore {collections: <the backup collections just fetched>} as super_admin -> 200 with {ok:true, restored:{...}.
    - After restore, GET /api/auth/me with the SAME super_admin token used before -> expect 200 (session preserved, not locked out).
    """
    print("\n=== SCENARIO 5: Backup & Restore ===")
    
    # GET /admin/backup as super_admin
    print("\n[5.1] GET /admin/backup as super_admin...")
    r = requests.get(f"{BASE_URL}/admin/backup", headers={"Authorization": f"Bearer {super_token}"})
    assert r.status_code == 200, f"GET /admin/backup failed: {r.status_code} {r.text}"
    backup = r.json()
    assert "collections" in backup, "Backup missing 'collections' key"
    collections = backup["collections"]
    expected_keys = ["users", "lomba", "peserta", "hasil", "juara", "templates", "files", "settings"]
    for key in expected_keys:
        assert key in collections, f"Backup missing collection '{key}'"
        assert isinstance(collections[key], list), f"Collection '{key}' is not an array"
    print(f"✅ GET /admin/backup OK: collections={list(collections.keys())}")
    
    # GET /admin/backup as non-super -> 403
    print("\n[5.2] GET /admin/backup as non-super (create admin_madrasah)...")
    # Create admin_madrasah if not exists
    r = requests.post(f"{BASE_URL}/users", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"name": "Admin MI Backup Test", "email": "admin.backup.test@porseni.id", "role": "admin_madrasah", "madrasah_name": "MI Backup Test"})
    if r.status_code == 200:
        print("✅ admin_madrasah created for backup test")
    elif r.status_code == 400 and "sudah terdaftar" in r.text:
        print("✅ admin_madrasah already exists")
    else:
        assert False, f"Create admin_madrasah failed: {r.status_code} {r.text}"
    
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin.backup.test@porseni.id", "password": "12345678"})
    assert r.status_code == 200, f"admin_madrasah login failed: {r.status_code} {r.text}"
    admin_backup_token = r.json()["token"]
    
    r = requests.get(f"{BASE_URL}/admin/backup", headers={"Authorization": f"Bearer {admin_backup_token}"})
    assert r.status_code == 403, f"Expected 403 for non-super GET /admin/backup, got {r.status_code}"
    print("✅ Non-super GET /admin/backup rejected with 403")
    
    # POST /admin/restore as super_admin
    print("\n[5.3] POST /admin/restore as super_admin...")
    r = requests.post(f"{BASE_URL}/admin/restore", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"collections": collections})
    assert r.status_code == 200, f"POST /admin/restore failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is True, f"Expected ok=true, got {data.get('ok')}"
    assert "restored" in data, "Restore response missing 'restored' key"
    print(f"✅ POST /admin/restore OK: restored={data['restored']}")
    
    # GET /auth/me with SAME super_admin token -> expect 200 (session preserved)
    print("\n[5.4] GET /auth/me with SAME super_admin token (session preserved)...")
    r = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {super_token}"})
    assert r.status_code == 200, f"GET /auth/me after restore failed: {r.status_code} {r.text}"
    me = r.json()
    assert me["email"] == "super@porseni.id", f"Expected super@porseni.id, got {me.get('email')}"
    print(f"✅ GET /auth/me OK: session preserved, email={me['email']}")
    
    print("\n✅ SCENARIO 5 PASSED: Backup & Restore working correctly, session preserved")


def test_scenario_6_compute_complete_5_files(super_token, admin_token):
    """
    Scenario 6: computeComplete requires 5 files now
    - As admin_madrasah, POST /peserta with only 3 files akte,surat_ket,pas_photo (each {id:"x",name:"y"}) and gender+lomba_id -> expect complete:false (because nisn_doc & raport missing).
    - PUT /peserta/:id adding nisn_doc and raport (all 5 files present) -> expect complete:true.
    """
    print("\n=== SCENARIO 6: computeComplete requires 5 files now ===")
    
    # Create lomba
    print("\n[6.1] Create lomba (individu)...")
    r = requests.post(f"{BASE_URL}/lomba", 
                      headers={"Authorization": f"Bearer {super_token}"},
                      json={"name": "Test Lomba 5 Files", "type": "individu"})
    assert r.status_code == 200, f"Create lomba failed: {r.status_code} {r.text}"
    lomba_id = r.json()["id"]
    print(f"✅ Lomba created: {lomba_id}")
    
    # POST /peserta with only 3 files
    print("\n[6.2] POST /peserta with only 3 files (akte, surat_ket, pas_photo)...")
    r = requests.post(f"{BASE_URL}/peserta", 
                      headers={"Authorization": f"Bearer {admin_token}"},
                      json={
                          "participant_name": "Test 5 Files",
                          "gender": "L",
                          "lomba_id": lomba_id,
                          "files": {
                              "akte": {"id": "akte123", "name": "akte.pdf"},
                              "surat_ket": {"id": "surat123", "name": "surat.pdf"},
                              "pas_photo": {"id": "photo123", "name": "photo.jpg"}
                          }
                      })
    assert r.status_code == 200, f"POST /peserta failed: {r.status_code} {r.text}"
    data = r.json()
    peserta_id = data["id"]
    assert data["complete"] is False, f"Expected complete=false with 3 files, got {data.get('complete')}"
    print(f"✅ POST /peserta OK: complete=false (only 3 files)")
    
    # PUT /peserta/:id adding nisn_doc and raport (all 5 files)
    print("\n[6.3] PUT /peserta/:id adding nisn_doc and raport (all 5 files)...")
    r = requests.put(f"{BASE_URL}/peserta/{peserta_id}", 
                     headers={"Authorization": f"Bearer {admin_token}"},
                     json={
                         "files": {
                             "akte": {"id": "akte123", "name": "akte.pdf"},
                             "surat_ket": {"id": "surat123", "name": "surat.pdf"},
                             "pas_photo": {"id": "photo123", "name": "photo.jpg"},
                             "nisn_doc": {"id": "nisn123", "name": "nisn.pdf"},
                             "raport": {"id": "raport123", "name": "raport.pdf"}
                         }
                     })
    assert r.status_code == 200, f"PUT /peserta failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["complete"] is True, f"Expected complete=true with 5 files, got {data.get('complete')}"
    print(f"✅ PUT /peserta OK: complete=true (all 5 files)")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/peserta/{peserta_id}", headers={"Authorization": f"Bearer {super_token}"})
    requests.delete(f"{BASE_URL}/lomba/{lomba_id}", headers={"Authorization": f"Bearer {super_token}"})
    
    print("\n✅ SCENARIO 6 PASSED: computeComplete requires 5 files (akte, surat_ket, pas_photo, nisn_doc, raport)")


def main():
    print("=" * 80)
    print("BACKEND TEST: NEW DELTA - Peserta verify super_admin-only; POST /users bulk create;")
    print("lomba idcard_image_url; juara gender; backup/restore; 5 required files")
    print("=" * 80)
    
    try:
        super_token, admin_token = test_scenario_1_post_users_bulk_create()
        test_scenario_2_peserta_verify_super_admin_only(super_token, admin_token)
        test_scenario_3_lomba_idcard_image_url(super_token)
        test_scenario_4_juara_gender(super_token, admin_token)
        test_scenario_5_backup_restore(super_token)
        test_scenario_6_compute_complete_5_files(super_token, admin_token)
        
        print("\n" + "=" * 80)
        print("✅ ALL 6 SCENARIOS PASSED")
        print("=" * 80)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
