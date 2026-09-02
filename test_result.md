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
        -comment: "✅ ALL TESTS PASSED (3 tests): POST /lomba with super_admin creates lomba with judging_criteria array, GET /lomba public access works, unauthorized POST blocked with 403. Lomba created successfully with UUID."
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
        -working: "NA"
        -agent: "main"
        -comment: "admin_madrasah sees created_by; panitia sees assigned lomba_id; super sees all. PUT /peserta/:id/status."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (6 tests): POST /peserta auto-generates nomor_peserta (001, 002, etc.), drive_path format correct '[Lomba]/[Madrasah]/[Peserta]', role filtering works (admin_madrasah sees only own, panitia sees only assigned lomba_id, super_admin sees all), PUT /peserta/:id/status updates status successfully."
  - task: "Hasil upload record + Juara assign/list/delete"
    implemented: true
    working: true
    file: "app/api/[[...path]]/route.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: "Juara POST upserts one per rank per lomba."
        -working: true
        -agent: "testing"
        -comment: "✅ ALL TESTS PASSED (4 tests): POST /hasil creates hasil record, GET /hasil?lomba_id= filters correctly, POST /juara upserts winner (one per rank per lomba), GET /juara?lomba_id= returns filtered list. Upsert behavior verified."
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
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "Auth register/login/me (role-based, token auth, super_admin auto-verified, others pending)"
    - "Lomba CRUD (super_admin only for write, public GET)"
    - "Peserta CRUD role-filtered + nomor_peserta auto + drive_path mock + status update"
    - "Templates upsert by type (certificate/idcard) + File upload (disk) + File serve"
    - "Users management (list/verify/delete) super_admin"
    - "Hasil upload record + Juara assign/list/delete"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    -agent: "main"
    -message: "Please test all backend APIs under /api. Auth uses Bearer token from /auth/login or /auth/register (super_admin returns token immediately; other roles return {pending:true} and must be verified by super_admin before login). Suggested flow: register super_admin -> create lomba -> register admin_madrasah (pending) -> super verifies -> admin logs in -> creates peserta (check nomor_peserta auto + drive_path) -> register panitia with assigned_lomba_id -> super verifies -> panitia logs in, sees only own lomba peserta, updates status, assigns juara. Also test /upload (multipart) and GET /files/:id, and /templates upsert. Use UUIDs, no ObjectId."
    -agent: "testing"
    -message: "✅ BACKEND TESTING COMPLETE - ALL 30 TESTS PASSED! Comprehensive testing executed covering: (1) Auth: register/login/me with all role scenarios, auto-verification for super_admin, pending status for others, 403 for pending login, 401 for wrong password, 400 for duplicate email. (2) Lomba: CRUD with super_admin authorization, public GET access, judging_criteria array. (3) Users: list/verify/delete (super_admin only). (4) Peserta: CRUD with role-based filtering (admin_madrasah sees only created_by, panitia sees only assigned_lomba_id, super_admin sees all), nomor_peserta auto-generation (001, 002...), drive_path format '[Lomba]/[Madrasah]/[Peserta]', status update. (5) Hasil: create and list with lomba_id filter. (6) Juara: create with upsert behavior (one per rank per lomba), list, delete. (7) File: upload multipart and serve bytes. (8) Templates: upsert by type. (9) Security: No MongoDB ObjectId (_id), password, or token leaks in responses. All endpoints working correctly with proper authorization and data validation."