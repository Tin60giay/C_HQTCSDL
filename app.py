from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import pyodbc
import json

app = Flask(__name__)
app.secret_key = 'super_secret_key_qlds'

SERVER_NAME = 'localhost\\SQLEXPRESS'
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
                    cursor.execute("EXEC SP_DANGNHAP_GV ?", (username,))
                    row = cursor.fetchone()
                    if row:
                        magv = row.USER_NAME.strip()
                        
                        # Lấy Database Role trực tiếp từ SQL Server
                        cursor.execute(
                            "SELECT R.name FROM sys.database_role_members RM "
                            "JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id "
                            "JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id "
                            "WHERE U.name = ?",
                            (magv,)
                        )
                        role_row = cursor.fetchone()
                        if role_row:
                            nhom = role_row.name.strip()
                        else:
                            nhom = 'KHOA'
                            
                        session['username'] = magv
                        session['hoten'] = row.HOTEN.strip()
                        session['group'] = nhom
                        session['tenkhoa'] = row.TENGROUP.strip()
                        session['role'] = 'GV'
                        session['khoa'] = khoa
                        session['db_login'] = username
                        session['db_pass'] = password
                        conn.close()
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Không tìm thấy thông tin giảng viên tương ứng.')
                except Exception as e:
                    flash(f'Lỗi: {str(e)}')
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
                        # [QUA_HAN_SP_2026] Lưu cờ quá hạn từ SP_DANGNHAP_SV
                        session['quahan'] = bool(getattr(row, 'QUAHAN', 0))
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
    """Trả về 10 hành động gần nhất dạng JSON."""
    return jsonify(session.get('history', []))


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
            # Thêm LTC → hoàn tác = hủy lớp đó
            cursor.execute("EXEC SP_XOA_LOPTINCHI ?", (d['maltc'],))
            msg = f"Đã hủy lớp tín chỉ #{d['maltc']}"
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
        else:
            return jsonify({'ok': False, 'msg': 'Loại hành động không hỗ trợ hoàn tác'}), 400

        row = cursor.fetchone()
        conn.commit()
        thongbao = row.THONGBAO if (row and hasattr(row, 'THONGBAO')) else msg
        # Xóa hành động đã undo khỏi history
        history.pop(idx)
        session['history'] = history
        session.modified = True
        return jsonify({'ok': True, 'msg': thongbao})
    except Exception as e:
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
            cursor.execute("SELECT HO,TEN,MAKHOA FROM GIANGVIEN WHERE MAGV=?", (magv,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_XOA_GIANGVIEN ?", (magv,))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Xóa thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('XOA_GV', f'Xóa GV {magv} - {old.HO.strip()} {old.TEN.strip()}',
                             {'magv': magv, 'makhoa': old.MAKHOA.strip(),
                              'ho': old.HO.strip(), 'ten': old.TEN.strip()})
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
                
                # Kiểm tra đóng băng môn học
                cursor.execute("EXEC SP_CHECK_MONHOC_HISTORY ?", (m['MAMH'],))
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
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Lấy dữ liệu cũ để lưu history
            cursor.execute("SELECT TENMH, SOTIET_LT, SOTIET_TH FROM MONHOC WHERE MAMH=?", (mamh,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_SUA_MONHOC ?, ?, ?, ?", (mamh, tenmh, sotiet_lt, sotiet_th))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Cập nhật thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('SUA_MH', f'Sửa môn học {mamh}',
                             {'mamh': mamh,
                              'tenmh_cu': old.TENMH.strip(), 'lt_cu': old.SOTIET_LT, 'th_cu': old.SOTIET_TH})
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
            # Kiểm tra ràng buộc: có SV đăng ký không
            cursor.execute("""
                SELECT COUNT(*) FROM DANGKY DK
                INNER JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC
                WHERE LTC.MAMH = ? AND (DK.HUYDANGKY=0 OR DK.HUYDANGKY IS NULL)
            """, (mamh,))
            so_dk = cursor.fetchone()[0]
            if so_dk > 0:
                flash(f'Không thể xóa: môn học đang có {so_dk} sinh viên đã đăng ký.')
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

            cursor.execute("SELECT HO, TEN, PHAI, DIACHI, NGAYSINH, MALOP FROM SINHVIEN WHERE MASV=?", (masv,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_SUA_SV ?, ?, ?, ?, ?, ?, ?",
                           (masv, ho, ten, phai, diachi, ngaysinh, malop_sv))
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
    if conn:
        try:
            cursor = conn.cursor()
            nk = nienkhoa if nienkhoa else None
            hk = int(hocky) if hocky else None
            mk = makhoa_filter if makhoa_filter else None
            cursor.execute("EXEC SP_GETALL_LOPTINCHI ?, ?, ?", (nk, hk, mk))
            rows = cursor.fetchall()
            ltc_list = [{'MALTC': r.MALTC, 'NIENKHOA': r.NIENKHOA.strip(),
                         'HOCKY': r.HOCKY, 'MAMH': r.MAMH.strip(),
                         'TENMH': r.TENMH.strip(), 'NHOM': r.NHOM,
                         'MAGV': r.MAGV.strip(), 'TENGV': r.TENGV.strip(),
                         'MAKHOA': r.MAKHOA.strip(), 'TENKHOA': r.TENKHOA.strip(),
                         'SOSVTOITHIEU': r.SOSVTOITHIEU, 'SOSV_DANGKY': r.SOSV_DANGKY,
                         'IS_FROZEN': is_frozen(r.NIENKHOA.strip())} for r in rows]
            cursor.execute("EXEC SP_GET_ALL_MONHOC")
            monhoc_list = [{'MAMH': r.MAMH.strip(), 'TENMH': r.TENMH.strip()} for r in cursor.fetchall()]
            cursor.execute("EXEC SP_GETALL_GIANGVIEN")
            gv_list = [{'MAGV': r.MAGV.strip(), 'HOTEN': r.HOTEN.strip(),
                        'MAKHOA': r.MAKHOA.strip()} for r in cursor.fetchall()]
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return render_template('loptinchi.html', ltc_list=ltc_list,
                           monhoc_list=monhoc_list, gv_list=gv_list,
                           khoa_list=khoa_list,
                           nienkhoa_list=get_nienkhoa_list(),
                           nienkhoa=nienkhoa, hocky=hocky, makhoa_filter=makhoa_filter,
                           hoten=session.get('hoten'), group=session.get('group'))


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
                             {'maltc': maltc})
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

            cursor.execute("SELECT NIENKHOA,HOCKY,MAMH,NHOM,MAGV,MAKHOA,SOSVTOITHIEU FROM LOPTINCHI WHERE MALTC=?", (maltc,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_SUA_LOPTINCHI ?, ?, ?, ?, ?, ?, ?, ?",
                           (maltc, nienkhoa, hocky, mamh, nhom, magv, makhoa, sosvtoithieu))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Cập nhật thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('SUA_LTC', f'Sửa lớp TC #{maltc}',
                             {'maltc': maltc,
                              'nienkhoa_cu': old.NIENKHOA.strip(), 'hocky_cu': old.HOCKY,
                              'mamh_cu': old.MAMH.strip(), 'nhom_cu': old.NHOM,
                              'magv_cu': old.MAGV.strip(), 'makhoa_cu': old.MAKHOA.strip(),
                              'sosv_cu': old.SOSVTOITHIEU})
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return redirect(url_for('loptinchi'))


@app.route('/loptinchi/xoa', methods=['POST'])
@require_group('PGV')
def loptinchi_xoa():
    maltc = request.form.get('maltc', 0)
    conn, _ = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA ĐÓNG BĂNG
            cursor.execute("SELECT NIENKHOA FROM LOPTINCHI WHERE MALTC = ?", (maltc,))
            r = cursor.fetchone()
            if r and is_frozen(r.NIENKHOA):
                flash(f"Lỗi: Không thể xóa lớp tín chỉ #{maltc} vì dữ liệu lịch sử đã bị đóng băng.", "error")
                return redirect(url_for('loptinchi'))

            cursor.execute("SELECT NIENKHOA,HOCKY,MAMH,NHOM FROM LOPTINCHI WHERE MALTC=?", (maltc,))
            old = cursor.fetchone()
            cursor.execute("EXEC SP_XOA_LOPTINCHI ?", (maltc,))
            row = cursor.fetchone()
            conn.commit()
            flash(row.THONGBAO if row else 'Hủy thành công.')
            if row and row.KETQUA == 1 and old:
                push_history('XOA_LTC',
                             f'Hủy lớp TC #{maltc} — {old.MAMH.strip()} Nhóm {old.NHOM} NK {old.NIENKHOA.strip()} HK{old.HOCKY}',
                             {'maltc': maltc})
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
    monhoc_list, khoa_list = [], get_danh_sach_khoa()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_GET_ALL_MONHOC")
            monhoc_list = [{'MAMH': r.MAMH.strip(), 'TENMH': r.TENMH.strip()} for r in cursor.fetchall()]
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return render_template('nhapdiem.html', monhoc_list=monhoc_list,
                           khoa_list=khoa_list,
                           nienkhoa_list=get_nienkhoa_list(),
                           hoten=session.get('hoten'), group=session.get('group'))


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
            "SELECT MALTC FROM LOPTINCHI WHERE NIENKHOA=? AND HOCKY=? AND MAMH=? AND NHOM=? AND HUYLOP=0",
            (nienkhoa, int(hocky), mamh, int(nhom))
        )
        ltc_row = cursor.fetchone()
        if not ltc_row:
            return jsonify({'ok': False, 'msg': 'Không tìm thấy lớp tín chỉ tương ứng'})
        maltc = ltc_row[0]
        cursor.execute("EXEC SP_GET_SINHVIEN_THEO_LTC ?", (maltc,))
        rows = cursor.fetchall()
        sv_list = [{'MASV': r.MASV.strip(), 'HOTEN': r.HOTEN.strip(),
                    'DIEM_CC': r.DIEM_CC, 'DIEM_GK': r.DIEM_GK,
                    'DIEM_CK': r.DIEM_CK, 'DIEM_HM': r.DIEM_HM} for r in rows]
        # Lấy tenmh
        cursor.execute("SELECT TENMH FROM MONHOC WHERE MAMH=?", (mamh,))
        mh_row = cursor.fetchone()
        tenmh = mh_row.TENMH.strip() if mh_row else mamh
        return jsonify({'ok': True, 'maltc': maltc, 'sv_list': sv_list,
                        'tenmh': tenmh, 'nhom': nhom, 'nienkhoa': nienkhoa, 'hocky': hocky})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500
    finally:
        conn.close()


@app.route('/nhapdiem/ghidiem', methods=['POST'])
@require_group('PGV', 'KHOA')
def nhapdiem_ghidiem():
    """Ghi toàn bộ điểm — gọi SP_NHAP_DIEM cho từng dòng."""
    maltc = request.form.get('maltc', 0)
    masv_list = request.form.getlist('masv[]')
    diem_cc_list = request.form.getlist('diem_cc[]')
    diem_gk_list = request.form.getlist('diem_gk[]')
    diem_ck_list = request.form.getlist('diem_ck[]')
    conn, _ = get_db()
    if not conn:
        flash('Không thể kết nối DB.')
        return redirect(url_for('nhapdiem'))
    errors = []
    try:
        cursor = conn.cursor()
        for i, masv in enumerate(masv_list):
            try:
                cc = int(diem_cc_list[i]) if diem_cc_list[i].strip() else None
                gk = float(diem_gk_list[i]) if diem_gk_list[i].strip() else None
                ck = float(diem_ck_list[i]) if diem_ck_list[i].strip() else None
                cursor.execute("EXEC SP_NHAP_DIEM ?, ?, ?, ?, ?",
                               (maltc, masv.strip(), cc, gk, ck))
                cursor.fetchone()
            except Exception as e:
                errors.append(f'{masv}: {e}')
        conn.commit()
        if errors:
            flash('Ghi điểm có lỗi: ' + '; '.join(errors))
        else:
            flash('Ghi điểm thành công!')
    except Exception as e:
        flash(f'Lỗi: {e}')
    finally:
        conn.close()
    return redirect(url_for('nhapdiem'))


# ----------------------------------------------------------------
# Đăng ký lớp tín chỉ — SV only
# ----------------------------------------------------------------
@app.route('/dangky')
@require_group('SV')
def dangky():
    # Chỉ lấy niên khóa thực tế đang có LTC — PGV mở lớp nào SV thấy niên khóa đó
    nk_list = get_nienkhoa_co_lop()
    return render_template('dangky.html',
                           hoten=session.get('hoten'),
                           masv=session.get('username'),
                           malop=session.get('malop', ''),
                           nienkhoa_list=nk_list,
                           quahan=session.get('quahan', False),
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
        ltc_list = [{'MALTC': r.MALTC, 'MAMH': r.MAMH.strip(),
                     'TENMH': r.TENMH.strip(), 'NHOM': r.NHOM,
                     'TENGV': r.TENGV.strip(), 'TENKHOA': r.TENKHOA.strip(),
                     'SOSVTOITHIEU': r.SOSVTOITHIEU, 'SOSV_DANGKY': r.SOSV_DANGKY,
                     'DA_DANGKY': r.DA_DANGKY,
                     'IS_FROZEN': is_frozen(nienkhoa)} for r in rows]
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

        # [QUA_HAN_SP_2026] Nếu SV đã quá hạn (KHOAHOC + 7 năm) → từ chối
        if session.get('quahan'):
            return jsonify({'ok': False, 'msg': 'Tài khoản của bạn đã quá hạn, chỉ có thể xem phiếu điểm.'})

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

        # [QUA_HAN_SP_2026] Nếu SV đã quá hạn → từ chối
        if session.get('quahan'):
            return jsonify({'ok': False, 'msg': 'Tài khoản của bạn đã quá hạn, không thể hủy đăng ký.'})

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
    quahan = session.get('quahan', False)
    conn, _ = get_db()
    diem_list = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("EXEC SP_XEM_PHIEU_DIEM ?", (masv,))
            rows = cursor.fetchall()
            for r in rows:
                diem_list.append({
                    'NIENKHOA': r.NIENKHOA.strip() if r.NIENKHOA else '',
                    'HOCKY': r.HOCKY,
                    'MAMH': r.MAMH.strip() if r.MAMH else '',
                    'TENMH': r.TENMH.strip() if r.TENMH else '',
                    'NHOM': r.NHOM,
                    'TENGV': r.TENGV.strip() if r.TENGV else '',
                    'DIEM_CC': r.DIEM_CC,
                    'DIEM_GK': r.DIEM_GK,
                    'DIEM_CK': r.DIEM_CK,
                    'DIEM_TK': r.DIEM_TK
                })
        except Exception as e:
            flash(f'Lỗi: {e}')
        finally:
            conn.close()
    return render_template('phieu_diem.html',
                           phieu_diem=diem_list,
                           sv={'MASV': masv, 'HOTEN': hoten, 'MALOP': malop},
                           quahan=quahan,
                           hoten=hoten,
                           group=session.get('group'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
