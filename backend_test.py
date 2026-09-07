#!/usr/bin/env python3
"""
Backend API Test Suite for Porseni MI Plosoklaten
Tests: Users PUT edit — email (dedup) + role (with role-consistent field cleanup)
"""

import requests
import json
import sys

BASE_URL = "https://absensi-foto-cetak.preview.emergentagent.com/api"

def log(msg):
    print(f"[TEST] {msg}")

def test_users_put_edit():
    """
    Test Users PUT edit — now accepts email (dedup) + role (with role-consistent field cleanup)
    
    Steps:
    1. Login super_admin, get token (Bearer)
    2. Create 2 lomba (Test Lomba A - Olahraga/individu, Test Lomba B - Seni/individu), capture IDs
    3. POST /api/users create panitia user with assigned_lomba_id = Lomba A id
    4. PUT /api/users/:id {assigned_lomba_id: Lomba B id} - verify it changes to Lomba B
    5. PUT /api/users/:id {role:'admin_madrasah', madrasah_name:'MI Test'} - verify assigned_lomba_id becomes null and madrasah_name='MI Test'
    6. Create another user with email user.two@porseni.id, then PUT panitia user {email:'user.two@porseni.id'} - should return 400 (duplicate)
    7. PUT panitia user {email:'panitia.new@porseni.id'} (unique) - should persist; login with new email and default password 12345678 should succeed
    8. Regression: PUT {name:'Renamed'} and PUT {status:'pending'} still work. Non-super attempt (create/login admin_madrasah, use its token) PUT /api/users/:id must return 403
    """
    
    try:
        # Step 1: Login super_admin
        log("Step 1: Login super_admin (super@porseni.id / admin123)")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "super@porseni.id",
            "password": "admin123"
        })
        assert resp.status_code == 200, f"Super admin login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        super_token = data.get("token")
        assert super_token, "No token in super admin login response"
        log(f"✅ Super admin login successful, token: {super_token[:20]}...")
        
        headers = {"Authorization": f"Bearer {super_token}"}
        
        # Step 2: Create 2 lomba
        log("Step 2: Create Test Lomba A (Olahraga/individu)")
        resp = requests.post(f"{BASE_URL}/lomba", json={
            "name": "Test Lomba A",
            "category": "Olahraga",
            "type": "individu"
        }, headers=headers)
        assert resp.status_code == 200, f"Create Lomba A failed: {resp.status_code} {resp.text}"
        lomba_a = resp.json()
        lomba_a_id = lomba_a.get("id")
        assert lomba_a_id, "No id in Lomba A response"
        log(f"✅ Lomba A created: {lomba_a_id}, name={lomba_a.get('name')}")
        
        log("Step 2: Create Test Lomba B (Seni/individu)")
        resp = requests.post(f"{BASE_URL}/lomba", json={
            "name": "Test Lomba B",
            "category": "Seni",
            "type": "individu"
        }, headers=headers)
        assert resp.status_code == 200, f"Create Lomba B failed: {resp.status_code} {resp.text}"
        lomba_b = resp.json()
        lomba_b_id = lomba_b.get("id")
        assert lomba_b_id, "No id in Lomba B response"
        log(f"✅ Lomba B created: {lomba_b_id}, name={lomba_b.get('name')}")
        
        # Step 3: POST /api/users create panitia user with assigned_lomba_id = Lomba A id
        log(f"Step 3: Create panitia user 'Panitia Test' with assigned_lomba_id={lomba_a_id}")
        resp = requests.post(f"{BASE_URL}/users", json={
            "name": "Panitia Test",
            "email": "panitia.test@porseni.id",
            "role": "panitia",
            "assigned_lomba_id": lomba_a_id
        }, headers=headers)
        assert resp.status_code == 200, f"Create panitia user failed: {resp.status_code} {resp.text}"
        panitia_user = resp.json()
        panitia_id = panitia_user.get("id")
        assert panitia_id, "No id in panitia user response"
        assert panitia_user.get("assigned_lomba_id") == lomba_a_id, f"assigned_lomba_id mismatch: expected {lomba_a_id}, got {panitia_user.get('assigned_lomba_id')}"
        assert panitia_user.get("role") == "panitia", f"Role mismatch: expected panitia, got {panitia_user.get('role')}"
        assert panitia_user.get("status") == "verified", f"Status should be verified, got {panitia_user.get('status')}"
        log(f"✅ Panitia user created: {panitia_id}, assigned_lomba_id={panitia_user.get('assigned_lomba_id')}")
        
        # Step 4: PUT /api/users/:id {assigned_lomba_id: Lomba B id} - verify it changes to Lomba B
        log(f"Step 4: PUT /api/users/{panitia_id} {{assigned_lomba_id: {lomba_b_id}}}")
        resp = requests.put(f"{BASE_URL}/users/{panitia_id}", json={
            "assigned_lomba_id": lomba_b_id
        }, headers=headers)
        assert resp.status_code == 200, f"PUT assigned_lomba_id failed: {resp.status_code} {resp.text}"
        updated_user = resp.json()
        assert updated_user.get("assigned_lomba_id") == lomba_b_id, f"assigned_lomba_id not updated: expected {lomba_b_id}, got {updated_user.get('assigned_lomba_id')}"
        log(f"✅ assigned_lomba_id updated to Lomba B: {updated_user.get('assigned_lomba_id')}")
        
        # Verify with GET /api/users
        log("Step 4: Verify with GET /api/users")
        resp = requests.get(f"{BASE_URL}/users", headers=headers)
        assert resp.status_code == 200, f"GET /users failed: {resp.status_code} {resp.text}"
        users = resp.json()
        panitia_in_list = next((u for u in users if u.get("id") == panitia_id), None)
        assert panitia_in_list, "Panitia user not found in GET /users"
        assert panitia_in_list.get("assigned_lomba_id") == lomba_b_id, f"GET /users shows wrong assigned_lomba_id: expected {lomba_b_id}, got {panitia_in_list.get('assigned_lomba_id')}"
        log(f"✅ GET /users confirms assigned_lomba_id={panitia_in_list.get('assigned_lomba_id')}")
        
        # Step 5: PUT /api/users/:id {role:'admin_madrasah', madrasah_name:'MI Test'} - verify assigned_lomba_id becomes null and madrasah_name='MI Test'
        log(f"Step 5: PUT /api/users/{panitia_id} {{role:'admin_madrasah', madrasah_name:'MI Test'}}")
        resp = requests.put(f"{BASE_URL}/users/{panitia_id}", json={
            "role": "admin_madrasah",
            "madrasah_name": "MI Test"
        }, headers=headers)
        assert resp.status_code == 200, f"PUT role change failed: {resp.status_code} {resp.text}"
        updated_user = resp.json()
        assert updated_user.get("role") == "admin_madrasah", f"Role not updated: expected admin_madrasah, got {updated_user.get('role')}"
        assert updated_user.get("madrasah_name") == "MI Test", f"madrasah_name not updated: expected 'MI Test', got {updated_user.get('madrasah_name')}"
        assert updated_user.get("assigned_lomba_id") is None, f"assigned_lomba_id should be null for admin_madrasah, got {updated_user.get('assigned_lomba_id')}"
        log(f"✅ Role changed to admin_madrasah, madrasah_name='MI Test', assigned_lomba_id=null")
        
        # Verify with GET /api/users
        log("Step 5: Verify with GET /api/users")
        resp = requests.get(f"{BASE_URL}/users", headers=headers)
        assert resp.status_code == 200, f"GET /users failed: {resp.status_code} {resp.text}"
        users = resp.json()
        user_in_list = next((u for u in users if u.get("id") == panitia_id), None)
        assert user_in_list, "User not found in GET /users"
        assert user_in_list.get("role") == "admin_madrasah", f"GET /users shows wrong role: expected admin_madrasah, got {user_in_list.get('role')}"
        assert user_in_list.get("madrasah_name") == "MI Test", f"GET /users shows wrong madrasah_name: expected 'MI Test', got {user_in_list.get('madrasah_name')}"
        assert user_in_list.get("assigned_lomba_id") is None, f"GET /users shows assigned_lomba_id should be null, got {user_in_list.get('assigned_lomba_id')}"
        log(f"✅ GET /users confirms role=admin_madrasah, madrasah_name='MI Test', assigned_lomba_id=null")
        
        # Step 6: Create another user with email user.two@porseni.id, then PUT panitia user {email:'user.two@porseni.id'} - should return 400 (duplicate)
        log("Step 6: Create another user 'User Two' with email user.two@porseni.id")
        resp = requests.post(f"{BASE_URL}/users", json={
            "name": "User Two",
            "email": "user.two@porseni.id",
            "role": "admin_madrasah",
            "madrasah_name": "MI Two"
        }, headers=headers)
        assert resp.status_code == 200, f"Create User Two failed: {resp.status_code} {resp.text}"
        user_two = resp.json()
        user_two_id = user_two.get("id")
        assert user_two_id, "No id in User Two response"
        log(f"✅ User Two created: {user_two_id}, email={user_two.get('email')}")
        
        log(f"Step 6: PUT /api/users/{panitia_id} {{email:'user.two@porseni.id'}} - should return 400 (duplicate)")
        resp = requests.put(f"{BASE_URL}/users/{panitia_id}", json={
            "email": "user.two@porseni.id"
        }, headers=headers)
        assert resp.status_code == 400, f"Expected 400 for duplicate email, got {resp.status_code} {resp.text}"
        error_data = resp.json()
        assert "error" in error_data, "No error field in 400 response"
        log(f"✅ Duplicate email rejected with 400: {error_data.get('error')}")
        
        # Step 7: PUT panitia user {email:'panitia.new@porseni.id'} (unique) - should persist; login with new email and default password 12345678 should succeed
        log(f"Step 7: PUT /api/users/{panitia_id} {{email:'panitia.new@porseni.id'}} (unique)")
        resp = requests.put(f"{BASE_URL}/users/{panitia_id}", json={
            "email": "panitia.new@porseni.id"
        }, headers=headers)
        assert resp.status_code == 200, f"PUT unique email failed: {resp.status_code} {resp.text}"
        updated_user = resp.json()
        assert updated_user.get("email") == "panitia.new@porseni.id", f"Email not updated: expected 'panitia.new@porseni.id', got {updated_user.get('email')}"
        log(f"✅ Email updated to 'panitia.new@porseni.id'")
        
        # Verify with GET /api/users
        log("Step 7: Verify with GET /api/users")
        resp = requests.get(f"{BASE_URL}/users", headers=headers)
        assert resp.status_code == 200, f"GET /users failed: {resp.status_code} {resp.text}"
        users = resp.json()
        user_in_list = next((u for u in users if u.get("id") == panitia_id), None)
        assert user_in_list, "User not found in GET /users"
        assert user_in_list.get("email") == "panitia.new@porseni.id", f"GET /users shows wrong email: expected 'panitia.new@porseni.id', got {user_in_list.get('email')}"
        log(f"✅ GET /users confirms email='panitia.new@porseni.id'")
        
        # Login with new email and default password 12345678
        log("Step 7: Login with new email 'panitia.new@porseni.id' and default password '12345678'")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "panitia.new@porseni.id",
            "password": "12345678"
        })
        assert resp.status_code == 200, f"Login with new email failed: {resp.status_code} {resp.text}"
        login_data = resp.json()
        assert "token" in login_data, "No token in login response"
        assert login_data.get("user", {}).get("email") == "panitia.new@porseni.id", f"Login user email mismatch: expected 'panitia.new@porseni.id', got {login_data.get('user', {}).get('email')}"
        log(f"✅ Login with new email successful, token: {login_data.get('token')[:20]}...")
        
        # Step 8: Regression: PUT {name:'Renamed'} and PUT {status:'pending'} still work
        log(f"Step 8: Regression - PUT /api/users/{panitia_id} {{name:'Renamed'}}")
        resp = requests.put(f"{BASE_URL}/users/{panitia_id}", json={
            "name": "Renamed"
        }, headers=headers)
        assert resp.status_code == 200, f"PUT name failed: {resp.status_code} {resp.text}"
        updated_user = resp.json()
        assert updated_user.get("name") == "Renamed", f"Name not updated: expected 'Renamed', got {updated_user.get('name')}"
        log(f"✅ PUT name='Renamed' successful")
        
        log(f"Step 8: Regression - PUT /api/users/{panitia_id} {{status:'pending'}}")
        resp = requests.put(f"{BASE_URL}/users/{panitia_id}", json={
            "status": "pending"
        }, headers=headers)
        assert resp.status_code == 200, f"PUT status failed: {resp.status_code} {resp.text}"
        updated_user = resp.json()
        assert updated_user.get("status") == "pending", f"Status not updated: expected 'pending', got {updated_user.get('status')}"
        log(f"✅ PUT status='pending' successful")
        
        # Step 8: Non-super attempt (create/login admin_madrasah, use its token) PUT /api/users/:id must return 403
        log("Step 8: Create and login admin_madrasah user for non-super test")
        resp = requests.post(f"{BASE_URL}/users", json={
            "name": "Admin Madrasah Test",
            "email": "admin.test@porseni.id",
            "role": "admin_madrasah",
            "madrasah_name": "MI Test Admin"
        }, headers=headers)
        assert resp.status_code == 200, f"Create admin_madrasah failed: {resp.status_code} {resp.text}"
        admin_user = resp.json()
        admin_id = admin_user.get("id")
        log(f"✅ Admin madrasah user created: {admin_id}")
        
        # Login as admin_madrasah
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin.test@porseni.id",
            "password": "12345678"
        })
        assert resp.status_code == 200, f"Admin madrasah login failed: {resp.status_code} {resp.text}"
        admin_token = resp.json().get("token")
        assert admin_token, "No token in admin madrasah login response"
        log(f"✅ Admin madrasah login successful, token: {admin_token[:20]}...")
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try to PUT /api/users/:id as admin_madrasah - should return 403
        log(f"Step 8: Non-super attempt - PUT /api/users/{panitia_id} as admin_madrasah - should return 403")
        resp = requests.put(f"{BASE_URL}/users/{panitia_id}", json={
            "name": "Should Fail"
        }, headers=admin_headers)
        assert resp.status_code == 403, f"Expected 403 for non-super PUT /users, got {resp.status_code} {resp.text}"
        error_data = resp.json()
        assert "error" in error_data, "No error field in 403 response"
        log(f"✅ Non-super PUT /users rejected with 403: {error_data.get('error')}")
        
        # Cleanup: Delete test lomba and users
        log("Cleanup: Deleting test lomba and users")
        requests.delete(f"{BASE_URL}/lomba/{lomba_a_id}", headers=headers)
        requests.delete(f"{BASE_URL}/lomba/{lomba_b_id}", headers=headers)
        requests.delete(f"{BASE_URL}/users/{panitia_id}", headers=headers)
        requests.delete(f"{BASE_URL}/users/{user_two_id}", headers=headers)
        requests.delete(f"{BASE_URL}/users/{admin_id}", headers=headers)
        log("✅ Cleanup complete")
        
        log("=" * 80)
        log("✅ ALL TESTS PASSED - Users PUT edit (email dedup + role) working correctly")
        log("=" * 80)
        return True
        
    except AssertionError as e:
        log(f"❌ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        log(f"❌ TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_users_put_edit()
    sys.exit(0 if success else 1)
