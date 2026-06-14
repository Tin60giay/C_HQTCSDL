# HDSD 3.1 — Hướng dẫn chi tiết chức năng **Đăng nhập**

> **Mục tiêu:** Giải thích toàn bộ lý thuyết + cơ chế hoạt động của chức năng đăng nhập trong chương trình QLDSV_HTC, bao gồm: giao diện form, luồng xử lý backend (Flask + SQL Server), sự khác biệt giữa Giảng Viên và Sinh Viên, cách kết nối SQL Server Authentication, các lỗi thường gặp và cách xử lý.
>
> **Phạm vi:** Mục **3.1 Đăng nhập** trong đề bài thực hành (GV + SV). Không bao gồm các chức năng sau đăng nhập (3.2, 3.3, …).
>
> **File liên quan trong source code:**
> - `app.py` (route `/` — hàm `login()`, khoảng dòng 199–289)
> - `templates/login.html` (giao diện form đăng nhập)
> - `setup_login.sql` (2 stored procedure: `SP_DANGNHAP_GV` + `SP_DANGNHAP_SV`)
> - `CRITICAL.md` (bảng mã lỗi + công thức tính "sinh viên quá hạn")

---

## 1. Tổng quan nghiệp vụ

### 1.1 Mục đích
Trước khi sử dụng bất kỳ chức năng nào của hệ thống (xem điểm, đăng ký lớp tín chỉ, nhập điểm, …), **mỗi người dùng (Giảng viên / Sinh viên) phải đăng nhập** để hệ thống biết:

| Thông tin cần biết | Mục đích |
|---|---|
| Username / Mã SV | Định danh người dùng |
| Password | Xác thực quyền truy cập |
| Vai trò (GV / SV) | Phân quyền chức năng |
| Khoa / Lớp | Hiển thị dữ liệu đúng phạm vi |

### 1.2 Hai cơ chế đăng nhập

Đề bài yêu cầu **2 cơ chế khác nhau** cho 2 nhóm người dùng:

| Nhóm | Cơ chế | Tài khoản dùng để kết nối SQL Server |
|---|---|---|
| **Giảng viên** | Đăng nhập bằng `Login` + `Password` riêng của từng GV | Tài khoản GV (do `setup_login.sql` tạo ra từ bảng `GIANGVIEN`) |
| **Sinh viên** | Tất cả SV **dùng chung** 1 tài khoản `sv` để kết nối DB, nhưng vẫn phải nhập **Mã SV** + **Password** riêng để xác thực danh tính | Tài khoản `sv` (login chung do `setup_login.sql` tạo, password `sv`) |

> **Vì sao SV dùng chung?** Vì SQL Server quản lý quyền ở cấp **Login** (instance), nhưng SV chỉ cần quyền hạn chế (xem điểm, đăng ký LTC). Tạo 1 login `sv` chung + cấp quyền trên các SP là đủ cho cả nghìn SV, tiết kiệm công quản trị. Bảo mật danh tính SV vẫn đảm bảo vì mỗi SV phải nhập đúng `MASV` + `PASSWORD` riêng khi gọi `SP_DANGNHAP_SV`.

---

## 2. Giao diện người dùng (Frontend)

### 2.1 Mô tả form đăng nhập

Mở trình duyệt tại `http://127.0.0.1:5001/` (sau khi chạy `python app.py`) sẽ thấy form như sau:

```
┌─────────────────────────────────────┐
│           [Logo PTIT]               │
│       Hệ Thống QLDSV                │
│  Quản lý Điểm Sinh Viên - Tín Chỉ  │
│                                     │
│   [GIẢNG VIÊN]  [SINH VIÊN]        │  ← 2 tab chọn vai trò
│  ┌─────────────────────────────┐    │
│  │ LOGIN                       │    │  ← Label đổi: GV → "LOGIN" / SV → "MÃ SV"
│  │ [______________________]    │    │
│  │ PASSWORD                    │    │
│  │ [______________________]    │    │
│  │                             │    │
│  │ [        Đăng nhập       ]  │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### 2.2 Cơ chế đổi label (GV ↔ SV)

Trong `templates/login.html` dòng 250, label mặc định là `LOGIN`. Khi bấm chọn tab **Sinh Viên**:
- JavaScript `changeLabel()` (dòng 266–282) tự động đổi:
  - Label: `LOGIN` → `MÃ SV`
  - Placeholder: `GV01` → `N23DCCI079`
- Khi bấm lại tab **Giảng Viên**: đổi ngược lại.

> **Lưu ý:** Hành vi này chỉ thay đổi **hiển thị** (DOM). Không thay đổi `name` của input (`name="username"`), không ảnh hưởng tới backend.

### 2.3 Các trường (field) trong form

| Trường | `name` trong HTML | Bắt buộc? | Mô tả |
|---|---|---|---|
| Role | `role` (radio: `GV` / `SV`) | ✅ (mặc định `GV`) | Vai trò đăng nhập |
| Username / Mã SV | `username` | ✅ | Với GV: `MAGV` (VD: `GV01`). Với SV: `MASV` (VD: `N23DCCI079`) |
| Password | `password` | ✅ | Mật khẩu tương ứng |
| ~~Khoa~~ | `khoa` | ❌ | **Hiện KHÔNG có field này trong form** — chỉ tồn tại trong route `/` với giá trị rỗng |

---

## 3. Luồng xử lý Backend (Flask + SQL Server)

### 3.1 Sơ đồ tổng quát

```
Người dùng                Flask (app.py)              SQL Server
    │                          │                          │
    │ 1. Submit form           │                          │
    │ POST /  role=GV  ───────>│                          │
    │   username=GV01          │                          │
    │   password=GV01          │                          │
    │                          │ 2. get_db_connection(    │
    │                          │     GV01, GV01)          │
    │                          │  (SQL Server Auth)       │
    │                          │ ──────────────────────>  │
    │                          │                          │
    │                          │ 3. EXEC SP_DANGNHAP_GV   │
    │                          │    'GV01'                │
    │                          │ ──────────────────────>  │
    │                          │                          │
    │                          │ 4. <Hoten, TenKhoa,      │
    │                          │     Nhom>                │
    │                          │ <──────────────────────  │
    │                          │                          │
    │                          │ 5. SELECT R.name         │
    │                          │    FROM sys.database_     │
    │                          │    role_members RM        │
    │                          │    JOIN ...               │
    │                          │ ──────────────────────>  │
    │                          │ <──────────────────────  │
    │                          │                          │
    │                          │ 6. session[...] = ...    │
    │                          │                          │
    │ 7. 302 Redirect          │                          │
    │   /dashboard             │                          │
    │ <──────────────────────  │                          │
```

### 3.2 Giảng viên (role = GV) — chi tiết

**Bước 1–2: Kết nối SQL Server bằng tài khoản GV**

```python
conn, error = get_db_connection(username, password)
```

- Gọi hàm `get_db_connection(user, pwd)` → tạo `pyodbc.connect()` với **SQL Server Authentication** (`UID=user; PWD=pwd`).
- Nếu **sai username/password** → `conn = None` → flash `"Sai tài khoản hoặc mật khẩu! (SQL Server Authentication)"`.
- Nếu **đúng** → kết nối thành công, tiếp tục bước 3.

> **Vì sao SV không dùng cơ chế này?** Vì SV không có login riêng trong SQL Server. Họ dùng chung login `sv` (xem mục 3.3).

**Bước 3–4: Gọi `SP_DANGNHAP_GV`**

```sql
EXEC SP_DANGNHAP_GV 'GV01'
```

- SP trả về 1 dòng gồm: `USER_NAME`, `HOTEN`, `TENGROUP` (tên khoa).
- Nếu SP trả `None` (không tìm thấy GV) → flash `"Không tìm thấy thông tin giảng viên tương ứng."`.

**Bước 5: Xác định nhóm quyền (PGV / KHOA) từ SQL Server**

```sql
SELECT R.name 
FROM sys.database_role_members RM 
JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id 
JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id 
WHERE U.name = 'GV01'
```

- Truy vấn trực tiếp `sys.database_role_members` để xem GV đang thuộc role database nào (`PGV` = Phòng Giáo Vụ, `KHOA` = Giảng viên thuộc khoa, hoặc các role khác).
- Nếu không tìm thấy → mặc định `'KHOA'`.

**Bước 6: Lưu session + Redirect**

```python
session['username'] = 'GV01'
session['hoten']    = 'Nguyễn Văn A'
session['group']    = 'PGV'           # hoặc 'KHOA'
session['tenkhoa']  = 'Công nghệ Thông tin'
session['role']     = 'GV'
session['khoa']     = khoa           # lấy từ form, mặc định ''
session['db_login'] = 'GV01'
session['db_pass']  = 'GV01'
return redirect('/dashboard')
```

- `session['db_login']` và `session['db_pass']` được lưu để **các route sau này** dùng kết nối lại DB mà **không bắt user nhập lại** (xem `get_db()` trong `app.py`).

### 3.3 Sinh viên (role = SV) — chi tiết

**Bước 1: Kết nối SQL Server bằng tài khoản CHUNG `sv`**

```python
conn, error = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
```

- `SV_SHARED_LOGIN = 'sv'`, `SV_SHARED_PASSWORD = 'sv'` (định nghĩa trong `app.py`).
- Login `sv` này do `setup_login.sql` tạo, có quyền `EXECUTE` trên các SP SV (`SP_DANGNHAP_SV`, `SP_GET_THONGTIN_SV`, `SP_DANGKY_LTC`, `SP_XEM_PHIEU_DIEM`, `SP_GET_LOPTINCHI_DANGKY`, `SP_GET_ALL_NIENKHOA`) + quyền `SELECT` trên một số bảng + `INSERT/UPDATE` trên `DANGKY`.
- Nếu kết nối thất bại (do chưa chạy `setup_login.sql`) → flash thông báo lỗi chi tiết.

**Bước 2: Gọi `SP_DANGNHAP_SV` với Mã SV + Password**

```sql
EXEC SP_DANGNHAP_SV 'N23DCCI079', 'matkhauSV'
```

- SP kiểm tra `MASV` + `PASSWORD` có khớp trong bảng `SINHVIEN` không, **đồng thời kiểm tra `DANGHIHOC = 0`** (chưa nghỉ học).
- Trả về: `USER_NAME`, `HOTEN`, `TENGROUP` (tên khoa), `MALOP`, `TENLOP`, **`QUAHAN`** (cờ sinh viên quá hạn — xem mục 3.4).

**Bước 3 (đặc biệt): Nếu SP trả `None` khi password sai**

```python
if not row:
    cursor.execute("EXEC SP_DANGNHAP_SV ?, ?", (username, ''))
    row = cursor.fetchone()
```

- Mục đích: vẫn lấy thông tin sinh viên (tên, lớp) **để hiển thị thông báo lỗi thân thiện** (VD: "Mã SV không tồn tại" thay vì chung chung "Sai thông tin").
- Nếu vẫn không tìm thấy → flash `"Mã Sinh Viên hoặc Mật khẩu không đúng!"`.

**Bước 4: Lưu session + Redirect**

```python
session['username'] = 'N23DCCI079'
session['hoten']    = 'Trần Thị B'
session['group']    = 'SV'
session['tenkhoa']  = 'Công nghệ Thông tin'
session['role']     = 'SV'
session['khoa']     = khoa
session['malop']    = 'D23DCCI01'
session['quahan']   = bool(row.QUAHAN)   # ← mới thêm ở QUA_HAN_SP_2026
session['db_login'] = 'sv'
session['db_pass']  = 'sv'
return redirect('/dashboard')
```

### 3.4 Cờ QUAHAN (Sinh viên quá hạn)

Đây là cờ mới được bổ sung trong `SP_DANGNHAP_SV` (marker `[QUA_HAN_SP_2026]` trong `setup_login.sql`).

**Công thức:**
```sql
QUAHAN = 1  khi  YEAR(GETDATE()) - CAST(LEFT(LOP.KHOAHOC, 4) AS INT) > 7
QUAHAN = 0  trong trường hợp còn lại
```

**Ví dụ:**
- SV lớp K2021 (`KHOAHOC='2021-2025'`, năm bắt đầu 2021): năm 2026 → `2026 - 2021 = 5 ≤ 7` → `QUAHAN = 0` (bình thường).
- SV lớp K2017 (`KHOAHOC='2017-2021'`, năm bắt đầu 2017): năm 2026 → `2026 - 2017 = 9 > 7` → `QUAHAN = 1` (quá hạn).

**Ảnh hưởng:**
- Vẫn đăng nhập được, vẫn xem phiếu điểm.
- Bị **làm mờ** nút "Đăng ký"/"Hủy đăng ký" trong trang `dangky.html`.
- Bị chặn hoàn toàn ở 3 SP: `SP_DANGKY_LTC`, `SP_HUY_DANGKY`, `SP_NHAP_DIEM` (mã lỗi `-20`).

**Vì sao dùng `YEAR(GETDATE())` thay vì hard-code năm?**
- Hệ thống chạy liên tục nhiều năm không cần bảo trì mốc.
- Khi sang năm 2027, 2028, ..., công thức tự động tăng theo thời gian thực.
- Nhược điểm: nếu server SQL chạy sai giờ hệ thống thì có thể lệch.

---

## 4. Bảo mật & Phân quyền

### 4.1 Cơ chế SQL Server Authentication

Chương trình dùng **2-tier authentication**:

```
Layer 1: SQL Server Login (instance-level)
  - Login 'sv' (chung cho SV) + Login 'GVxx' (riêng cho từng GV)
  - Login name = password mặc định (đơn giản hóa cho bài thực hành)
  - Kết nối qua pyodbc với UID + PWD

Layer 2: Database Role + Permission (database-level)
  - GV: role 'PGV' hoặc 'KHOA' (phân quyền theo chức năng)
  - SV: login 'sv' được cấp quyền EXECUTE trên các SP SV + SELECT/INSERT/UPDATE hạn chế
```

### 4.2 Quyền của từng vai trò

| Vai trò | Group trong session | Quyền truy cập |
|---|---|---|
| **PGV** (Phòng Giáo vụ) | `PGV` | Toàn quyền: quản lý Khoa, Giảng viên, Môn học, Lớp, Sinh viên, Lớp tín chỉ, Nhập điểm |
| **KHOA** (Giảng viên thuộc khoa) | `KHOA` | Nhập điểm + xem lớp tín chỉ thuộc khoa mình |
| **SV** (Sinh viên) | `SV` | Xem phiếu điểm, đăng ký / hủy lớp tín chỉ, **bị vô hiệu hóa nếu quá hạn** |
| **GV** (Giảng viên thường) | `KHOA` (mặc định) | Tương tự KHOA |

### 4.3 Các route được bảo vệ

Mọi route (trừ `/` và `/logout`) đều có decorator `@login_required` hoặc `@require_group('PGV')` / `@require_group('SV')`. Nếu chưa đăng nhập → tự động redirect về `/`. Nếu đăng nhập nhưng sai group → trả 403.

Ví dụ:
```python
@app.route('/loptinchi')
@require_group('PGV', 'KHOA')   # chỉ PGV hoặc KHOA mới vào được
def loptinchi():
    ...

@app.route('/phieu_diem')
@require_group('SV')            # chỉ SV mới vào được
def phieu_diem():
    ...
```

---

## 5. Các lỗi thường gặp & Cách xử lý

### 5.1 Lỗi kết nối SQL Server

| Thông báo flash | Nguyên nhân | Cách xử lý |
|---|---|---|
| `Sai tài khoản hoặc mật khẩu! (SQL Server Authentication)` | GV nhập sai `username` hoặc `password` không khớp với SQL Login | Kiểm tra lại; mặc định `username == password` (VD: `GV01` / `GV01`). Chạy lại `setup_login.sql` để tạo lại login nếu cần. |
| `Lỗi kết nối DB bằng tài khoản SV chung. Chi tiết: ...` | Chưa chạy `setup_login.sql`, hoặc login `sv` chưa được tạo | Chạy lại `setup_login.sql` trên SSMS. |
| `Lỗi: <exception>. Đảm bảo đã chạy setup_login.sql trên SSMS.` | SP `SP_DANGNHAP_GV` / `SP_DANGNHAP_SV` chưa tồn tại | Chạy lại `setup_login.sql` để tạo SP. |
| `Không tìm thấy thông tin giảng viên tương ứng.` | SP chạy nhưng không trả dòng nào (GV chưa có trong bảng `GIANGVIEN`) | Thêm GV vào bảng `GIANGVIEN` rồi chạy lại `setup_login.sql`. |

### 5.2 Lỗi đăng nhập SV

| Tình huống | Kết quả |
|---|---|
| Nhập sai `MASV` | Flash `"Mã Sinh Viên hoặc Mật khẩu không đúng!"` |
| Nhập đúng `MASV` nhưng sai `PASSWORD` | Flash `"Mã Sinh Viên hoặc Mật khẩu không đúng!"` |
| Nhập đúng nhưng `DANGHIHOC = 1` (đã nghỉ học) | SP trả `None` → flash `"Mã Sinh Viên hoặc Mật khẩu không đúng!"` |
| SV thuộc lớp quá hạn | Vẫn login được, nhưng bị làm mờ nút ĐK + banner cảnh báo |

### 5.3 Lỗi session hết hạn

- Flask mặc định session là **client-side cookie** (kích thước giới hạn 4 KB), mã hóa bằng `SECRET_KEY`.
- Nếu restart Flask mà giữ nguyên `SECRET_KEY` → session cũ vẫn dùng được.
- Nếu thay đổi `SECRET_KEY` → tất cả session cũ bị vô hiệu → phải đăng nhập lại.

### 5.4 Lỗi quên đăng xuất

- Nếu không bấm **Đăng xuất** mà chỉ đóng tab → session vẫn còn trong cookie (tồn tại đến khi hết hạn hoặc xóa cookie).
- Mở tab mới → vẫn vào thẳng Dashboard mà không cần đăng nhập lại.
- Cách khắc phục: bấm **Đăng xuất** trước khi rời máy.

---

## 6. Hướng dẫn sử dụng (Step-by-step)

### 6.1 Cho Giảng viên

1. Mở trình duyệt, truy cập `http://127.0.0.1:5001/`.
2. Tab mặc định là **Giảng Viên** (label `LOGIN`).
3. Nhập `Login` (VD: `GV01`) và `Password` (mặc định giống login, VD: `GV01`).
4. Bấm **Đăng nhập**.
5. Nếu thành công → chuyển sang trang Dashboard, hiển thị:
   - Tên: Nguyễn Văn A
   - Khoa: Công nghệ Thông tin
   - Nhóm: PGV (hoặc KHOA)
6. Sử dụng menu bên trái để truy cập chức năng (Mở lớp tín chỉ, Nhập điểm, ...).
7. Khi muốn thoát → bấm **Đăng xuất** ở góc trên bên phải.

### 6.2 Cho Sinh viên

1. Mở trình duyệt, truy cập `http://127.0.0.1:5001/`.
2. Bấm chọn tab **Sinh Viên** (label tự đổi thành `MÃ SV`).
3. Nhập `Mã SV` (VD: `N23DCCI079`) và `Password` (mật khẩu cá nhân).
4. Bấm **Đăng nhập**.
5. Nếu thành công → chuyển sang trang Dashboard với các menu dành cho SV:
   - 📄 Phiếu Điểm Cá Nhân
   - 📝 Đăng Ký Lớp Tín Chỉ
   - 🔑 Đổi Mật Khẩu
6. **Nếu bạn thuộc diện "quá hạn"** (KHOAHOC + 7 năm):
   - Vẫn vào được Dashboard.
   - Thấy banner đỏ cảnh báo.
   - Nút "Đăng ký" và "Hủy đăng ký" bị làm mờ, không bấm được.
   - Khi bấm thử → thông báo "Bạn đã quá hạn 7 năm kể từ khóa học. Vui lòng xem bảng điểm cá nhân."
   - Chỉ có thể xem **Phiếu Điểm Cá Nhân** (chức năng duy nhất còn hoạt động).
7. Khi muốn thoát → bấm **Đăng xuất**.

---

## 7. Mã nguồn tham chiếu

### 7.1 Frontend (templates/login.html)

```html
<form method="POST" action="/">
    <div class="role-tabs">
        <label class="tab-btn active" id="tabGV">
            <input type="radio" name="role" value="GV" checked onclick="changeLabel()"> Giảng Viên
        </label>
        <label class="tab-btn" id="tabSV">
            <input type="radio" name="role" value="SV" onclick="changeLabel()"> Sinh Viên
        </label>
    </div>

    <div class="form-card">
        <div class="form-group">
            <label id="lblUsername">LOGIN</label>
            <input type="text" id="inputUsername" name="username" required>
        </div>
        <div class="form-group">
            <label>PASSWORD</label>
            <input type="password" name="password" required placeholder="123456">
        </div>
        <button type="submit">Đăng nhập</button>
    </div>
</form>
```

```javascript
function changeLabel() {
    var isSV = document.querySelector('input[name="role"][value="SV"]').checked;
    document.getElementById('tabGV').classList.toggle('active', !isSV);
    document.getElementById('tabSV').classList.toggle('active', isSV);
    var label = document.getElementById("lblUsername");
    var input = document.getElementById("inputUsername");
    if (isSV) {
        label.innerText = "MÃ SV";
        input.placeholder = "N23DCCI079";
    } else {
        label.innerText = "LOGIN";
        input.placeholder = "GV01";
    }
}
```

### 7.2 Backend — Route đăng nhập (app.py dòng 199–289)

```python
@app.route('/', methods=['GET', 'POST'])
def login():
    khoa_list = get_danh_sach_khoa()

    if request.method == 'POST':
        role     = request.form.get('role')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        khoa     = request.form.get('khoa', '').strip()

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
                        cursor.execute(
                            "SELECT R.name FROM sys.database_role_members RM "
                            "JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id "
                            "JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id "
                            "WHERE U.name = ?", (magv,)
                        )
                        role_row = cursor.fetchone()
                        nhom = role_row.name.strip() if role_row else 'KHOA'
                        session['username'] = magv
                        session['hoten']    = row.HOTEN.strip()
                        session['group']    = nhom
                        session['tenkhoa']  = row.TENGROUP.strip()
                        session['role']     = 'GV'
                        session['khoa']     = khoa
                        session['db_login'] = username
                        session['db_pass']  = password
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
                        # Lấy thông tin SV để hiển thị thông báo lỗi thân thiện
                        cursor.execute("EXEC SP_DANGNHAP_SV ?, ?", (username, ''))
                        row = cursor.fetchone()
                    if row:
                        session['username'] = row.USER_NAME.strip()
                        session['hoten']    = row.HOTEN.strip()
                        session['group']    = 'SV'
                        session['tenkhoa']  = row.TENGROUP.strip()
                        session['role']     = 'SV'
                        session['khoa']     = khoa
                        session['malop']    = row.MALOP.strip() if hasattr(row, 'MALOP') and row.MALOP else ''
                        session['quahan']   = bool(getattr(row, 'QUAHAN', 0))
                        session['db_login'] = SV_SHARED_LOGIN
                        session['db_pass']  = SV_SHARED_PASSWORD
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
```

### 7.3 Stored Procedure (setup_login.sql)

```sql
-- SP_DANGNHAP_GV: trả về (USER_NAME, HOTEN, TENGROUP)
CREATE PROCEDURE SP_DANGNHAP_GV
    @MAGV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    SELECT RTRIM(GV.MAGV) AS USER_NAME,
           RTRIM(GV.HO) + N' ' + RTRIM(GV.TEN) AS HOTEN,
           RTRIM(K.TENKHOA) AS TENGROUP
    FROM GIANGVIEN GV
    INNER JOIN KHOA K ON GV.MAKHOA = K.MAKHOA
    WHERE GV.MAGV = @MAGV
END
```

```sql
-- SP_DANGNHAP_SV: trả về (USER_NAME, HOTEN, TENGROUP, MALOP, TENLOP, QUAHAN)
CREATE PROCEDURE SP_DANGNHAP_SV
    @MASV     NCHAR(10),
    @PASSWORD NVARCHAR(40)
AS
BEGIN
    SET NOCOUNT ON

    DECLARE @KhoaHocNBD INT = NULL
    DECLARE @QuaHan BIT = 0

    SELECT @KhoaHocNBD = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    IF @KhoaHocNBD IS NOT NULL AND (YEAR(GETDATE()) - @KhoaHocNBD) > 7
        SET @QuaHan = 1

    SELECT SV.MASV AS USER_NAME,
           RTRIM(SV.HO) + N' ' + RTRIM(SV.TEN) AS HOTEN,
           K.TENKHOA AS TENGROUP,
           RTRIM(SV.MALOP) AS MALOP,
           RTRIM(L.TENLOP) AS TENLOP,
           @QuaHan AS QUAHAN
    FROM SINHVIEN SV
    INNER JOIN LOP  L ON SV.MALOP = L.MALOP
    INNER JOIN KHOA K ON L.MAKHOA = K.MAKHOA
    WHERE SV.MASV     = @MASV
      AND SV.PASSWORD = @PASSWORD
      AND SV.DANGHIHOC = 0
END
```

---

## 8. Sơ đồ phân quyền tổng thể (tổng hợp từ 3.1)

```
                          ┌─────────────┐
                          │  /  (login) │
                          └──────┬──────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
            role=GV          role=SV            (none)
                │                │                │
                ▼                ▼                ▼
    ┌───────────────────┐  ┌──────────────┐  (redirect về /)
    │  SQL Auth GVxx   │  │  Login sv    │
    │  EXEC SP_DANGNHAP │  │  EXEC SP_D.. │
    │  _GV + query role │  │  _SV (có QH) │
    └─────────┬─────────┘  └──────┬───────┘
              │                   │
              ▼                   ▼
       session[group]      session[group]='SV'
       = 'PGV' / 'KHOA'
              │                   │
              ├─ PGV ─────► toàn quyền CRUD
              │   (Khoa, GV, MH, Lớp, SV, LTC, Nhập điểm)
              │
              └─ KHOA ────► Nhập điểm + LTC theo khoa
                                 │
                                 ├─ QUAHAN=0 ─► Xem điểm + ĐK/Hủy LTC
                                 │
                                 └─ QUAHAN=1 ─► CHỈ xem điểm (nút khác mờ)
```

---

## 9. Câu hỏi thường gặp (FAQ)

**Q1: Tại sao khi nhập đúng tài khoản SV nhưng vẫn báo "Mã Sinh Viên hoặc Mật khẩu không đúng"?**
A: Có 3 khả năng:
- Mã SV không tồn tại trong bảng `SINHVIEN` (do chưa thêm SV).
- Password không khớp.
- SV đã nghỉ học (`DANGHIHOC = 1`).

Kiểm tra bằng SSMS: `SELECT * FROM SINHVIEN WHERE MASV = '...'`.

**Q2: Tại sao tôi đăng nhập GV thành công nhưng trang Dashboard báo lỗi?**
A: Có thể do `SP_DANGNHAP_GV` hoặc các SP khác (như `SP_GETALL_LOPTINCHI`) chưa được tạo. Chạy lại `setup_login.sql` trên SSMS.

**Q3: Form đăng nhập hiện không có dropdown chọn Khoa, vậy `session['khoa']` lấy từ đâu?**
A: Trong đề bài có đề cập "trên từng khoa", nhưng **form hiện tại chưa có field chọn khoa** (xem mục 2.3). Biến `khoa` được lấy từ `request.form.get('khoa', '')` nhưng mặc định rỗng. Biến này hiện được lưu vào session nhưng **chưa được dùng để phân quyền/lọc dữ liệu theo khoa** trong các route. Nếu cần phân quyền chặt hơn theo khoa, cần bổ sung thêm dropdown và logic kiểm tra.

**Q4: Mật khẩu mặc định của GV là gì?**
A: Mật khẩu mặc định bằng chính `MAGV` (VD: `GV01` / `GV01`). Đây là cấu hình đơn giản hóa cho bài thực hành — `setup_login.sql` tạo login với cú pháp `CREATE LOGIN [GVxx] WITH PASSWORD = N'GVxx'`.

**Q5: Làm sao để đổi mật khẩu?**
A: Chức năng đổi mật khẩu nằm ở menu **🔑 Đổi Mật Khẩu** (chỉ dành cho SV). PGV/GV đổi mật khẩu bằng cách chạy lệnh SQL trên SSMS.

**Q6: Tại sao tôi không bấm được nút "Đăng ký" lớp tín chỉ?**
A: Bạn thuộc diện "sinh viên quá hạn" (KHOAHOC + 7 năm). Tính năng này bị vô hiệu hóa theo yêu cầu. Bạn vẫn có thể xem **Phiếu Điểm Cá Nhân**.

---

## 10. Tóm tắt nhanh

| Nhóm | Cơ chế kết nối DB | Xác thực danh tính | Kết quả |
|---|---|---|---|
| **GV** | SQL Login riêng (`MAGV` / `MAGV`) | Bằng cách kết nối thành công + `SP_DANGNHAP_GV` | session với `group = PGV` hoặc `KHOA` |
| **SV** | SQL Login chung (`sv` / `sv`) | Bằng `SP_DANGNHAP_SV(MASV, PASSWORD)` + check `DANGHIHOC=0` | session với `group = SV` + cờ `QUAHAN` |
