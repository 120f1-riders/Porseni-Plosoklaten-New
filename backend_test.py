#!/usr/bin/env python3
"""
Backend test for DELETE /peserta/:id authorization scoping
Tests role-based authorization: super_admin (any), admin_madrasah (own only), panitia (forbidden)
"""

import requests
import json
import sys

BASE_URL = "https://sequential-id-maker.preview.emergentagent.com/api"

def test_delete_peserta_authorization():
    """
    Test DELETE /peserta/:id authorization scoping:
    - super_admin: can delete ANY peserta (200)
    - admin_madrasah: can delete ONLY its own peserta (created_by === self). Deleting another madrasah's peserta -> 403
    - panitia: always 403
    - unknown/non-existent peserta id -> 404
    - no auth token -> 401
    """
    print("\n" + "="*80)
    print("TEST: DELETE /peserta/:id Authorization Scoping")
    print("="*80)
    
    # Step 1: Login super_admin
    print("\n[1] Login super_admin (super@porseni.id/admin123)")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "super@porseni.id",
            "password": "admin123"
        })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        data = resp.json()
        super_token = data.get("token")
        if not super_token:
            print(f"    ❌ FAILED: No token in response")
            return False
        print(f"    ✅ PASSED: super_admin login successful, token: {super_token[:20]}...")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during super_admin login: {e}")
        return False
    
    # Step 2: Create a lomba
    print("\n[2] Create a lomba (POST /api/lomba)")
    try:
        resp = requests.post(f"{BASE_URL}/lomba", 
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Test Delete Auth",
                "category": "Olahraga",
                "type": "individu"
            })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        lomba = resp.json()
        lomba_id = lomba.get("id")
        print(f"    ✅ PASSED: Lomba created, id: {lomba_id}")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during lomba creation: {e}")
        return False
    
    # Step 3: Create admin_madrasah user 'MI A'
    print("\n[3] Create admin_madrasah user 'MI A' (POST /api/users)")
    try:
        resp = requests.post(f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Admin MI A",
                "email": f"mi.a.{lomba_id[:8]}@test.porseni.id",
                "role": "admin_madrasah",
                "madrasah_name": "MI A"
            })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        mi_a_user = resp.json()
        mi_a_email = mi_a_user.get("email")
        print(f"    ✅ PASSED: MI A user created, email: {mi_a_email}")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during MI A user creation: {e}")
        return False
    
    # Step 3b: Login MI A (default password 12345678)
    print("\n[3b] Login MI A (default password 12345678)")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": mi_a_email,
            "password": "12345678"
        })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        data = resp.json()
        mi_a_token = data.get("token")
        if not mi_a_token:
            print(f"    ❌ FAILED: No token in response")
            return False
        print(f"    ✅ PASSED: MI A login successful, token: {mi_a_token[:20]}...")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during MI A login: {e}")
        return False
    
    # Step 4: Create admin_madrasah user 'MI B'
    print("\n[4] Create admin_madrasah user 'MI B' (POST /api/users)")
    try:
        resp = requests.post(f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Admin MI B",
                "email": f"mi.b.{lomba_id[:8]}@test.porseni.id",
                "role": "admin_madrasah",
                "madrasah_name": "MI B"
            })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        mi_b_user = resp.json()
        mi_b_email = mi_b_user.get("email")
        print(f"    ✅ PASSED: MI B user created, email: {mi_b_email}")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during MI B user creation: {e}")
        return False
    
    # Step 4b: Login MI B
    print("\n[4b] Login MI B (default password 12345678)")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": mi_b_email,
            "password": "12345678"
        })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        data = resp.json()
        mi_b_token = data.get("token")
        if not mi_b_token:
            print(f"    ❌ FAILED: No token in response")
            return False
        print(f"    ✅ PASSED: MI B login successful, token: {mi_b_token[:20]}...")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during MI B login: {e}")
        return False
    
    # Step 5: MI A creates peserta1
    print("\n[5] MI A: POST /api/peserta -> peserta1 (created_by MI A)")
    try:
        resp = requests.post(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {mi_a_token}"},
            json={
                "participant_name": "Peserta A",
                "gender": "L",
                "lomba_id": lomba_id
            })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        peserta1 = resp.json()
        peserta1_id = peserta1.get("id")
        print(f"    ✅ PASSED: Peserta A created by MI A, id: {peserta1_id}")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during peserta1 creation: {e}")
        return False
    
    # Step 6: MI B creates peserta2
    print("\n[6] MI B: POST /api/peserta -> peserta2 (created_by MI B)")
    try:
        resp = requests.post(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {mi_b_token}"},
            json={
                "participant_name": "Peserta B",
                "gender": "P",
                "lomba_id": lomba_id
            })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        peserta2 = resp.json()
        peserta2_id = peserta2.get("id")
        print(f"    ✅ PASSED: Peserta B created by MI B, id: {peserta2_id}")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during peserta2 creation: {e}")
        return False
    
    # Step 7: MI A tries to DELETE peserta2 (not own) -> expect 403
    print("\n[7] MI A DELETE /api/peserta/<peserta2.id> -> expect 403 (not own)")
    try:
        resp = requests.delete(f"{BASE_URL}/peserta/{peserta2_id}",
            headers={"Authorization": f"Bearer {mi_a_token}"})
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 403:
            print(f"    ❌ FAILED: Expected 403, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        print(f"    ✅ PASSED: MI A cannot delete MI B's peserta (403)")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during MI A delete peserta2: {e}")
        return False
    
    # Step 8: MI A DELETE peserta1 (own) -> expect 200
    print("\n[8] MI A DELETE /api/peserta/<peserta1.id> -> expect 200 (own)")
    try:
        resp = requests.delete(f"{BASE_URL}/peserta/{peserta1_id}",
            headers={"Authorization": f"Bearer {mi_a_token}"})
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        print(f"    ✅ PASSED: MI A successfully deleted own peserta (200)")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during MI A delete peserta1: {e}")
        return False
    
    # Step 8b: Verify peserta1 is gone (GET /api/peserta as MI A)
    print("\n[8b] Verify peserta1 is gone (GET /api/peserta as MI A)")
    try:
        resp = requests.get(f"{BASE_URL}/peserta",
            headers={"Authorization": f"Bearer {mi_a_token}"})
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        peserta_list = resp.json()
        peserta1_exists = any(p.get("id") == peserta1_id for p in peserta_list)
        if peserta1_exists:
            print(f"    ❌ FAILED: peserta1 still exists in GET /peserta")
            return False
        print(f"    ✅ PASSED: peserta1 no longer in MI A's peserta list")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during GET /peserta: {e}")
        return False
    
    # Step 9: Create panitia user
    print("\n[9] Create panitia user (POST /api/users)")
    try:
        resp = requests.post(f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {super_token}"},
            json={
                "name": "Panitia Test",
                "email": f"panitia.{lomba_id[:8]}@test.porseni.id",
                "role": "panitia",
                "assigned_lomba_id": lomba_id
            })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        panitia_user = resp.json()
        panitia_email = panitia_user.get("email")
        print(f"    ✅ PASSED: Panitia user created, email: {panitia_email}")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during panitia user creation: {e}")
        return False
    
    # Step 9b: Login panitia
    print("\n[9b] Login panitia (default password 12345678)")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": panitia_email,
            "password": "12345678"
        })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        data = resp.json()
        panitia_token = data.get("token")
        if not panitia_token:
            print(f"    ❌ FAILED: No token in response")
            return False
        print(f"    ✅ PASSED: Panitia login successful, token: {panitia_token[:20]}...")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during panitia login: {e}")
        return False
    
    # Step 9c: Panitia tries to DELETE peserta2 -> expect 403
    print("\n[9c] Panitia DELETE /api/peserta/<peserta2.id> -> expect 403")
    try:
        resp = requests.delete(f"{BASE_URL}/peserta/{peserta2_id}",
            headers={"Authorization": f"Bearer {panitia_token}"})
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 403:
            print(f"    ❌ FAILED: Expected 403, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        print(f"    ✅ PASSED: Panitia cannot delete peserta (403)")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during panitia delete peserta2: {e}")
        return False
    
    # Step 10: super_admin DELETE peserta2 -> expect 200
    print("\n[10] super_admin DELETE /api/peserta/<peserta2.id> -> expect 200")
    try:
        resp = requests.delete(f"{BASE_URL}/peserta/{peserta2_id}",
            headers={"Authorization": f"Bearer {super_token}"})
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        print(f"    ✅ PASSED: super_admin successfully deleted peserta2 (200)")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during super_admin delete peserta2: {e}")
        return False
    
    # Step 11: super_admin DELETE nonexistent-id-123 -> expect 404
    print("\n[11] super_admin DELETE /api/peserta/nonexistent-id-123 -> expect 404")
    try:
        resp = requests.delete(f"{BASE_URL}/peserta/nonexistent-id-123",
            headers={"Authorization": f"Bearer {super_token}"})
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 404:
            print(f"    ❌ FAILED: Expected 404, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        print(f"    ✅ PASSED: DELETE nonexistent peserta returns 404")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during delete nonexistent: {e}")
        return False
    
    # Step 12: DELETE with NO Authorization header -> expect 401
    print("\n[12] DELETE /api/peserta/<any> with NO Authorization header -> expect 401")
    try:
        resp = requests.delete(f"{BASE_URL}/peserta/{lomba_id}")  # use lomba_id as dummy id
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 401:
            print(f"    ❌ FAILED: Expected 401, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        print(f"    ✅ PASSED: DELETE without token returns 401")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during delete without token: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ ALL DELETE /peserta/:id AUTHORIZATION TESTS PASSED")
    print("="*80)
    return True


def test_regression():
    """
    Quick regression tests:
    - GET /api/lomba (public) returns 200
    - super_admin login returns 200 with no password/token leak
    """
    print("\n" + "="*80)
    print("REGRESSION TESTS")
    print("="*80)
    
    # Test 1: GET /api/lomba (public)
    print("\n[R1] GET /api/lomba (public, no auth) -> expect 200")
    try:
        resp = requests.get(f"{BASE_URL}/lomba")
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        data = resp.json()
        if not isinstance(data, list):
            print(f"    ❌ FAILED: Expected array, got {type(data)}")
            return False
        print(f"    ✅ PASSED: GET /lomba returns 200 with array ({len(data)} items)")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during GET /lomba: {e}")
        return False
    
    # Test 2: super_admin login with no password/token leak
    print("\n[R2] super_admin login -> expect 200 with no password/token leak")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "super@porseni.id",
            "password": "admin123"
        })
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"    Response: {resp.text}")
            return False
        data = resp.json()
        token = data.get("token")
        user = data.get("user")
        if not token:
            print(f"    ❌ FAILED: No token in response")
            return False
        if not user:
            print(f"    ❌ FAILED: No user in response")
            return False
        # Check for leaks
        if "password" in user or "password_plain" in user or "token" in user or "_id" in user:
            print(f"    ❌ FAILED: User object contains sensitive fields: {user.keys()}")
            return False
        print(f"    ✅ PASSED: super_admin login successful, no sensitive data leaks")
    except Exception as e:
        print(f"    ❌ FAILED: Exception during super_admin login: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ ALL REGRESSION TESTS PASSED")
    print("="*80)
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("BACKEND TESTING: DELETE /peserta/:id Authorization Scoping")
    print("Base URL:", BASE_URL)
    print("="*80)
    
    all_passed = True
    
    # Run main authorization tests
    if not test_delete_peserta_authorization():
        all_passed = False
    
    # Run regression tests
    if not test_regression():
        all_passed = False
    
    if all_passed:
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED 🎉")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ SOME TESTS FAILED")
        print("="*80)
        sys.exit(1)
