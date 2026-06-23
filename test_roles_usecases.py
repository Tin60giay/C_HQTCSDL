import requests
import re
import sys
import pyodbc

def db_cleanup_ltc(maltc):
    try:
        conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QLDSV_HTC;Trusted_Connection=yes;')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM DANGKY WHERE MALTC = ?", (maltc,))
        cursor.execute("DELETE FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[CLEANUP ERROR] {e}")

# Reconfigure console output to support Vietnamese accents in Windows Command Prompt
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

BASE_URL = 'http://127.0.0.1:5001'

def get_session(username, password, role, khoa=''):
    session = requests.Session()
    session.get(BASE_URL + '/')
    data = {
        'role': role,
        'username': username,
        'password': password,
        'khoa': khoa
    }
    r = session.post(BASE_URL + '/', data=data, allow_redirects=True)
    if 'dashboard' in r.url:
        print(f"[SUCCESS] Login successful for user: {username} ({role})")
        return session
    else:
        print(f"[FAIL] Login failed for user: {username} ({role}). URL: {r.url}")
        return None

def test_subject_usecases():
    print("\n==============================================")
    print("TEST CASE: MON HOC (SUBJECTS)")
    print("==============================================")
    
    s_pgv = get_session('GV01', 'GV01', 'GV')     # PGV Role
    s_gv = get_session('GV03', 'GV03', 'GV')      # GV / KHOA Role
    s_sv = get_session('N15DCCN001', '123', 'SV', 'CNTT')  # SV Role
    
    if not (s_pgv and s_gv and s_sv):
        print("[ERROR] Failed to establish all test sessions. Aborting.")
        return
        
    subject_code = "TESTMH99"
    subject_name = "Mon Hoc Test Auto 99"
    
    # --- PRE-CLEANUP: If subject TESTMH99 already exists, delete it first ---
    r_check = s_pgv.get(BASE_URL + '/monhoc')
    if subject_code in r_check.text:
        print(f"[CLEANUP] Found pre-existing test subject {subject_code}. Deleting it...")
        s_pgv.post(BASE_URL + '/monhoc/xoa', data={'mamh': subject_code}, allow_redirects=True)
    
    # --- STEP 1: PGV adds a new subject ---
    print("\n--- Step 1: PGV attempts to add a new subject ---")
    data = {
        'mamh': subject_code,
        'tenmh': subject_name,
        'sotiet_lt': '45',
        'sotiet_th': '15'
    }
    r = s_pgv.post(BASE_URL + '/monhoc/them', data=data, allow_redirects=True)
    
    # Verify it exists in HTML
    r_check = s_pgv.get(BASE_URL + '/monhoc')
    if subject_code in r_check.text:
        print(f"[PASS] Subject {subject_code} successfully created and displayed by PGV.")
    else:
        print(f"[FAIL] Subject {subject_code} not found in the list.")

    # --- STEP 2: GV/KHOA attempts to add a subject (should be blocked) ---
    print("\n--- Step 2: KHOA/GV attempts to add a subject (should be blocked) ---")
    data_gv = {
        'mamh': 'TESTGV99',
        'tenmh': 'Blocked Subject',
        'sotiet_lt': '30',
        'sotiet_th': '0'
    }
    r = s_gv.post(BASE_URL + '/monhoc/them', data=data_gv, allow_redirects=True)
    if "Bạn không có quyền truy cập" in r.text or "dashboard" in r.url:
        print("[PASS] KHOA/GV was successfully blocked from adding subjects.")
    else:
        print("[FAIL] KHOA/GV was NOT blocked from adding subjects.")

    # --- STEP 3: SV attempts to add a subject (should be blocked) ---
    print("\n--- Step 3: SV attempts to add a subject (should be blocked) ---")
    r = s_sv.post(BASE_URL + '/monhoc/them', data=data_gv, allow_redirects=True)
    if "Bạn không có quyền truy cập" in r.text or "dashboard" in r.url:
        print("[PASS] SV was successfully blocked from adding subjects.")
    else:
        print("[FAIL] SV was NOT blocked from adding subjects.")

    # --- STEP 4: PGV edits the subject ---
    print("\n--- Step 4: PGV edits the subject ---")
    data_edit = {
        'mamh': subject_code,
        'tenmh': subject_name + " (Modified)",
        'sotiet_lt': '45',
        'sotiet_th': '15'
    }
    r = s_pgv.post(BASE_URL + '/monhoc/ghi', data=data_edit, allow_redirects=True)
    
    # Verify modification
    r_check = s_pgv.get(BASE_URL + '/monhoc')
    if "(Modified)" in r_check.text:
        print("[PASS] Subject successfully edited by PGV.")
    else:
        print("[FAIL] Subject modifications not saved.")

    # --- STEP 5: GV/KHOA attempts to edit the subject (should be blocked) ---
    print("\n--- Step 5: KHOA/GV attempts to edit the subject ---")
    r = s_gv.post(BASE_URL + '/monhoc/ghi', data=data_edit, allow_redirects=True)
    if "Bạn không có quyền truy cập" in r.text or "dashboard" in r.url:
        print("[PASS] KHOA/GV was blocked from editing.")
    else:
        print("[FAIL] KHOA/GV was NOT blocked from editing.")

    # --- STEP 6: PGV edits a used subject to change hours (should be blocked by validation) ---
    print("\n--- Step 6: PGV edits a frozen/used subject (should be blocked by validation) ---")
    # CTDL is used in credit classes
    data_frozen = {
        'mamh': 'CTDL',
        'tenmh': 'Cau truc du lieu & Giai thuat (Fake)',
        'sotiet_lt': '50',  # change hours
        'sotiet_th': '5'
    }
    r = s_pgv.post(BASE_URL + '/monhoc/ghi', data=data_frozen, allow_redirects=True)
    if "Không thể sửa đổi số tiết" in r.text or "đã phát sinh" in r.text or "Lỗi" in r.text:
        print("[PASS] DB validation correctly blocked changing hours of active subject CTDL.")
    else:
        print("[FAIL] System allowed changing hours of active subject CTDL.")

    # --- STEP 7: SV attempts to delete the subject (should be blocked) ---
    print("\n--- Step 7: SV attempts to delete the subject ---")
    r = s_sv.post(BASE_URL + '/monhoc/xoa', data={'mamh': subject_code}, allow_redirects=True)
    if "Bạn không có quyền truy cập" in r.text or "dashboard" in r.url:
        print("[PASS] SV was blocked from deleting.")
    else:
        print("[FAIL] SV was NOT blocked from deleting.")

    # --- STEP 8: PGV deletes the test subject ---
    print("\n--- Step 8: PGV deletes the test subject ---")
    r = s_pgv.post(BASE_URL + '/monhoc/xoa', data={'mamh': subject_code}, allow_redirects=True)
    
    r_check = s_pgv.get(BASE_URL + '/monhoc')
    if subject_code not in r_check.text:
        print("[PASS] Test subject successfully deleted by PGV.")
    else:
        print("[FAIL] Test subject still remains in list after deletion.")

    # --- STEP 9: PGV attempts to delete an active subject (should be blocked) ---
    print("\n--- Step 9: PGV attempts to delete an active subject ---")
    r = s_pgv.post(BASE_URL + '/monhoc/xoa', data={'mamh': 'CTDL'}, allow_redirects=True)
    if "Không thể xóa" in r.text or "đã được sử dụng" in r.text or "Lỗi" in r.text:
        print("[PASS] Logic correctly blocked deletion of active subject CTDL.")
    else:
        print("[FAIL] System allowed deleting active subject CTDL.")

def test_credit_class_usecases():
    print("\n==============================================")
    print("TEST CASE: LOP TIN CHI (CREDIT CLASSES)")
    print("==============================================")
    
    s_pgv = get_session('GV01', 'GV01', 'GV')
    s_gv = get_session('GV03', 'GV03', 'GV')
    s_sv = get_session('N15DCCN001', '123', 'SV', 'CNTT')
    
    if not (s_pgv and s_gv and s_sv):
        print("[ERROR] Failed to establish all test sessions. Aborting.")
        return

    test_nienkhoa = "2026-2027"
    test_hocky = "1"
    test_mamh = "AV"
    test_nhom = "99"
    test_magv = "GV01"
    test_makhoa = "CNTT"
    test_sosv = "15"
    
    # --- PRE-CLEANUP: If a credit class with nhom=99 on 2026-2027 already exists, delete it first ---
    r_check = s_pgv.get(BASE_URL + '/loptinchi')
    match = re.search(r"chonDong\(this,\s*'(\d+)',\s*'2026-2027',\s*1,\s*'AV',\s*99", r_check.text)
    if match:
        existing_maltc = int(match.group(1))
        print(f"[CLEANUP] Found pre-existing test credit class #{existing_maltc}. Deleting directly from database...")
        db_cleanup_ltc(existing_maltc)
    
    # --- STEP 1: PGV opens a credit class ---
    print("\n--- Step 1: PGV attempts to open a new credit class ---")
    data_open = {
        'nienkhoa': test_nienkhoa,
        'hocky': test_hocky,
        'mamh': test_mamh,
        'nhom': test_nhom,
        'magv': test_magv,
        'makhoa': test_makhoa,
        'sosvtoithieu': test_sosv
    }
    r = s_pgv.post(BASE_URL + '/loptinchi/them', data=data_open, allow_redirects=True)
    
    # We need to find the MALTC generated.
    r_check = s_pgv.get(BASE_URL + '/loptinchi')
    match = re.search(r"chonDong\(this,\s*'(\d+)',\s*'2026-2027',\s*1,\s*'AV',\s*99", r_check.text)
    if match:
        maltc = match.group(1)
        print(f"[PASS] Credit class successfully created with MALTC: {maltc}")
    else:
        print("[FAIL] Could not find created credit class MALTC.")
        return

    # --- STEP 2: GV/KHOA attempts to open a credit class (should be blocked) ---
    print("\n--- Step 2: KHOA/GV attempts to open a credit class ---")
    r = s_gv.post(BASE_URL + '/loptinchi/them', data=data_open, allow_redirects=True)
    if "Bạn không có quyền truy cập" in r.text or "dashboard" in r.url:
        print("[PASS] KHOA/GV was blocked from opening credit classes.")
    else:
        print("[FAIL] KHOA/GV was NOT blocked.")

    # --- STEP 3: SV attempts to open a credit class (should be blocked) ---
    print("\n--- Step 3: SV attempts to open a credit class ---")
    r = s_sv.post(BASE_URL + '/loptinchi/them', data=data_open, allow_redirects=True)
    if "Bạn không có quyền truy cập" in r.text or "dashboard" in r.url:
        print("[PASS] SV was blocked from opening credit classes.")
    else:
        print("[FAIL] SV was NOT blocked.")

    # --- STEP 4: PGV edits the credit class ---
    print("\n--- Step 4: PGV edits the credit class ---")
    data_edit = {
        'maltc': maltc,
        'nienkhoa': test_nienkhoa,
        'hocky': test_hocky,
        'mamh': test_mamh,
        'nhom': test_nhom,
        'magv': 'GV02',  # change teacher
        'makhoa': test_makhoa,
        'sosvtoithieu': '20' # change min students
    }
    r = s_pgv.post(BASE_URL + '/loptinchi/ghi', data=data_edit, allow_redirects=True)
    
    r_check = s_pgv.get(BASE_URL + '/loptinchi')
    if 'GV02' in r_check.text or 'data-magv="GV02"' in r_check.text or f"chonDong(this, '{maltc}', '2026-2027', 1, 'AV', 99, 'GV02'" in r_check.text.replace(' ', ''):
        print("[PASS] Credit class successfully edited (Instructor changed to GV02).")
    else:
        # Fallback check on string presence
        if 'GV02' in r_check.text:
            print("[PASS] Credit class successfully edited (Instructor GV02 found in list).")
        else:
            print("[FAIL] Credit class edit was not saved.")

    # --- STEP 5: PGV edits credit class in a frozen year (should be blocked) ---
    print("\n--- Step 5: PGV attempts to edit a credit class in a frozen/historic year (< 2025) ---")
    # Let's find a historic credit class MALTC
    match_historic = re.search(r"chonDong\(this,\s*'(\d+)',\s*'([^']+)',\s*\d+,\s*'[^']+',\s*\d+", r_check.text)
    historic_maltc = None
    if match_historic:
        all_matches = re.findall(r"chonDong\(this,\s*'(\d+)',\s*'([^']+)',\s*\d+,\s*'[^']+',\s*\d+", r_check.text)
        for m_id, m_nk in all_matches:
            try:
                if int(m_nk.split('-')[0]) < 2025:
                    historic_maltc = m_id
                    print(f"Found historic credit class MALTC: {historic_maltc} (Niên khóa: {m_nk})")
                    break
            except: pass
    
    if historic_maltc:
        data_hist = {
            'maltc': historic_maltc,
            'nienkhoa': '2024-2025',
            'hocky': '1',
            'mamh': 'CTDL',
            'nhom': '1',
            'magv': 'GV01',
            'makhoa': 'CNTT',
            'sosvtoithieu': '10'
        }
        r = s_pgv.post(BASE_URL + '/loptinchi/ghi', data=data_hist, allow_redirects=True)
        if "bị đóng băng" in r.text or "Lỗi" in r.text:
            print("[PASS] System correctly blocked editing of frozen/historic credit classes.")
        else:
            print("[FAIL] System allowed editing a frozen/historic credit class.")
    else:
        print("[SKIP] No historic credit classes found in the database to test.")

    # --- STEP 6: PGV cancels the test credit class (Since physical delete is removed) ---
    print("\n--- Step 6: PGV attempts to cancel the class ---")
    data_del = {
        'maltc': maltc,
        'action_type': 'huy_lop'
    }
    r = s_pgv.post(BASE_URL + '/loptinchi/xoa', data=data_del, allow_redirects=True)
    
    r_check = s_pgv.get(BASE_URL + '/loptinchi')
    if "cancelled-row" in r_check.text or "Đã hủy" in r_check.text:
        print("[PASS] Credit class successfully cancelled.")
    else:
        print("[FAIL] Credit class was not cancelled.")
        
    db_cleanup_ltc(maltc)

if __name__ == '__main__':
    test_subject_usecases()
    test_credit_class_usecases()
