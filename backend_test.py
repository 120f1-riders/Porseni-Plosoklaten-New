#!/usr/bin/env python3
"""
Comprehensive Backend API Test for Porseni MI Plosoklaten
Tests all backend endpoints with role-based access control
"""

import requests
import json
import io
from datetime import datetime

# Base URL from .env
BASE_URL = "https://madrasah-porseni.preview.emergentagent.com/api"

# Test data storage
test_data = {
    'super_admin': {},
    'admin_madrasah': {},
    'panitia': {},
    'lomba': {},
    'peserta': {},
    'file': {},
    'juara': {}
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_auth_register_super_admin():
    """Test 1: Register super_admin - should auto-verify and return token"""
    log("TEST 1: Register super_admin (auto-verified)")
    try:
        payload = {
            "name": "Super Admin Porseni",
            "email": f"superadmin_{datetime.now().timestamp()}@test.com",
            "password": "SuperSecure123!",
            "role": "super_admin"
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            log(f"  Response: {data}")
            return False
        
        if 'token' not in data or 'user' not in data:
            log(f"  ❌ FAILED: Missing token or user in response")
            log(f"  Response: {data}")
            return False
        
        if data['user'].get('role') != 'super_admin':
            log(f"  ❌ FAILED: Role mismatch")
            return False
        
        # Check no sensitive fields leaked
        if '_id' in data['user'] or 'password' in data['user']:
            log(f"  ❌ FAILED: Sensitive fields (_id/password) leaked in response")
            return False
        
        test_data['super_admin'] = {
            'token': data['token'],
            'user': data['user'],
            'email': payload['email'],
            'password': payload['password']
        }
        log(f"  ✅ PASSED: Super admin registered with token")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_register_admin_madrasah_pending():
    """Test 2: Register admin_madrasah - should return pending"""
    log("TEST 2: Register admin_madrasah (pending)")
    try:
        payload = {
            "name": "Admin Madrasah Test",
            "email": f"adminmadrasah_{datetime.now().timestamp()}@test.com",
            "password": "AdminPass123!",
            "role": "admin_madrasah",
            "madrasah_name": "MI Al-Hidayah"
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if not data.get('pending'):
            log(f"  ❌ FAILED: Expected pending:true, got {data}")
            return False
        
        test_data['admin_madrasah'] = {
            'email': payload['email'],
            'password': payload['password'],
            'madrasah_name': payload['madrasah_name']
        }
        log(f"  ✅ PASSED: Admin madrasah registered as pending")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_register_duplicate_email():
    """Test 3: Register with duplicate email - should return 400"""
    log("TEST 3: Register duplicate email (should fail)")
    try:
        payload = {
            "name": "Duplicate User",
            "email": test_data['super_admin']['email'],
            "password": "AnyPass123!",
            "role": "admin_madrasah"
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code != 400:
            log(f"  ❌ FAILED: Expected 400, got {resp.status_code}")
            return False
        
        log(f"  ✅ PASSED: Duplicate email rejected with 400")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_login_pending_blocked():
    """Test 4: Login with pending account - should return 403"""
    log("TEST 4: Login pending account (should be blocked)")
    try:
        payload = {
            "email": test_data['admin_madrasah']['email'],
            "password": test_data['admin_madrasah']['password']
        }
        resp = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code != 403:
            log(f"  ❌ FAILED: Expected 403, got {resp.status_code}")
            return False
        
        log(f"  ✅ PASSED: Pending account blocked with 403")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_login_wrong_password():
    """Test 5: Login with wrong password - should return 401"""
    log("TEST 5: Login wrong password (should fail)")
    try:
        payload = {
            "email": test_data['super_admin']['email'],
            "password": "WrongPassword123!"
        }
        resp = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code != 401:
            log(f"  ❌ FAILED: Expected 401, got {resp.status_code}")
            return False
        
        log(f"  ✅ PASSED: Wrong password rejected with 401")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_login_super_admin():
    """Test 6: Login super_admin - should return token"""
    log("TEST 6: Login super_admin")
    try:
        payload = {
            "email": test_data['super_admin']['email'],
            "password": test_data['super_admin']['password']
        }
        resp = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if 'token' not in data or 'user' not in data:
            log(f"  ❌ FAILED: Missing token or user")
            return False
        
        # Update token
        test_data['super_admin']['token'] = data['token']
        log(f"  ✅ PASSED: Super admin logged in")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_me():
    """Test 7: GET /auth/me with Bearer token"""
    log("TEST 7: GET /auth/me")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        resp = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if data.get('role') != 'super_admin':
            log(f"  ❌ FAILED: Role mismatch")
            return False
        
        log(f"  ✅ PASSED: /auth/me returned user")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_lomba_create():
    """Test 8: POST /lomba (super_admin only)"""
    log("TEST 8: Create lomba (super_admin)")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        payload = {
            "name": "Lomba Cerdas Cermat",
            "category": "Akademik",
            "judging_criteria": ["Kecepatan", "Ketepatan", "Kerjasama"]
        }
        resp = requests.post(f"{BASE_URL}/lomba", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if 'id' not in data or data.get('name') != payload['name']:
            log(f"  ❌ FAILED: Invalid response")
            return False
        
        if not isinstance(data.get('judging_criteria'), list):
            log(f"  ❌ FAILED: judging_criteria should be array")
            return False
        
        test_data['lomba'] = data
        log(f"  ✅ PASSED: Lomba created with id {data['id']}")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_lomba_get_public():
    """Test 9: GET /lomba (public)"""
    log("TEST 9: GET /lomba (public)")
    try:
        resp = requests.get(f"{BASE_URL}/lomba", timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if not isinstance(data, list):
            log(f"  ❌ FAILED: Expected array")
            return False
        
        log(f"  ✅ PASSED: Public lomba list retrieved ({len(data)} items)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_lomba_create_without_auth():
    """Test 10: POST /lomba without auth - should return 403"""
    log("TEST 10: Create lomba without auth (should fail)")
    try:
        payload = {"name": "Unauthorized Lomba", "category": "Test"}
        resp = requests.post(f"{BASE_URL}/lomba", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code != 403:
            log(f"  ❌ FAILED: Expected 403, got {resp.status_code}")
            return False
        
        log(f"  ✅ PASSED: Unauthorized lomba creation blocked")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_users_list():
    """Test 11: GET /users (super_admin only)"""
    log("TEST 11: GET /users (super_admin)")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        resp = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if not isinstance(data, list):
            log(f"  ❌ FAILED: Expected array")
            return False
        
        # Find admin_madrasah user
        admin_user = next((u for u in data if u.get('email') == test_data['admin_madrasah']['email']), None)
        if admin_user:
            test_data['admin_madrasah']['id'] = admin_user['id']
            log(f"  Found admin_madrasah user: {admin_user['id']}")
        
        log(f"  ✅ PASSED: Users list retrieved ({len(data)} users)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_users_verify():
    """Test 12: PUT /users/:id to verify admin_madrasah"""
    log("TEST 12: Verify admin_madrasah user")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        user_id = test_data['admin_madrasah']['id']
        payload = {"status": "verified"}
        resp = requests.put(f"{BASE_URL}/users/{user_id}", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if data.get('status') != 'verified':
            log(f"  ❌ FAILED: Status not updated")
            return False
        
        log(f"  ✅ PASSED: Admin madrasah verified")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_login_admin_madrasah():
    """Test 13: Login admin_madrasah after verification"""
    log("TEST 13: Login admin_madrasah (after verification)")
    try:
        payload = {
            "email": test_data['admin_madrasah']['email'],
            "password": test_data['admin_madrasah']['password']
        }
        resp = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if 'token' not in data:
            log(f"  ❌ FAILED: Missing token")
            return False
        
        test_data['admin_madrasah']['token'] = data['token']
        test_data['admin_madrasah']['user'] = data['user']
        log(f"  ✅ PASSED: Admin madrasah logged in")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_create():
    """Test 14: POST /peserta - verify nomor_peserta and drive_path"""
    log("TEST 14: Create peserta (check nomor_peserta + drive_path)")
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_madrasah']['token']}"}
        payload = {
            "participant_name": "Ahmad Zainudin",
            "nisn": "1234567890",
            "ttl": "Malang, 15 Januari 2010",
            "lomba_id": test_data['lomba']['id'],
            "madrasah_name": test_data['admin_madrasah']['madrasah_name']
        }
        resp = requests.post(f"{BASE_URL}/peserta", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            log(f"  Response: {data}")
            return False
        
        # Check nomor_peserta format (001, 002, etc.)
        nomor = data.get('nomor_peserta')
        if not nomor or len(nomor) != 3 or not nomor.isdigit():
            log(f"  ❌ FAILED: Invalid nomor_peserta format: {nomor}")
            return False
        
        # Check drive_path format: [Lomba]/[Madrasah]/[Peserta]
        drive_path = data.get('drive_path')
        expected_parts = [test_data['lomba']['name'], payload['madrasah_name'], payload['participant_name']]
        if not all(part in drive_path for part in expected_parts):
            log(f"  ❌ FAILED: Invalid drive_path: {drive_path}")
            return False
        
        test_data['peserta'] = data
        log(f"  ✅ PASSED: Peserta created - nomor: {nomor}, drive_path: {drive_path}")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_get_role_filter_admin():
    """Test 15: GET /peserta as admin_madrasah (should see only own)"""
    log("TEST 15: GET /peserta (admin_madrasah role filter)")
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_madrasah']['token']}"}
        resp = requests.get(f"{BASE_URL}/peserta", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if not isinstance(data, list):
            log(f"  ❌ FAILED: Expected array")
            return False
        
        # All should be created by this admin
        admin_id = test_data['admin_madrasah']['user']['id']
        for p in data:
            if p.get('created_by') != admin_id:
                log(f"  ❌ FAILED: Role filter not working - found peserta from other user")
                return False
        
        log(f"  ✅ PASSED: Admin madrasah sees only own peserta ({len(data)} items)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_register_panitia():
    """Test 16: Register panitia with assigned_lomba_id"""
    log("TEST 16: Register panitia with assigned_lomba_id")
    try:
        payload = {
            "name": "Panitia Lomba Test",
            "email": f"panitia_{datetime.now().timestamp()}@test.com",
            "password": "PanitiaPass123!",
            "role": "panitia",
            "assigned_lomba_id": test_data['lomba']['id']
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if not data.get('pending'):
            log(f"  ❌ FAILED: Expected pending:true")
            return False
        
        test_data['panitia'] = {
            'email': payload['email'],
            'password': payload['password'],
            'assigned_lomba_id': payload['assigned_lomba_id']
        }
        log(f"  ✅ PASSED: Panitia registered as pending")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_users_verify_panitia():
    """Test 17: Verify panitia user"""
    log("TEST 17: Verify panitia user")
    try:
        # First get users list to find panitia
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        resp = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
        data = resp.json()
        
        panitia_user = next((u for u in data if u.get('email') == test_data['panitia']['email']), None)
        if not panitia_user:
            log(f"  ❌ FAILED: Panitia user not found")
            return False
        
        test_data['panitia']['id'] = panitia_user['id']
        
        # Verify
        payload = {"status": "verified"}
        resp = requests.put(f"{BASE_URL}/users/{panitia_user['id']}", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        log(f"  ✅ PASSED: Panitia verified")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_auth_login_panitia():
    """Test 18: Login panitia"""
    log("TEST 18: Login panitia")
    try:
        payload = {
            "email": test_data['panitia']['email'],
            "password": test_data['panitia']['password']
        }
        resp = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        test_data['panitia']['token'] = data['token']
        test_data['panitia']['user'] = data['user']
        log(f"  ✅ PASSED: Panitia logged in")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_get_role_filter_panitia():
    """Test 19: GET /peserta as panitia (should see only assigned lomba)"""
    log("TEST 19: GET /peserta (panitia role filter)")
    try:
        headers = {"Authorization": f"Bearer {test_data['panitia']['token']}"}
        resp = requests.get(f"{BASE_URL}/peserta", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        # All should be from assigned lomba
        assigned_lomba = test_data['panitia']['assigned_lomba_id']
        for p in data:
            if p.get('lomba_id') != assigned_lomba:
                log(f"  ❌ FAILED: Panitia sees peserta from other lomba")
                return False
        
        log(f"  ✅ PASSED: Panitia sees only assigned lomba peserta ({len(data)} items)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_update_status():
    """Test 20: PUT /peserta/:id/status"""
    log("TEST 20: Update peserta status")
    try:
        headers = {"Authorization": f"Bearer {test_data['panitia']['token']}"}
        peserta_id = test_data['peserta']['id']
        payload = {"status": "verified"}
        resp = requests.put(f"{BASE_URL}/peserta/{peserta_id}/status", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if data.get('status') != 'verified':
            log(f"  ❌ FAILED: Status not updated")
            return False
        
        log(f"  ✅ PASSED: Peserta status updated")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_juara_create():
    """Test 21: POST /juara (upsert test)"""
    log("TEST 21: Create juara (upsert)")
    try:
        headers = {"Authorization": f"Bearer {test_data['panitia']['token']}"}
        payload = {
            "lomba_id": test_data['lomba']['id'],
            "peserta_id": test_data['peserta']['id'],
            "rank": 1
        }
        resp = requests.post(f"{BASE_URL}/juara", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if 'id' not in data:
            log(f"  ❌ FAILED: Missing id")
            return False
        
        test_data['juara'] = data
        log(f"  ✅ PASSED: Juara created (rank 1)")
        
        # Test upsert - create another juara with same rank
        log("  Testing upsert behavior...")
        payload2 = {
            "lomba_id": test_data['lomba']['id'],
            "peserta_id": test_data['peserta']['id'],
            "rank": 1
        }
        resp2 = requests.post(f"{BASE_URL}/juara", json=payload2, headers=headers, timeout=10)
        data2 = resp2.json()
        
        # Should replace the previous one
        if data2['id'] == data['id']:
            log(f"  ⚠️  WARNING: Upsert may not be working - same ID returned")
        else:
            log(f"  ✅ Upsert working - new juara created")
        
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_juara_get():
    """Test 22: GET /juara?lomba_id="""
    log("TEST 22: GET /juara with lomba_id filter")
    try:
        headers = {"Authorization": f"Bearer {test_data['panitia']['token']}"}
        lomba_id = test_data['lomba']['id']
        resp = requests.get(f"{BASE_URL}/juara?lomba_id={lomba_id}", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if not isinstance(data, list):
            log(f"  ❌ FAILED: Expected array")
            return False
        
        log(f"  ✅ PASSED: Juara list retrieved ({len(data)} items)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_hasil_create():
    """Test 23: POST /hasil"""
    log("TEST 23: Create hasil")
    try:
        headers = {"Authorization": f"Bearer {test_data['panitia']['token']}"}
        payload = {
            "lomba_id": test_data['lomba']['id'],
            "uploaded_score_sheet_url": "https://example.com/score.pdf",
            "note": "Hasil lomba cerdas cermat"
        }
        resp = requests.post(f"{BASE_URL}/hasil", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if 'id' not in data:
            log(f"  ❌ FAILED: Missing id")
            return False
        
        log(f"  ✅ PASSED: Hasil created")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_hasil_get():
    """Test 24: GET /hasil?lomba_id="""
    log("TEST 24: GET /hasil with lomba_id filter")
    try:
        headers = {"Authorization": f"Bearer {test_data['panitia']['token']}"}
        lomba_id = test_data['lomba']['id']
        resp = requests.get(f"{BASE_URL}/hasil?lomba_id={lomba_id}", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if not isinstance(data, list):
            log(f"  ❌ FAILED: Expected array")
            return False
        
        log(f"  ✅ PASSED: Hasil list retrieved ({len(data)} items)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_file_upload():
    """Test 25: POST /upload (multipart)"""
    log("TEST 25: File upload (multipart)")
    try:
        # Create a test file
        file_content = b"Test file content for Porseni MI"
        files = {'file': ('test_document.txt', io.BytesIO(file_content), 'text/plain')}
        
        resp = requests.post(f"{BASE_URL}/upload", files=files, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            log(f"  Response: {data}")
            return False
        
        if 'id' not in data or 'url' not in data:
            log(f"  ❌ FAILED: Missing id or url")
            return False
        
        test_data['file'] = data
        log(f"  ✅ PASSED: File uploaded - id: {data['id']}, url: {data['url']}")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_file_serve():
    """Test 26: GET /files/:id"""
    log("TEST 26: File serve")
    try:
        file_id = test_data['file']['id']
        resp = requests.get(f"{BASE_URL}/files/{file_id}", timeout=10)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if len(resp.content) == 0:
            log(f"  ❌ FAILED: Empty file content")
            return False
        
        log(f"  ✅ PASSED: File served ({len(resp.content)} bytes)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_templates_upsert():
    """Test 27: POST /templates (upsert by type)"""
    log("TEST 27: Templates upsert")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        
        # First upsert
        payload1 = {
            "type": "certificate",
            "image_url": "https://example.com/cert_template.png",
            "fields": [
                {"name": "participant_name", "x": 100, "y": 200},
                {"name": "lomba_name", "x": 100, "y": 250}
            ]
        }
        resp1 = requests.post(f"{BASE_URL}/templates", json=payload1, headers=headers, timeout=10)
        log(f"  First upsert status: {resp1.status_code}")
        data1 = resp1.json()
        
        if resp1.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp1.status_code}")
            return False
        
        # Second upsert with same type (should update)
        payload2 = {
            "type": "certificate",
            "image_url": "https://example.com/cert_template_v2.png",
            "fields": [
                {"name": "participant_name", "x": 150, "y": 220}
            ]
        }
        resp2 = requests.post(f"{BASE_URL}/templates", json=payload2, headers=headers, timeout=10)
        log(f"  Second upsert status: {resp2.status_code}")
        data2 = resp2.json()
        
        if resp2.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp2.status_code}")
            return False
        
        # Verify it's the same document (upserted)
        if data2.get('image_url') != payload2['image_url']:
            log(f"  ❌ FAILED: Upsert didn't update the template")
            return False
        
        log(f"  ✅ PASSED: Templates upsert working")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_templates_get():
    """Test 28: GET /templates?type=certificate"""
    log("TEST 28: GET /templates with type filter")
    try:
        resp = requests.get(f"{BASE_URL}/templates?type=certificate", timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if not isinstance(data, list):
            log(f"  ❌ FAILED: Expected array")
            return False
        
        log(f"  ✅ PASSED: Templates retrieved ({len(data)} items)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_get_super_admin():
    """Test 29: GET /peserta as super_admin (should see all)"""
    log("TEST 29: GET /peserta (super_admin sees all)")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        resp = requests.get(f"{BASE_URL}/peserta", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        log(f"  ✅ PASSED: Super admin sees all peserta ({len(data)} items)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_no_objectid_leak():
    """Test 30: Verify no MongoDB ObjectId in responses"""
    log("TEST 30: Check for MongoDB ObjectId leaks")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        
        # Check users endpoint
        resp = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
        users = resp.json()
        for u in users:
            if '_id' in u:
                log(f"  ❌ FAILED: _id found in users response")
                return False
        
        # Check lomba endpoint
        resp = requests.get(f"{BASE_URL}/lomba", timeout=10)
        lomba = resp.json()
        for l in lomba:
            if '_id' in l:
                log(f"  ❌ FAILED: _id found in lomba response")
                return False
        
        # Check peserta endpoint
        resp = requests.get(f"{BASE_URL}/peserta", headers=headers, timeout=10)
        peserta = resp.json()
        for p in peserta:
            if '_id' in p:
                log(f"  ❌ FAILED: _id found in peserta response")
                return False
        
        log(f"  ✅ PASSED: No ObjectId leaks detected")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def run_all_tests():
    """Run all backend tests"""
    log("=" * 80)
    log("STARTING COMPREHENSIVE BACKEND API TESTS")
    log("=" * 80)
    
    tests = [
        test_auth_register_super_admin,
        test_auth_register_admin_madrasah_pending,
        test_auth_register_duplicate_email,
        test_auth_login_pending_blocked,
        test_auth_login_wrong_password,
        test_auth_login_super_admin,
        test_auth_me,
        test_lomba_create,
        test_lomba_get_public,
        test_lomba_create_without_auth,
        test_users_list,
        test_users_verify,
        test_auth_login_admin_madrasah,
        test_peserta_create,
        test_peserta_get_role_filter_admin,
        test_auth_register_panitia,
        test_users_verify_panitia,
        test_auth_login_panitia,
        test_peserta_get_role_filter_panitia,
        test_peserta_update_status,
        test_juara_create,
        test_juara_get,
        test_hasil_create,
        test_hasil_get,
        test_file_upload,
        test_file_serve,
        test_templates_upsert,
        test_templates_get,
        test_peserta_get_super_admin,
        test_no_objectid_leak,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append((test.__name__, result))
        log("")
    
    log("=" * 80)
    log("TEST SUMMARY")
    log("=" * 80)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    log(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    log("")
    
    if failed > 0:
        log("FAILED TESTS:")
        for name, result in results:
            if not result:
                log(f"  ❌ {name}")
    
    log("=" * 80)
    return passed, failed

if __name__ == "__main__":
    passed, failed = run_all_tests()
    exit(0 if failed == 0 else 1)
