#!/usr/bin/env python3
"""
Backend test for: Panitia GET /peserta requires status='verified'
Tests that panitia users only see verified peserta (not pending/unverified ones)
"""
import requests
import json

BASE_URL = "https://eb9e70ff-02ce-4629-97f3-d0b2aa6e6fbe.preview.emergentagent.com/api"

def test_panitia_verified_filter():
    """
    Test that panitia GET /peserta only returns verified peserta.
    Steps:
    1. super_admin login
    2. Create an individu lomba
    3. Create panitia user assigned to that lomba
    4. Create admin_madrasah user
    5. admin_madrasah creates a COMPLETE peserta (5 files) -> status defaults 'pending'
    6. panitia GET /peserta -> MUST be EMPTY (peserta complete but not verified)
    7. super_admin verifies the peserta (PUT /peserta/:id/status {status:'verified'})
    8. panitia GET /peserta -> MUST contain that 1 peserta
    9. Regression: admin_madrasah still sees own peserta, super_admin sees all
    10. Verify no sensitive data leaks in login response
    """
    print("\n" + "="*80)
    print("TEST: Panitia GET /peserta requires status='verified'")
    print("="*80)
    
    try:
        # Step 1: super_admin login
        print("\n[1] Super admin login (super@porseni.id / admin123)...")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "super@porseni.id",
            "password": "admin123"
        })
        assert resp.status_code == 200, f"Super admin login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        super_token = data.get("token")
        assert super_token, "No token in super admin login response"
        
        # Check no sensitive data leaks in login response
        user_obj = data.get("user", {})
        assert "_id" not in user_obj, "Login response leaks _id"
        assert "password" not in user_obj, "Login response leaks password hash"
        assert "password_plain" not in user_obj, "Login response leaks password_plain"
        assert "token" not in user_obj, "Login response leaks token in user object"
        print(f"✅ Super admin login successful, token: {super_token[:20]}...")
        
        # Step 2: Create an individu lomba
        print("\n[2] Creating individu lomba (Test Verify Lomba)...")
        resp = requests.post(f"{BASE_URL}/lomba", 
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Test Verify Lomba",
                "category": "Olahraga",
                "type": "individu"
            }
        )
        assert resp.status_code == 200, f"Create lomba failed: {resp.status_code} {resp.text}"
        lomba = resp.json()
        lomba_id = lomba.get("id")
        assert lomba_id, "No lomba id in response"
        print(f"✅ Lomba created: {lomba.get('name')} (id: {lomba_id})")
        
        # Step 3: Create panitia user assigned to that lomba
        print("\n[3] Creating panitia user (panitia.x@porseni.id) assigned to lomba...")
        resp = requests.post(f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Panitia X",
                "email": "panitia.x@porseni.id",
                "role": "panitia",
                "assigned_lomba_id": lomba_id
            }
        )
        assert resp.status_code == 200, f"Create panitia failed: {resp.status_code} {resp.text}"
        panitia_user = resp.json()
        print(f"✅ Panitia user created: {panitia_user.get('name')} (email: {panitia_user.get('email')})")
        
        # Step 3b: Panitia login
        print("\n[3b] Panitia login (panitia.x@porseni.id / 12345678)...")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "panitia.x@porseni.id",
            "password": "12345678"
        })
        assert resp.status_code == 200, f"Panitia login failed: {resp.status_code} {resp.text}"
        panitia_token = resp.json().get("token")
        assert panitia_token, "No token in panitia login response"
        print(f"✅ Panitia login successful, token: {panitia_token[:20]}...")
        
        # Step 4: Create admin_madrasah user
        print("\n[4] Creating admin_madrasah user (mi.x@porseni.id)...")
        resp = requests.post(f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "MI X",
                "email": "mi.x@porseni.id",
                "role": "admin_madrasah",
                "madrasah_name": "MI X"
            }
        )
        assert resp.status_code == 200, f"Create admin_madrasah failed: {resp.status_code} {resp.text}"
        admin_user = resp.json()
        print(f"✅ Admin madrasah user created: {admin_user.get('name')} (email: {admin_user.get('email')})")
        
        # Step 4b: Admin madrasah login
        print("\n[4b] Admin madrasah login (mi.x@porseni.id / 12345678)...")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "mi.x@porseni.id",
            "password": "12345678"
        })
        assert resp.status_code == 200, f"Admin madrasah login failed: {resp.status_code} {resp.text}"
        admin_token = resp.json().get("token")
        assert admin_token, "No token in admin madrasah login response"
        print(f"✅ Admin madrasah login successful, token: {admin_token[:20]}...")
        
        # Step 5: Admin madrasah creates a COMPLETE peserta (5 files)
        print("\n[5] Admin madrasah creates COMPLETE peserta (5 files present)...")
        resp = requests.post(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "participant_name": "Ahmad Test",
                "gender": "L",
                "lomba_id": lomba_id,
                "nisn": "1234567890",
                "ttl": "Kediri, 01-01-2010",
                "files": {
                    "akte": {"id": "f1", "name": "akte.pdf"},
                    "surat_ket": {"id": "f2", "name": "surat_ket.pdf"},
                    "pas_photo": {"id": "f3", "name": "pas_photo.jpg"},
                    "nisn_doc": {"id": "f4", "name": "nisn.pdf"},
                    "raport": {"id": "f5", "name": "raport.pdf"}
                }
            }
        )
        assert resp.status_code == 200, f"Create peserta failed: {resp.status_code} {resp.text}"
        peserta = resp.json()
        peserta_id = peserta.get("id")
        assert peserta_id, "No peserta id in response"
        assert peserta.get("complete") == True, f"Peserta should be complete=true, got: {peserta.get('complete')}"
        assert peserta.get("status") == "pending", f"Peserta status should be 'pending', got: {peserta.get('status')}"
        print(f"✅ Peserta created: {peserta.get('participant_name')} (id: {peserta_id})")
        print(f"   complete={peserta.get('complete')}, status={peserta.get('status')}")
        
        # Step 6: CORE TEST - Panitia GET /peserta should be EMPTY (peserta complete but NOT verified)
        print("\n[6] 🔍 CORE TEST: Panitia GET /peserta (should be EMPTY - peserta not verified yet)...")
        resp = requests.get(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {panitia_token}"}
        )
        assert resp.status_code == 200, f"Panitia GET /peserta failed: {resp.status_code} {resp.text}"
        panitia_peserta = resp.json()
        assert isinstance(panitia_peserta, list), f"Expected array, got: {type(panitia_peserta)}"
        
        if len(panitia_peserta) == 0:
            print(f"✅ PASS: Panitia GET /peserta returns EMPTY array (unverified peserta correctly hidden)")
        else:
            print(f"❌ FAIL: Panitia GET /peserta returned {len(panitia_peserta)} peserta (should be 0)")
            print(f"   Peserta returned: {json.dumps(panitia_peserta, indent=2)}")
            raise AssertionError(f"BUG: Panitia sees {len(panitia_peserta)} unverified peserta (should be 0)")
        
        # Step 7: Super admin verifies the peserta
        print("\n[7] Super admin verifies peserta (PUT /peserta/:id/status {status:'verified'})...")
        resp = requests.put(f"{BASE_URL}/peserta/{peserta_id}/status",
            headers={"Authorization": f"Bearer {super_token}"},
            json={"status": "verified"}
        )
        assert resp.status_code == 200, f"Verify peserta failed: {resp.status_code} {resp.text}"
        verified_peserta = resp.json()
        assert verified_peserta.get("status") == "verified", f"Status should be 'verified', got: {verified_peserta.get('status')}"
        print(f"✅ Peserta verified: status={verified_peserta.get('status')}")
        
        # Step 8: CORE TEST - Panitia GET /peserta should now contain that 1 peserta
        print("\n[8] 🔍 CORE TEST: Panitia GET /peserta (should now contain 1 verified peserta)...")
        resp = requests.get(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {panitia_token}"}
        )
        assert resp.status_code == 200, f"Panitia GET /peserta failed: {resp.status_code} {resp.text}"
        panitia_peserta = resp.json()
        assert isinstance(panitia_peserta, list), f"Expected array, got: {type(panitia_peserta)}"
        
        if len(panitia_peserta) == 1:
            print(f"✅ PASS: Panitia GET /peserta returns 1 peserta (verified peserta now visible)")
            returned_peserta = panitia_peserta[0]
            assert returned_peserta.get("id") == peserta_id, f"Wrong peserta id: {returned_peserta.get('id')} != {peserta_id}"
            assert returned_peserta.get("status") == "verified", f"Status should be 'verified', got: {returned_peserta.get('status')}"
            print(f"   Peserta: {returned_peserta.get('participant_name')} (status={returned_peserta.get('status')})")
        else:
            print(f"❌ FAIL: Panitia GET /peserta returned {len(panitia_peserta)} peserta (should be 1)")
            print(f"   Peserta returned: {json.dumps(panitia_peserta, indent=2)}")
            raise AssertionError(f"BUG: Panitia sees {len(panitia_peserta)} peserta after verification (should be 1)")
        
        # Step 9: Regression - admin_madrasah still sees own peserta (regardless of verify status)
        print("\n[9] Regression: Admin madrasah GET /peserta (should see own peserta regardless of verify)...")
        resp = requests.get(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200, f"Admin madrasah GET /peserta failed: {resp.status_code} {resp.text}"
        admin_peserta = resp.json()
        assert isinstance(admin_peserta, list), f"Expected array, got: {type(admin_peserta)}"
        assert len(admin_peserta) >= 1, f"Admin madrasah should see at least 1 peserta (own), got: {len(admin_peserta)}"
        print(f"✅ Admin madrasah sees {len(admin_peserta)} peserta (own peserta visible)")
        
        # Step 9b: Regression - super_admin sees all peserta
        print("\n[9b] Regression: Super admin GET /peserta (should see all peserta)...")
        resp = requests.get(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {super_token}"}
        )
        assert resp.status_code == 200, f"Super admin GET /peserta failed: {resp.status_code} {resp.text}"
        super_peserta = resp.json()
        assert isinstance(super_peserta, list), f"Expected array, got: {type(super_peserta)}"
        assert len(super_peserta) >= 1, f"Super admin should see at least 1 peserta, got: {len(super_peserta)}"
        print(f"✅ Super admin sees {len(super_peserta)} peserta (all peserta visible)")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED - BUG FIX VERIFIED")
        print("="*80)
        print("\nSummary:")
        print("  ✅ Step 5 (empty for panitia when unverified): PASS")
        print("  ✅ Step 7 (visible after verify): PASS")
        print("  ✅ Regression (admin_madrasah sees own): PASS")
        print("  ✅ Regression (super_admin sees all): PASS")
        print("  ✅ No sensitive data leaks in login: PASS")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_panitia_verified_filter()
    exit(0 if success else 1)
