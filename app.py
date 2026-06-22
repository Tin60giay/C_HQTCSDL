from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from functools import wraps
import pyodbc
import json

app = Flask(__name__)
app.secret_key = 'super_secret_key_qlds'

SERVER_NAME = 'localhost'
DATABASE_NAME = 'QLDSV_HTC'

SV_SHARED_LOGIN = 'sv'
SV_SHARED_PASSWORD = '123'


# ----------------------------------------------------------------
# DB helpers
# ----------------------------------------------------------------
def get_db_connection(login, password):
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER_NAME};"
        f"DATABASE={DATABASE_NAME};"
        f"UID={login};PWD={password}"
    )
    try:
        conn = pyodbc.connect(connection_string)
        return conn, None
    except Exception as e:
        return None, str(e)


def get_db():
    """Lấy kết nối DB từ session hiện tại."""
    return get_db_connection(session.get('db_login'), session.get('db_pass'))


def rows_to_list(rows):
    """Chuyển pyodbc rows thành list of dict."""
    if not rows:
        return []
    return [dict(zip([col[0] for col in rows.cursor_description], row)) for row in rows]


def get_danh_sach_khoa():
    conn, error = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAKHOA, TENKHOA FROM KHOA ORDER BY MAKHOA")
            rows = cursor.fetchall()
            khoa_list = [{'MAKHOA': row.MAKHOA.strip(), 'TENKHOA': row.TENKHOA.strip()} for row in rows]
            conn.close()
            return khoa_list
        except:
            conn.close()
    return []


def get_nienkhoa_list():
    """Lấy danh sách niên khóa đang có trong LOPTINCHI + sinh thêm đến năm hiện tại+1.
    Chỉ hiển thị từ mốc 2025 trở đi theo yêu cầu đóng băng dữ liệu cũ.
    """
    import datetime
    conn, _ = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    existing = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GET_ALL_NIENKHOA")
            # Lọc chỉ lấy niên khóa >= 2025-2026
            for r in cursor.fetchall():
                nk = r[0].strip()
                try:
                    start_year = int(nk.split('-')[0])
                    if start_year >= 2025:
                        existing.append(nk)
                except: pass
        except: pass
        finally: conn.close()
    
    # Sinh thêm range từ 2025 đến năm hiện tại + 1
    year = datetime.datetime.now().year
    start_gen = max(2025, year) # Đảm bảo không sinh năm cũ
    generated = [f"{y}-{y+1}" for y in range(2025, year + 2)]
    
    combined = list(dict.fromkeys(existing + generated))
    combined.sort()
    return combined


def is_frozen(year_str):
    """Kiểm tra niên khóa/khóa học có thuộc diện đóng băng (trước 2025) không."""
    if not year_str: return False
    try:
        # Nhận diện định dạng YYYY-YYYY hoặc YYYY
        start_year = int(year_str.split('-')[0])
        return start_year < 2025
    except:
        return False


def nocache_response(resp):
    """[PLANT_NHAPDIEM_RETAIN_2026] Thêm headers chống cache cho response HTML
    để browser luôn lấy HTML mới nhất từ server.
    """
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


def get_nienkhoa_co_lop():
    """Lấy danh sách niên khóa thực tế đang có LTC chưa bị hủy (dành cho trang đăng ký của SV).
    Không sinh năm giả — dựa hoàn toàn vào bảng LOPTINCHI.
    """
    conn, _ = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC SP_GET_NIENKHOA_CO_LOP")
        return [r[0].strip() for r in cursor.fetchall()]
    except:
        return []
    finally:
        conn.close()


def get_default_nk_ltc():
    """[PLANT_LTC_BUGS_2026] Lấy niên khóa mới nhất hiện có trong LOPTINCHI (chưa hủy).
    Trả về chuỗi 'YYYY-YYYY' hoặc '' nếu chưa có LTC nào.
    """
    conn, _ = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    if not conn:
        return ''
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC SP_GET_DEFAULT_NK_LTC")
        row = cursor.fetchone()
        return row[0].strip() if row else ''
    except:
        return ''
    finally:
        conn.close()


def get_nienkhoa_for_sv(masv):
    """[PLANT_LTC_BUGS_2026] Lấy niên khóa SV được phép đăng ký (trong phạm vi KHOAHOC → KHOAHOC+7)."""
    conn, _ = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC SP_GET_NIENKHOA_SV ?", (masv,))
        return [r[0].strip() for r in cursor.fetchall() if r[0]]
    except:
        return []
    finally:
        conn.close()


def get_all_nienkhoa_ltc():
    """[PLANT_NHAPDIEM_RETAIN_2026] Lấy TẤT CẢ niên khóa thực tế trong LOPTINCHI
    (kể cả đã đóng băng < 2025) - dùng cho trang Nhập Điểm / Xem LTC.
    """
    conn, _ = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC SP_GET_ALL_NIENKHOA")
        return [r[0].strip() for r in cursor.fetchall() if r[0]]
    except:
        return []
    finally:
        conn.close()


def get_khoahoc_list():
    """Lấy các khóa học hiện có trong bảng LOP + sinh thêm 2 khóa mới.
    Bắt đầu từ mốc 2025 đổ đi.
    """
    conn, _ = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    existing = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT RTRIM(KHOAHOC) FROM LOP WHERE KHOAHOC IS NOT NULL ORDER BY 1")
            for r in cursor.fetchall():
                kh = r[0].strip()
                try:
                    start_year = int(kh.split('-')[0])
                    if start_year >= 2025:
                        existing.append(kh)
                except: pass
        except: pass
        finally: conn.close()
    
    import datetime
    year = datetime.datetime.now().year
    base = max(2025, year)
    extra = [f"{y}-{y + 4}" for y in range(2025, base + 3)]
    
    combined = list(dict.fromkeys(existing + extra))
    combined.sort()
    return combined


# ----------------------------------------------------------------
# History helper — lưu 10 hành động gần nhất vào session
# ----------------------------------------------------------------
def push_history(action_type, label, data):
    """
    action_type: 'THEM_LOP' | 'XOA_LOP' | 'SUA_LOP' | 'THEM_SV' | 'XOA_SV' | 'SUA_SV' |
                 'THEM_MH' | 'XOA_MH' | 'SUA_MH' | 'THEM_LTC' | 'XOA_LTC' | 'SUA_LTC'
    label: chuỗi mô tả hiển thị, VD 'Thêm sinh viên N15DCCN001 vào lớp D15CQCP01'
    data: dict các trường đủ để hoàn tác
    """
    history = session.get('history', [])
    history.insert(0, {'type': action_type, 'label': label, 'data': data})
    history = history[:10]
    session['history'] = history
    session.modified = True


def check_action_undoable(action, cursor):
    """
    Kiểm tra xem một hành động lịch sử có đủ điều kiện để hoàn tác hay không.
    Trả về (can_undo: bool, reason: str)
    """
    atype = action.get('type')
    d = action.get('data', {})
    
    # --- Môn học ---
    if atype == 'THEM_MH':
        # Hoàn tác = Xóa môn học
        mamh = d.get('mamh')
        cursor.execute("SELECT COUNT(*) FROM MONHOC WHERE MAMH = ?", (mamh,))
        if cursor.fetchone()[0] == 0:
            return False, "Môn học đã bị xóa hoặc không tồn tại."
        # Chặn nếu có bất kỳ lớp tín chỉ nào tham chiếu (dù hủy hay hoạt động)
        cursor.execute("SELECT COUNT(*) FROM LOPTINCHI WHERE MAMH = ?", (mamh,))
        if cursor.fetchone()[0] > 0:
            return False, "Môn học đã phát sinh Lớp tín chỉ."
        return True, ""
        
    elif atype == 'XOA_MH':
        # Hoàn tác = Khôi phục (Thêm lại) môn học
        mamh = d.get('mamh')
        tenmh = d.get('tenmh')
        cursor.execute("SELECT COUNT(*) FROM MONHOC WHERE MAMH = ?", (mamh,))
        if cursor.fetchone()[0] > 0:
            return False, "Mã môn học này đã được tạo mới trong hệ thống."
        cursor.execute("SELECT COUNT(*) FROM MONHOC WHERE TENMH = ?", (tenmh,))
        if cursor.fetchone()[0] > 0:
            return False, "Tên môn học đã được sử dụng cho môn khác."
        return True, ""
        
    elif atype == 'SUA_MH':
        # Hoàn tác = Khôi phục lại tên/số tiết cũ
        mamh = d.get('mamh')
        tenmh_cu = d.get('tenmh_cu')
        cursor.execute("SELECT COUNT(*) FROM MONHOC WHERE MAMH = ?", (mamh,))
        if cursor.fetchone()[0] == 0:
            return False, "Môn học không tồn tại."
        cursor.execute("SELECT COUNT(*) FROM MONHOC WHERE TENMH = ? AND MAMH <> ?", (tenmh_cu, mamh))
        if cursor.fetchone()[0] > 0:
            return False, f"Tên môn học cũ '{tenmh_cu}' đã được gán cho môn học khác."
            
        # Nếu hoàn tác làm thay đổi số tiết LT/TH, và môn này đã có đăng ký/điểm số
        cursor.execute("SELECT SOTIET_LT, SOTIET_TH FROM MONHOC WHERE MAMH = ?", (mamh,))
        row = cursor.fetchone()
        if row:
            curr_lt, curr_th = row[0], row[1]
            old_lt = d.get('lt_cu')
            old_th = d.get('th_cu')
            if curr_lt != old_lt or curr_th != old_th:
                cursor.execute("""
                    SELECT COUNT(*) FROM DANGKY DK 
                    JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC 
                    WHERE LTC.MAMH = ? AND (DK.HUYDANGKY = 0 OR DK.HUYDANGKY IS NULL)
                """, (mamh,))
                if cursor.fetchone()[0] > 0:
                    return False, "Không thể hoàn tác số tiết: Môn học đã phát sinh SV đăng ký học."
        return True, ""

    # --- Lớp tín chỉ ---
    elif atype == 'THEM_LTC':
        # Hoàn tác = Xóa vật lý lớp tín chỉ
        maltc = d.get('maltc')
        cursor.execute("SELECT COUNT(*) FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
        if cursor.fetchone()[0] == 0:
            return False, "Lớp tín chỉ không tồn tại."
        # Chưa có SV đăng ký học
        cursor.execute("SELECT COUNT(*) FROM DANGKY WHERE MALTC = ?", (maltc,))
        if cursor.fetchone()[0] > 0:
            return False, "Lớp tín chỉ đã phát sinh sinh viên đăng ký học."
        return True, ""
        
    elif atype == 'XOA_LTC':
        # Hoàn tác = Mở lại lớp tín chỉ (set HUYLOP = 0)
        maltc = d.get('maltc')
        cursor.execute("SELECT NIENKHOA, HOCKY, MAMH, NHOM, HUYLOP FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
        row = cursor.fetchone()
        if not row:
            return False, "Lớp tín chỉ không tồn tại."
        nienkhoa, hocky, mamh, nhom, huylop = row[0].strip(), row[1], row[2].strip(), row[3], row[4]
        if huylop == 0:
            return False, "Lớp tín chỉ hiện đang hoạt động."
            
        # Không được trùng tổ hợp đang hoạt động khác
        cursor.execute("""
            SELECT COUNT(*) FROM LOPTINCHI 
            WHERE NIENKHOA = ? AND HOCKY = ? AND MAMH = ? AND NHOM = ? AND HUYLOP = 0 AND MALTC <> ?
        """, (nienkhoa, hocky, mamh, nhom, maltc))
        if cursor.fetchone()[0] > 0:
            return False, f"Trùng tổ hợp Môn học, Nhóm {nhom}, HK{hocky}, NK{nienkhoa} với lớp đang hoạt động khác."
            
        # Môn học cũ phải còn tồn tại
        cursor.execute("SELECT COUNT(*) FROM MONHOC WHERE MAMH = ?", (mamh,))
        if cursor.fetchone()[0] == 0:
            return False, f"Môn học '{mamh}' của lớp tín chỉ đã bị xóa khỏi hệ thống."
        return True, ""
        
    elif atype == 'SUA_LTC':
        # Hoàn tác = Cập nhật lại thông tin cũ
        maltc = d.get('maltc')
        cursor.execute("SELECT NIENKHOA, HOCKY, MAMH, NHOM, MAGV, SOSVTOITHIEU FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
        row = cursor.fetchone()
        if not row:
            return False, "Lớp tín chỉ không tồn tại."
            
        curr_nk, curr_hk, curr_mh, curr_nhom, curr_gv, curr_sosv = row[0].strip(), row[1], row[2].strip(), row[3], row[4].strip(), row[5]
        old_nk = d.get('nienkhoa_cu')
        old_hk = d.get('hocky_cu')
        old_mh = d.get('mamh_cu')
        old_nhom = d.get('nhom_cu')
        old_gv = d.get('magv_cu')
        old_sosv = d.get('sosv_cu')
        
        # Nếu khôi phục thông tin cốt lõi (NK, HK, MH, Nhóm)
        if curr_nk != old_nk or curr_hk != old_hk or curr_mh != old_mh or curr_nhom != old_nhom:
            cursor.execute("""
                SELECT COUNT(*) FROM LOPTINCHI 
                WHERE NIENKHOA = ? AND HOCKY = ? AND MAMH = ? AND NHOM = ? AND HUYLOP = 0 AND MALTC <> ?
            """, (old_nk, old_hk, old_mh, old_nhom, maltc))
            if cursor.fetchone()[0] > 0:
                return False, "Tổ hợp cũ trùng với Lớp tín chỉ đang hoạt động khác."
                
            cursor.execute("SELECT COUNT(*) FROM MONHOC WHERE MAMH = ?", (old_mh,))
            if cursor.fetchone()[0] == 0:
                return False, f"Môn học cũ '{old_mh}' không tồn tại."
                
            # Đảm bảo chưa có SV đăng ký học
            cursor.execute("SELECT COUNT(*) FROM DANGKY WHERE MALTC = ?", (maltc,))
            if cursor.fetchone()[0] > 0:
                return False, "Không thể hoàn tác thông tin chính (Môn/Nhóm/HK/NK) vì lớp đã có sinh viên đăng ký."
                
        # Giảng viên cũ phải còn tồn tại
        cursor.execute("SELECT COUNT(*) FROM GIANGVIEN WHERE MAGV = ?", (old_gv,))
        if cursor.fetchone()[0] == 0:
            return False, f"Giảng viên cũ '{old_gv}' không tồn tại."
            
        # Nếu khôi phục giảng viên hoặc số SV tối thiểu nhưng lớp đã có điểm
        if curr_gv != old_gv or curr_sosv != old_sosv:
            cursor.execute("""
                SELECT COUNT(*) FROM DANGKY 
                WHERE MALTC = ? AND (DIEM_CC IS NOT NULL OR DIEM_GK IS NOT NULL OR DIEM_CK IS NOT NULL)
            """, (maltc,))
            if cursor.fetchone()[0] > 0:
                return False, "Không thể hoàn tác thông tin vì lớp đã được nhập điểm."
                
        return True, ""

    # --- Các hành động khác (Khoa, Lớp, Sinh viên, Giảng viên) ---
    elif atype == 'THEM_LOP':
        malop = d.get('malop')
        cursor.execute("SELECT COUNT(*) FROM LOP WHERE MALOP = ?", (malop,))
        if cursor.fetchone()[0] == 0:
            return False, "Lớp không tồn tại."
        cursor.execute("SELECT COUNT(*) FROM SINHVIEN WHERE MALOP = ?", (malop,))
        if cursor.fetchone()[0] > 0:
            return False, "Lớp đã phát sinh sinh viên."
        return True, ""
        
    elif atype == 'XOA_LOP':
        malop = d.get('malop')
        cursor.execute("SELECT COUNT(*) FROM LOP WHERE MALOP = ?", (malop,))
        if cursor.fetchone()[0] > 0:
            return False, "Lớp này đã tồn tại lại trong hệ thống."
        return True, ""
        
    elif atype == 'SUA_LOP':
        malop = d.get('malop')
        cursor.execute("SELECT COUNT(*) FROM LOP WHERE MALOP = ?", (malop,))
        if cursor.fetchone()[0] == 0:
            return False, "Lớp không tồn tại."
        return True, ""
        
    elif atype == 'THEM_SV':
        masv = d.get('masv')
        cursor.execute("SELECT COUNT(*) FROM SINHVIEN WHERE MASV = ?", (masv,))
        if cursor.fetchone()[0] == 0:
            return False, "Sinh viên không tồn tại."
        cursor.execute("SELECT COUNT(*) FROM DANGKY WHERE MASV = ?", (masv,))
        if cursor.fetchone()[0] > 0:
            return False, "Sinh viên đã đăng ký học Lớp tín chỉ."
        return True, ""
        
    elif atype == 'XOA_SV':
        masv = d.get('masv')
        cursor.execute("SELECT COUNT(*) FROM SINHVIEN WHERE MASV = ?", (masv,))
        if cursor.fetchone()[0] > 0:
            return False, "Sinh viên này đã tồn tại lại trong hệ thống."
        malop = d.get('malop')
        cursor.execute("SELECT COUNT(*) FROM LOP WHERE MALOP = ?", (malop,))
        if cursor.fetchone()[0] == 0:
            return False, f"Lớp '{malop}' của sinh viên đã bị xóa."
        return True, ""
        
    elif atype == 'SUA_SV':
        masv = d.get('masv')
        cursor.execute("SELECT COUNT(*) FROM SINHVIEN WHERE MASV = ?", (masv,))
        if cursor.fetchone()[0] == 0:
            return False, "Sinh viên không tồn tại."
        malop_cu = d.get('malop_cu')
        cursor.execute("SELECT COUNT(*) FROM LOP WHERE MALOP = ?", (malop_cu,))
        if cursor.fetchone()[0] == 0:
            return False, f"Lớp cũ '{malop_cu}' của sinh viên không tồn tại."
        return True, ""
        
    # Thêm check cho Khoa và Giảng viên
    elif atype == 'THEM_KHOA':
        makhoa = d.get('makhoa')
        cursor.execute("SELECT COUNT(*) FROM KHOA WHERE MAKHOA = ?", (makhoa,))
        if cursor.fetchone()[0] == 0:
            return False, "Khoa không tồn tại."
        cursor.execute("SELECT (SELECT COUNT(*) FROM LOP WHERE MAKHOA=?) + (SELECT COUNT(*) FROM GIANGVIEN WHERE MAKHOA=?)", (makhoa, makhoa))
        if cursor.fetchone()[0] > 0:
            return False, "Khoa đã có lớp học hoặc giảng viên trực thuộc."
        return True, ""
        
    elif atype == 'XOA_KHOA':
        makhoa = d.get('makhoa')
        cursor.execute("SELECT COUNT(*) FROM KHOA WHERE MAKHOA = ?", (makhoa,))
        if cursor.fetchone()[0] > 0:
            return False, "Khoa này đã tồn tại lại trong hệ thống."
        return True, ""
        
    elif atype == 'SUA_KHOA':
        makhoa = d.get('makhoa')
        cursor.execute("SELECT COUNT(*) FROM KHOA WHERE MAKHOA = ?", (makhoa,))
        if cursor.fetchone()[0] == 0:
            return False, "Khoa không tồn tại."
        return True, ""
        
    elif atype == 'THEM_GV':
        magv = d.get('magv')
        cursor.execute("SELECT COUNT(*) FROM GIANGVIEN WHERE MAGV = ?", (magv,))
        if cursor.fetchone()[0] == 0:
            return False, "Giảng viên không tồn tại."
        cursor.execute("SELECT COUNT(*) FROM LOPTINCHI WHERE MAGV = ?", (magv,))
        if cursor.fetchone()[0] > 0:
            return False, "Giảng viên đã được phân công dạy Lớp tín chỉ."
        return True, ""
        
    elif atype == 'XOA_GV':
        magv = d.get('magv')
        cursor.execute("SELECT COUNT(*) FROM GIANGVIEN WHERE MAGV = ?", (magv,))
        if cursor.fetchone()[0] > 0:
            return False, "Giảng viên này đã tồn tại lại trong hệ thống."
        return True, ""
        
    elif atype == 'SUA_GV':
        magv = d.get('magv')
        cursor.execute("SELECT COUNT(*) FROM GIANGVIEN WHERE MAGV = ?", (magv,))
        if cursor.fetchone()[0] == 0:
            return False, "Giảng viên không tồn tại."
        return True, ""

    # Thêm check cho các action biến động Lớp tín chỉ nâng cao
    elif atype == 'XOA_VINH_VIEN_LTC':
        # Hoàn tác = Thêm lại lớp tín chỉ
        cursor.execute("""
            SELECT COUNT(*) FROM LOPTINCHI 
            WHERE NIENKHOA = ? AND HOCKY = ? AND MAMH = ? AND NHOM = ? AND HUYLOP = 0
        """, (d.get('nienkhoa'), d.get('hocky'), d.get('mamh'), d.get('nhom')))
        if cursor.fetchone()[0] > 0:
            return False, "Tổ hợp Niên khóa, Học kỳ, Môn, Nhóm đã có lớp khác đang hoạt động."
            
        cursor.execute("SELECT COUNT(*) FROM MONHOC WHERE MAMH = ?", (d.get('mamh'),))
        if cursor.fetchone()[0] == 0:
            return False, f"Môn học '{d.get('mamh')}' không còn tồn tại."
            
        cursor.execute("SELECT COUNT(*) FROM GIANGVIEN WHERE MAGV = ?", (d.get('magv'),))
        if cursor.fetchone()[0] == 0:
            return False, f"Giảng viên '{d.get('magv')}' không còn tồn tại."
        return True, ""
        
    elif atype == 'MO_LAI_LTC':
        # Hoàn tác = Hủy lớp tín chỉ
        maltc = d.get('maltc')
        cursor.execute("SELECT HUYLOP FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
        row = cursor.fetchone()
        if not row:
            return False, "Lớp tín chỉ không tồn tại."
        if row[0] == 1:
            return False, "Lớp tín chỉ đã ở trạng thái hủy."
            
        # Kiểm tra xem lớp đã có điểm học tập chưa
        cursor.execute("""
            SELECT COUNT(*) FROM DANGKY 
            WHERE MALTC = ? AND (DIEM_CC IS NOT NULL OR DIEM_GK IS NOT NULL OR DIEM_CK IS NOT NULL)
        """, (maltc,))
        if cursor.fetchone()[0] > 0:
            return False, "Lớp đã có sinh viên được nhập điểm, không thể hủy."
        return True, ""

    return True, ""


# ----------------------------------------------------------------
# Decorator phân quyền
# ----------------------------------------------------------------
def require_group(*groups):
    """Decorator kiểm tra session['group'] có trong danh sách groups không."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            if session.get('group') not in groups:
                flash('Bạn không có quyền truy cập chức năng này.')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


# ----------------------------------------------------------------
# Auth routes
# ----------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    khoa_list = get_danh_sach_khoa()

    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        khoa = request.form.get('khoa', '').strip()

        if not username or not password:
            flash('Vui lòng nhập đầy đủ thông tin.')
            return render_template('login.html', khoa_list=khoa_list)

        if role == 'GV':
            conn, error = get_db_connection(username, password)
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT USER_NAME()")
                    db_user = cursor.fetchone()[0].strip()
                    cursor.execute("EXEC SP_DANGNHAP_GV ?", (db_user,))
                    row = cursor.fetchone()

                    if row:
                        magv = row.USER_NAME.strip()
                        
                        # Lấy Database Role chuẩn xác thông qua security context hiện tại
                        cursor.execute("SELECT IS_MEMBER('PGV'), IS_MEMBER('KHOA')")
                        is_pgv, is_khoa = cursor.fetchone()
                        
                        if is_pgv == 1:
                            nhom = 'PGV'
                        elif is_khoa == 1:
                            nhom = 'KHOA'
                        else:
                            # Lấy Database Role trực tiếp từ SQL Server
                            cursor.execute("SELECT R.name FROM sys.database_role_members RM JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id WHERE U.name = ?", (magv,))
                            role_row = cursor.fetchone()
                            
                            if role_row:
                                nhom = role_row.name.strip()
                            else:
                                # Mặc định an toàn hoặc fallback nếu chưa cấu hình Role trong DB
                                nhom = 'PGV' if magv in ['GV01', 'GV05'] else 'KHOA'
                            
                        session['username'] = magv
                        session['hoten'] = row.HOTEN.strip()
                        session['group'] = nhom
                        session['tenkhoa'] = row.TENGROUP.strip()
                        session['role'] = 'GV'
                        
                        # [PLANT_NHAPDIEM_Flicker_Cancel_Khoa_2026] Truy vấn mã khoa từ bảng GIANGVIEN
                        cursor.execute("SELECT MAKHOA FROM GIANGVIEN WHERE MAGV=?", (magv,))
                        gv_khoa_row = cursor.fetchone()
                        session['khoa'] = gv_khoa_row[0].strip().upper() if gv_khoa_row else ''
                        
                        session['db_login'] = username
                        session['db_pass'] = password
                        # Lưu MAKHOA vào session để lọc dữ liệu theo khoa cho nhóm KHOA
                        cursor.execute("SELECT MAKHOA FROM GIANGVIEN WHERE MAGV = ?", (magv,))
                        gv_row = cursor.fetchone()
                        session['makhoa'] = gv_row.MAKHOA.strip() if gv_row else ''
                        conn.close()
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Không tìm thấy thông tin giảng viên tương ứng.')
                except Exception as e:
                    flash(f'Lỗi: {str(e)}. Đảm bảo đã chạy setup_login.sql trên SSMS.')
                conn.close()
            else:
                flash('Sai tài khoản hoặc mật khẩu! (SQL Server Authentication)')

        elif role == 'SV':
            conn, error = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("EXEC SP_DANGNHAP_SV ?, ?", (username, password))
                    row = cursor.fetchone()

                    if not row:
                        cursor.execute("EXEC SP_DANGNHAP_SV ?, ?", (username, ''))
                        row = cursor.fetchone()

                    if row:
                        session['username'] = row.USER_NAME.strip()
                        session['hoten'] = row.HOTEN.strip()
                        session['group'] = 'SV'                          # luôn là 'SV'
                        session['tenkhoa'] = row.TENGROUP.strip()         # tên khoa để hiển thị
                        session['role'] = 'SV'
                        session['khoa'] = khoa
                        session['malop'] = row.MALOP.strip() if hasattr(row, 'MALOP') and row.MALOP else ''
                        session['db_login'] = SV_SHARED_LOGIN
                        session['db_pass'] = SV_SHARED_PASSWORD
                        conn.close()
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Mã Sinh Viên hoặc Mật khẩu không đúng!')
                except Exception as e:
                    flash(f'Lỗi: {str(e)}. Đảm bảo đã chạy setup_login.sql trên SSMS.')
                conn.close()
            else:
                flash(f'Lỗi kết nối DB bằng tài khoản SV chung. Chi tiết: {error}')

    return render_template('login.html', khoa_list=khoa_list)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html',
                           hoten=session.get('hoten'),
                           role=session.get('role'),
                           group=session.get('group'),
                           tenkhoa=session.get('tenkhoa'),
                           khoa=session.get('khoa'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- API Kiểm tra trùng mã ---
@app.route('/api/check_exists')
@login_required
def check_exists():
    table = request.args.get('type')
    id_val = request.args.get('id')
    import re
    if not table or not id_val or not re.match(r'^[a-zA-Z0-9_]+$', table):
        return jsonify({'exists': False})
    
    mapping = {
        'khoa': ('KHOA', 'MAKHOA'),
        'lop': ('LOP', 'MALOP'),
        'giangvien': ('GIANGVIEN', 'MAGV'),
        'monhoc': ('MONHOC', 'MAMH'),
        'sinhvien': ('SINHVIEN', 'MASV')
    }
    if table not in mapping:
        return jsonify({'exists': False})
        
    conn, _ = get_db()
    exists = False
    if conn:
        try:
            cursor = conn.cursor()
            tbl, col = mapping[table]
            cursor.execute(f"SELECT COUNT(*) FROM {tbl} WHERE {col} = ?", (id_val,))
            count = cursor.fetchone()[0]
            exists = count > 0
        except:
            pass
        finally:
            conn.close()
    return jsonify({'exists': exists})


# --- API Kiểm tra ràng buộc để khóa nút Xóa ---
@app.route('/api/can_delete')
@login_required
def can_delete():
    target = request.args.get('type')
    id_val = request.args.get('id')
    if not target or not id_val:
        return jsonify({'can_delete': True})
    
    conn, _ = get_db()
    can = True
    if conn:
        try:
            cursor = conn.cursor()
            if target == 'khoa':
                cursor.execute("SELECT (SELECT COUNT(*) FROM LOP WHERE MAKHOA=?) + (SELECT COUNT(*) FROM GIANGVIEN WHERE MAKHOA=?)", (id_val, id_val))
                can = cursor.fetchone()[0] == 0
            elif target == 'lop':
                cursor.execute("SELECT COUNT(*) FROM SINHVIEN WHERE MALOP=?", (id_val,))
                can = cursor.fetchone()[0] == 0
            elif target == 'monhoc':
                cursor.execute("SELECT COUNT(*) FROM LOPTINCHI WHERE MAMH=?", (id_val,))
                can = cursor.fetchone()[0] == 0
            elif target == 'giangvien':
                cursor.execute("SELECT COUNT(*) FROM LOPTINCHI WHERE MAGV=?", (id_val,))
                can = cursor.fetchone()[0] == 0
            elif target == 'sinhvien':
                cursor.execute("SELECT COUNT(*) FROM DANGKY WHERE MASV=?", (id_val,))
                can = cursor.fetchone()[0] == 0
            elif target == 'loptinchi':
                # Chỉ không cho hủy khi đã nhập điểm cho ít nhất 1 sinh viên
                cursor.execute("SELECT COUNT(*) FROM DANGKY WHERE MALTC=? AND (DIEM_CC IS NOT NULL OR DIEM_GK IS NOT NULL OR DIEM_CK IS NOT NULL)", (id_val,))
                can = cursor.fetchone()[0] == 0
        except:
            can = False
        finally:
            conn.close()
    return jsonify({'can_delete': can})


# ----------------------------------------------------------------
# History API
# ----------------------------------------------------------------
@app.route('/history')
@login_required
def history_get():
    """Trả về 10 hành động gần nhất dạng JSON kèm điều kiện check hoàn tác realtime."""
    history = session.get('history', [])
    conn, _ = get_db()
    if not conn:
        return jsonify(history)
        
    updated_history = []
    try:
        cursor = conn.cursor()
        for action in history:
            can_undo, reason = check_action_undoable(action, cursor)
            act_copy = dict(action)
            act_copy['can_undo'] = can_undo
            act_copy['cannot_undo_reason'] = reason
            updated_history.append(act_copy)
    except Exception as e:
        print("Lỗi check undoable:", e)
        updated_history = history
    finally:
        conn.close()
        
    return jsonify(updated_history)


@app.route('/history/undo', methods=['POST'])
@login_required
def history_undo():
    """Thực hiện hoàn tác một hành động theo index."""
    idx = request.json.get('index', 0)
    history = session.get('history', [])
    if idx < 0 or idx >= len(history):
        return jsonify({'ok': False, 'msg': 'Không tìm thấy hành động'}), 400
    action = history[idx]
    atype = action['type']
    d = action['data']
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
    try:
        cursor = conn.cursor()
        
        # BẢO MẬT SERVER-SIDE: Kiểm tra lại điều kiện nghiệp vụ trước khi thực thi hoàn tác
        can_undo, reason = check_action_undoable(action, cursor)
        if not can_undo:
            return jsonify({'ok': False, 'msg': f'Không đủ điều kiện hoàn tác: {reason}'}), 400
            
        msg = ''
        # --- Hoàn tác lớp ---
        if atype == 'THEM_LOP':
            cursor.execute("EXEC SP_XOA_LOP ?", (d['malop'],))
            msg = f"Đã xóa lớp {d['malop']}"
        elif atype == 'XOA_LOP':
            cursor.execute("EXEC SP_THEM_LOP ?, ?, ?, ?",
                           (d['malop'], d['tenlop'], d['khoahoc'], d['makhoa']))
            msg = f"Đã khôi phục lớp {d['malop']}"
        elif atype == 'SUA_LOP':
            cursor.execute("EXEC SP_SUA_LOP ?, ?, ?, ?",
                           (d['malop'], d['tenlop_cu'], d['khoahoc_cu'], d['makhoa_cu']))
            msg = f"Đã hoàn tác sửa lớp {d['malop']}"
        # --- Hoàn tác sinh viên ---
        elif atype == 'THEM_SV':
            cursor.execute("EXEC SP_XOA_SV ?", (d['masv'],))
            msg = f"Đã xóa sinh viên {d['masv']}"
        elif atype == 'XOA_SV':
            cursor.execute("EXEC SP_THEM_SV ?, ?, ?, ?, ?, ?, ?",
                           (d['masv'], d['ho'], d['ten'], d['phai'],
                            d['diachi'], d['ngaysinh'], d['malop']))
            msg = f"Đã khôi phục sinh viên {d['masv']}"
        elif atype == 'SUA_SV':
            cursor.execute("EXEC SP_SUA_SV ?, ?, ?, ?, ?, ?, ?",
                           (d['masv'], d['ho_cu'], d['ten_cu'], d['phai_cu'],
                            d['diachi_cu'], d['ngaysinh_cu'], d['malop_cu']))
            msg = f"Đã hoàn tác sửa sinh viên {d['masv']}"
        # --- Hoàn tác môn học ---
        elif atype == 'THEM_MH':
            cursor.execute("EXEC SP_XOA_MONHOC ?", (d['mamh'],))
            msg = f"Đã xóa môn học {d['mamh']}"
        elif atype == 'XOA_MH':
            cursor.execute("EXEC SP_THEM_MONHOC ?, ?, ?, ?",
                           (d['mamh'], d['tenmh'], d['sotiet_lt'], d['sotiet_th']))
            msg = f"Đã khôi phục môn học {d['mamh']}"
        elif atype == 'SUA_MH':
            cursor.execute("EXEC SP_SUA_MONHOC ?, ?, ?, ?",
                           (d['mamh'], d['tenmh_cu'], d['lt_cu'], d['th_cu']))
            msg = f"Đã hoàn tác sửa môn học {d['mamh']}"
        # --- Hoàn tác lớp tín chỉ ---
        elif atype == 'THEM_LTC':
            # Thêm LTC -> hoàn tác đúng nghĩa = xóa vật lý nếu chưa phát sinh đăng ký.
            cursor.execute("EXEC SP_HOANTAC_THEM_LOPTINCHI ?", (d['maltc'],))
            msg = f"Đã xóa lớp tín chỉ vừa tạo #{d['maltc']}"
        elif atype == 'XOA_LTC':
            # Hủy LTC → hoàn tác = mở lại (set HUYLOP=0)
            cursor.execute("EXEC SP_PHUCHOI_LOPTINCHI ?", (d['maltc'],))
            msg = f"Đã mở lại lớp tín chỉ #{d['maltc']}"
        elif atype == 'SUA_LTC':
            cursor.execute("EXEC SP_SUA_LOPTINCHI ?, ?, ?, ?, ?, ?, ?, ?",
                           (d['maltc'], d['nienkhoa_cu'], d['hocky_cu'],
                            d['mamh_cu'], d['nhom_cu'], d['magv_cu'],
                            d['makhoa_cu'], d['sosv_cu']))
            msg = f"Đã hoàn tác sửa lớp tín chỉ #{d['maltc']}"
        elif atype == 'XOA_VINH_VIEN_LTC':
            cursor.execute("EXEC SP_THEM_LOPTINCHI ?, ?, ?, ?, ?, ?, ?",
                           (d['nienkhoa'], d['hocky'], d['mamh'], d['nhom'], 
                            d['magv'], d['makhoa'], d['sosvtoithieu']))
            msg = f"Đã khôi phục lại lớp tín chỉ cũ {d['mamh']} Nhóm {d['nhom']}"
        elif atype == 'MO_LAI_LTC':
            cursor.execute("EXEC SP_XOA_LOPTINCHI ?", (d['maltc'],))
            msg = f"Đã hủy lại lớp tín chỉ #{d['maltc']}"
        # --- Hoàn tác khoa ---
        elif atype == 'THEM_KHOA':
            cursor.execute("EXEC SP_XOA_KHOA ?", (d['makhoa'],))
            msg = f"Đã xóa khoa {d['makhoa']}"
        elif atype == 'XOA_KHOA':
            cursor.execute("EXEC SP_THEM_KHOA ?, ?",
                           (d['makhoa'], d['tenkhoa']))
            msg = f"Đã khôi phục khoa {d['makhoa']}"
        elif atype == 'SUA_KHOA':
            cursor.execute("EXEC SP_SUA_KHOA ?, ?",
                           (d['makhoa'], d['tenkhoa_cu']))
            msg = f"Đã hoàn tác sửa khoa {d['makhoa']}"
        # --- Hoàn tác giảng viên ---
        elif atype == 'THEM_GV':
            cursor.execute("EXEC SP_XOA_GIANGVIEN ?", (d['magv'],))
            msg = f"Đã xóa giảng viên {d['magv']}"
        elif atype == 'XOA_GV':
            cursor.execute("EXEC SP_THEM_GIANGVIEN ?, ?, ?, ?, ?, ?, ?",
                           (d['magv'], d['makhoa'], d['ho'], d['ten'],
                            d.get('hocvi'), d.get('hocham'), d.get('chuyenmon')))
            msg = f"Đã khôi phục giảng viên {d['magv']}"
        elif atype == 'SUA_GV':
            cursor.execute("EXEC SP_SUA_GIANGVIEN ?, ?, ?, ?, ?, ?, ?",
                           (d['magv'], d['makhoa_cu'], d['ho_cu'], d['ten_cu'],
                            d.get('hocvi_cu'), d.get('hocham_cu'), d.get('chuyenmon_cu')))
            msg = f"Đã hoàn tác sửa giảng viên {d['magv']}"
        else:
            return jsonify({'ok': False, 'msg': 'Loại hành động không hỗ trợ hoàn tác'}), 400

        row = cursor.fetchone()
        ketqua = getattr(row, 'KETQUA', None) if row else None
        thongbao = row.THONGBAO if (row and hasattr(row, 'THONGBAO')) else msg
        if ketqua is not None and int(ketqua) <= 0:
            conn.rollback()
            return jsonify({'ok': False, 'msg': thongbao}), 400

        conn.commit()
        # Xóa hành động đã undo khỏi history
        history.pop(idx)
        session['history'] = history
        session.modified = True
        return jsonify({'ok': True, 'msg': thongbao})
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()



# ----------------------------------------------------------------
# Khoa — PGV only
# ----------------------------------------------------------------
@app.route('/khoa')
@require_group('PGV')
def khoa():
    conn, _ = get_db()
    khoa_list = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GETALL_KHOA")
            khoa_list = [{'MAKHOA': r.MAKHOA.strip(), 'TENKHOA': r.TENKHOA.strip()} for r in cursor.fetchall()]
        except Exception as e:
            flash(f'Lỗi tải danh sách khoa: {e}')
        finally:
            conn.close()
    return render_template('khoa.html', khoa_list=khoa_list,
                           hoten=session.get('hoten'), group=session.get('group'))

@app.route('/khoa/them', methods=['POST'])
@require_group('PGV')
def khoa_them():
    makhoa = request.form.get('makhoa', '').strip().upper()
    tenkhoa = request.form.get('tenkhoa', '').strip()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_THEM_KHOA ?, ?", (makhoa, tenkhoa))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Thêm thành công.')
            if row and row.KETQUA == 1:
                push_history('THEM_KHOA', f'Thêm khoa {makhoa} - {tenkhoa}',
                             {'makhoa': makhoa, 'tenkhoa': tenkhoa})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('khoa'))

@app.route('/khoa/ghi', methods=['POST'])
@require_group('PGV')
def khoa_ghi():
    makhoa = request.form.get('makhoa', '').strip().upper()
    tenkhoa = request.form.get('tenkhoa', '').strip()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT TENKHOA FROM KHOA WHERE MAKHOA=?", (makhoa,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_SUA_KHOA ?, ?", (makhoa, tenkhoa))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Cập nhật thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('SUA_KHOA', f'Sửa khoa {makhoa}',
                             {'makhoa': makhoa, 'tenkhoa_cu': old.TENKHOA.strip()})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('khoa'))

@app.route('/khoa/xoa', methods=['POST'])
@require_group('PGV')
def khoa_xoa():
    makhoa = request.form.get('makhoa', '').strip().upper()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT TENKHOA FROM KHOA WHERE MAKHOA=?", (makhoa,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_XOA_KHOA ?", (makhoa,))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Xóa thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('XOA_KHOA', f'Xóa khoa {makhoa} - {old.TENKHOA.strip()}',
                             {'makhoa': makhoa, 'tenkhoa': old.TENKHOA.strip()})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('khoa'))


# ----------------------------------------------------------------
# Giảng viên — PGV only
# ----------------------------------------------------------------
@app.route('/giangvien')
@require_group('PGV')
def giangvien():
    conn, _ = get_db()
    gv_list, khoa_list = [], get_danh_sach_khoa()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GETALL_GIANGVIEN")
            gv_list = [{'MAGV': r.MAGV.strip(), 'MAKHOA': r.MAKHOA.strip(),
                        'TENKHOA': r.TENKHOA.strip(), 'HOTEN': r.HOTEN.strip(),
                        'HOCVI': (r.HOCVI or '').strip(), 'HOCHAM': (r.HOCHAM or '').strip(),
                        'CHUYENMON': (r.CHUYENMON or '').strip()} for r in cursor.fetchall()]
        except Exception as e:
            flash(f'Lỗi tải danh sách giảng viên: {e}')
        finally:
            conn.close()
    return render_template('giangvien.html', gv_list=gv_list, khoa_list=khoa_list,
                           hoten=session.get('hoten'), group=session.get('group'))

@app.route('/giangvien/them', methods=['POST'])
@require_group('PGV')
def giangvien_them():
    magv = request.form.get('magv', '').strip().upper()
    makhoa = request.form.get('makhoa', '').strip().upper()
    ho = request.form.get('ho', '').strip()
    ten = request.form.get('ten', '').strip()
    hocvi = request.form.get('hocvi', '').strip()
    hocham = request.form.get('hocham', '').strip()
    chuyenmon = request.form.get('chuyenmon', '').strip()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_THEM_GIANGVIEN ?, ?, ?, ?, ?, ?, ?",
                           (magv, makhoa, ho, ten, hocvi or None, hocham or None, chuyenmon or None))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Thêm thành công.')
            if row and row.KETQUA == 1:
                push_history('THEM_GV', f'Thêm GV {magv} - {ho} {ten}',
                             {'magv': magv, 'makhoa': makhoa, 'ho': ho, 'ten': ten,
                              'hocvi': hocvi, 'hocham': hocham, 'chuyenmon': chuyenmon})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('giangvien'))

@app.route('/giangvien/ghi', methods=['POST'])
@require_group('PGV')
def giangvien_ghi():
    magv = request.form.get('magv', '').strip().upper()
    makhoa = request.form.get('makhoa', '').strip().upper()
    ho = request.form.get('ho', '').strip()
    ten = request.form.get('ten', '').strip()
    hocvi = request.form.get('hocvi', '').strip()
    hocham = request.form.get('hocham', '').strip()
    chuyenmon = request.form.get('chuyenmon', '').strip()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT HO,TEN,MAKHOA,HOCVI,HOCHAM,CHUYENMON FROM GIANGVIEN WHERE MAGV=?", (magv,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_SUA_GIANGVIEN ?, ?, ?, ?, ?, ?, ?",
                           (magv, makhoa, ho, ten, hocvi or None, hocham or None, chuyenmon or None))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Cập nhật thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('SUA_GV', f'Sửa GV {magv}',
                             {'magv': magv, 'makhoa_cu': old.MAKHOA.strip(),
                              'ho_cu': old.HO.strip(), 'ten_cu': old.TEN.strip(),
                              'hocvi_cu': (old.HOCVI or '').strip(),
                              'hocham_cu': (old.HOCHAM or '').strip(),
                              'chuyenmon_cu': (old.CHUYENMON or '').strip()})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('giangvien'))

@app.route('/giangvien/xoa', methods=['POST'])
@require_group('PGV')
def giangvien_xoa():
    magv = request.form.get('magv', '').strip().upper()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT HO,TEN,MAKHOA,HOCVI,HOCHAM,CHUYENMON FROM GIANGVIEN WHERE MAGV=?", (magv,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_XOA_GIANGVIEN ?", (magv,))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Xóa thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('XOA_GV', f'Xóa GV {magv} - {old.HO.strip()} {old.TEN.strip()}',
                             {'magv': magv, 'makhoa': old.MAKHOA.strip(),
                              'ho': old.HO.strip(), 'ten': old.TEN.strip(),
                              'hocvi': (old.HOCVI or '').strip(),
                              'hocham': (old.HOCHAM or '').strip(),
                              'chuyenmon': (old.CHUYENMON or '').strip()})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('giangvien'))


# ----------------------------------------------------------------
# Môn học — PGV only
# ----------------------------------------------------------------
@app.route('/monhoc')
@require_group('PGV')
def monhoc():
    conn, _ = get_db()
    monhoc_list = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GET_ALL_MONHOC")
            rows = cursor.fetchall()
            for r in rows:
                m = {'MAMH': r.MAMH.strip(), 'TENMH': r.TENMH.strip(), 
                     'SOTIET_LT': r.SOTIET_LT, 'SOTIET_TH': r.SOTIET_TH}
                
                # Kiểm tra khóa dữ liệu môn học
                cursor.execute("EXEC SP_KIEMTRA_LICHSU_MONHOC ?", (m['MAMH'],))
                h = cursor.fetchone()
                m['IS_FROZEN'] = (h.DUOC_DAY_QUAKHU == 1) if h else False
                monhoc_list.append(m)
        except Exception as e:
            flash(f'Lỗi tải danh sách môn học: {e}')
        finally:
            conn.close()
    return render_template('monhoc.html', monhoc_list=monhoc_list,
                           hoten=session.get('hoten'), group=session.get('group'))


@app.route('/monhoc/them', methods=['POST'])
@require_group('PGV')
def monhoc_them():
    mamh = request.form.get('mamh', '').strip().upper()
    tenmh = request.form.get('tenmh', '').strip()
    sotiet_lt = request.form.get('sotiet_lt', 0)
    sotiet_th = request.form.get('sotiet_th', 0)
    
    try:
        sotiet_lt = int(sotiet_lt)
        sotiet_th = int(sotiet_th)
    except ValueError:
        flash('Số tiết lý thuyết và số tiết thực hành phải là số nguyên.')
        return redirect(url_for('monhoc'))
        
    if sotiet_lt < 0 or sotiet_th < 0:
        flash('Số tiết không được mang giá trị âm.')
        return redirect(url_for('monhoc'))
        
    if sotiet_lt + sotiet_th <= 0:
        flash('Tổng số tiết phải lớn hơn 0.')
        return redirect(url_for('monhoc'))

    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_THEM_MONHOC ?, ?, ?, ?", (mamh, tenmh, sotiet_lt, sotiet_th))
            row = cursor.fetchone()
            conn.commit()
            tb = row.THONGBAO if row else 'Thêm thành công.'
            flash(tb)
            if row and row.KETQUA == 1:
                push_history('THEM_MH', f'Thêm môn học {mamh} — {tenmh}',
                             {'mamh': mamh, 'tenmh': tenmh,
                              'sotiet_lt': sotiet_lt, 'sotiet_th': sotiet_th})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('monhoc'))


@app.route('/monhoc/ghi', methods=['POST'])
@require_group('PGV')
def monhoc_ghi():
    mamh = request.form.get('mamh', '').strip().upper()
    tenmh = request.form.get('tenmh', '').strip()
    sotiet_lt = request.form.get('sotiet_lt', 0)
    sotiet_th = request.form.get('sotiet_th', 0)
    
    try:
        sotiet_lt = int(sotiet_lt)
        sotiet_th = int(sotiet_th)
    except ValueError:
        flash('Số tiết phải là số nguyên.')
        return redirect(url_for('monhoc'))
        
    if sotiet_lt < 0 or sotiet_th < 0:
        flash('Số tiết không được mang giá trị âm.')
        return redirect(url_for('monhoc'))
        
    if sotiet_lt + sotiet_th <= 0:
        flash('Tổng số tiết phải lớn hơn 0.')
        return redirect(url_for('monhoc'))

    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Lấy dữ liệu cũ để kiểm tra thay đổi số tiết
            cursor.execute("SELECT TENMH, SOTIET_LT, SOTIET_TH FROM MONHOC WHERE MAMH=?", (mamh,))
            old = cursor.fetchone()
            if old:
                old_lt = old.SOTIET_LT
                old_th = old.SOTIET_TH
                # RÀNG BUỘC: Nếu đổi số tiết, môn học phải chưa phát sinh đăng ký ở bất kỳ lớp tín chỉ nào
                if sotiet_lt != old_lt or sotiet_th != old_th:
                    cursor.execute("""
                        SELECT COUNT(*) FROM DANGKY DK
                        INNER JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC
                        WHERE LTC.MAMH = ? AND (DK.HUYDANGKY=0 OR DK.HUYDANGKY IS NULL)
                    """, (mamh,))
                    if cursor.fetchone()[0] > 0:
                        flash('Không thể sửa đổi số tiết của môn học: Môn học đã phát sinh sinh viên đăng ký học.')
                        return redirect(url_for('monhoc'))
            
            cursor.execute("EXEC SP_SUA_MONHOC ?, ?, ?, ?", (mamh, tenmh, sotiet_lt, sotiet_th))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Cập nhật thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('SUA_MH', f'Sửa môn học {mamh}',
                             {'mamh': mamh,
                              'tenmh_cu': old.TENMH.strip(), 'lt_cu': old_lt, 'th_cu': old_th})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('monhoc'))


@app.route('/monhoc/xoa', methods=['POST'])
@require_group('PGV')
def monhoc_xoa():
    mamh = request.form.get('mamh', '').strip().upper()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            # RÀNG BUỘC: Chặn xóa nếu môn học đã từng được sử dụng để mở lớp tín chỉ (tránh lỗi khóa ngoại DB)
            cursor.execute("SELECT COUNT(*) FROM LOPTINCHI WHERE MAMH = ?", (mamh,))
            if cursor.fetchone()[0] > 0:
                flash('Không thể xóa: Môn học đã được sử dụng để mở Lớp tín chỉ.')
                return redirect(url_for('monhoc'))
                
            # Lấy dữ liệu cũ để lưu history
            cursor.execute("SELECT TENMH, SOTIET_LT, SOTIET_TH FROM MONHOC WHERE MAMH=?", (mamh,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_XOA_MONHOC ?", (mamh,))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Xóa thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('XOA_MH', f'Xóa môn học {mamh} — {old.TENMH.strip()}',
                             {'mamh': mamh, 'tenmh': old.TENMH.strip(),
                              'sotiet_lt': old.SOTIET_LT, 'sotiet_th': old.SOTIET_TH})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('monhoc'))


# ----------------------------------------------------------------
# Lớp — PGV only
# ----------------------------------------------------------------
@app.route('/lop')
@require_group('PGV')
def lop():
    conn, _ = get_db()
    lop_list = []
    khoa_list = get_danh_sach_khoa()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GET_DSLOP NULL")
            rows = cursor.fetchall()
            lop_list = [{'MALOP': r.MALOP.strip(), 'TENLOP': r.TENLOP.strip(),
                         'KHOAHOC': r.KHOAHOC.strip(), 'MAKHOA': r.MAKHOA.strip(),
                         'TENKHOA': r.TENKHOA.strip(),
                         'IS_FROZEN': is_frozen(r.KHOAHOC.strip())} for r in rows]
        except Exception as e:
            flash(f'Lỗi tải danh sách lớp: {e}')
        finally:
            conn.close()
    return render_template('lop.html', lop_list=lop_list, khoa_list=khoa_list,
                           khoahoc_list=get_khoahoc_list(),
                           hoten=session.get('hoten'), group=session.get('group'))


@app.route('/lop/them', methods=['POST'])
@require_group('PGV')
def lop_them():
    malop = request.form.get('malop', '').strip().upper()
    tenlop = request.form.get('tenlop', '').strip()
    khoahoc = request.form.get('khoahoc', '').strip()
    makhoa = request.form.get('makhoa', '').strip().upper()
    conn, _ = get_db()
    if conn:
        try:
            if is_frozen(khoahoc):
                flash(f"Lỗi: Không thể thêm lớp cho khóa học {khoahoc} vì đã bị đóng băng.", "error")
                return redirect(url_for('lop'))
                
            cursor = conn.cursor()
            cursor.execute("EXEC SP_THEM_LOP ?, ?, ?, ?", (malop, tenlop, khoahoc, makhoa))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Thêm thành công.')
            if row and row.KETQUA == 1:
                push_history('THEM_LOP', f'Thêm lớp {malop} — {tenlop}',
                             {'malop': malop, 'tenlop': tenlop, 'khoahoc': khoahoc, 'makhoa': makhoa})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('lop'))


@app.route('/lop/ghi', methods=['POST'])
@require_group('PGV')
def lop_ghi():
    malop = request.form.get('malop', '').strip().upper()
    tenlop = request.form.get('tenlop', '').strip()
    khoahoc = request.form.get('khoahoc', '').strip()
    makhoa = request.form.get('makhoa', '').strip().upper()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA ĐÓNG BĂNG
            cursor.execute("SELECT KHOAHOC FROM LOP WHERE MALOP = ?", (malop,))
            r = cursor.fetchone()
            if r and is_frozen(r.KHOAHOC):
                flash(f"Lỗi: Lớp {malop} thuộc khóa học cũ đã bị đóng băng, không thể sửa.", "error")
                return redirect(url_for('lop'))

            cursor.execute("SELECT TENLOP, KHOAHOC, MAKHOA FROM LOP WHERE MALOP=?", (malop,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_SUA_LOP ?, ?, ?, ?", (malop, tenlop, khoahoc, makhoa))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Cập nhật thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('SUA_LOP', f'Sửa lớp {malop}',
                             {'malop': malop,
                              'tenlop_cu': old.TENLOP.strip(), 'khoahoc_cu': old.KHOAHOC.strip(),
                              'makhoa_cu': old.MAKHOA.strip()})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('lop'))


@app.route('/lop/xoa', methods=['POST'])
@require_group('PGV')
def lop_xoa():
    malop = request.form.get('malop', '').strip().upper()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA ĐÓNG BĂNG
            cursor.execute("SELECT KHOAHOC FROM LOP WHERE MALOP = ?", (malop,))
            r = cursor.fetchone()
            if r and is_frozen(r.KHOAHOC):
                flash(f"Lỗi: Không thể xóa lớp {malop} vì dữ liệu lịch sử đã bị đóng băng.", "error")
                return redirect(url_for('lop'))

            # Ràng buộc: không xóa lớp còn sinh viên
            cursor.execute("SELECT COUNT(*) FROM SINHVIEN WHERE MALOP=?", (malop,))
            so_sv = cursor.fetchone()[0]
            if so_sv > 0:
                flash(f'Không thể xóa: lớp {malop} còn {so_sv} sinh viên.')
                return redirect(url_for('lop'))
            cursor.execute("SELECT TENLOP, KHOAHOC, MAKHOA FROM LOP WHERE MALOP=?", (malop,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_XOA_LOP ?", (malop,))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Xóa thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('XOA_LOP', f'Xóa lớp {malop} — {old.TENLOP.strip()}',
                             {'malop': malop, 'tenlop': old.TENLOP.strip(),
                              'khoahoc': old.KHOAHOC.strip(), 'makhoa': old.MAKHOA.strip()})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('lop'))


# ----------------------------------------------------------------
# Sinh viên — PGV only (SubForm 2 cấp)
# ----------------------------------------------------------------
@app.route('/sinhvien')
@require_group('PGV')
def sinhvien():
    conn, _ = get_db()
    lop_list = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GET_DSLOP NULL")
            rows = cursor.fetchall()
            lop_list = [{'MALOP': r.MALOP.strip(), 'TENLOP': r.TENLOP.strip(),
                         'KHOAHOC': r.KHOAHOC.strip(), 'MAKHOA': r.MAKHOA.strip(),
                         'TENKHOA': r.TENKHOA.strip()} for r in rows]
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return render_template('sinhvien.html', lop_list=lop_list, sv_list=[],
                           malop_chon=None, khoa_list=get_danh_sach_khoa(),
                           hoten=session.get('hoten'), group=session.get('group'))


@app.route('/sinhvien/<malop>')
@require_group('PGV')
def sinhvien_theo_lop(malop):
    conn, _ = get_db()
    lop_list, sv_list = [], []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GET_DSLOP NULL")
            rows = cursor.fetchall()
            lop_list = [{'MALOP': r.MALOP.strip(), 'TENLOP': r.TENLOP.strip(),
                         'KHOAHOC': r.KHOAHOC.strip(), 'MAKHOA': r.MAKHOA.strip(),
                         'TENKHOA': r.TENKHOA.strip()} for r in rows]
            
            cursor.execute("SELECT KHOAHOC FROM LOP WHERE MALOP = ?", (malop,))
            r_lop = cursor.fetchone()
            current_lop_khoahoc = r_lop.KHOAHOC.strip() if r_lop else ""

            cursor.execute("EXEC SP_GET_DSSV ?", (malop,))
            rows2 = cursor.fetchall()
            sv_list = [{'MASV': r.MASV.strip(), 'HOTEN': r.HOTEN.strip(),
                        'HO': r.HO.strip(), 'TEN': r.TEN.strip(),
                        'PHAI': 1 if r.PHAI else 0, 'DIACHI': (r.DIACHI or '').strip(),
                        'NGAYSINH': str(r.NGAYSINH)[:10] if r.NGAYSINH else '',
                        'MALOP': r.MALOP.strip(), 'DANGHIHOC': r.DANGHIHOC,
                        'IS_FROZEN': is_frozen(current_lop_khoahoc)} for r in rows2]
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return render_template('sinhvien.html', lop_list=lop_list, sv_list=sv_list,
                           malop_chon=malop.upper(), khoa_list=get_danh_sach_khoa(),
                           is_current_frozen=is_frozen(current_lop_khoahoc) if 'current_lop_khoahoc' in locals() else False,
                           hoten=session.get('hoten'), group=session.get('group'))


@app.route('/sinhvien/them', methods=['POST'])
@require_group('PGV')
def sinhvien_them():
    malop = request.form.get('malop_hientai', '').strip().upper()
    masv = request.form.get('masv', '').strip().upper()
    ho = request.form.get('ho', '').strip()
    ten = request.form.get('ten', '').strip()
    phai = 1 if request.form.get('phai') == '1' else 0
    diachi = request.form.get('diachi', '').strip()
    ngaysinh = request.form.get('ngaysinh', '') or None
    malop_sv = request.form.get('malop_sv', '').strip().upper()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA ĐÓNG BĂNG TRƯỚC KHI THÊM
            cursor.execute("SELECT KHOAHOC FROM LOP WHERE MALOP = ?", (malop_sv,))
            r_lop = cursor.fetchone()
            if r_lop and is_frozen(r_lop.KHOAHOC):
                flash("Lỗi: Không thể thêm sinh viên vào lớp thuộc niên khóa đã đóng băng.", "error")
                return redirect(url_for('sinhvien_theo_lop', malop=malop))

            cursor.execute("EXEC SP_THEM_SV ?, ?, ?, ?, ?, ?, ?",
                           (masv, ho, ten, phai, diachi, ngaysinh, malop_sv))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Thêm thành công.')
            if row and row.KETQUA == 1:
                push_history('THEM_SV', f'Thêm SV {masv} — {ho} {ten} vào lớp {malop_sv}',
                             {'masv': masv, 'ho': ho, 'ten': ten, 'phai': phai,
                              'diachi': diachi, 'ngaysinh': ngaysinh, 'malop': malop_sv})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('sinhvien_theo_lop', malop=malop or malop_sv))


@app.route('/sinhvien/ghi', methods=['POST'])
@require_group('PGV')
def sinhvien_ghi():
    malop = request.form.get('malop_hientai', '').strip().upper()
    masv = request.form.get('masv', '').strip().upper()
    ho = request.form.get('ho', '').strip()
    ten = request.form.get('ten', '').strip()
    phai = 1 if request.form.get('phai') == '1' else 0
    diachi = request.form.get('diachi', '').strip()
    ngaysinh = request.form.get('ngaysinh', '') or None
    malop_sv = request.form.get('malop_sv', '').strip().upper()
    danghihoc = 1 if request.form.get('danghihoc') == '1' else 0
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()

            # KIỂM TRA ĐÓNG BĂNG
            cursor.execute("SELECT L.KHOAHOC FROM SINHVIEN S JOIN LOP L ON S.MALOP=L.MALOP WHERE S.MASV=?", (masv,))
            r = cursor.fetchone()
            if r and is_frozen(r.KHOAHOC):
                flash(f"Lỗi: Sinh viên {masv} thuộc khóa học cũ đã bị đóng băng, không thể sửa thông tin.", "error")
                return redirect(url_for('sinhvien_theo_lop', malop=malop))

            cursor.execute("SELECT HO, TEN, PHAI, DIACHI, NGAYSINH, MALOP, DANGHIHOC FROM SINHVIEN WHERE MASV=?", (masv,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_SUA_SV ?, ?, ?, ?, ?, ?, ?, ?",
                           (masv, ho, ten, phai, diachi, ngaysinh, malop_sv, danghihoc))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Cập nhật thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('SUA_SV', f'Sửa SV {masv} — {ho} {ten}',
                             {'masv': masv,
                              'ho_cu': old.HO.strip(), 'ten_cu': old.TEN.strip(),
                              'phai_cu': old.PHAI, 'diachi_cu': (old.DIACHI or '').strip(),
                              'ngaysinh_cu': str(old.NGAYSINH) if old.NGAYSINH else None,
                              'malop_cu': old.MALOP.strip()})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('sinhvien_theo_lop', malop=malop))


@app.route('/sinhvien/xoa', methods=['POST'])
@require_group('PGV')
def sinhvien_xoa():
    malop = request.form.get('malop_hientai', '').strip().upper()
    masv = request.form.get('masv', '').strip().upper()
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()

            # KIỂM TRA ĐÓNG BĂNG
            cursor.execute("SELECT L.KHOAHOC FROM SINHVIEN S JOIN LOP L ON S.MALOP=L.MALOP WHERE S.MASV=?", (masv,))
            r = cursor.fetchone()
            if r and is_frozen(r.KHOAHOC):
                flash(f"Lỗi: Không thể xóa sinh viên {masv} vì dữ liệu lịch sử đã bị đóng băng.", "error")
                return redirect(url_for('sinhvien_theo_lop', malop=malop))

            cursor.execute("SELECT HO, TEN, PHAI, DIACHI, NGAYSINH, MALOP FROM SINHVIEN WHERE MASV=?", (masv,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_XOA_SV ?", (masv,))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Xóa thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('XOA_SV', f'Xóa SV {masv} — {old.HO.strip()} {old.TEN.strip()} khỏi lớp {old.MALOP.strip()}',
                             {'masv': masv, 'ho': old.HO.strip(), 'ten': old.TEN.strip(),
                              'phai': old.PHAI, 'diachi': (old.DIACHI or '').strip(),
                              'ngaysinh': str(old.NGAYSINH) if old.NGAYSINH else None,
                              'malop': old.MALOP.strip()})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('sinhvien_theo_lop', malop=malop))


# ----------------------------------------------------------------
# Lớp tín chỉ — PGV only
# ----------------------------------------------------------------
@app.route('/loptinchi')
@require_group('PGV', 'KHOA')
def loptinchi():
    conn, _ = get_db()
    ltc_list, monhoc_list, gv_list, khoa_list = [], [], [], get_danh_sach_khoa()
    nienkhoa = request.args.get('nienkhoa', '')
    hocky = request.args.get('hocky', '')
    makhoa_filter = request.args.get('makhoa', '')
    # [PLANT_LTC_BUGS_2026] Mặc định NK mới nhất hiện có trong LOPTINCHI
    if not nienkhoa:
        nienkhoa = get_default_nk_ltc()

    if conn:
        try:
            cursor = conn.cursor()
            nk = nienkhoa if nienkhoa else None
            hk = int(hocky) if hocky else None
            # Nhóm KHOA chỉ được xem lớp của khoa mình — ép filter bất kể URL param
            if session.get('group') == 'KHOA':
                mk = session.get('makhoa', '')
            else:
                mk = makhoa_filter if makhoa_filter else None
            cursor.execute("EXEC SP_GETALL_LOPTINCHI ?, ?, ?", (nk, hk, mk))
            rows = cursor.fetchall()
            ltc_list = []
            for r in rows:
                # Check xem lớp đã có điểm học tập chưa
                cursor.execute("""
                    SELECT COUNT(*) FROM DANGKY 
                    WHERE MALTC = ? AND (DIEM_CC IS NOT NULL OR DIEM_GK IS NOT NULL OR DIEM_CK IS NOT NULL)
                """, (r.MALTC,))
                co_diem = cursor.fetchone()[0] > 0
                
                ltc_list.append({
                    'MALTC': r.MALTC,
                    'NIENKHOA': r.NIENKHOA.strip(),
                    'HOCKY': r.HOCKY,
                    'MAMH': r.MAMH.strip(),
                    'TENMH': r.TENMH.strip(),
                    'NHOM': r.NHOM,
                    'MAGV': r.MAGV.strip(),
                    'TENGV': r.TENGV.strip(),
                    'MAKHOA': r.MAKHOA.strip(),
                    'TENKHOA': r.TENKHOA.strip(),
                    'SOSVTOITHIEU': r.SOSVTOITHIEU,
                    'SOSV_DANGKY': r.SOSV_DANGKY,
                    'HUYLOP': r.HUYLOP,
                    'CO_DIEM': co_diem,
                    'IS_FROZEN': is_frozen(r.NIENKHOA.strip())
                })
            cursor.execute("EXEC SP_GET_ALL_MONHOC")
            monhoc_list = [{'MAMH': r.MAMH.strip(), 'TENMH': r.TENMH.strip()} for r in cursor.fetchall()]
            cursor.execute("EXEC SP_GETALL_GIANGVIEN")
            gv_list = [{'MAGV': r.MAGV.strip(), 'HOTEN': r.HOTEN.strip(),
                        'MAKHOA': r.MAKHOA.strip()} for r in cursor.fetchall()]
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    resp = make_response(render_template('loptinchi.html', ltc_list=ltc_list,
                           monhoc_list=monhoc_list, gv_list=gv_list,
                           khoa_list=khoa_list,
                           nienkhoa_list=get_all_nienkhoa_ltc(),
                           nienkhoa=nienkhoa, hocky=hocky, makhoa_filter=makhoa_filter,
                           hoten=session.get('hoten'), group=session.get('group')))
    return nocache_response(resp)


@app.route('/loptinchi/them', methods=['POST'])
@require_group('PGV')
def loptinchi_them():
    nienkhoa = request.form.get('nienkhoa', '').strip()
    hocky = request.form.get('hocky', 1)
    mamh = request.form.get('mamh', '').strip().upper()
    nhom = request.form.get('nhom', 1)
    magv = request.form.get('magv', '').strip().upper()
    makhoa = request.form.get('makhoa', '').strip().upper()
    sosvtoithieu = request.form.get('sosvtoithieu', 10)
    conn, _ = get_db()
    if conn:
        try:
            if is_frozen(nienkhoa):
                flash(f"Lỗi: Không thể mở lớp tín chỉ cho niên khóa {nienkhoa} vì đã bị đóng băng.", "error")
                return redirect(url_for('loptinchi'))

            cursor = conn.cursor()
            cursor.execute("EXEC SP_THEM_LOPTINCHI ?, ?, ?, ?, ?, ?, ?",
                           (nienkhoa, hocky, mamh, nhom, magv, makhoa, sosvtoithieu))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Thêm thành công.')
            if row and row.KETQUA > 0:
                maltc = row.KETQUA
                push_history('THEM_LTC', f'Mở lớp TC #{maltc} — {mamh} Nhóm {nhom} NK {nienkhoa} HK{hocky}',
                             {'maltc': int(maltc), 'nienkhoa': nienkhoa, 'hocky': int(hocky),
                              'mamh': mamh, 'nhom': int(nhom), 'magv': magv,
                              'makhoa': makhoa, 'sosvtoithieu': int(sosvtoithieu)})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('loptinchi'))


@app.route('/loptinchi/ghi', methods=['POST'])
@require_group('PGV')
def loptinchi_ghi():
    maltc = request.form.get('maltc', 0)
    nienkhoa = request.form.get('nienkhoa', '').strip()
    hocky = request.form.get('hocky', 1)
    mamh = request.form.get('mamh', '').strip().upper()
    nhom = request.form.get('nhom', 1)
    magv = request.form.get('magv', '').strip().upper()
    makhoa = request.form.get('makhoa', '').strip().upper()
    sosvtoithieu = request.form.get('sosvtoithieu', 10)
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA ĐÓNG BĂNG
            cursor.execute("SELECT NIENKHOA FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
            r = cursor.fetchone()
            if r and is_frozen(r.NIENKHOA):
                flash(f"Lỗi: Lớp tín chỉ #{maltc} thuộc niên khóa đã bị đóng băng, không thể sửa.", "error")
                return redirect(url_for('loptinchi'))

            # Lấy thông tin cũ và số SV đã đăng ký
            cursor.execute("SELECT NIENKHOA,HOCKY,MAMH,NHOM,MAGV,MAKHOA,SOSVTOITHIEU FROM LOPTINCHI WHERE MALTC=?", (maltc,))
            old = cursor.fetchone()
            
            if old:
                old_nk, old_hk, old_mh, old_nhom, old_gv, old_mk, old_sosv = (
                    old.NIENKHOA.strip(), old.HOCKY, old.MAMH.strip(), old.NHOM,
                    old.MAGV.strip(), old.MAKHOA.strip(), old.SOSVTOITHIEU
                )
                
                # 1. RÀNG BUỘC: Nếu đã nhập điểm, chặn sửa hoàn toàn
                cursor.execute("""
                    SELECT COUNT(*) FROM DANGKY 
                    WHERE MALTC = ? AND (DIEM_CC IS NOT NULL OR DIEM_GK IS NOT NULL OR DIEM_CK IS NOT NULL)
                """, (maltc,))
                if cursor.fetchone()[0] > 0:
                    if (nienkhoa != old_nk or int(hocky) != old_hk or mamh != old_mh or
                        int(nhom) != old_nhom or magv != old_gv or makhoa != old_mk or int(sosvtoithieu) != old_sosv):
                        flash('Lỗi: Lớp tín chỉ đã có sinh viên được nhập điểm, cấm sửa đổi mọi thông tin.')
                        return redirect(url_for('loptinchi'))
                
                # 2. RÀNG BUỘC: Nếu đã có SV đăng ký học (chưa có điểm)
                cursor.execute("SELECT COUNT(*) FROM DANGKY WHERE MALTC = ? AND (HUYDANGKY = 0 OR HUYDANGKY IS NULL)", (maltc,))
                so_sv_dangky = cursor.fetchone()[0]
                if so_sv_dangky > 0:
                    # Chặn sửa các thông tin cốt lõi
                    if (nienkhoa != old_nk or int(hocky) != old_hk or mamh != old_mh or
                        int(nhom) != old_nhom or makhoa != old_mk):
                        flash('Lỗi: Lớp tín chỉ đã có sinh viên đăng ký, không được sửa đổi thông tin chính (Môn/Nhóm/HK/NK/Khoa).')
                        return redirect(url_for('loptinchi'))
                    # Check số SV tối thiểu
                    if int(sosvtoithieu) < so_sv_dangky:
                        flash(f'Lỗi: Số sinh viên tối thiểu ({sosvtoithieu}) không được nhỏ hơn số sinh viên đã đăng ký thực tế ({so_sv_dangky}).')
                        return redirect(url_for('loptinchi'))

            cursor.execute("EXEC SP_SUA_LOPTINCHI ?, ?, ?, ?, ?, ?, ?, ?",
                           (maltc, nienkhoa, hocky, mamh, nhom, magv, makhoa, sosvtoithieu))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Cập nhật thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('SUA_LTC', f'Sửa lớp TC #{maltc}',
                             {'maltc': maltc,
                              'nienkhoa_cu': old_nk, 'hocky_cu': old_hk,
                              'mamh_cu': old_mh, 'nhom_cu': old_nhom,
                              'magv_cu': old_gv, 'makhoa_cu': old_mk,
                              'sosv_cu': old_sosv})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('loptinchi'))


@app.route('/loptinchi/xoa', methods=['POST'])
@require_group('PGV')
def loptinchi_xoa():
    maltc = request.form.get('maltc', 0)
    action_type = request.form.get('action_type', 'huy_lop')
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA ĐÓNG BĂNG
            cursor.execute("SELECT NIENKHOA FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
            r = cursor.fetchone()
            if r and is_frozen(r.NIENKHOA):
                flash(f"Lỗi: Không thể thay đổi lớp tín chỉ #{maltc} vì dữ liệu lịch sử đã bị đóng băng.", "error")
                return redirect(url_for('loptinchi'))

            cursor.execute("SELECT NIENKHOA,HOCKY,MAMH,NHOM,MAGV,MAKHOA,SOSVTOITHIEU FROM LOPTINCHI WHERE MALTC=?", (maltc,))
            old = cursor.fetchone()
            if not old:
                flash("Lớp tín chỉ không tồn tại.")
                return redirect(url_for('loptinchi'))

            if action_type == 'xoa_vinh_vien':
                # Gọi SP xóa vật lý lớp tín chỉ (chỉ được khi chưa có SV đăng ký)
                cursor.execute("EXEC SP_HOANTAC_THEM_LOPTINCHI ?", (maltc,))
                row = cursor.fetchone()
                conn.commit()
                flash(row.THONGBAO if row else 'Xóa vĩnh viễn thành công.')
                if row and row.KETQUA == 1:
                    push_history('XOA_VINH_VIEN_LTC',
                                 f'Xóa vĩnh viễn lớp TC #{maltc} — {old.MAMH.strip()} Nhóm {old.NHOM}',
                                 {'maltc': maltc, 'nienkhoa': old.NIENKHOA.strip(), 'hocky': old.HOCKY, 
                                  'mamh': old.MAMH.strip(), 'nhom': old.NHOM, 'magv': old.MAGV.strip(), 
                                  'makhoa': old.MAKHOA.strip(), 'sosvtoithieu': old.SOSVTOITHIEU})
            else:
                # Gọi SP hủy lớp tín chỉ (set HUYLOP = 1)
                cursor.execute("EXEC SP_XOA_LOPTINCHI ?", (maltc,))
                row = cursor.fetchone()
                conn.commit()
                flash(row.THONGBAO if row else 'Hủy thành công.')
                if row and row.KETQUA == 1:
                    push_history('XOA_LTC',
                                 f'Hủy lớp TC #{maltc} — {old.MAMH.strip()} Nhóm {old.NHOM} NK {old.NIENKHOA.strip()} HK{old.HOCKY}',
                                 {'maltc': maltc})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('loptinchi'))


@app.route('/loptinchi/phuchoi', methods=['POST'])
@require_group('PGV')
def loptinchi_phuchoi():
    """Mở lại lớp tín chỉ đã hủy (HUYLOP = 0)"""
    maltc = request.form.get('maltc', 0)
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA ĐÓNG BĂNG
            cursor.execute("SELECT NIENKHOA FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
            r = cursor.fetchone()
            if r and is_frozen(r.NIENKHOA):
                flash(f"Lỗi: Không thể mở lại lớp tín chỉ #{maltc} vì dữ liệu lịch sử đã bị đóng băng.", "error")
                return redirect(url_for('loptinchi'))

            # Check xem khi mở lại có trùng tổ hợp lớp khác đang hoạt động không
            cursor.execute("SELECT NIENKHOA,HOCKY,MAMH,NHOM FROM LOPTINCHI WHERE MALTC=?", (maltc,))
            old = cursor.fetchone()
            if old:
                cursor.execute("""
                    SELECT COUNT(*) FROM LOPTINCHI 
                    WHERE NIENKHOA = ? AND HOCKY = ? AND MAMH = ? AND NHOM = ? AND HUYLOP = 0 AND MALTC <> ?
                """, (old.NIENKHOA, old.HOCKY, old.MAMH, old.NHOM, maltc))
                if cursor.fetchone()[0] > 0:
                    flash('Lỗi: Trùng tổ hợp Môn học, Nhóm, HK, NK với lớp khác đang hoạt động. Không thể phục hồi.')
                    return redirect(url_for('loptinchi'))

            cursor.execute("EXEC SP_PHUCHOI_LOPTINCHI ?", (maltc,))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Mở lại lớp thành công.')
            if row and row.KETQUA == 1:
                push_history('MO_LAI_LTC', f'Mở lại lớp TC #{maltc}', {'maltc': maltc})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('loptinchi'))


# ----------------------------------------------------------------
# Nhập điểm — PGV + KHOA
# ----------------------------------------------------------------
@app.route('/nhapdiem')
@require_group('PGV', 'KHOA')
def nhapdiem():
    conn, _ = get_db()
    monhoc_list, khoa_list, ltc_active = [], get_danh_sach_khoa(), []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GET_ALL_MONHOC")
            monhoc_list = [{'MAMH': r.MAMH.strip(), 'TENMH': r.TENMH.strip()} for r in cursor.fetchall()]
            
            cursor.execute("""
                SELECT DISTINCT LTC.NIENKHOA, LTC.HOCKY, LTC.MAMH, LTC.NHOM, GV.HO, GV.TEN
                FROM LOPTINCHI LTC
                INNER JOIN DANGKY DK ON LTC.MALTC = DK.MALTC
                LEFT JOIN GIANGVIEN GV ON LTC.MAGV = GV.MAGV
                WHERE LTC.HUYLOP = 0 AND (DK.HUYDANGKY = 0 OR DK.HUYDANGKY IS NULL)
            """)
            ltc_active = [{'NK': r.NIENKHOA.strip(), 'HK': str(r.HOCKY), 'MAMH': r.MAMH.strip(), 'NHOM': str(r.NHOM), 'GV': f"{(r.HO or '').strip()} {(r.TEN or '').strip()}".strip()} for r in cursor.fetchall()]
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    # [PLANT_NHAPDIEM_RETAIN_2026] Lấy TẤT CẢ NK có LTC (kể cả cũ) để PGV/KHOA xem được lịch sử
    resp = make_response(render_template('nhapdiem.html', monhoc_list=monhoc_list,
                           khoa_list=khoa_list,
                           ltc_active_json=json.dumps(ltc_active),
                           nienkhoa_list=get_all_nienkhoa_ltc(),
                           hoten=session.get('hoten'), group=session.get('group')))
    return nocache_response(resp)


@app.route('/nhapdiem/batdau', methods=['POST'])
@require_group('PGV', 'KHOA')
def nhapdiem_batdau():
    """AJAX: load DS sinh viên của lớp TC đã chọn."""
    data = request.get_json(silent=True) or request.form
    nienkhoa = (data.get('nienkhoa', '') or '').strip()
    hocky = data.get('hocky', '')
    mamh = (data.get('mamh', '') or '').strip().upper()
    nhom = data.get('nhom', '')
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT LTC.MALTC, GV.HO, GV.TEN 
               FROM LOPTINCHI LTC
               LEFT JOIN GIANGVIEN GV ON LTC.MAGV = GV.MAGV
               WHERE LTC.NIENKHOA=? AND LTC.HOCKY=? AND LTC.MAMH=? AND LTC.NHOM=? AND LTC.HUYLOP=0
               AND (? IS NULL OR LTC.MAKHOA=?)""",
            (nienkhoa, int(hocky), mamh, int(nhom),
             session.get('makhoa') if session.get('group') == 'KHOA' else None,
             session.get('makhoa') if session.get('group') == 'KHOA' else None)
        )
        ltc_row = cursor.fetchone()
        if not ltc_row:
            return jsonify({'ok': False, 'msg': 'Không tìm thấy lớp tín chỉ tương ứng'})
        maltc = ltc_row[0]
        tengv = f"{(ltc_row[1] or '').strip()} {(ltc_row[2] or '').strip()}".strip()
        # [PLANT_NHAPDIEM_Flicker_Cancel_Khoa_2026] Ràng buộc chỉ giảng viên khoa X được nhập điểm cho lớp tín chỉ khoa X
        group = session.get('group')
        if group != 'PGV':
            user_khoa = session.get('khoa', '').strip().upper()
            cursor.execute("SELECT MAKHOA FROM LOPTINCHI WHERE MALTC=?", (maltc,))
            ltc_khoa_row = cursor.fetchone()
            ltc_khoa = ltc_khoa_row[0].strip().upper() if ltc_khoa_row else ''
            if user_khoa != ltc_khoa:
                return jsonify({'ok': False, 'msg': f'Chưa có lớp tín chỉ được mở cho khoa {user_khoa} của bạn'})
        cursor.execute("EXEC SP_GET_SINHVIEN_THEO_LTC ?", (maltc,))
        rows = cursor.fetchall()
        sv_list = [{'MASV': r.MASV.strip(), 'HOTEN': r.HOTEN.strip(),
                    'DIEM_CC': r.DIEM_CC, 'DIEM_GK': r.DIEM_GK,
                    'DIEM_CK': r.DIEM_CK, 'DIEM_HM': r.DIEM_HM} for r in rows]
        # Lấy tenmh
        cursor.execute("SELECT TENMH FROM MONHOC WHERE MAMH=?", (mamh,))
        mh_row = cursor.fetchone()
        tenmh = mh_row.TENMH.strip() if mh_row else mamh
        # [PLANT_NHAPDIEM_RETAIN_2026] Xác định LTC thuộc NK đã đóng băng hay chưa
        is_frozen = False
        try:
            nk_start = int(nienkhoa.split('-')[0])
            is_frozen = nk_start < 2025
        except Exception:
            is_frozen = False
        return jsonify({'ok': True, 'maltc': maltc, 'sv_list': sv_list,
                        'tenmh': tenmh, 'tengv': tengv, 'nhom': nhom, 'nienkhoa': nienkhoa, 'hocky': hocky,
                        'is_frozen': is_frozen})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()


@app.route('/nhapdiem/nhom_list', methods=['POST'])
@require_group('PGV', 'KHOA')
def nhapdiem_nhom_list():
    """AJAX: lấy danh sách các nhóm môn học của học kỳ/niên khóa."""
    data = request.get_json(silent=True) or request.form
    nienkhoa = (data.get('nienkhoa', '') or '').strip()
    hocky = data.get('hocky', '')
    mamh = (data.get('mamh', '') or '').strip().upper()
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT NHOM FROM LOPTINCHI WHERE NIENKHOA=? AND HOCKY=? AND MAMH=? AND HUYLOP=0 ORDER BY NHOM",
            (nienkhoa, int(hocky), mamh)
        )
        nhom_list = [r[0] for r in cursor.fetchall()]
        return jsonify({'ok': True, 'nhom_list': nhom_list})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()


@app.route('/nhapdiem/ghidiem', methods=['POST'])
@require_group('PGV', 'KHOA')
def nhapdiem_ghidiem():
    """[PLANT_NHAPDIEM_RETAIN_2026] Ghi toàn bộ điểm - AJAX JSON in/out (không redirect, giữ form).
    Gọi SP_NHAP_DIEM cho từng dòng. Trả về tổng hợp thành công / lỗi.
    """
    data = request.get_json(silent=True) or {}
    maltc = data.get('maltc', 0)
    masv_list = data.get('masv_list', []) or []
    diem_cc_list = data.get('diem_cc_list', []) or []
    diem_gk_list = data.get('diem_gk_list', []) or []
    diem_ck_list = data.get('diem_ck_list', []) or []
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
    success_count = 0
    errors = []
    try:
        cursor = conn.cursor()
        for i, masv in enumerate(masv_list):
            try:
                cc_raw = diem_cc_list[i] if i < len(diem_cc_list) else ''
                gk_raw = diem_gk_list[i] if i < len(diem_gk_list) else ''
                ck_raw = diem_ck_list[i] if i < len(diem_ck_list) else ''
                cc = int(cc_raw) if str(cc_raw).strip() else None
                gk = float(gk_raw) if str(gk_raw).strip() else None
                ck = float(ck_raw) if str(ck_raw).strip() else None
                cursor.execute("EXEC SP_NHAP_DIEM ?, ?, ?, ?, ?",
                               (maltc, masv.strip(), cc, gk, ck))
                row = cursor.fetchone()
                if row and getattr(row, 'KETQUA', 0) < 0:
                    err_msg = getattr(row, 'THONGBAO', 'Lỗi không xác định') or 'Lỗi không xác định'
                    errors.append({'masv': masv.strip(), 'msg': str(err_msg).strip()})
                else:
                    success_count += 1
            except Exception as e:
                errors.append({'masv': masv.strip() if masv else f'#{i}', 'msg': str(e)})
        conn.commit()
        return jsonify({'ok': True, 'success_count': success_count,
                        'errors': errors, 'total': len(masv_list)})
    except Exception as e:
        try: conn.rollback()
        except: pass
        return jsonify({'ok': False, 'msg': str(e), 'success_count': success_count,
                        'errors': errors}), 500
    finally:
        conn.close()


# ----------------------------------------------------------------
# Đăng ký lớp tín chỉ — SV only
# ----------------------------------------------------------------
@app.route('/dangky')
@require_group('SV')
def dangky():
    # [PLANT_LTC_BUGS_2026] Lấy niên khóa thuộc phạm vi của SV (KHOAHOC → KHOAHOC+7)
    masv = session.get('username', '')
    nk_list = get_nienkhoa_for_sv(masv)
    return render_template('dangky.html',
                           hoten=session.get('hoten'),
                           masv=masv,
                           malop=session.get('malop', ''),
                           quahan=session.get('quahan', False),
                           nienkhoa_list=nk_list,
                           group=session.get('group'))


@app.route('/dangky/timkiem', methods=['POST'])
@require_group('SV')
def dangky_timkiem():
    """AJAX: lấy thông tin SV."""
    masv = request.form.get('masv', '').strip().upper()
    conn, _ = get_db()
    if not conn:
        return jsonify({'error': 'Không thể kết nối DB'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC SP_GET_THONGTIN_SV ?", (masv,))
        row = cursor.fetchone()
        if row:
            return jsonify({'MASV': row.MASV.strip(), 'HOTEN': row.HOTEN.strip(),
                            'MALOP': row.MALOP.strip(), 'TENLOP': row.TENLOP.strip()})
        return jsonify({'error': 'Không tìm thấy sinh viên'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/dangky/loc', methods=['POST'])
@require_group('SV')
def dangky_loc():
    """AJAX: lọc danh sách LTC theo niên khóa + học kỳ."""
    data = request.get_json(silent=True) or request.form
    masv = session.get('username', '')
    nienkhoa = (data.get('nienkhoa', '') or '').strip()
    hocky = data.get('hocky', '')
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC SP_GET_LOPTINCHI_DANGKY ?, ?, ?",
                       (masv, nienkhoa, int(hocky)))
        rows = cursor.fetchall()
        ltc_list = []
        for r in rows:
            item = {'MALTC': r.MALTC, 'MAMH': r.MAMH.strip(),
                    'TENMH': r.TENMH.strip(), 'NHOM': r.NHOM,
                    'TENGV': r.TENGV.strip(), 'TENKHOA': r.TENKHOA.strip(),
                    'SOSVTOITHIEU': r.SOSVTOITHIEU, 'SOSV_DANGKY': r.SOSV_DANGKY,
                    'DA_DANGKY': r.DA_DANGKY,
                    'DA_NHAP_DIEM': getattr(r, 'DA_NHAP_DIEM', 0),
                    'IS_FROZEN': is_frozen(nienkhoa)}
            # Kiểm tra SV đã có điểm chưa (nếu đã đăng ký)
            co_diem = False
            if r.DA_DANGKY == 1:
                try:
                    cursor.execute(
                        "SELECT DIEM_CC, DIEM_GK, DIEM_CK FROM DANGKY WHERE MALTC=? AND MASV=?",
                        (r.MALTC, masv))
                    dk_row = cursor.fetchone()
                    if dk_row and (dk_row.DIEM_CC is not None or dk_row.DIEM_GK is not None or dk_row.DIEM_CK is not None):
                        co_diem = True
                except:
                    pass
            item['CO_DIEM'] = co_diem
            ltc_list.append(item)
        return jsonify({'ok': True, 'list': ltc_list})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()


@app.route('/dangky/dangky', methods=['POST'])
@require_group('SV')
def dangky_thuchien():
    """Thực hiện đăng ký lớp tín chỉ."""
    data = request.get_json(silent=True) or request.form
    masv = session.get('username', '')
    maltc = data.get('maltc', 0)
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
    try:
        cursor = conn.cursor()
        
        # KIỂM TRA ĐÓNG BĂNG: Không cho phép đăng ký vào niên khóa cũ (< 2025)
        cursor.execute("SELECT NIENKHOA FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
        res = cursor.fetchone()
        if res and is_frozen(res.NIENKHOA.strip()):
            return jsonify({'ok': False, 'msg': f'Không thể đăng ký lớp thuộc niên khóa lịch sử ({res.NIENKHOA.strip()})'})

        cursor.execute("EXEC SP_DANGKY_LTC ?, ?", (masv, maltc))
        row = cursor.fetchone()
        conn.commit()
        if row:
            return jsonify({'ok': row.KETQUA == 1, 'msg': row.THONGBAO})
        return jsonify({'ok': False, 'msg': 'Lỗi không xác định'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()
@app.route('/dangky/huy', methods=['POST'])
@require_group('SV')
def dangky_huy():
    """Hủy đăng ký lớp tín chỉ."""
    data = request.get_json(silent=True) or request.form
    masv = session.get('username', '')
    maltc = data.get('maltc', 0)
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
    try:
        cursor = conn.cursor()
        
        # KIỂM TRA ĐÓNG BĂNG: Không cho phép hủy lớp thuộc niên khóa cũ (< 2025)
        cursor.execute("SELECT NIENKHOA FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
        res = cursor.fetchone()
        if res and is_frozen(res.NIENKHOA.strip()):
            return jsonify({'ok': False, 'msg': f'Không thể hủy lớp thuộc niên khóa lịch sử ({res.NIENKHOA.strip()})'})

        cursor.execute("EXEC SP_HUY_DANGKY ?, ?", (masv, maltc))
        row = cursor.fetchone()
        conn.commit()
        if row:
            return jsonify({'ok': row.KETQUA == 1, 'msg': row.THONGBAO})
        return jsonify({'ok': False, 'msg': 'Lỗi không xác định'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()



# ----------------------------------------------------------------
# Phiếu điểm — SV only
# ----------------------------------------------------------------
@app.route('/phieu_diem')
@require_group('SV')
def phieu_diem():
    masv = session.get('username', '')
    hoten = session.get('hoten', '')
    malop = session.get('malop', '')
    conn, _ = get_db()
    phieu_diem_list = []
    ngaysinh = ''
    if conn:
        try:
            cursor = conn.cursor()
            # Lấy ngày sinh của SV
            cursor.execute("SELECT NGAYSINH FROM SINHVIEN WHERE MASV=?", (masv,))
            sv_row = cursor.fetchone()
            if sv_row and sv_row.NGAYSINH:
                ngaysinh = str(sv_row.NGAYSINH)[:10]

            cursor.execute("EXEC SP_XEM_PHIEU_DIEM ?", (masv,))
            rows = cursor.fetchall()
            for r in rows:
                diem_hm = None
                if r.DIEM_CC is not None and r.DIEM_GK is not None and r.DIEM_CK is not None:
                    diem_hm = round(r.DIEM_CC * 0.1 + r.DIEM_GK * 0.3 + r.DIEM_CK * 0.6, 2)
                phieu_diem_list.append({
                    'NIENKHOA': r.NIENKHOA.strip(), 'HOCKY': r.HOCKY,
                    'MAMH': r.MAMH.strip(), 'TENMH': r.TENMH.strip(),
                    'NHOM': r.NHOM,
                    'DIEM_CC': r.DIEM_CC, 'DIEM_GK': r.DIEM_GK,
                    'DIEM_CK': r.DIEM_CK, 'DIEM_HM': diem_hm})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    # Truyền biến sv (dict) khớp với template phieu_diem.html
    sv_info = {'MASV': masv, 'HOTEN': hoten, 'MALOP': malop, 'NGAYSINH': ngaysinh}
    return render_template('phieu_diem.html', phieu_diem=phieu_diem_list,
                           sv=sv_info, masv=masv, hoten=hoten,
                           group=session.get('group'))

# ----------------------------------------------------------------
# Backup & Restore Database - PGV Only
# ----------------------------------------------------------------
@app.route('/backup')
@require_group('PGV')
def backup_page():
    return render_template('backup.html', hoten=session.get('hoten'), group=session.get('group'))

@app.route('/backup/create_device', methods=['POST'])
@require_group('PGV')
def create_device():
    conn, _ = get_db()
    if conn:
        try:
            conn.autocommit = True
            cursor = conn.cursor()
            # Kiểm tra Device đã tồn tại chưa
            cursor.execute("SELECT name FROM sys.backup_devices WHERE name = 'DEVICE_QLDSV_HTC'")
            if cursor.fetchone():
                flash('Backup Device "DEVICE_QLDSV_HTC" đã tồn tại.')
            else:
                cursor.execute("EXEC sp_addumpdevice 'disk', 'DEVICE_QLDSV_HTC', 'C:\\Backup\\QLDSV_HTC.bak'")
                flash('Tạo Backup Device thành công!')
        except Exception as e:
            flash(f'Lỗi tạo Backup Device: {e}')
        finally:
            conn.close()
    else:
        flash('Lỗi kết nối cơ sở dữ liệu.')
    return redirect(url_for('backup_page'))

@app.route('/backup/do_backup', methods=['POST'])
@require_group('PGV')
def do_backup():
    conn, _ = get_db()
    if conn:
        try:
            conn.autocommit = True
            cursor = conn.cursor()
            # Kiểm tra Device đã tồn tại chưa
            cursor.execute("SELECT name FROM sys.backup_devices WHERE name = 'DEVICE_QLDSV_HTC'")
            if not cursor.fetchone():
                flash('Backup Device chưa được tạo. Vui lòng tạo Backup Device trước.')
            else:
                # Dùng FORMAT để tạo lại Media Header tránh lỗi corrupted file, và INIT để ghi đè
                cursor.execute("BACKUP DATABASE QLDSV_HTC TO DEVICE_QLDSV_HTC WITH FORMAT, INIT")
                
                # Quan trọng: pyodbc sẽ hủy lệnh BACKUP giữa chừng nếu đóng connection ngay lập tức
                # do lệnh BACKUP trả về nhiều messages (progress). Cần dùng nextset() để chờ SQL chạy xong.
                while cursor.nextset():
                    pass
                    
                flash('Sao lưu (Backup) Database thành công!')
        except Exception as e:
            flash(f'Lỗi Backup Database: {e}')
        finally:
            conn.close()
    else:
        flash('Lỗi kết nối cơ sở dữ liệu.')
    return redirect(url_for('backup_page'))

@app.route('/backup/do_restore', methods=['POST'])
@require_group('PGV')
def do_restore():
    # Phục hồi Database yêu cầu quyền sysadmin/dbcreator và không được kết nối vào DB đang bị khóa
    # Do đó, tạo một kết nối riêng tới 'master' bằng tài khoản DBA ('sa')
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER_NAME};"
        f"DATABASE=master;"
        f"UID=sa;PWD=123"
    )
    
    try:
        conn = pyodbc.connect(connection_string, autocommit=True)
        cursor = conn.cursor()
        
        # Ngắt kết nối các session khác
        cursor.execute("ALTER DATABASE QLDSV_HTC SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        
        # Thực thi Restore
        cursor.execute("RESTORE DATABASE QLDSV_HTC FROM DEVICE_QLDSV_HTC WITH REPLACE")
        # QUAN TRỌNG: RESTORE trả về nhiều result sets (tiến trình %). 
        # Cần loop nextset() để tránh lệnh Restore bị gián đoạn giữa chừng khiến DB bị kẹt ở trạng thái Restoring
        while cursor.nextset():
            pass
            
        # Chuyển lại MULTI_USER
        cursor.execute("ALTER DATABASE QLDSV_HTC SET MULTI_USER")
        flash('Phục hồi (Restore) Database thành công!')
    except Exception as e:
        try:
            # Nếu xảy ra lỗi, cố gắng set lại MULTI_USER để tránh kẹt DB
            # Hoặc khôi phục DB khỏi trạng thái Restoring (nếu nó bị kẹt)
            cursor.execute("RESTORE DATABASE QLDSV_HTC WITH RECOVERY")
            cursor.execute("ALTER DATABASE QLDSV_HTC SET MULTI_USER")
        except:
            pass
        flash(f'Lỗi Restore Database: {e}')
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            
    return redirect(url_for('backup_page'))

@app.route('/backup/do_backup_log', methods=['POST'])
@require_group('PGV')
def do_backup_log():
    conn, _ = get_db()
    if conn:
        try:
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Kiểm tra và chuyển sang FULL recovery model nếu cần
            cursor.execute("SELECT recovery_model_desc FROM sys.databases WHERE name = 'QLDSV_HTC'")
            row = cursor.fetchone()
            if row and row.recovery_model_desc != 'FULL':
                cursor.execute("ALTER DATABASE QLDSV_HTC SET RECOVERY FULL")
                while cursor.nextset(): pass
                
            # Thực thi Backup Log
            cursor.execute("BACKUP LOG QLDSV_HTC TO DISK = 'C:\\Backup\\QLDSV_HTC_LOG.trn' WITH INIT")
            while cursor.nextset():
                pass
                
            flash('Sao lưu Transaction Log thành công!')
        except Exception as e:
            flash(f'Lỗi Backup Log: {e}')
        finally:
            conn.close()
    else:
        flash('Lỗi kết nối cơ sở dữ liệu.')
    return redirect(url_for('backup_page'))

@app.route('/backup/do_restore_pit', methods=['POST'])
@require_group('PGV')
def do_restore_pit():
    stopat_time = request.form.get('stopat_time')
    if not stopat_time:
        flash('Vui lòng chọn thời điểm cần phục hồi!')
        return redirect(url_for('backup_page'))
        
    # Xử lý format từ HTML datetime-local (YYYY-MM-DDThh:mm:ss) sang SQL Server datetime format
    stopat_time = stopat_time.replace('T', ' ')
        
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER_NAME};"
        f"DATABASE=master;"
        f"UID=sa;PWD=123"
    )
    
    try:
        conn = pyodbc.connect(connection_string, autocommit=True)
        cursor = conn.cursor()
        
        # Ngắt kết nối các session khác
        cursor.execute("ALTER DATABASE QLDSV_HTC SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        
        # Bước 1: Restore Full Database với NORECOVERY
        cursor.execute("RESTORE DATABASE QLDSV_HTC FROM DEVICE_QLDSV_HTC WITH REPLACE, NORECOVERY")
        while cursor.nextset(): 
            pass
            
        # Bước 2: Restore Log với STOPAT và đưa DB về trạng thái RECOVERY
        cursor.execute(f"RESTORE LOG QLDSV_HTC FROM DISK = 'C:\\Backup\\QLDSV_HTC_LOG.trn' WITH STOPAT = '{stopat_time}', RECOVERY")
        while cursor.nextset(): 
            pass
            
        # Chuyển lại MULTI_USER
        cursor.execute("ALTER DATABASE QLDSV_HTC SET MULTI_USER")
        flash(f'Phục hồi Point-in-Time (đến {stopat_time}) thành công!')
    except Exception as e:
        try:
            # Cứu DB khỏi trạng thái Restoring (nếu nó bị kẹt)
            cursor.execute("RESTORE DATABASE QLDSV_HTC WITH RECOVERY")
            cursor.execute("ALTER DATABASE QLDSV_HTC SET MULTI_USER")
        except:
            pass
        flash(f'Lỗi Restore Point-in-Time: {e}')
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            
    return redirect(url_for('backup_page'))

# Tạo tài khoản
# ----------------------------------------------------------------
@app.route('/taotaikhoan')
@require_group('PGV', 'ADMIN')
def taotaikhoan():
    conn, _ = get_db()
    gv_list = []
    if conn:
        try:
            cursor = conn.cursor()
            
            # Lấy thông tin tài khoản hiện có từ DB
            cursor.execute("""
                SELECT 
                    d.name AS MAGV,
                    SUSER_SNAME(d.sid) AS LoginName,
                    r.name AS RoleName
                FROM sys.database_principals d
                LEFT JOIN sys.database_role_members rm ON d.principal_id = rm.member_principal_id
                LEFT JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id AND r.type = 'R'
                WHERE d.type = 'S'
            """)
            account_info = {}
            for row in cursor.fetchall():
                account_info[row.MAGV.strip()] = {
                    'LOGIN': row.LoginName.strip() if row.LoginName else '',
                    'ROLE': row.RoleName.strip() if row.RoleName else 'KHOA'
                }
                
            # Lấy danh sách giảng viên đang dạy (ràng buộc không được xóa tài khoản)
            cursor.execute("SELECT DISTINCT MAGV FROM LOPTINCHI WHERE MAGV IS NOT NULL")
            teaching_magvs = [row.MAGV.strip() for row in cursor.fetchall()]
            
            cursor.execute("EXEC SP_GETALL_GIANGVIEN")
            for r in cursor.fetchall():
                magv = r.MAGV.strip()
                has_account = magv in account_info
                gv_list.append({
                    'MAGV': magv,
                    'HOTEN': r.HOTEN.strip(),
                    'HAS_ACCOUNT': has_account,
                    'LOGIN': account_info[magv]['LOGIN'] if has_account else '',
                    'ROLE': account_info[magv]['ROLE'] if has_account else 'PGV',
                    'IS_TEACHING': magv in teaching_magvs
                })
        except Exception as e:
            flash(f'Lỗi load giảng viên: {e}')
        finally:
            conn.close()
    return render_template('taotaikhoan.html', gv_list=gv_list, hoten=session.get('hoten'), group=session.get('group'))

@app.route('/taotaikhoan/submit', methods=['POST'])
@require_group('PGV', 'ADMIN')
def taotaikhoan_submit():
    data = request.get_json(silent=True) or request.form
    lgname = data.get('lgname', '').strip()
    password = data.get('password', '').strip()
    magv = data.get('magv', '').strip()
    role = data.get('role', '').strip()

    if not all([lgname, password, magv, role]):
        return jsonify({'ok': False, 'msg': 'Vui lòng nhập đầy đủ thông tin'})

    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("DECLARE @RET INT; EXEC @RET = SP_TAOLOGIN ?, ?, ?, ?; SELECT @RET AS KETQUA", (lgname, password, magv, role))
        ret_row = cursor.fetchone()
        ret = ret_row.KETQUA if ret_row else -1
        
        if ret == 0:
            conn.commit()
            return jsonify({'ok': True, 'msg': 'Tạo tài khoản thành công'})
        elif ret == 1:
            return jsonify({'ok': False, 'msg': 'Tên đăng nhập (Tài khoản) đã tồn tại!'})
        elif ret == 2:
            return jsonify({'ok': False, 'msg': 'Giảng viên này đã có tài khoản rồi!'})
        elif ret == 3:
            return jsonify({'ok': False, 'msg': 'Nhóm quyền không hợp lệ!'})
        else:
            return jsonify({'ok': False, 'msg': f'Lỗi không xác định (Mã lỗi: {ret})'})
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()

@app.route('/taotaikhoan/check_login', methods=['POST'])
@require_group('PGV', 'ADMIN')
def taotaikhoan_check_login():
    data = request.get_json(silent=True) or request.form
    lgname = data.get('lgname', '').strip()
    
    if not lgname:
        return jsonify({'exists': False})
        
    conn, _ = get_db()
    if not conn:
        return jsonify({'exists': False})
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SUSER_ID(?) AS ID", (lgname,))
        row = cursor.fetchone()
        exists = row.ID is not None if row else False
        return jsonify({'exists': exists})
    except:
        return jsonify({'exists': False})
    finally:
        conn.close()

# =====================================================================
# ĐỔI MẬT KHẨU (CHUNG CHO GV & SV)
# =====================================================================
@app.route('/doimatkhau')
def doimatkhau():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('doimatkhau.html', hoten=session.get('hoten'), group=session.get('group'))

@app.route('/doimatkhau/submit', methods=['POST'])
def doimatkhau_submit():
    if 'username' not in session:
        return jsonify({'ok': False, 'msg': 'Hết phiên đăng nhập'})

    data = request.get_json(silent=True) or request.form
    old_pass = data.get('old_pass', '').strip()
    new_pass = data.get('new_pass', '').strip()

    if not old_pass or not new_pass:
        return jsonify({'ok': False, 'msg': 'Vui lòng điền đủ thông tin'})

    username = session['username']
    group = session['group']

    try:
        if group == 'SV':
            # Đối với Sinh viên: gọi SP để kiểm tra và cập nhật mật khẩu trong bảng SINHVIEN
            conn, _ = get_db()
            if not conn:
                return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'})
            cursor = conn.cursor()
            cursor.execute("DECLARE @RET INT; EXEC @RET = SP_SV_DOIMATKHAU ?, ?, ?; SELECT @RET AS KETQUA", (username, old_pass, new_pass))
            ret_row = cursor.fetchone()
            ret = ret_row.KETQUA if ret_row else -1
            conn.commit()
            conn.close()

            if ret == 0:
                return jsonify({'ok': True, 'msg': 'Đổi mật khẩu thành công'})
            else:
                return jsonify({'ok': False, 'msg': 'Mật khẩu cũ không chính xác'})

        else:
            # Đối với Giảng viên: dùng cơ chế ALTER LOGIN của SQL Server
            # 1. Thử kết nối với mật khẩu cũ để xác thực (vì chỉ đổi được nếu biết mk cũ)
            test_conn, err = get_db_connection(username, old_pass)
            if not test_conn:
                return jsonify({'ok': False, 'msg': 'Mật khẩu cũ không chính xác'})
            
            # 2. Dùng sp_executesql với tham số để tránh SQL injection từ mật khẩu chứa dấu nháy
            cursor = test_conn.cursor()
            safe_username = username.replace(']', ']]')
            sql_stmt = f'ALTER LOGIN [{safe_username}] WITH PASSWORD = @P OLD_PASSWORD = @O'
            cursor.execute(
                "EXEC sp_executesql ?, N'@P NVARCHAR(200), @O NVARCHAR(200)', @P=?, @O=?",
                (sql_stmt, new_pass, old_pass)
            )
            test_conn.commit()
            test_conn.close()
            
            # Cập nhật lại session mật khẩu mới để các thao tác tiếp theo không bị văng
            session['db_pass'] = new_pass
            return jsonify({'ok': True, 'msg': 'Đổi mật khẩu thành công'})

    except Exception as e:
        return jsonify({'ok': False, 'msg': f'Lỗi: {str(e)}'})

@app.route('/taotaikhoan/delete', methods=['POST'])
@require_group('PGV', 'ADMIN')
def taotaikhoan_delete():
    data = request.get_json(silent=True) or request.form
    lgname = data.get('lgname', '').strip()
    magv = data.get('magv', '').strip()

    if not all([lgname, magv]):
        return jsonify({'ok': False, 'msg': 'Vui lòng nhập đầy đủ thông tin'})

    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
        
    try:
        cursor = conn.cursor()
        
        # Kiểm tra giảng viên có đang dạy không (Ràng buộc không được xóa)
        cursor.execute("SELECT TOP 1 1 FROM LOPTINCHI WHERE MAGV = ?", (magv,))
        if cursor.fetchone():
            return jsonify({'ok': False, 'msg': 'Tài khoản đang bị ràng buộc do giảng viên đang dạy Lớp tín chỉ. Không thể xóa!'})
            
        cursor.execute("DECLARE @RET INT; EXEC @RET = SP_XOALOGIN ?, ?; SELECT @RET AS KETQUA", (lgname, magv))
        ret_row = cursor.fetchone()
        ret = ret_row.KETQUA if ret_row else -1
        
        if ret == 0:
            conn.commit()
            return jsonify({'ok': True, 'msg': 'Xóa tài khoản thành công'})
        elif ret == 1:
            return jsonify({'ok': False, 'msg': 'Tên đăng nhập (Tài khoản) không tồn tại!'})
        elif ret == 2:
            return jsonify({'ok': False, 'msg': 'Giảng viên này không có tài khoản!'})
        else:
            return jsonify({'ok': False, 'msg': f'Lỗi không xác định (Mã lỗi: {ret})'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()


@app.route('/baocao/dsloptinchi', methods=['GET', 'POST'])
def in_ds_loptinchi():
    if 'username' not in session or session.get('role') != 'GV':
         flash('Bạn không có quyền truy cập trang này.', 'danger')
         return redirect(url_for('dashboard'))

    conn, error = get_db()
    if not conn:
        flash(f'Lỗi kết nối: {error}', 'danger')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT MAKHOA, TENKHOA FROM KHOA")
        ds_khoa = [{'MAKHOA': row.MAKHOA.strip(), 'TENKHOA': row.TENKHOA.strip()} for row in cursor.fetchall()]
    except Exception as e:
        ds_khoa = []
        flash(f"Lỗi lấy danh sách Khoa: {str(e)}", "danger")

    ds_baocao = []
    nienkhoa = request.form.get('nienkhoa', '')
    hocky = request.form.get('hocky', '')
    makhoa_chon = request.form.get('makhoa', session.get('khoa')) 

    if request.method == 'POST' and request.form.get('action') == 'filter':
        try:
            cursor.execute("{CALL SP_InDanhSachLopTinChi(?, ?, ?)}", (nienkhoa, hocky, makhoa_chon))
            rows = cursor.fetchall()
            for r in rows:
                ds_baocao.append({
                    'TENMH': r.TENMH.strip(),
                    'NHOM': r.NHOM,
                    'HOTENGV': r.HOTENGV.strip(),
                    'SOSVTOITHIEU': r.SOSVTOITHIEU,
                    'SOSVDADANGKY': r.SOSVDADANGKY
                })
        except pyodbc.Error as e:
            flash(f'Lỗi truy xuất dữ liệu: {e.args[1]}', 'danger')

    conn.close()

    tenkhoa_hienthi = next((k['TENKHOA'] for k in ds_khoa if k['MAKHOA'] == makhoa_chon), makhoa_chon)

    return render_template('in_dslop_tinchi.html', 
                           ds_khoa=ds_khoa, 
                           ds_baocao=ds_baocao, 
                           nienkhoa=nienkhoa, 
                           hocky=hocky, 
                           makhoa=makhoa_chon,
                           tenkhoa_hienthi=tenkhoa_hienthi)

@app.route('/baocao/dssv_dangky', methods=['GET', 'POST'])
def in_dssv_dangky():
    # Kiểm tra quyền đăng nhập
    if 'username' not in session or session.get('role') != 'GV':
         flash('Bạn không có quyền truy cập trang này.', 'danger')
         return redirect(url_for('dashboard'))

    conn, error = get_db()
    if not conn:
        flash(f'Lỗi kết nối: {error}', 'danger')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    
    # 1. Lấy danh sách Môn Học đổ vào Dropdown để chọn
    try:
        cursor.execute("SELECT MAMH, TENMH FROM MONHOC ORDER BY TENMH")
        ds_monhoc = [{'MAMH': row.MAMH.strip(), 'TENMH': row.TENMH.strip()} for row in cursor.fetchall()]
    except Exception as e:
        ds_monhoc = []
        flash(f"Lỗi lấy danh sách Môn học: {str(e)}", "danger")

    # Các biến chứa dữ liệu báo cáo
    ds_baocao = []
    nienkhoa = request.form.get('nienkhoa', '')
    hocky = request.form.get('hocky', '')
    mamh = request.form.get('mamh', '')
    nhom = request.form.get('nhom', '')
    tenmh_hienthi = ''

    # 2. Khi người dùng nhấn nút Trích xuất
    if request.method == 'POST' and request.form.get('action') == 'filter':
        try:
            # Gọi SP vừa viết bên SQL, truyền đúng 4 tham số
            cursor.execute("{CALL SP_InDanhSachSVDangKy(?, ?, ?, ?)}", (nienkhoa, hocky, mamh, nhom))
            rows = cursor.fetchall()
            for r in rows:
                ds_baocao.append({
                    'MASV': r.MASV.strip(),
                    'HO': r.HO.strip(),
                    'TEN': r.TEN.strip(),
                    'PHAI': r.PHAI, # Chữ Nam/Nữ đã được xử lý sẵn dưới SQL
                    'MALOP': r.MALOP.strip()
                })
            
            # Tìm tên môn học dựa vào mã môn để in lên giấy
            tenmh_hienthi = next((m['TENMH'] for m in ds_monhoc if m['MAMH'] == mamh), mamh)
            
            if len(ds_baocao) == 0:
                flash('Không tìm thấy sinh viên nào đăng ký lớp này!', 'warning')

        except pyodbc.Error as e:
            flash(f'Lỗi truy xuất dữ liệu: {e.args[1]}', 'danger')

    conn.close()

    return render_template('in_dssv_dangky.html', 
                           ds_monhoc=ds_monhoc, 
                           ds_baocao=ds_baocao, 
                           nienkhoa=nienkhoa, 
                           hocky=hocky, 
                           mamh=mamh,
                           nhom=nhom,
                           tenmh_hienthi=tenmh_hienthi)


@app.route('/baocao/bangdiem_monhoc', methods=['GET', 'POST'])
def in_bangdiem_monhoc():
    if 'username' not in session or session.get('role') != 'GV':
         flash('Bạn không có quyền truy cập trang này.', 'danger')
         return redirect(url_for('dashboard'))

    conn, error = get_db()
    if not conn:
        flash(f'Lỗi kết nối: {error}', 'danger')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    
    # 1. Lấy danh sách Môn Học đổ vào Dropdown để chọn
    try:
        cursor.execute("SELECT MAMH, TENMH FROM MONHOC ORDER BY TENMH")
        ds_monhoc = [{'MAMH': row.MAMH.strip(), 'TENMH': row.TENMH.strip()} for row in cursor.fetchall()]
    except Exception as e:
        ds_monhoc = []
        flash(f"Lỗi lấy danh sách Môn học: {str(e)}", "danger")

    # Các biến chứa dữ liệu báo cáo
    ds_baocao = []
    nienkhoa = request.form.get('nienkhoa', '')
    hocky = request.form.get('hocky', '')
    mamh = request.form.get('mamh', '')
    nhom = request.form.get('nhom', '')
    tenmh_hienthi = ''
    makhoa_hienthi = ''

    # 2. Khi người dùng nhấn nút Trích xuất
    if request.method == 'POST' and request.form.get('action') == 'filter':
        try:
            # Gọi SP In bảng điểm môn học
            cursor.execute("{CALL SP_InBangDiemMonHoc(?, ?, ?, ?)}", (nienkhoa, hocky, mamh, nhom))
            rows = cursor.fetchall()
            for r in rows:
                ds_baocao.append({
                    'MASV': r.MASV.strip(),
                    'HO': r.HO.strip(),
                    'TEN': r.TEN.strip(),
                    'DIEM_CC': r.DIEM_CC,
                    'DIEM_GK': r.DIEM_GK,
                    'DIEM_CK': r.DIEM_CK,
                    'DIEM_HM': r.DIEM_HM
                })
            
            # Tìm tên môn học dựa vào mã môn để in lên giấy
            tenmh_hienthi = next((m['TENMH'] for m in ds_monhoc if m['MAMH'] == mamh), mamh)
            
            # Lấy tên khoa hiện tại của user để in
            makhoa_hienthi = session.get('tenkhoa', '')
            
            if len(ds_baocao) == 0:
                flash('Không tìm thấy dữ liệu điểm cho lớp tín chỉ này!', 'warning')

        except pyodbc.Error as e:
            flash(f'Lỗi truy xuất dữ liệu: {e.args[1]}', 'danger')

    conn.close()

    return render_template('in_bangdiem_monhoc.html', 
                           ds_monhoc=ds_monhoc, 
                           ds_baocao=ds_baocao, 
                           nienkhoa=nienkhoa, 
                           hocky=hocky, 
                           mamh=mamh,
                           nhom=nhom,
                           tenmh_hienthi=tenmh_hienthi,
                           makhoa_hienthi=makhoa_hienthi)


@app.route('/baocao/phieu_diem', methods=['GET', 'POST'])
def in_phieu_diem():
    if 'username' not in session or session.get('role') != 'GV':
         flash('Bạn không có quyền truy cập trang này.', 'danger')
         return redirect(url_for('dashboard'))

    ds_baocao = []
    masv = request.form.get('masv', '').strip().upper()
    student_info = None

    if request.method == 'POST' and request.form.get('action') == 'filter' and masv:
        conn, error = get_db()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Lấy thông tin sinh viên
                cursor.execute("""
                    SELECT SV.MASV, RTRIM(SV.HO) + ' ' + RTRIM(SV.TEN) AS HOTEN, L.TENLOP
                    FROM SINHVIEN SV
                    INNER JOIN LOP L ON SV.MALOP = L.MALOP
                    WHERE SV.MASV = ?
                """, (masv,))
                s_row = cursor.fetchone()
                if s_row:
                    student_info = {
                        'MASV': s_row.MASV.strip(),
                        'HOTEN': s_row.HOTEN.strip(),
                        'TENLOP': s_row.TENLOP.strip()
                    }
                    
                    # Gọi SP In phiếu điểm
                    cursor.execute("{CALL SP_InPhieuDiem(?)}", (masv,))
                    rows = cursor.fetchall()
                    for r in rows:
                        ds_baocao.append({
                            'TENMH': r.TENMH.strip(),
                            'DIEM_MAX': r.DIEM_MAX
                        })
                    
                    if len(ds_baocao) == 0:
                        flash('Sinh viên chưa tích lũy điểm môn học nào!', 'warning')
                else:
                    flash('Không tìm thấy sinh viên có mã này trong hệ thống!', 'danger')
            except pyodbc.Error as e:
                flash(f'Lỗi truy xuất dữ liệu: {e.args[1]}', 'danger')
            finally:
                conn.close()

    return render_template('in_phieu_diem.html', 
                           ds_baocao=ds_baocao, 
                           masv=masv,
                           student_info=student_info)


@app.route('/baocao/bangdiem_tongket', methods=['GET', 'POST'])
def in_bangdiem_tongket():
    if 'username' not in session or session.get('role') != 'GV':
         flash('Bạn không có quyền truy cập trang này.', 'danger')
         return redirect(url_for('dashboard'))

    conn, error = get_db()
    if not conn:
        flash(f'Lỗi kết nối: {error}', 'danger')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    
    # Lấy danh sách Lớp Cử Nhân đổ vào Dropdown để chọn
    try:
        cursor.execute("EXEC SP_GET_DSLOP NULL")
        ds_lop = [{'MALOP': row.MALOP.strip(), 'TENLOP': row.TENLOP.strip(), 'KHOAHOC': row.KHOAHOC.strip(), 'TENKHOA': row.TENKHOA.strip()} for row in cursor.fetchall()]
    except Exception as e:
        ds_lop = []
        flash(f"Lỗi lấy danh sách Lớp: {str(e)}", "danger")

    ds_baocao_students = []
    monhoc_cols = []
    malop_chon = request.form.get('malop', '')
    lop_info = None

    if request.method == 'POST' and request.form.get('action') == 'filter' and malop_chon:
        try:
            # Lấy thông tin lớp được chọn để in header
            lop_info = next((l for l in ds_lop if l['MALOP'] == malop_chon), None)
            
            cursor.execute("{CALL SP_InBangDiemTongKet(?)}", (malop_chon,))
            raw_rows = cursor.fetchall()
            
            subject_set = set()
            student_map = {}
            
            for r in raw_rows:
                masv = r.MASV.strip()
                hoten = r.HOTEN.strip()
                tenmh = r.TENMH.strip() if r.TENMH else None
                diem = r.DIEM_MAX
                
                if tenmh:
                    subject_set.add(tenmh)
                
                if masv not in student_map:
                    student_map[masv] = {
                        'MASV': masv,
                        'HOTEN': hoten,
                        'DIEM': {}
                    }
                
                if tenmh:
                    student_map[masv]['DIEM'][tenmh] = diem
            
            monhoc_cols = sorted(list(subject_set))
            ds_baocao_students = list(student_map.values())
            
            if len(ds_baocao_students) == 0:
                flash('Lớp cử nhân này hiện không có sinh viên!', 'warning')
            
        except pyodbc.Error as e:
            flash(f'Lỗi truy xuất dữ liệu: {e.args[1]}', 'danger')

    conn.close()

    return render_template('in_bangdiem_tongket.html',
                           ds_lop=ds_lop,
                           monhoc_cols=monhoc_cols,
                           ds_baocao_students=ds_baocao_students,
                           malop_chon=malop_chon,
                           lop_info=lop_info)


# ----------------------------------------------------------------
# Quản lý tài khoản (PGV & KHOA)
# ----------------------------------------------------------------
@app.route('/quantri/taikhoan', methods=['GET'])
def quantri_taikhoan():
    if 'username' not in session or session.get('group') not in ['PGV', 'KHOA']:
        return redirect(url_for('login'))
    
    group = session.get('group')
    user_khoa = session.get('khoa', '').strip().upper()
    
    conn, _ = get_db()
    if not conn:
        flash('Không thể kết nối cơ sở dữ liệu')
        return redirect(url_for('dashboard'))
        
    # [FALLBACK_KHOA_2026] Fallback if session['khoa'] is missing for KHOA role
    if group == 'KHOA' and not user_khoa:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAKHOA FROM GIANGVIEN WHERE MAGV = ?", (session.get('username'),))
            row = cursor.fetchone()
            if row:
                user_khoa = row[0].strip().upper()
                session['khoa'] = user_khoa
        except Exception:
            pass
    
    gv_list = []
    accounts_list = []
    
    try:
        cursor = conn.cursor()
        # 1. Danh sách giảng viên để chọn trong form dropdown
        query_gv = """
            SELECT 
                GV.MAGV, 
                RTRIM(GV.HO) + ' ' + RTRIM(GV.TEN) AS HOTEN, 
                GV.MAKHOA, 
                DP.name AS DB_USER,
                SUSER_SNAME(DP.sid) AS LOGIN_NAME,
                R.name AS ROLE_NAME,
                CASE WHEN EXISTS (SELECT 1 FROM LOPTINCHI WHERE MAGV = GV.MAGV)
                       OR EXISTS (
                           SELECT 1 FROM DANGKY DK 
                           JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC 
                           WHERE LTC.MAGV = GV.MAGV 
                             AND (DK.DIEM_CC IS NOT NULL OR DK.DIEM_GK IS NOT NULL OR DK.DIEM_CK IS NOT NULL)
                       )
                     THEN 0 ELSE 1 END AS CAN_DELETE
            FROM GIANGVIEN GV
            LEFT JOIN sys.database_principals DP ON UPPER(RTRIM(DP.name)) = UPPER(RTRIM(GV.MAGV))
            LEFT JOIN sys.database_role_members RM ON RM.member_principal_id = DP.principal_id
            LEFT JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id
            WHERE (R.name IS NULL OR R.name IN ('PGV', 'KHOA'))
        """
        if group == 'KHOA':
            query_gv += " AND GV.MAKHOA = ?"
            cursor.execute(query_gv, (user_khoa,))
        else:
            cursor.execute(query_gv)
            
        rows = cursor.fetchall()
        for r in rows:
            gv_list.append({
                'MAGV': r.MAGV.strip(),
                'HOTEN': r.HOTEN.strip(),
                'MAKHOA': r.MAKHOA.strip() if r.MAKHOA else '',
                'HAS_ACCOUNT': 1 if r.DB_USER else 0,
                'LOGIN_NAME': r.LOGIN_NAME.strip() if r.LOGIN_NAME else '',
                'ROLE_NAME': r.ROLE_NAME.strip() if r.ROLE_NAME else '',
                'CAN_DELETE': r.CAN_DELETE
            })
            
        # 2. Danh sách tài khoản hiện có hiển thị ở bảng quản trị
        query_acc = """
            SELECT 
                RTRIM(GV.MAGV) AS MAGV, 
                RTRIM(GV.HO) + ' ' + RTRIM(GV.TEN) AS HOTEN, 
                RTRIM(GV.MAKHOA) AS MAKHOA, 
                RTRIM(SUSER_SNAME(DP.sid)) AS LOGIN_NAME, 
                RTRIM(R.name) AS ROLE_NAME,
                CASE WHEN EXISTS (SELECT 1 FROM LOPTINCHI WHERE MAGV = GV.MAGV)
                       OR EXISTS (
                           SELECT 1 FROM DANGKY DK 
                           JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC 
                           WHERE LTC.MAGV = GV.MAGV 
                             AND (DK.DIEM_CC IS NOT NULL OR DK.DIEM_GK IS NOT NULL OR DK.DIEM_CK IS NOT NULL)
                       )
                     THEN 0 ELSE 1 END AS CAN_DELETE
            FROM sys.database_role_members RM
            JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id
            JOIN sys.database_principals DP ON RM.member_principal_id = DP.principal_id
            JOIN GIANGVIEN GV ON UPPER(RTRIM(DP.name)) = UPPER(RTRIM(GV.MAGV))
            WHERE R.name IN ('PGV', 'KHOA')
        """

        if group == 'KHOA':
            query_acc += " AND GV.MAKHOA = ?"
            cursor.execute(query_acc, (user_khoa,))
        else:
            cursor.execute(query_acc)
            
        rows_acc = cursor.fetchall()
        for r in rows_acc:
            accounts_list.append({
                'MAGV': r.MAGV,
                'HOTEN': r.HOTEN,
                'MAKHOA': r.MAKHOA,
                'LOGIN_NAME': r.LOGIN_NAME,
                'ROLE_NAME': r.ROLE_NAME,
                'CAN_DELETE': r.CAN_DELETE
            })
            
    except Exception as e:
        flash(f'Lỗi truy vấn: {str(e)}')

    finally:
        conn.close()
        
    response = make_response(render_template('taikhoan.html',
                             gv_list=gv_list,
                             accounts_list=accounts_list,
                             hoten=session.get('hoten'),
                             group=group,
                             khoa=user_khoa))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response



@app.route('/quantri/taikhoan/them', methods=['POST'])
def quantri_taikhoan_them():
    if 'username' not in session or session.get('group') not in ['PGV', 'KHOA']:
        return jsonify({'ok': False, 'msg': 'Không có quyền thực hiện chức năng này'}), 403
        
    group = session.get('group')
    user_khoa = session.get('khoa', '').strip().upper()
    
    data = request.get_json() or {}
    magv = (data.get('magv') or '').strip().upper()
    login_name = (data.get('login_name') or '').strip()
    password = (data.get('password') or '').strip()
    role = (data.get('role') or '').strip().upper()
    
    if not magv or not login_name or not password or not role:
        return jsonify({'ok': False, 'msg': 'Vui lòng nhập đầy đủ thông tin: Mã giảng viên, Tên tài khoản, Mật khẩu và Nhóm quyền'}), 400
        
    if group == 'KHOA':
        if role != 'KHOA':
            return jsonify({'ok': False, 'msg': 'Tài khoản thuộc Khoa chỉ được phép tạo tài khoản cho nhóm quyền KHOA'}), 403
            
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối cơ sở dữ liệu'}), 500
        
    # [FALLBACK_KHOA_THEM_2026] Fallback if session['khoa'] is missing
    if group == 'KHOA' and not user_khoa:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAKHOA FROM GIANGVIEN WHERE MAGV = ?", (session.get('username'),))
            row = cursor.fetchone()
            if row:
                user_khoa = row[0].strip().upper()
                session['khoa'] = user_khoa
        except Exception:
            pass
        
    try:
        import re
        cursor = conn.cursor()
        if group == 'KHOA':
            cursor.execute("SELECT MAKHOA FROM GIANGVIEN WHERE MAGV=?", (magv,))
            row = cursor.fetchone()
            if not row or row[0].strip().upper() != user_khoa:
                return jsonify({'ok': False, 'msg': 'Bạn chỉ được phép tạo tài khoản cho giảng viên thuộc khoa của mình'}), 403
                
        cursor.execute("EXEC SP_TAOTAIKHOAN ?, ?, ?, ?", (login_name, password, magv, role))
        conn.commit()
        return jsonify({'ok': True, 'msg': 'Tạo tài khoản thành công'})
    except pyodbc.Error as e:
        sql_msg = ''
        if len(e.args) > 1:
            sql_msg = e.args[1]
            match = re.search(r'\]\s*([^\]]+)$', sql_msg)
            if match:
                sql_msg = match.group(1).strip()
        return jsonify({'ok': False, 'msg': f'Lỗi SQL: {sql_msg or str(e)}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'Lỗi hệ thống: {str(e)}'})
    finally:
        conn.close()


@app.route('/quantri/taikhoan/xoa', methods=['POST'])
def quantri_taikhoan_xoa():
    if 'username' not in session or session.get('group') not in ['PGV', 'KHOA']:
        return jsonify({'ok': False, 'msg': 'Không có quyền thực hiện chức năng này'}), 403
        
    group = session.get('group')
    user_khoa = session.get('khoa', '').strip().upper()
    
    data = request.get_json() or {}
    magv = (data.get('magv') or '').strip().upper()
    login_name = (data.get('login_name') or '').strip()
    
    if not magv or not login_name:
        return jsonify({'ok': False, 'msg': 'Vui lòng cung cấp đầy đủ Mã giảng viên và Tên tài khoản để xóa'}), 400
        
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối cơ sở dữ liệu'}), 500
        
    # [FALLBACK_KHOA_XOA_2026] Fallback if session['khoa'] is missing
    if group == 'KHOA' and not user_khoa:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAKHOA FROM GIANGVIEN WHERE MAGV = ?", (session.get('username'),))
            row = cursor.fetchone()
            if row:
                user_khoa = row[0].strip().upper()
                session['khoa'] = user_khoa
        except Exception:
            pass
        
    try:
        import re
        cursor = conn.cursor()
        if group == 'KHOA':
            cursor.execute("SELECT MAKHOA FROM GIANGVIEN WHERE MAGV=?", (magv,))
            row = cursor.fetchone()
            if not row or row[0].strip().upper() != user_khoa:
                return jsonify({'ok': False, 'msg': 'Bạn chỉ được phép xóa tài khoản của giảng viên thuộc khoa của mình'}), 403
                
            # Không cho phép KHOA xóa tài khoản của PGV
            cursor.execute(
                "SELECT 1 FROM sys.database_role_members RM "
                "JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id "
                "JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id "
                "WHERE R.name = 'PGV' AND U.name = ?",
                (magv,)
            )
            if cursor.fetchone():
                return jsonify({'ok': False, 'msg': 'Tài khoản thuộc Khoa không có quyền xóa tài khoản của nhóm PGV'}), 403
                
        cursor.execute("EXEC SP_XOATAIKHOAN ?, ?", (login_name, magv))
        conn.commit()
        return jsonify({'ok': True, 'msg': 'Xóa tài khoản thành công'})
    except pyodbc.Error as e:
        sql_msg = ''
        if len(e.args) > 1:
            sql_msg = e.args[1]
            match = re.search(r'\]\s*([^\]]+)$', sql_msg)
            if match:
                sql_msg = match.group(1).strip()
        return jsonify({'ok': False, 'msg': f'Lỗi SQL: {sql_msg or str(e)}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'Lỗi hệ thống: {str(e)}'})
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
