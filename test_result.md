#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "SIM Porseni MI Kecamatan Plosoklaten - role-based competition management app (Super Admin, Admin Madrasah, Panitia). Next.js + MongoDB. Features: auth+roles, lomba CRUD, participant registration with file upload, verification, print sheets, results/winners, certificate & ID card engine."

backend:
  - task: "Auth register/login/me (role-based, token auth, super_admin auto-verified, others pending)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Token stored in user.token, Bearer auth. super_admin auto verified; admin_madrasah/panitia pending until verified. Login blocks pending accounts."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (7 tests): super_admin register returns token immediately, admin_madrasah/panitia return {pending:true}, duplicate email rejected with 400, pending account login blocked with 403, wrong password rejected with 401, verified accounts login successfully, /auth/me returns user with Bearer token. No _id/password/token leaks."
  - task: "Lomba CRUD (super_admin only for write, public GET)"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "GET public, POST/PUT/DELETE require super_admin. judging_criteria array."
        -working: true
        -agent: "testing"
        -comment: "ALL TESTS PASSED earlier."
        -working: "NA"
        -agent: "main"
        -comment: "CHANGE: added 'type' field (individu|kelompok) to POST and PUT. Default 'individu'. Please retest POST/PUT persist type and GET returns it."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (5 tests): POST /lomba with type='individu' returns type='individu', POST /lomba with type='kelompok' returns type='kelompok', POST /lomba WITHOUT type defaults to type='individu', PUT /lomba/:id changing type from individu to kelompok persists correctly, GET /lomba returns type field on all lomba. Type field working as expected."
  - task: "Users management (list/verify/delete) super_admin"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "PUT status verify, DELETE. Only super_admin."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (3 tests): GET /users returns all users (super_admin only), PUT /users/:id {status:'verified'} successfully verifies pending users, user verification enables login. No sensitive data leaks."
  - task: "Peserta CRUD role-filtered + nomor_peserta auto + drive_path mock + status update"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "testing"
        -comment: "ALL TESTS PASSED earlier (nomor_peserta auto, drive_path, role filtering, status update)."
        -working: "NA"
        -agent: "main"
        -comment: "CHANGE: added 'gender' (L|P) and computed 'complete' boolean (complete = participant_name+gender+lomba_id present AND files akte+surat_ket+pas_photo all uploaded). POST stores gender+complete. General PUT /peserta/:id now accepts gender+files and RECOMPUTES complete (also updates lomba_name when lomba_id changes). GET /peserta for PANITIA now filters {lomba_id, complete:true} so incomplete peserta are hidden from panitia. admin_madrasah still sees all own; super_admin sees all. Please retest: (1) POST with gender + partial files => complete:false; (2) PUT to add all 3 files => complete:true; (3) panitia GET only sees complete peserta of assigned lomba."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (7 tests): POST /peserta with gender='L' and no files returns complete=false with nomor_peserta auto-generated, POST /peserta with gender='P' and all 3 files returns complete=true, POST /peserta WITHOUT gender saves gender='' and complete=false even with files present, PUT /peserta/:id adding all 3 files recomputes complete to true, PUT /peserta/:id changing lomba_id updates lomba_name accordingly, GET /peserta as PANITIA returns ONLY complete=true peserta of assigned lomba (incomplete peserta hidden), admin_madrasah GET /peserta returns all own peserta (complete + incomplete), super_admin GET /peserta returns all peserta. Gender field and complete flag working correctly with proper visibility filtering."
  - task: "Hasil upload record + Juara assign/list/delete"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        -working: true
        -agent: "testing"
        -comment: "ALL TESTS PASSED earlier (hasil create/list, juara upsert one per rank per lomba)."
        -working: "NA"
        -agent: "main"
        -comment: "CHANGE: Juara POST now supports GROUP winners. If body.is_group true OR lomba.type==='kelompok', stores {is_group:true, madrasah_name, peserta_id:null, participant_name=madrasah_name}. Individual path unchanged (peserta_id, is_group:false). Still upserts one per rank per lomba (deleteMany by lomba_id+rank). Please retest: individual juara assign still works; group juara assign with {lomba_id,rank,madrasah_name,is_group:true} stores madrasah_name; upsert replaces same rank."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (5 tests): POST /juara for kelompok lomba with is_group=true stores {is_group:true, madrasah_name:'MI Al-Hidayah', peserta_id:null, participant_name:'MI Al-Hidayah'}, POST /juara again with same rank different madrasah upserts correctly (only one Juara 1 per lomba), POST /juara for individu lomba with peserta_id stores {is_group:false, participant_name from peserta, madrasah_name from peserta}, GET /juara?lomba_id= filters correctly, DELETE /juara/:id works. Group winner support working correctly with proper upsert behavior."
  - task: "Templates upsert by type (certificate/idcard) + File upload (disk) + File serve"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "POST /upload multipart -> disk .uploads + files collection. GET /files/:id serves bytes. Templates upsert by type."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (4 tests): POST /upload multipart returns {id,url,name}, GET /files/:id serves file bytes correctly, POST /templates upserts by type (updates existing, creates new), GET /templates?type= filters correctly. File upload and serve working."

frontend:
  - task: "Full UI (Auth, role dashboards, registration, print, cert/idcard engine)"
    implemented: true
    working: "NA"
    file: "app/page.js and components/porseni/*"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Not tested yet; awaiting user permission for frontend testing."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 2
  run_ui: false

test_plan:
  current_focus:
    - "Lomba CRUD (super_admin only for write, public GET)"
    - "Peserta CRUD role-filtered + nomor_peserta auto + drive_path mock + status update"
    - "Hasil upload record + Juara assign/list/delete"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    -agent: "main"
    -message: "Fixed missing /app/.env (MONGO_URL was unset causing ALL API 500s). Recreated .env (MONGO_URL local, DB_NAME=porseni_db). Super admin seeded: super@porseni.id / admin123. NEW backend changes to retest: (1) Lomba type field individu|kelompok; (2) Peserta gender L|P + computed complete flag + panitia GET filters complete:true + PUT recomputes complete; (3) Juara group support (is_group, madrasah_name). Please test these focusing on the deltas. Use super@porseni.id/admin123, create an admin_madrasah (verify it), create lomba individu & kelompok, register peserta, complete files, test panitia visibility."
    -agent: "testing"
    -message: "✅ BACKEND TESTING COMPLETE - ALL 22 TESTS PASSED. Tested all recent changes: (1) Lomba type field (individu/kelompok with defaults) working correctly, (2) Peserta gender (L/P) and complete flag computed correctly, panitia visibility filter working (only sees complete peserta of assigned lomba), (3) Juara group support working (is_group, madrasah_name for kelompok lomba, upsert behavior correct). No sensitive data leaks (_id/password/token). All backend APIs functioning as expected. Ready for main agent to summarize and finish."