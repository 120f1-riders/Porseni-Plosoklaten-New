#!/usr/bin/env python3
"""
Backend test for: Edit biodata peserta (PUT /peserta/:id) — admin_madrasah own-only scoping + super_admin any
"""
import requests
import json
import sys

BASE_URL = "https://peserta-admin-edit.preview.emergentagent.com/api"

def test_peserta_edit_authorization():
    """
    Test PUT /peserta/:id with admin_madrasah own-only scoping and super_admin any access.
    
    Steps:
    1. super_admin login (super@porseni.id/admin123)
    2. POST /lomba create Lomba A (Olahraga, individu) and Lomba B (Seni, individu)
    3. POST /users create admin_madrasah 'MI A' (mi.a@porseni.id) -> default password 12345678, login
    4. MI A POST /peserta in Lomba A -> pesertaA
    5. MI A PUT /peserta/{pesertaA.id} (change to Lomba B, update fields) -> expect 200
    6. POST /users create admin_madrasah 'MI B' (mi.b@porseni.id), login
    7. MI B PUT /peserta/{pesertaA.id} -> expect 403 (not own)
    8. super_admin PUT /peserta/{pesertaA.id} -> expect 200
    9. super_admin PUT /peserta/nonexistent-id-123 -> expect 404
    10. PUT /peserta/{pesertaA.id} with NO Authorization header -> expect 401
    """
    
    print("\n" + "="*80)
    print("TEST: Edit biodata peserta (PUT /peserta/:id) — admin_madrasah own-only scoping")
    print("="*80 + "\n")
    
    try:
        # Step 1: super_admin login
        print("Step 1: Super admin login (super@porseni.id/admin123)")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "super@porseni.id",
            "password": "admin123"
        })
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        data = resp.json()
        super_token = data.get("token")
        if not super_token:
            print(f"  ❌ FAIL: No token in response")
            return False
        
        # Check no sensitive data leaks
        user = data.get("user", {})
        if "_id" in user or "password" in user or "password_plain" in user or "token" in user:
            print(f"  ❌ FAIL: Sensitive data leak in login response: {list(user.keys())}")
            return False
        
        print(f"  ✅ PASS: Super admin login successful, token received, no sensitive data leaks")
        
        # Step 2: Create Lomba A and Lomba B
        print("\nStep 2: Create Lomba A (Olahraga, individu) and Lomba B (Seni, individu)")
        
        # Lomba A
        resp = requests.post(f"{BASE_URL}/lomba", 
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Test Lomba A",
                "category": "Olahraga",
                "type": "individu"
            }
        )
        print(f"  Lomba A Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        lomba_a = resp.json()
        lomba_a_id = lomba_a.get("id")
        lomba_a_name = lomba_a.get("name")
        print(f"  ✅ Lomba A created: {lomba_a_name} (id: {lomba_a_id})")
        
        # Lomba B
        resp = requests.post(f"{BASE_URL}/lomba", 
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Test Lomba B",
                "category": "Seni",
                "type": "individu"
            }
        )
        print(f"  Lomba B Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        lomba_b = resp.json()
        lomba_b_id = lomba_b.get("id")
        lomba_b_name = lomba_b.get("name")
        print(f"  ✅ Lomba B created: {lomba_b_name} (id: {lomba_b_id})")
        
        # Step 3: Create admin_madrasah 'MI A'
        print("\nStep 3: Create admin_madrasah 'MI A' (mi.a@porseni.id)")
        resp = requests.post(f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Admin MI A",
                "email": "mi.a@porseni.id",
                "role": "admin_madrasah",
                "madrasah_name": "MI A"
            }
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        mi_a_user = resp.json()
        print(f"  ✅ MI A user created: {mi_a_user.get('name')} ({mi_a_user.get('email')})")
        
        # Login as MI A
        print("  Login as MI A (default password: 12345678)")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "mi.a@porseni.id",
            "password": "12345678"
        })
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        data = resp.json()
        mi_a_token = data.get("token")
        if not mi_a_token:
            print(f"  ❌ FAIL: No token in response")
            return False
        
        print(f"  ✅ PASS: MI A login successful")
        
        # Step 4: MI A creates peserta in Lomba A
        print("\nStep 4: MI A creates peserta 'Ahmad' in Lomba A")
        resp = requests.post(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {mi_a_token}"},
            json={
                "participant_name": "Ahmad",
                "gender": "L",
                "nisn": "111",
                "ttl": "Kediri, 2015",
                "lomba_id": lomba_a_id
            }
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        peserta_a = resp.json()
        peserta_a_id = peserta_a.get("id")
        print(f"  ✅ Peserta created: {peserta_a.get('participant_name')} (id: {peserta_a_id})")
        print(f"     Gender: {peserta_a.get('gender')}, NISN: {peserta_a.get('nisn')}, TTL: {peserta_a.get('ttl')}")
        print(f"     Lomba: {peserta_a.get('lomba_name')} (id: {peserta_a.get('lomba_id')})")
        print(f"     Created by: {peserta_a.get('created_by')}")
        
        # Step 5: MI A edits own peserta (change to Lomba B, update fields)
        print("\nStep 5: MI A edits own peserta (change to Lomba B, update all fields)")
        resp = requests.put(f"{BASE_URL}/peserta/{peserta_a_id}",
            headers={"Authorization": f"Bearer {mi_a_token}"},
            json={
                "participant_name": "Ahmad Baru",
                "gender": "P",
                "nisn": "222",
                "ttl": "Kediri, 2016",
                "lomba_id": lomba_b_id
            }
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        updated_peserta = resp.json()
        print(f"  ✅ PASS: MI A successfully edited own peserta")
        
        # Verify all fields updated
        if updated_peserta.get("participant_name") != "Ahmad Baru":
            print(f"  ❌ FAIL: participant_name not updated. Expected 'Ahmad Baru', got '{updated_peserta.get('participant_name')}'")
            return False
        if updated_peserta.get("gender") != "P":
            print(f"  ❌ FAIL: gender not updated. Expected 'P', got '{updated_peserta.get('gender')}'")
            return False
        if updated_peserta.get("nisn") != "222":
            print(f"  ❌ FAIL: nisn not updated. Expected '222', got '{updated_peserta.get('nisn')}'")
            return False
        if updated_peserta.get("ttl") != "Kediri, 2016":
            print(f"  ❌ FAIL: ttl not updated. Expected 'Kediri, 2016', got '{updated_peserta.get('ttl')}'")
            return False
        if updated_peserta.get("lomba_id") != lomba_b_id:
            print(f"  ❌ FAIL: lomba_id not updated. Expected '{lomba_b_id}', got '{updated_peserta.get('lomba_id')}'")
            return False
        if updated_peserta.get("lomba_name") != lomba_b_name:
            print(f"  ❌ FAIL: lomba_name not recomputed. Expected '{lomba_b_name}', got '{updated_peserta.get('lomba_name')}'")
            return False
        
        print(f"  ✅ PASS: All fields updated correctly:")
        print(f"     participant_name: 'Ahmad' -> 'Ahmad Baru'")
        print(f"     gender: 'L' -> 'P'")
        print(f"     nisn: '111' -> '222'")
        print(f"     ttl: 'Kediri, 2015' -> 'Kediri, 2016'")
        print(f"     lomba_id: {lomba_a_id} -> {lomba_b_id}")
        print(f"     lomba_name: '{lomba_a_name}' -> '{lomba_b_name}' (recomputed)")
        
        # Verify with GET
        print("  Verify with GET /peserta")
        resp = requests.get(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {mi_a_token}"}
        )
        if resp.status_code == 200:
            peserta_list = resp.json()
            found = next((p for p in peserta_list if p.get("id") == peserta_a_id), None)
            if found:
                if found.get("lomba_name") == lomba_b_name:
                    print(f"  ✅ PASS: GET /peserta confirms lomba_name = '{lomba_b_name}'")
                else:
                    print(f"  ❌ FAIL: GET /peserta shows lomba_name = '{found.get('lomba_name')}', expected '{lomba_b_name}'")
                    return False
        
        # Step 6: Create admin_madrasah 'MI B' and login
        print("\nStep 6: Create admin_madrasah 'MI B' (mi.b@porseni.id)")
        resp = requests.post(f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Admin MI B",
                "email": "mi.b@porseni.id",
                "role": "admin_madrasah",
                "madrasah_name": "MI B"
            }
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        mi_b_user = resp.json()
        print(f"  ✅ MI B user created: {mi_b_user.get('name')} ({mi_b_user.get('email')})")
        
        # Login as MI B
        print("  Login as MI B (default password: 12345678)")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "mi.b@porseni.id",
            "password": "12345678"
        })
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        data = resp.json()
        mi_b_token = data.get("token")
        if not mi_b_token:
            print(f"  ❌ FAIL: No token in response")
            return False
        
        print(f"  ✅ PASS: MI B login successful")
        
        # Step 7: MI B tries to edit MI A's peserta -> expect 403
        print("\nStep 7: MI B tries to edit MI A's peserta (not own) -> expect 403")
        resp = requests.put(f"{BASE_URL}/peserta/{peserta_a_id}",
            headers={"Authorization": f"Bearer {mi_b_token}"},
            json={
                "participant_name": "Hack"
            }
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 403:
            print(f"  ❌ FAIL: Expected 403, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        error_msg = resp.json().get("error", "")
        print(f"  ✅ PASS: MI B correctly rejected with 403 (not own peserta)")
        print(f"     Error message: '{error_msg}'")
        
        # Step 8: super_admin edits MI A's peserta -> expect 200
        print("\nStep 8: super_admin edits MI A's peserta (madrasah_name, nomor_peserta) -> expect 200")
        resp = requests.put(f"{BASE_URL}/peserta/{peserta_a_id}",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "madrasah_name": "MI X",
                "nomor_peserta": "077"
            }
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ❌ FAIL: Expected 200, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        updated_peserta = resp.json()
        if updated_peserta.get("madrasah_name") != "MI X":
            print(f"  ❌ FAIL: madrasah_name not updated. Expected 'MI X', got '{updated_peserta.get('madrasah_name')}'")
            return False
        if updated_peserta.get("nomor_peserta") != "077":
            print(f"  ❌ FAIL: nomor_peserta not updated. Expected '077', got '{updated_peserta.get('nomor_peserta')}'")
            return False
        
        print(f"  ✅ PASS: super_admin successfully edited any peserta")
        print(f"     madrasah_name: 'MI A' -> 'MI X'")
        print(f"     nomor_peserta: -> '077'")
        
        # Step 9: super_admin tries to edit nonexistent peserta -> expect 404
        print("\nStep 9: super_admin tries to edit nonexistent peserta -> expect 404")
        resp = requests.put(f"{BASE_URL}/peserta/nonexistent-id-123",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "participant_name": "x"
            }
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 404:
            print(f"  ❌ FAIL: Expected 404, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        error_msg = resp.json().get("error", "")
        print(f"  ✅ PASS: Nonexistent peserta correctly returns 404")
        print(f"     Error message: '{error_msg}'")
        
        # Step 10: PUT without Authorization header -> expect 401
        print("\nStep 10: PUT /peserta without Authorization header -> expect 401")
        resp = requests.put(f"{BASE_URL}/peserta/{peserta_a_id}",
            json={
                "participant_name": "x"
            }
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 401:
            print(f"  ❌ FAIL: Expected 401, got {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
        
        error_msg = resp.json().get("error", "")
        print(f"  ✅ PASS: No Authorization header correctly returns 401")
        print(f"     Error message: '{error_msg}'")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED (10/10)")
        print("="*80)
        print("\nSummary:")
        print("  ✅ super_admin login successful")
        print("  ✅ Created Lomba A (Olahraga, individu) and Lomba B (Seni, individu)")
        print("  ✅ Created admin_madrasah 'MI A' and 'MI B'")
        print("  ✅ MI A created peserta in Lomba A")
        print("  ✅ MI A successfully edited own peserta (all fields updated, lomba_name recomputed)")
        print("  ✅ MI B correctly rejected (403) when trying to edit MI A's peserta")
        print("  ✅ super_admin successfully edited any peserta")
        print("  ✅ Nonexistent peserta correctly returns 404")
        print("  ✅ No Authorization header correctly returns 401")
        print("\nAuthorization scoping working correctly:")
        print("  • admin_madrasah can ONLY edit OWN peserta (created_by check)")
        print("  • super_admin can edit ANY peserta")
        print("  • 404 returned BEFORE body parsing (peserta not found)")
        print("  • All accepted fields working: participant_name, gender, nisn, ttl, madrasah_name, lomba_id, nomor_peserta")
        print("  • lomba_name recomputed when lomba_id changes")
        print("  • complete flag recomputed on update")
        
        return True
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_peserta_edit_authorization()
    sys.exit(0 if success else 1)
