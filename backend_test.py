#!/usr/bin/env python3
"""
Backend API Test for SIM Porseni MI - Testing Recent Changes
Focus: Lomba type field, Peserta gender+complete, Panitia visibility, Juara group support
"""

import requests
import json
from datetime import datetime

# Base URL
BASE_URL = "https://event-checklist-5.preview.emergentagent.com/api"

# Test data storage
test_data = {
    'super_admin': {'email': 'super@porseni.id', 'password': 'admin123'},
    'admin_madrasah': {},
    'panitia': {},
    'lomba_individu': {},
    'lomba_kelompok': {},
    'peserta_incomplete': {},
    'peserta_complete': {},
    'peserta_no_gender': {},
    'files': {}
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_super_admin_login():
    """Test: Login as seeded super admin"""
    log("TEST: Login super admin (super@porseni.id)")
    try:
        payload = {
            "email": test_data['super_admin']['email'],
            "password": test_data['super_admin']['password']
        }
        resp = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        log(f"  Status: {resp.status_code}")
        
        if resp.status_code == 401:
            # Try to register if login fails
            log("  Login failed, attempting to register super_admin...")
            reg_payload = {
                "name": "Super Admin",
                "email": test_data['super_admin']['email'],
                "password": test_data['super_admin']['password'],
                "role": "super_admin"
            }
            resp = requests.post(f"{BASE_URL}/auth/register", json=reg_payload, timeout=10)
            log(f"  Register status: {resp.status_code}")
            data = resp.json()
            if resp.status_code != 200 or 'token' not in data:
                log(f"  ❌ FAILED: Cannot register super_admin: {data}")
                return False
            test_data['super_admin']['token'] = data['token']
            log(f"  ✅ Super admin registered and logged in")
            return True
        
        data = resp.json()
        if resp.status_code != 200 or 'token' not in data:
            log(f"  ❌ FAILED: {data}")
            return False
        
        test_data['super_admin']['token'] = data['token']
        log(f"  ✅ PASSED: Super admin logged in")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

# ============================================================================
# LOMBA TYPE FIELD TESTS
# ============================================================================

def test_lomba_create_with_type_individu():
    """Test: POST /lomba with type:'individu'"""
    log("TEST: Create lomba with type='individu'")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        payload = {
            "name": "Kaligrafi",
            "category": "Seni",
            "type": "individu",
            "judging_criteria": ["Kerapian", "Keindahan"]
        }
        resp = requests.post(f"{BASE_URL}/lomba", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('type') != 'individu':
            log(f"  ❌ FAILED: Expected type='individu', got '{data.get('type')}'")
            return False
        
        test_data['lomba_individu'] = data
        log(f"  ✅ PASSED: Lomba created with type='individu', id={data['id']}")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_lomba_create_with_type_kelompok():
    """Test: POST /lomba with type:'kelompok'"""
    log("TEST: Create lomba with type='kelompok'")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        payload = {
            "name": "Cerdas Cermat",
            "category": "Seni",
            "type": "kelompok"
        }
        resp = requests.post(f"{BASE_URL}/lomba", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('type') != 'kelompok':
            log(f"  ❌ FAILED: Expected type='kelompok', got '{data.get('type')}'")
            return False
        
        test_data['lomba_kelompok'] = data
        log(f"  ✅ PASSED: Lomba created with type='kelompok', id={data['id']}")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_lomba_create_without_type():
    """Test: POST /lomba WITHOUT type (should default to 'individu')"""
    log("TEST: Create lomba WITHOUT type (default to 'individu')")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        payload = {
            "name": "Lomba Default Type",
            "category": "Olahraga"
        }
        resp = requests.post(f"{BASE_URL}/lomba", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('type') != 'individu':
            log(f"  ❌ FAILED: Expected default type='individu', got '{data.get('type')}'")
            return False
        
        log(f"  ✅ PASSED: Lomba defaults to type='individu'")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_lomba_update_type():
    """Test: PUT /lomba/:id changing type from individu to kelompok"""
    log("TEST: Update lomba type from 'individu' to 'kelompok'")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        lomba_id = test_data['lomba_individu']['id']
        payload = {"type": "kelompok"}
        resp = requests.put(f"{BASE_URL}/lomba/{lomba_id}", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('type') != 'kelompok':
            log(f"  ❌ FAILED: Type not updated, got '{data.get('type')}'")
            return False
        
        # Revert back to individu for later tests
        payload2 = {"type": "individu"}
        resp2 = requests.put(f"{BASE_URL}/lomba/{lomba_id}", json=payload2, headers=headers, timeout=10)
        
        log(f"  ✅ PASSED: Lomba type updated successfully")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_lomba_get_returns_type():
    """Test: GET /lomba returns type field on each lomba"""
    log("TEST: GET /lomba returns type field")
    try:
        resp = requests.get(f"{BASE_URL}/lomba", timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if not isinstance(data, list) or len(data) == 0:
            log(f"  ❌ FAILED: Expected non-empty array")
            return False
        
        for lomba in data:
            if 'type' not in lomba:
                log(f"  ❌ FAILED: Lomba missing 'type' field: {lomba}")
                return False
        
        log(f"  ✅ PASSED: All lomba have type field ({len(data)} lomba)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

# ============================================================================
# PESERTA GENDER + COMPLETE FLAG TESTS
# ============================================================================

def test_create_admin_madrasah():
    """Test: Create and verify admin_madrasah user"""
    log("TEST: Create admin_madrasah user")
    try:
        # Register
        payload = {
            "name": "Admin MI Al-Hidayah",
            "email": f"admin_{datetime.now().timestamp()}@alhidayah.sch.id",
            "password": "AdminPass123!",
            "role": "admin_madrasah",
            "madrasah_name": "MI Al-Hidayah"
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        log(f"  Register status: {resp.status_code}")
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Registration failed")
            return False
        
        test_data['admin_madrasah']['email'] = payload['email']
        test_data['admin_madrasah']['password'] = payload['password']
        test_data['admin_madrasah']['madrasah_name'] = payload['madrasah_name']
        
        # Get user ID
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        resp = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
        users = resp.json()
        admin_user = next((u for u in users if u.get('email') == payload['email']), None)
        
        if not admin_user:
            log(f"  ❌ FAILED: Admin user not found")
            return False
        
        # Verify user
        verify_payload = {"status": "verified"}
        resp = requests.put(f"{BASE_URL}/users/{admin_user['id']}", json=verify_payload, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Verification failed")
            return False
        
        # Login
        login_payload = {"email": payload['email'], "password": payload['password']}
        resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=10)
        data = resp.json()
        
        if resp.status_code != 200 or 'token' not in data:
            log(f"  ❌ FAILED: Login failed")
            return False
        
        test_data['admin_madrasah']['token'] = data['token']
        test_data['admin_madrasah']['id'] = data['user']['id']
        log(f"  ✅ PASSED: Admin madrasah created and verified")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_create_incomplete():
    """Test: POST /peserta with gender='L' but no files => complete:false"""
    log("TEST: Create peserta with gender='L', no files => complete:false")
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_madrasah']['token']}"}
        payload = {
            "participant_name": "Ahmad Zainudin",
            "gender": "L",
            "lomba_id": test_data['lomba_individu']['id'],
            "files": {}
        }
        resp = requests.post(f"{BASE_URL}/peserta", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('gender') != 'L':
            log(f"  ❌ FAILED: Expected gender='L', got '{data.get('gender')}'")
            return False
        
        if data.get('complete') != False:
            log(f"  ❌ FAILED: Expected complete=false, got {data.get('complete')}")
            return False
        
        if not data.get('nomor_peserta'):
            log(f"  ❌ FAILED: nomor_peserta not auto-generated")
            return False
        
        test_data['peserta_incomplete'] = data
        log(f"  ✅ PASSED: Peserta created - gender='L', complete=false, nomor={data['nomor_peserta']}")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_create_complete():
    """Test: POST /peserta with gender='P' and all files => complete:true"""
    log("TEST: Create peserta with gender='P' and all files => complete:true")
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_madrasah']['token']}"}
        payload = {
            "participant_name": "Fatimah Azzahra",
            "gender": "P",
            "lomba_id": test_data['lomba_individu']['id'],
            "files": {
                "akte": {"id": "file-akte-123", "name": "akte.pdf"},
                "surat_ket": {"id": "file-surat-456", "name": "surat_ket.pdf"},
                "pas_photo": {"id": "file-photo-789", "name": "photo.jpg"}
            }
        }
        resp = requests.post(f"{BASE_URL}/peserta", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('gender') != 'P':
            log(f"  ❌ FAILED: Expected gender='P', got '{data.get('gender')}'")
            return False
        
        if data.get('complete') != True:
            log(f"  ❌ FAILED: Expected complete=true, got {data.get('complete')}")
            return False
        
        test_data['peserta_complete'] = data
        log(f"  ✅ PASSED: Peserta created - gender='P', complete=true")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_create_without_gender():
    """Test: POST /peserta WITHOUT gender => gender='' and complete:false"""
    log("TEST: Create peserta WITHOUT gender => gender='', complete=false")
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_madrasah']['token']}"}
        payload = {
            "participant_name": "Peserta No Gender",
            "lomba_id": test_data['lomba_individu']['id'],
            "files": {
                "akte": {"id": "file-akte-999", "name": "akte.pdf"},
                "surat_ket": {"id": "file-surat-999", "name": "surat_ket.pdf"},
                "pas_photo": {"id": "file-photo-999", "name": "photo.jpg"}
            }
        }
        resp = requests.post(f"{BASE_URL}/peserta", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('gender') != '':
            log(f"  ❌ FAILED: Expected gender='', got '{data.get('gender')}'")
            return False
        
        if data.get('complete') != False:
            log(f"  ❌ FAILED: Expected complete=false (missing gender), got {data.get('complete')}")
            return False
        
        test_data['peserta_no_gender'] = data
        log(f"  ✅ PASSED: Peserta without gender => gender='', complete=false")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_update_to_complete():
    """Test: PUT /peserta/:id to add all files => complete becomes true"""
    log("TEST: Update incomplete peserta with all files => complete=true")
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_madrasah']['token']}"}
        peserta_id = test_data['peserta_incomplete']['id']
        payload = {
            "files": {
                "akte": {"id": "file-akte-111", "name": "akte.pdf"},
                "surat_ket": {"id": "file-surat-222", "name": "surat_ket.pdf"},
                "pas_photo": {"id": "file-photo-333", "name": "photo.jpg"}
            }
        }
        resp = requests.put(f"{BASE_URL}/peserta/{peserta_id}", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('complete') != True:
            log(f"  ❌ FAILED: Expected complete=true after adding files, got {data.get('complete')}")
            return False
        
        log(f"  ✅ PASSED: Peserta updated - complete=true after adding files")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_peserta_update_lomba_id():
    """Test: PUT /peserta/:id changing lomba_id updates lomba_name"""
    log("TEST: Update peserta lomba_id => lomba_name updated")
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_madrasah']['token']}"}
        peserta_id = test_data['peserta_complete']['id']
        payload = {"lomba_id": test_data['lomba_kelompok']['id']}
        resp = requests.put(f"{BASE_URL}/peserta/{peserta_id}", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('lomba_name') != test_data['lomba_kelompok']['name']:
            log(f"  ❌ FAILED: lomba_name not updated, expected '{test_data['lomba_kelompok']['name']}', got '{data.get('lomba_name')}'")
            return False
        
        # Revert back
        payload2 = {"lomba_id": test_data['lomba_individu']['id']}
        requests.put(f"{BASE_URL}/peserta/{peserta_id}", json=payload2, headers=headers, timeout=10)
        
        log(f"  ✅ PASSED: lomba_name updated when lomba_id changed")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

# ============================================================================
# PANITIA VISIBILITY FILTER TESTS
# ============================================================================

def test_create_panitia():
    """Test: Create and verify panitia user"""
    log("TEST: Create panitia user with assigned_lomba_id")
    try:
        # Register
        payload = {
            "name": "Panitia Kaligrafi",
            "email": f"panitia_{datetime.now().timestamp()}@porseni.id",
            "password": "PanitiaPass123!",
            "role": "panitia",
            "assigned_lomba_id": test_data['lomba_individu']['id']
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
        log(f"  Register status: {resp.status_code}")
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Registration failed")
            return False
        
        test_data['panitia']['email'] = payload['email']
        test_data['panitia']['password'] = payload['password']
        test_data['panitia']['assigned_lomba_id'] = payload['assigned_lomba_id']
        
        # Get user ID and verify
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        resp = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
        users = resp.json()
        panitia_user = next((u for u in users if u.get('email') == payload['email']), None)
        
        if not panitia_user:
            log(f"  ❌ FAILED: Panitia user not found")
            return False
        
        verify_payload = {"status": "verified"}
        resp = requests.put(f"{BASE_URL}/users/{panitia_user['id']}", json=verify_payload, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: Verification failed")
            return False
        
        # Login
        login_payload = {"email": payload['email'], "password": payload['password']}
        resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=10)
        data = resp.json()
        
        if resp.status_code != 200 or 'token' not in data:
            log(f"  ❌ FAILED: Login failed")
            return False
        
        test_data['panitia']['token'] = data['token']
        log(f"  ✅ PASSED: Panitia created and verified")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_panitia_visibility_filter():
    """Test: GET /peserta as panitia => only complete:true peserta of assigned lomba"""
    log("TEST: Panitia GET /peserta => only complete peserta of assigned lomba")
    try:
        headers = {"Authorization": f"Bearer {test_data['panitia']['token']}"}
        resp = requests.get(f"{BASE_URL}/peserta", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if not isinstance(data, list):
            log(f"  ❌ FAILED: Expected array")
            return False
        
        assigned_lomba = test_data['panitia']['assigned_lomba_id']
        
        # Check all peserta are from assigned lomba AND complete=true
        for p in data:
            if p.get('lomba_id') != assigned_lomba:
                log(f"  ❌ FAILED: Panitia sees peserta from other lomba: {p['id']}")
                return False
            if p.get('complete') != True:
                log(f"  ❌ FAILED: Panitia sees incomplete peserta: {p['id']}, complete={p.get('complete')}")
                return False
        
        # Verify incomplete peserta (no gender) is NOT in the list
        incomplete_id = test_data['peserta_no_gender']['id']
        if any(p['id'] == incomplete_id for p in data):
            log(f"  ❌ FAILED: Panitia should NOT see incomplete peserta (no gender)")
            return False
        
        log(f"  ✅ PASSED: Panitia sees only complete peserta of assigned lomba ({len(data)} peserta)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_admin_madrasah_sees_all_own():
    """Test: GET /peserta as admin_madrasah => sees all own (complete + incomplete)"""
    log("TEST: Admin madrasah GET /peserta => sees all own peserta")
    try:
        headers = {"Authorization": f"Bearer {test_data['admin_madrasah']['token']}"}
        resp = requests.get(f"{BASE_URL}/peserta", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        # Should see both complete and incomplete
        has_complete = any(p['id'] == test_data['peserta_complete']['id'] for p in data)
        has_incomplete = any(p['id'] == test_data['peserta_incomplete']['id'] for p in data)
        
        if not has_complete or not has_incomplete:
            log(f"  ❌ FAILED: Admin madrasah should see both complete and incomplete peserta")
            return False
        
        log(f"  ✅ PASSED: Admin madrasah sees all own peserta ({len(data)} peserta)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_super_admin_sees_all():
    """Test: GET /peserta as super_admin => sees all peserta"""
    log("TEST: Super admin GET /peserta => sees all peserta")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        resp = requests.get(f"{BASE_URL}/peserta", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        log(f"  ✅ PASSED: Super admin sees all peserta ({len(data)} peserta)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

# ============================================================================
# JUARA GROUP SUPPORT TESTS
# ============================================================================

def test_juara_create_group():
    """Test: POST /juara for kelompok lomba with is_group:true"""
    log("TEST: Create group juara for kelompok lomba")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        payload = {
            "lomba_id": test_data['lomba_kelompok']['id'],
            "rank": "Juara 1",
            "madrasah_name": "MI Al-Hidayah",
            "is_group": True
        }
        resp = requests.post(f"{BASE_URL}/juara", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('is_group') != True:
            log(f"  ❌ FAILED: Expected is_group=true, got {data.get('is_group')}")
            return False
        
        if data.get('madrasah_name') != "MI Al-Hidayah":
            log(f"  ❌ FAILED: Expected madrasah_name='MI Al-Hidayah', got '{data.get('madrasah_name')}'")
            return False
        
        if data.get('participant_name') != "MI Al-Hidayah":
            log(f"  ❌ FAILED: Expected participant_name='MI Al-Hidayah', got '{data.get('participant_name')}'")
            return False
        
        if data.get('peserta_id') is not None:
            log(f"  ❌ FAILED: Expected peserta_id=null for group, got {data.get('peserta_id')}")
            return False
        
        test_data['juara_group'] = data
        log(f"  ✅ PASSED: Group juara created - is_group=true, madrasah_name='MI Al-Hidayah'")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_juara_upsert_same_rank():
    """Test: POST /juara again with same rank => upsert replaces"""
    log("TEST: Create juara with same rank => upsert replaces")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        payload = {
            "lomba_id": test_data['lomba_kelompok']['id'],
            "rank": "Juara 1",
            "madrasah_name": "MI Nurul Huda",
            "is_group": True
        }
        resp = requests.post(f"{BASE_URL}/juara", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('madrasah_name') != "MI Nurul Huda":
            log(f"  ❌ FAILED: Upsert didn't replace, got '{data.get('madrasah_name')}'")
            return False
        
        # Verify only one Juara 1 exists
        resp2 = requests.get(f"{BASE_URL}/juara?lomba_id={test_data['lomba_kelompok']['id']}", headers=headers, timeout=10)
        juara_list = resp2.json()
        juara_1_count = sum(1 for j in juara_list if j.get('rank') == 'Juara 1')
        
        if juara_1_count != 1:
            log(f"  ❌ FAILED: Expected 1 Juara 1, found {juara_1_count}")
            return False
        
        log(f"  ✅ PASSED: Upsert replaced previous Juara 1")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_juara_create_individual():
    """Test: POST /juara for individu lomba with peserta_id"""
    log("TEST: Create individual juara for individu lomba")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        payload = {
            "lomba_id": test_data['lomba_individu']['id'],
            "rank": "Juara 1",
            "peserta_id": test_data['peserta_complete']['id']
        }
        resp = requests.post(f"{BASE_URL}/juara", json=payload, headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if data.get('is_group') != False:
            log(f"  ❌ FAILED: Expected is_group=false, got {data.get('is_group')}")
            return False
        
        if data.get('participant_name') != test_data['peserta_complete']['participant_name']:
            log(f"  ❌ FAILED: participant_name mismatch")
            return False
        
        if data.get('madrasah_name') != test_data['peserta_complete']['madrasah_name']:
            log(f"  ❌ FAILED: madrasah_name not set from peserta")
            return False
        
        test_data['juara_individual'] = data
        log(f"  ✅ PASSED: Individual juara created - is_group=false, participant_name set")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_juara_get_filter():
    """Test: GET /juara?lomba_id= filters correctly"""
    log("TEST: GET /juara with lomba_id filter")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        
        # Get juara for individu lomba
        resp = requests.get(f"{BASE_URL}/juara?lomba_id={test_data['lomba_individu']['id']}", headers=headers, timeout=10)
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        # All should be from individu lomba
        for j in data:
            if j.get('lomba_id') != test_data['lomba_individu']['id']:
                log(f"  ❌ FAILED: Filter not working, found juara from other lomba")
                return False
        
        log(f"  ✅ PASSED: Juara filter working ({len(data)} juara)")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

def test_juara_delete():
    """Test: DELETE /juara/:id works"""
    log("TEST: DELETE /juara/:id")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        juara_id = test_data['juara_individual']['id']
        resp = requests.delete(f"{BASE_URL}/juara/{juara_id}", headers=headers, timeout=10)
        log(f"  Status: {resp.status_code}")
        data = resp.json()
        
        if resp.status_code != 200:
            log(f"  ❌ FAILED: {data}")
            return False
        
        if not data.get('ok'):
            log(f"  ❌ FAILED: Delete didn't return ok:true")
            return False
        
        log(f"  ✅ PASSED: Juara deleted successfully")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

# ============================================================================
# SECURITY TESTS
# ============================================================================

def test_no_sensitive_data_leak():
    """Test: Verify no _id/password/token leaks in responses"""
    log("TEST: Check for sensitive data leaks")
    try:
        headers = {"Authorization": f"Bearer {test_data['super_admin']['token']}"}
        
        # Check lomba
        resp = requests.get(f"{BASE_URL}/lomba", timeout=10)
        lomba = resp.json()
        for l in lomba:
            if '_id' in l or 'password' in l or 'token' in l:
                log(f"  ❌ FAILED: Sensitive data in lomba response")
                return False
        
        # Check peserta
        resp = requests.get(f"{BASE_URL}/peserta", headers=headers, timeout=10)
        peserta = resp.json()
        for p in peserta:
            if '_id' in p or 'password' in p or 'token' in p:
                log(f"  ❌ FAILED: Sensitive data in peserta response")
                return False
        
        # Check juara
        resp = requests.get(f"{BASE_URL}/juara", headers=headers, timeout=10)
        juara = resp.json()
        for j in juara:
            if '_id' in j or 'password' in j or 'token' in j:
                log(f"  ❌ FAILED: Sensitive data in juara response")
                return False
        
        log(f"  ✅ PASSED: No sensitive data leaks detected")
        return True
    except Exception as e:
        log(f"  ❌ EXCEPTION: {str(e)}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all backend tests"""
    log("=" * 80)
    log("SIM PORSENI BACKEND API TESTS - RECENT CHANGES")
    log("=" * 80)
    
    tests = [
        # Auth
        ("Super Admin Login", test_super_admin_login),
        
        # Lomba type field tests
        ("Lomba: Create with type='individu'", test_lomba_create_with_type_individu),
        ("Lomba: Create with type='kelompok'", test_lomba_create_with_type_kelompok),
        ("Lomba: Create without type (default)", test_lomba_create_without_type),
        ("Lomba: Update type", test_lomba_update_type),
        ("Lomba: GET returns type field", test_lomba_get_returns_type),
        
        # Peserta gender + complete tests
        ("Setup: Create admin_madrasah", test_create_admin_madrasah),
        ("Peserta: Create with gender='L', no files", test_peserta_create_incomplete),
        ("Peserta: Create with gender='P', all files", test_peserta_create_complete),
        ("Peserta: Create without gender", test_peserta_create_without_gender),
        ("Peserta: Update to complete", test_peserta_update_to_complete),
        ("Peserta: Update lomba_id updates lomba_name", test_peserta_update_lomba_id),
        
        # Panitia visibility tests
        ("Setup: Create panitia", test_create_panitia),
        ("Panitia: Visibility filter (complete only)", test_panitia_visibility_filter),
        ("Admin Madrasah: Sees all own peserta", test_admin_madrasah_sees_all_own),
        ("Super Admin: Sees all peserta", test_super_admin_sees_all),
        
        # Juara group support tests
        ("Juara: Create group winner", test_juara_create_group),
        ("Juara: Upsert same rank", test_juara_upsert_same_rank),
        ("Juara: Create individual winner", test_juara_create_individual),
        ("Juara: GET with filter", test_juara_get_filter),
        ("Juara: DELETE", test_juara_delete),
        
        # Security
        ("Security: No sensitive data leaks", test_no_sensitive_data_leak),
    ]
    
    results = []
    for name, test_func in tests:
        log("")
        result = test_func()
        results.append((name, result))
    
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
    else:
        log("✅ ALL TESTS PASSED!")
    
    log("=" * 80)
    return passed, failed, results

if __name__ == "__main__":
    passed, failed, results = run_all_tests()
    exit(0 if failed == 0 else 1)
