#!/usr/bin/env python3
"""
Backend API Tests for SIM Porseni FASE 1
Tests: Profile self-service, Lomba team_size, Peserta nomor_peserta manual edit, Team registration
"""
import requests
import json
import sys

# Base URL from .env NEXT_PUBLIC_BASE_URL
BASE_URL = "https://sim-portal-5.preview.emergentagent.com/api"

# Seed accounts
SUPER_ADMIN = {"email": "super@porseni.id", "password": "admin123"}
ADMIN_MADRASAH = {"email": "admin.mi@porseni.id", "password": "admin123"}
PANITIA = {"email": "panitia@porseni.id", "password": "admin123"}

# Test results tracking
test_results = []

def log_test(name, passed, message=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status}: {name}"
    if message:
        result += f" - {message}"
    print(result)
    test_results.append({"name": name, "passed": passed, "message": message})
    return passed

def login(email, password):
    """Login and return token"""
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("token")
        else:
            print(f"Login failed for {email}: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        print(f"Login exception for {email}: {e}")
        return None

def get_lomba_by_name(name):
    """Get lomba by name"""
    try:
        resp = requests.get(f"{BASE_URL}/lomba", timeout=10)
        if resp.status_code == 200:
            lomba_list = resp.json()
            for lomba in lomba_list:
                if lomba.get("name") == name:
                    return lomba
        return None
    except Exception as e:
        print(f"Get lomba exception: {e}")
        return None

print("=" * 80)
print("BACKEND API TESTS - SIM Porseni FASE 1")
print("=" * 80)

# ============================================================================
# TEST 1: Profile self-service - GET /auth/profile
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: Profile self-service - GET /auth/profile")
print("=" * 80)

# Test 1.1: GET /auth/profile with super_admin token
print("\n[Test 1.1] GET /auth/profile with super_admin token")
super_token = login(SUPER_ADMIN["email"], SUPER_ADMIN["password"])
if super_token:
    try:
        resp = requests.get(f"{BASE_URL}/auth/profile", headers={"Authorization": f"Bearer {super_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            has_password_plain = "password_plain" in data
            # photo_url is optional, can be missing/null
            no_password = "password" not in data
            no_token = "token" not in data
            no_id = "_id" not in data
            
            if has_password_plain and no_password and no_token and no_id:
                log_test("1.1 GET /auth/profile super_admin", True, f"Returns password_plain={data.get('password_plain')}, photo_url={data.get('photo_url', 'null')}, no password/token/_id leak")
            else:
                log_test("1.1 GET /auth/profile super_admin", False, f"Missing fields or leaks: password_plain={has_password_plain}, no_password={no_password}, no_token={no_token}, no_id={no_id}")
        else:
            log_test("1.1 GET /auth/profile super_admin", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("1.1 GET /auth/profile super_admin", False, f"Exception: {e}")
else:
    log_test("1.1 GET /auth/profile super_admin", False, "Login failed")

# Test 1.2: GET /auth/profile with admin_madrasah token
print("\n[Test 1.2] GET /auth/profile with admin_madrasah token")
# NOTE: Password might be admin123 or newpass123 depending on previous test runs
admin_token = login(ADMIN_MADRASAH["email"], ADMIN_MADRASAH["password"])
if not admin_token:
    # Try with newpass123 if admin123 failed (from previous test run)
    admin_token = login(ADMIN_MADRASAH["email"], "newpass123")
print(f"DEBUG: admin_token after initial login: {admin_token[:20] if admin_token else 'None'}...")
if admin_token:
    try:
        resp = requests.get(f"{BASE_URL}/auth/profile", headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            has_password_plain = "password_plain" in data
            # photo_url is optional at this point (will be set in Test 2)
            has_madrasah_name = "madrasah_name" in data
            no_password = "password" not in data
            no_token = "token" not in data
            
            if has_password_plain and has_madrasah_name and no_password and no_token:
                log_test("1.2 GET /auth/profile admin_madrasah", True, f"Returns password_plain={data.get('password_plain')}, madrasah_name={data.get('madrasah_name')}, photo_url={data.get('photo_url', 'null')}, no leaks")
            else:
                log_test("1.2 GET /auth/profile admin_madrasah", False, f"Missing fields or leaks: password_plain={has_password_plain}, madrasah_name={has_madrasah_name}, no_password={no_password}, no_token={no_token}")
        else:
            log_test("1.2 GET /auth/profile admin_madrasah", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("1.2 GET /auth/profile admin_madrasah", False, f"Exception: {e}")
else:
    log_test("1.2 GET /auth/profile admin_madrasah", False, "Login failed")

# Test 1.3: GET /auth/profile with panitia token
print("\n[Test 1.3] GET /auth/profile with panitia token")
panitia_token = login(PANITIA["email"], PANITIA["password"])
if panitia_token:
    try:
        resp = requests.get(f"{BASE_URL}/auth/profile", headers={"Authorization": f"Bearer {panitia_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            has_password_plain = "password_plain" in data
            has_assigned_lomba_id = "assigned_lomba_id" in data
            no_password = "password" not in data
            
            if has_password_plain and has_assigned_lomba_id and no_password:
                log_test("1.3 GET /auth/profile panitia", True, f"Returns password_plain={data.get('password_plain')}, assigned_lomba_id={data.get('assigned_lomba_id')}, no leaks")
            else:
                log_test("1.3 GET /auth/profile panitia", False, f"Missing fields or leaks")
        else:
            log_test("1.3 GET /auth/profile panitia", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("1.3 GET /auth/profile panitia", False, f"Exception: {e}")
else:
    log_test("1.3 GET /auth/profile panitia", False, "Login failed")

# Test 1.4: GET /auth/profile with no token (401)
print("\n[Test 1.4] GET /auth/profile with no token")
try:
    resp = requests.get(f"{BASE_URL}/auth/profile", timeout=10)
    if resp.status_code == 401:
        log_test("1.4 GET /auth/profile no token", True, "Returns 401 as expected")
    else:
        log_test("1.4 GET /auth/profile no token", False, f"Expected 401, got {resp.status_code}")
except Exception as e:
    log_test("1.4 GET /auth/profile no token", False, f"Exception: {e}")

# Test 1.5: GET /auth/profile with invalid token (401)
print("\n[Test 1.5] GET /auth/profile with invalid token")
try:
    resp = requests.get(f"{BASE_URL}/auth/profile", headers={"Authorization": "Bearer invalid-token-xyz"}, timeout=10)
    if resp.status_code == 401:
        log_test("1.5 GET /auth/profile invalid token", True, "Returns 401 as expected")
    else:
        log_test("1.5 GET /auth/profile invalid token", False, f"Expected 401, got {resp.status_code}")
except Exception as e:
    log_test("1.5 GET /auth/profile invalid token", False, f"Exception: {e}")

# ============================================================================
# TEST 2: Profile self-service - PUT /auth/profile (password change on admin.mi)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: Profile self-service - PUT /auth/profile")
print("=" * 80)

# Test 2.1: PUT /auth/profile to update name, photo_url, password (admin.mi only)
print("\n[Test 2.1] PUT /auth/profile update name, photo_url, password (admin.mi)")
if admin_token:
    try:
        new_data = {
            "name": "Admin MI Updated",
            "photo_url": "/api/files/test-photo-123",
            "password": "newpass123"
        }
        resp = requests.put(f"{BASE_URL}/auth/profile", json=new_data, headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            name_updated = data.get("name") == "Admin MI Updated"
            photo_updated = data.get("photo_url") == "/api/files/test-photo-123"
            password_plain_updated = data.get("password_plain") == "newpass123"
            
            if name_updated and photo_updated and password_plain_updated:
                log_test("2.1 PUT /auth/profile update", True, f"Updated name={data.get('name')}, photo_url={data.get('photo_url')}, password_plain={data.get('password_plain')}")
            else:
                log_test("2.1 PUT /auth/profile update", False, f"Update failed: name={name_updated}, photo={photo_updated}, password_plain={password_plain_updated}")
        else:
            log_test("2.1 PUT /auth/profile update", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("2.1 PUT /auth/profile update", False, f"Exception: {e}")
else:
    log_test("2.1 PUT /auth/profile update", False, "No admin token")

# Test 2.2: Login with OLD password should fail
print("\n[Test 2.2] Login with OLD password (admin123) should fail")
try:
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_MADRASAH["email"], "password": "admin123"}, timeout=10)
    if resp.status_code == 401:
        log_test("2.2 Login with old password", True, "Old password rejected with 401 as expected")
    else:
        log_test("2.2 Login with old password", False, f"Expected 401, got {resp.status_code}")
except Exception as e:
    log_test("2.2 Login with old password", False, f"Exception: {e}")

# Test 2.3: Login with NEW password should succeed
print("\n[Test 2.3] Login with NEW password (newpass123) should succeed")
try:
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_MADRASAH["email"], "password": "newpass123"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        new_token = data.get("token")
        if new_token:
            admin_token = new_token  # Update admin_token for subsequent tests
            print(f"DEBUG: admin_token updated after password change: {admin_token[:20]}...")
            log_test("2.3 Login with new password", True, f"New password login succeeded, token={new_token[:20]}...")
        else:
            log_test("2.3 Login with new password", False, "No token in response")
    else:
        log_test("2.3 Login with new password", False, f"Status {resp.status_code}: {resp.text}")
except Exception as e:
    log_test("2.3 Login with new password", False, f"Exception: {e}")

# Test 2.4: GET /auth/profile shows updated name, photo_url, password_plain
print("\n[Test 2.4] GET /auth/profile shows updated data")
if admin_token:
    try:
        resp = requests.get(f"{BASE_URL}/auth/profile", headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            name_correct = data.get("name") == "Admin MI Updated"
            photo_correct = data.get("photo_url") == "/api/files/test-photo-123"
            password_plain_correct = data.get("password_plain") == "newpass123"
            
            if name_correct and photo_correct and password_plain_correct:
                log_test("2.4 GET /auth/profile after update", True, f"Shows updated name={data.get('name')}, photo_url={data.get('photo_url')}, password_plain={data.get('password_plain')}")
            else:
                log_test("2.4 GET /auth/profile after update", False, f"Data mismatch: name={name_correct}, photo={photo_correct}, password_plain={password_plain_correct}")
        else:
            log_test("2.4 GET /auth/profile after update", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("2.4 GET /auth/profile after update", False, f"Exception: {e}")
else:
    log_test("2.4 GET /auth/profile after update", False, "No admin token")

# Test 2.5: Verify /auth/login response does NOT leak password/password_plain/token
print("\n[Test 2.5] Verify /auth/login response does NOT leak password/password_plain/token")
try:
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_MADRASAH["email"], "password": "newpass123"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        user_obj = data.get("user", {})
        no_password = "password" not in user_obj
        no_password_plain = "password_plain" not in user_obj
        no_token_in_user = "token" not in user_obj
        
        if no_password and no_password_plain and no_token_in_user:
            log_test("2.5 Login response no leak", True, "Login response user object does NOT contain password/password_plain/token")
        else:
            log_test("2.5 Login response no leak", False, f"LEAK DETECTED: password={not no_password}, password_plain={not no_password_plain}, token={not no_token_in_user}")
    else:
        log_test("2.5 Login response no leak", False, f"Status {resp.status_code}: {resp.text}")
except Exception as e:
    log_test("2.5 Login response no leak", False, f"Exception: {e}")

# ============================================================================
# TEST 3: Lomba team_size field
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: Lomba team_size field")
print("=" * 80)

# Test 3.1: POST /lomba with type=kelompok and team_size=6
print("\n[Test 3.1] POST /lomba with type=kelompok and team_size=6")
test_lomba_kelompok_id = None
if super_token:
    try:
        lomba_data = {
            "name": "Test Kelompok Lomba",
            "category": "Olahraga",
            "type": "kelompok",
            "team_size": 6
        }
        resp = requests.post(f"{BASE_URL}/lomba", json=lomba_data, headers={"Authorization": f"Bearer {super_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            test_lomba_kelompok_id = data.get("id")
            team_size = data.get("team_size")
            if team_size == 6:
                log_test("3.1 POST lomba kelompok team_size=6", True, f"Created lomba id={test_lomba_kelompok_id}, team_size={team_size}")
            else:
                log_test("3.1 POST lomba kelompok team_size=6", False, f"Expected team_size=6, got {team_size}")
        else:
            log_test("3.1 POST lomba kelompok team_size=6", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("3.1 POST lomba kelompok team_size=6", False, f"Exception: {e}")
else:
    log_test("3.1 POST lomba kelompok team_size=6", False, "No super token")

# Test 3.2: POST /lomba with type=individu (team_size should be null)
print("\n[Test 3.2] POST /lomba with type=individu (team_size null)")
test_lomba_individu_id = None
if super_token:
    try:
        lomba_data = {
            "name": "Test Individu Lomba",
            "category": "Seni",
            "type": "individu"
        }
        resp = requests.post(f"{BASE_URL}/lomba", json=lomba_data, headers={"Authorization": f"Bearer {super_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            test_lomba_individu_id = data.get("id")
            team_size = data.get("team_size")
            if team_size is None:
                log_test("3.2 POST lomba individu team_size=null", True, f"Created lomba id={test_lomba_individu_id}, team_size={team_size}")
            else:
                log_test("3.2 POST lomba individu team_size=null", False, f"Expected team_size=null, got {team_size}")
        else:
            log_test("3.2 POST lomba individu team_size=null", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("3.2 POST lomba individu team_size=null", False, f"Exception: {e}")
else:
    log_test("3.2 POST lomba individu team_size=null", False, "No super token")

# Test 3.3: PUT /lomba/:id to update team_size to 8
print("\n[Test 3.3] PUT /lomba/:id to update team_size to 8")
if super_token and test_lomba_kelompok_id:
    try:
        resp = requests.put(f"{BASE_URL}/lomba/{test_lomba_kelompok_id}", json={"team_size": 8}, headers={"Authorization": f"Bearer {super_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            team_size = data.get("team_size")
            if team_size == 8:
                log_test("3.3 PUT lomba team_size=8", True, f"Updated team_size to {team_size}")
            else:
                log_test("3.3 PUT lomba team_size=8", False, f"Expected team_size=8, got {team_size}")
        else:
            log_test("3.3 PUT lomba team_size=8", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("3.3 PUT lomba team_size=8", False, f"Exception: {e}")
else:
    log_test("3.3 PUT lomba team_size=8", False, "No super token or lomba id")

# Test 3.4: GET /lomba returns team_size field
print("\n[Test 3.4] GET /lomba returns team_size field")
try:
    resp = requests.get(f"{BASE_URL}/lomba", timeout=10)
    if resp.status_code == 200:
        lomba_list = resp.json()
        found_kelompok = False
        found_individu = False
        for lomba in lomba_list:
            if lomba.get("id") == test_lomba_kelompok_id:
                found_kelompok = True
                if lomba.get("team_size") == 8:
                    log_test("3.4 GET lomba team_size kelompok", True, f"Kelompok lomba has team_size=8")
                else:
                    log_test("3.4 GET lomba team_size kelompok", False, f"Expected team_size=8, got {lomba.get('team_size')}")
            if lomba.get("id") == test_lomba_individu_id:
                found_individu = True
                if lomba.get("team_size") is None:
                    log_test("3.4 GET lomba team_size individu", True, f"Individu lomba has team_size=null")
                else:
                    log_test("3.4 GET lomba team_size individu", False, f"Expected team_size=null, got {lomba.get('team_size')}")
        if not found_kelompok:
            log_test("3.4 GET lomba team_size kelompok", False, "Kelompok lomba not found in list")
        if not found_individu:
            log_test("3.4 GET lomba team_size individu", False, "Individu lomba not found in list")
    else:
        log_test("3.4 GET lomba team_size", False, f"Status {resp.status_code}: {resp.text}")
except Exception as e:
    log_test("3.4 GET lomba team_size", False, f"Exception: {e}")

# Test 3.5: Clean up - DELETE test lomba
print("\n[Test 3.5] Clean up - DELETE test lomba")
if super_token:
    deleted_count = 0
    if test_lomba_kelompok_id:
        try:
            resp = requests.delete(f"{BASE_URL}/lomba/{test_lomba_kelompok_id}", headers={"Authorization": f"Bearer {super_token}"}, timeout=10)
            if resp.status_code == 200:
                deleted_count += 1
        except Exception as e:
            print(f"Delete kelompok lomba exception: {e}")
    
    if test_lomba_individu_id:
        try:
            resp = requests.delete(f"{BASE_URL}/lomba/{test_lomba_individu_id}", headers={"Authorization": f"Bearer {super_token}"}, timeout=10)
            if resp.status_code == 200:
                deleted_count += 1
        except Exception as e:
            print(f"Delete individu lomba exception: {e}")
    
    log_test("3.5 Clean up test lomba", True, f"Deleted {deleted_count} test lomba")
else:
    log_test("3.5 Clean up test lomba", False, "No super token")

# ============================================================================
# TEST 4: Peserta nomor_peserta manual edit
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: Peserta nomor_peserta manual edit")
print("=" * 80)

# Re-login to ensure we have a valid token (password is now newpass123)
print("\n[Re-login] Getting fresh admin token for Test 4")
admin_token = login(ADMIN_MADRASAH["email"], "newpass123")
if admin_token:
    print(f"DEBUG: Fresh admin_token for Test 4: {admin_token[:20]}...")
else:
    print("WARNING: Failed to get fresh admin token")

# Test 4.1: Create a peserta in Kaligrafi (individu) as admin_madrasah
print("\n[Test 4.1] POST /peserta to create participant in Kaligrafi")
print(f"DEBUG: admin_token before Test 4.1: {admin_token[:20] if admin_token else 'None'}...")
test_peserta_id = None
kaligrafi = get_lomba_by_name("Kaligrafi")
if admin_token and kaligrafi:
    try:
        peserta_data = {
            "participant_name": "Test Peserta Kaligrafi",
            "gender": "L",
            "nisn": "1234567890",
            "ttl": "Kediri, 01-01-2010",
            "lomba_id": kaligrafi.get("id")
        }
        resp = requests.post(f"{BASE_URL}/peserta", json=peserta_data, headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            test_peserta_id = data.get("id")
            nomor_peserta = data.get("nomor_peserta")
            log_test("4.1 POST peserta Kaligrafi", True, f"Created peserta id={test_peserta_id}, nomor_peserta={nomor_peserta}")
        else:
            log_test("4.1 POST peserta Kaligrafi", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("4.1 POST peserta Kaligrafi", False, f"Exception: {e}")
else:
    log_test("4.1 POST peserta Kaligrafi", False, f"No admin token ({admin_token is not None}) or Kaligrafi lomba not found ({kaligrafi is not None})")

# Test 4.2: PUT /peserta/:id to manually set nomor_peserta="099"
print("\n[Test 4.2] PUT /peserta/:id to set nomor_peserta='099'")
if admin_token and test_peserta_id:
    try:
        resp = requests.put(f"{BASE_URL}/peserta/{test_peserta_id}", json={"nomor_peserta": "099"}, headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            nomor_peserta = data.get("nomor_peserta")
            if nomor_peserta == "099":
                log_test("4.2 PUT peserta nomor_peserta", True, f"Updated nomor_peserta to {nomor_peserta}")
            else:
                log_test("4.2 PUT peserta nomor_peserta", False, f"Expected nomor_peserta='099', got {nomor_peserta}")
        else:
            log_test("4.2 PUT peserta nomor_peserta", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("4.2 PUT peserta nomor_peserta", False, f"Exception: {e}")
else:
    log_test("4.2 PUT peserta nomor_peserta", False, "No admin token or peserta id")

# Test 4.3: GET /peserta to verify nomor_peserta="099"
print("\n[Test 4.3] GET /peserta to verify nomor_peserta='099'")
if admin_token and test_peserta_id:
    try:
        resp = requests.get(f"{BASE_URL}/peserta", headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            peserta_list = resp.json()
            found = False
            for peserta in peserta_list:
                if peserta.get("id") == test_peserta_id:
                    found = True
                    nomor_peserta = peserta.get("nomor_peserta")
                    if nomor_peserta == "099":
                        log_test("4.3 GET peserta verify nomor_peserta", True, f"Verified nomor_peserta={nomor_peserta}")
                    else:
                        log_test("4.3 GET peserta verify nomor_peserta", False, f"Expected '099', got {nomor_peserta}")
                    break
            if not found:
                log_test("4.3 GET peserta verify nomor_peserta", False, "Peserta not found in list")
        else:
            log_test("4.3 GET peserta verify nomor_peserta", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("4.3 GET peserta verify nomor_peserta", False, f"Exception: {e}")
else:
    log_test("4.3 GET peserta verify nomor_peserta", False, "No admin token or peserta id")

# Clean up test peserta
if admin_token and test_peserta_id:
    try:
        requests.delete(f"{BASE_URL}/peserta/{test_peserta_id}", headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        print("Cleaned up test peserta")
    except:
        pass

# ============================================================================
# TEST 5: Team registration POST /peserta/team
# ============================================================================
print("\n" + "=" * 80)
print("TEST 5: Team registration POST /peserta/team")
print("=" * 80)

# Re-login to ensure we have a valid token
print("\n[Re-login] Getting fresh admin token for Test 5")
admin_token = login(ADMIN_MADRASAH["email"], "newpass123")
if admin_token:
    print(f"DEBUG: Fresh admin_token for Test 5: {admin_token[:20]}...")
else:
    print("WARNING: Failed to get fresh admin token")

# Test 5.1: POST /peserta/team with 3 members (no files) - complete=false
print("\n[Test 5.1] POST /peserta/team with 3 members (no files)")
test_team_id = None
test_member_ids = []
futsal = get_lomba_by_name("Futsal")
if admin_token and futsal:
    try:
        team_data = {
            "lomba_id": futsal.get("id"),
            "madrasah_name": "MI Al-Hidayah",
            "members": [
                {
                    "participant_name": "Pemain Futsal 1",
                    "gender": "L",
                    "nisn": "1111111111",
                    "ttl": "Kediri, 01-01-2010",
                    "files": {}
                },
                {
                    "participant_name": "Pemain Futsal 2",
                    "gender": "L",
                    "nisn": "2222222222",
                    "ttl": "Kediri, 02-02-2010",
                    "files": {}
                },
                {
                    "participant_name": "Pemain Futsal 3",
                    "gender": "L",
                    "nisn": "3333333333",
                    "ttl": "Kediri, 03-03-2010",
                    "files": {}
                }
            ]
        }
        resp = requests.post(f"{BASE_URL}/peserta/team", json=team_data, headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            test_team_id = data.get("team_id")
            team_name = data.get("team_name")
            count = data.get("count")
            members = data.get("members", [])
            
            # Verify response structure
            if test_team_id and team_name and count == 3 and len(members) == 3:
                # Verify each member
                all_correct = True
                nomor_peserta_list = []
                for member in members:
                    test_member_ids.append(member.get("id"))
                    is_group = member.get("is_group")
                    member_team_id = member.get("team_id")
                    complete = member.get("complete")
                    nomor_peserta = member.get("nomor_peserta")
                    nomor_peserta_list.append(nomor_peserta)
                    
                    if not (is_group == True and member_team_id == test_team_id and complete == False):
                        all_correct = False
                        break
                
                # Verify sequential nomor_peserta
                sequential = all(nomor_peserta_list[i] < nomor_peserta_list[i+1] for i in range(len(nomor_peserta_list)-1))
                
                if all_correct and sequential:
                    log_test("5.1 POST /peserta/team 3 members", True, f"Created team team_id={test_team_id}, count=3, all is_group=true, complete=false, sequential nomor_peserta={nomor_peserta_list}")
                else:
                    log_test("5.1 POST /peserta/team 3 members", False, f"Member validation failed: all_correct={all_correct}, sequential={sequential}")
            else:
                log_test("5.1 POST /peserta/team 3 members", False, f"Response structure invalid: team_id={test_team_id}, count={count}, members_len={len(members)}")
        else:
            log_test("5.1 POST /peserta/team 3 members", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("5.1 POST /peserta/team 3 members", False, f"Exception: {e}")
else:
    log_test("5.1 POST /peserta/team 3 members", False, "No admin token or Futsal lomba not found")

# Test 5.2: POST /peserta/team with 1 member WITH all 3 files - complete=true
print("\n[Test 5.2] POST /peserta/team with 1 member WITH all 3 files (complete=true)")
if admin_token and futsal:
    try:
        team_data = {
            "lomba_id": futsal.get("id"),
            "madrasah_name": "MI Al-Hidayah",
            "members": [
                {
                    "participant_name": "Pemain Futsal Complete",
                    "gender": "L",
                    "nisn": "9999999999",
                    "ttl": "Kediri, 09-09-2010",
                    "files": {
                        "akte": {"id": "file-akte-123", "name": "akte.pdf"},
                        "surat_ket": {"id": "file-surat-456", "name": "surat.pdf"},
                        "pas_photo": {"id": "file-photo-789", "name": "photo.jpg"}
                    }
                }
            ]
        }
        resp = requests.post(f"{BASE_URL}/peserta/team", json=team_data, headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            members = data.get("members", [])
            if len(members) == 1:
                member = members[0]
                test_member_ids.append(member.get("id"))
                complete = member.get("complete")
                files = member.get("files", {})
                has_all_files = "akte" in files and "surat_ket" in files and "pas_photo" in files
                
                if complete == True and has_all_files:
                    log_test("5.2 POST /peserta/team with files", True, f"Created member with complete=true, all 3 files present")
                else:
                    log_test("5.2 POST /peserta/team with files", False, f"Expected complete=true with all files, got complete={complete}, has_all_files={has_all_files}")
            else:
                log_test("5.2 POST /peserta/team with files", False, f"Expected 1 member, got {len(members)}")
        else:
            log_test("5.2 POST /peserta/team with files", False, f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("5.2 POST /peserta/team with files", False, f"Exception: {e}")
else:
    log_test("5.2 POST /peserta/team with files", False, "No admin token or Futsal lomba not found")

# Test 5.3: POST /peserta/team with empty members array - 400
print("\n[Test 5.3] POST /peserta/team with empty members array (expect 400)")
if admin_token and futsal:
    try:
        team_data = {
            "lomba_id": futsal.get("id"),
            "madrasah_name": "MI Al-Hidayah",
            "members": []
        }
        resp = requests.post(f"{BASE_URL}/peserta/team", json=team_data, headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 400:
            log_test("5.3 POST /peserta/team empty members", True, "Returns 400 as expected")
        else:
            log_test("5.3 POST /peserta/team empty members", False, f"Expected 400, got {resp.status_code}")
    except Exception as e:
        log_test("5.3 POST /peserta/team empty members", False, f"Exception: {e}")
else:
    log_test("5.3 POST /peserta/team empty members", False, "No admin token or Futsal lomba not found")

# Test 5.4: POST /peserta/team with no token - 401
print("\n[Test 5.4] POST /peserta/team with no token (expect 401)")
if futsal:
    try:
        team_data = {
            "lomba_id": futsal.get("id"),
            "madrasah_name": "MI Al-Hidayah",
            "members": [{"participant_name": "Test", "gender": "L", "nisn": "123", "ttl": "Kediri, 01-01-2010", "files": {}}]
        }
        resp = requests.post(f"{BASE_URL}/peserta/team", json=team_data, timeout=10)
        if resp.status_code == 401:
            log_test("5.4 POST /peserta/team no token", True, "Returns 401 as expected")
        else:
            log_test("5.4 POST /peserta/team no token", False, f"Expected 401, got {resp.status_code}")
    except Exception as e:
        log_test("5.4 POST /peserta/team no token", False, f"Exception: {e}")
else:
    log_test("5.4 POST /peserta/team no token", False, "Futsal lomba not found")

# Clean up test team members
if admin_token and test_member_ids:
    print(f"\nCleaning up {len(test_member_ids)} test team members...")
    for member_id in test_member_ids:
        try:
            requests.delete(f"{BASE_URL}/peserta/{member_id}", headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        except:
            pass
    print("Cleaned up test team members")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

passed = sum(1 for r in test_results if r["passed"])
failed = sum(1 for r in test_results if not r["passed"])
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

if failed > 0:
    print("\n❌ FAILED TESTS:")
    for r in test_results:
        if not r["passed"]:
            print(f"  - {r['name']}: {r['message']}")

print("\n" + "=" * 80)
print(f"FINAL PASSWORD FOR admin.mi@porseni.id: newpass123")
print("=" * 80)

sys.exit(0 if failed == 0 else 1)
