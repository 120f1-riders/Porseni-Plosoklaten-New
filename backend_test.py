#!/usr/bin/env python3
"""
Quick backend regression sanity check after next.config.js change.
Tests only 3 core endpoints to verify no runtime regression.
"""

import requests
import json
import sys

BASE_URL = "https://e88698cc-dcb7-42a3-aad7-bdcca643ed32.preview.emergentagent.com/api"

def test_lomba_public():
    """Test 1: GET /api/lomba (public, no auth) returns 200 with JSON array"""
    print("\n=== TEST 1: GET /api/lomba (public) ===")
    try:
        response = requests.get(f"{BASE_URL}/lomba", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        if not isinstance(data, list):
            print(f"❌ FAILED: Expected JSON array, got {type(data)}")
            return False
        
        print(f"✅ PASSED: Returns 200 with JSON array (length: {len(data)})")
        return True
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        return False

def test_super_admin_login():
    """Test 2: POST /api/auth/login with super_admin credentials"""
    print("\n=== TEST 2: POST /api/auth/login (super_admin) ===")
    try:
        payload = {
            "email": "super@porseni.id",
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
        
        data = response.json()
        
        # Check for token
        if "token" not in data:
            print(f"❌ FAILED: No token in response")
            return False, None
        
        # Check for user object
        if "user" not in data:
            print(f"❌ FAILED: No user object in response")
            return False, None
        
        user = data["user"]
        token = data["token"]
        
        # Check for sensitive data leaks
        sensitive_fields = ["password", "password_plain", "token", "_id"]
        leaked = [field for field in sensitive_fields if field in user]
        if leaked:
            print(f"❌ FAILED: User object leaks sensitive fields: {leaked}")
            return False, None
        
        print(f"✅ PASSED: Returns 200 with token and user object (role: {user.get('role')})")
        print(f"✅ No sensitive data leaks (password/password_plain/token/_id not in user object)")
        return True, token
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        return False, None

def test_auth_me(token):
    """Test 3: GET /api/auth/me with Bearer token"""
    print("\n=== TEST 3: GET /api/auth/me (with Bearer token) ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Check it's the super_admin user
        if data.get("email") != "super@porseni.id":
            print(f"❌ FAILED: Expected super@porseni.id, got {data.get('email')}")
            return False
        
        if data.get("role") != "super_admin":
            print(f"❌ FAILED: Expected role super_admin, got {data.get('role')}")
            return False
        
        print(f"✅ PASSED: Returns 200 with super_admin user (email: {data.get('email')})")
        return True
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        return False

def main():
    print("=" * 60)
    print("BACKEND REGRESSION SANITY CHECK")
    print("Testing 3 core endpoints after next.config.js change")
    print("=" * 60)
    
    results = []
    
    # Test 1: Public lomba endpoint
    results.append(("GET /api/lomba (public)", test_lomba_public()))
    
    # Test 2: Super admin login
    login_passed, token = test_super_admin_login()
    results.append(("POST /api/auth/login (super_admin)", login_passed))
    
    # Test 3: Auth me (only if login succeeded)
    if login_passed and token:
        results.append(("GET /api/auth/me (Bearer token)", test_auth_me(token)))
    else:
        print("\n⚠️ SKIPPING TEST 3: Login failed, no token available")
        results.append(("GET /api/auth/me (Bearer token)", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - No regression detected")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed - Regression detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())
