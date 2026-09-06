#!/usr/bin/env python3
"""
Quick backend regression sanity check after build config changes.
Tests only 3 core endpoints to verify runtime behavior unchanged.
"""
import requests
import json
import sys

BASE_URL = "https://e88698cc-dcb7-42a3-aad7-bdcca643ed32.preview.emergentagent.com/api"

def test_lomba_public():
    """Test 1: GET /api/lomba (public, no auth) returns HTTP 200 with JSON array"""
    print("\n=== TEST 1: GET /api/lomba (public) ===")
    try:
        response = requests.get(f"{BASE_URL}/lomba", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        print(f"Response type: {type(data)}")
        
        if not isinstance(data, list):
            print(f"❌ FAILED: Expected JSON array, got {type(data)}")
            return False
        
        print(f"✅ PASSED: GET /api/lomba returns 200 with JSON array (length: {len(data)})")
        return True
    except Exception as e:
        print(f"❌ FAILED: Exception - {str(e)}")
        return False

def test_login_no_leak():
    """Test 2: POST /api/auth/login returns 200 with token, NO password/password_plain/token leak in user object"""
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
        print(f"Response keys: {list(data.keys())}")
        
        # Check token exists
        if 'token' not in data:
            print(f"❌ FAILED: No 'token' field in response")
            return False, None
        
        token = data['token']
        print(f"Token received: {token[:20]}...")
        
        # Check user object exists
        if 'user' not in data:
            print(f"❌ FAILED: No 'user' field in response")
            return False, None
        
        user = data['user']
        print(f"User object keys: {list(user.keys())}")
        
        # Check for sensitive data leaks
        sensitive_fields = ['password', 'password_plain', 'token', '_id']
        leaked = [f for f in sensitive_fields if f in user]
        
        if leaked:
            print(f"❌ FAILED: User object leaks sensitive fields: {leaked}")
            return False, None
        
        # Check role
        if user.get('role') != 'super_admin':
            print(f"❌ FAILED: Expected role 'super_admin', got '{user.get('role')}'")
            return False, None
        
        print(f"✅ PASSED: Login returns 200 with token, user object has NO password/password_plain/token/_id leak")
        print(f"User role: {user.get('role')}, email: {user.get('email')}")
        return True, token
    except Exception as e:
        print(f"❌ FAILED: Exception - {str(e)}")
        return False, None

def test_auth_me(token):
    """Test 3: GET /api/auth/me with Bearer token returns 200 with super_admin user"""
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
        print(f"Response keys: {list(data.keys())}")
        
        # Check email
        if data.get('email') != 'super@porseni.id':
            print(f"❌ FAILED: Expected email 'super@porseni.id', got '{data.get('email')}'")
            return False
        
        # Check role
        if data.get('role') != 'super_admin':
            print(f"❌ FAILED: Expected role 'super_admin', got '{data.get('role')}'")
            return False
        
        print(f"✅ PASSED: /auth/me returns 200 with super_admin user")
        print(f"User: {data.get('email')}, role: {data.get('role')}")
        return True
    except Exception as e:
        print(f"❌ FAILED: Exception - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("REGRESSION SANITY CHECK - Build Config Changes")
    print("Testing 3 core endpoints after package.json + next.config.js changes")
    print("=" * 60)
    
    results = []
    
    # Test 1: Public lomba endpoint
    results.append(("GET /api/lomba (public)", test_lomba_public()))
    
    # Test 2: Login with no leak
    login_result, token = test_login_no_leak()
    results.append(("POST /api/auth/login (no leak)", login_result))
    
    # Test 3: Auth me (only if login succeeded)
    if token:
        results.append(("GET /api/auth/me (Bearer)", test_auth_me(token)))
    else:
        print("\n⚠️ SKIPPED: GET /api/auth/me (login failed, no token)")
        results.append(("GET /api/auth/me (Bearer)", False))
    
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
        print("\n🎉 ALL REGRESSION TESTS PASSED - No runtime impact from build config changes")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed - Potential regression detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())
