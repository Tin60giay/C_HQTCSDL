# Kế Hoạch Phân Quyền 3 Nhóm — Không Sửa DB, Thêm SP Mới

> **Ràng buộc:**
> - ❌ KHÔNG thay đổi schema DB (bảng, cột, dữ liệu)
> - ❌ KHÔNG sửa SP đã có (`SP_DANGNHAP_GV`, `SP_DANGNHAP_SV`)
> - ✅ ĐƯỢC thêm Stored Procedure mới
> - ✅ ĐƯỢC sửa `app.py` và `templates/`

---

## 1. Xác Định Nhóm PGV / KHOA

Vì DB không có cột `NHOM`, cách duy nhất xác định nhóm **không sửa DB** là định nghĩa trong `app.py`:

```python
# app.py — khai báo ở đầu file
PGV_LOGINS = ['GV01', 'GV05']   # Liệt kê MAGV thuộc Phòng Giáo Vụ
# GV không có trong list → tự động nhóm KHOA
```

Sau khi `SP_DANGNHAP_GV` xác thực thành công:
```python
magv = row.USER_NAME.strip()
nhom = 'PGV' if magv in PGV_LOGINS else 'KHOA'
session['group']   = nhom                    # 'PGV' hoặc 'KHOA'
session['tenkhoa'] = row.TENGROUP.strip()    # TENKHOA để hiển thị
```

---

## 2. Stored Procedures Mới Cần Thêm (vào `setup_login.sql`)

> Các SP hiện có **giữ nguyên**, chỉ **THÊM** SP mới bên dưới.

---

### 2.1 Nhóm SP — Dành cho PGV (Toàn quyền)

#### `SP_GETALL_KHOA` — Lấy danh sách khoa
```sql
CREATE PROCEDURE SP_GETALL_KHOA
AS
BEGIN
    SET NOCOUNT ON
    SELECT MAKHOA, TENKHOA FROM KHOA ORDER BY MAKHOA
END
```

#### `SP_GETALL_GIANGVIEN` — Lấy danh sách giảng viên
```sql
CREATE PROCEDURE SP_GETALL_GIANGVIEN
AS
BEGIN
    SET NOCOUNT ON
    SELECT GV.MAGV, GV.MAKHOA, K.TENKHOA,
           RTRIM(GV.HO) + ' ' + RTRIM(GV.TEN) AS HOTEN,
           GV.HOCVI, GV.HOCHAM, GV.CHUYENMON
    FROM GIANGVIEN GV
    INNER JOIN KHOA K ON GV.MAKHOA = K.MAKHOA
    ORDER BY GV.MAKHOA, GV.MAGV
END
```

#### `SP_GETALL_SINHVIEN` — Lấy danh sách sinh viên
```sql
CREATE PROCEDURE SP_GETALL_SINHVIEN
    @MAKHOA NCHAR(10) = NULL   -- NULL = lấy tất cả
AS
BEGIN
    SET NOCOUNT ON
    SELECT SV.MASV,
           RTRIM(SV.HO) + ' ' + RTRIM(SV.TEN) AS HOTEN,
           SV.PHAI, SV.DIACHI, SV.NGAYSINH,
           L.MALOP, L.TENLOP,
           K.MAKHOA, K.TENKHOA,
           SV.DANGHIHOC
    FROM SINHVIEN SV
    INNER JOIN LOP L      ON SV.MALOP  = L.MALOP
    INNER JOIN KHOA K     ON L.MAKHOA  = K.MAKHOA
    WHERE (@MAKHOA IS NULL OR K.MAKHOA = @MAKHOA)
    ORDER BY K.MAKHOA, L.MALOP, SV.MASV
END
```

#### `SP_GETALL_LOPTINCHI` — Lấy danh sách lớp tín chỉ
```sql
CREATE PROCEDURE SP_GETALL_LOPTINCHI
    @NIENKHOA NCHAR(9) = NULL,
    @HOCKY    INT      = NULL,
    @MAKHOA   NCHAR(10) = NULL
AS
BEGIN
    SET NOCOUNT ON
    SELECT LTC.MALTC, LTC.NIENKHOA, LTC.HOCKY,
           LTC.MAMH, MH.TENMH,
           LTC.NHOM,
           LTC.MAGV,
           RTRIM(GV.HO) + ' ' + RTRIM(GV.TEN) AS TENGV,
           LTC.MAKHOA, K.TENKHOA,
           LTC.SOSVTOITHIEU, LTC.HUYLOP,
           COUNT(DK.MASV) AS SOSV_DANGKY
    FROM LOPTINCHI LTC
    INNER JOIN MONHOC   MH ON LTC.MAMH  = MH.MAMH
    INNER JOIN GIANGVIEN GV ON LTC.MAGV = GV.MAGV
    INNER JOIN KHOA      K  ON LTC.MAKHOA = K.MAKHOA
    LEFT  JOIN DANGKY   DK  ON LTC.MALTC = DK.MALTC AND DK.HUYDANGKY = 0
    WHERE (@NIENKHOA IS NULL OR LTC.NIENKHOA = @NIENKHOA)
      AND (@HOCKY    IS NULL OR LTC.HOCKY    = @HOCKY)
      AND (@MAKHOA   IS NULL OR LTC.MAKHOA   = @MAKHOA)
      AND LTC.HUYLOP = 0
    GROUP BY LTC.MALTC, LTC.NIENKHOA, LTC.HOCKY,
             LTC.MAMH, MH.TENMH, LTC.NHOM,
             LTC.MAGV, GV.HO, GV.TEN,
             LTC.MAKHOA, K.TENKHOA,
             LTC.SOSVTOITHIEU, LTC.HUYLOP
    ORDER BY LTC.NIENKHOA, LTC.HOCKY, LTC.MAMH, LTC.NHOM
END
```

#### `SP_NHAP_DIEM` — Nhập điểm sinh viên (PGV + KHOA)
```sql
CREATE PROCEDURE SP_NHAP_DIEM
    @MALTC    INT,
    @MASV     NCHAR(10),
    @DIEM_CC  INT   = NULL,
    @DIEM_GK  FLOAT = NULL,
    @DIEM_CK  FLOAT = NULL
AS
BEGIN
    SET NOCOUNT ON
    UPDATE DANGKY
    SET DIEM_CC = @DIEM_CC,
        DIEM_GK = @DIEM_GK,
        DIEM_CK = @DIEM_CK
    WHERE MALTC = @MALTC AND MASV = @MASV
END
```

---

### 2.2 Nhóm SP — Dành cho Sinh viên

#### `SP_DANGKY_LTC` — Đăng ký lớp tín chỉ
```sql
CREATE PROCEDURE SP_DANGKY_LTC
    @MASV  NCHAR(10),
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON

    -- Kiểm tra đã đăng ký chưa
    IF EXISTS (SELECT 1 FROM DANGKY WHERE MASV = @MASV AND MALTC = @MALTC AND HUYDANGKY = 0)
    BEGIN
        SELECT -1 AS KETQUA, N'Bạn đã đăng ký lớp này rồi' AS THONGBAO
        RETURN
    END

    -- Kiểm tra lớp còn mở không
    IF NOT EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC AND HUYLOP = 0)
    BEGIN
        SELECT -2 AS KETQUA, N'Lớp tín chỉ đã bị hủy hoặc không tồn tại' AS THONGBAO
        RETURN
    END

    INSERT INTO DANGKY (MALTC, MASV, HUYDANGKY)
    VALUES (@MALTC, @MASV, 0)

    SELECT 1 AS KETQUA, N'Đăng ký thành công' AS THONGBAO
END
```

#### `SP_XEM_PHIEU_DIEM` — Xem phiếu điểm cá nhân
```sql
CREATE PROCEDURE SP_XEM_PHIEU_DIEM
    @MASV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    SELECT
        LTC.NIENKHOA, LTC.HOCKY,
        MH.MAMH, MH.TENMH,
        LTC.NHOM,
        RTRIM(GV.HO) + ' ' + RTRIM(GV.TEN) AS TENGV,
        DK.DIEM_CC, DK.DIEM_GK, DK.DIEM_CK,
        -- Công thức tính điểm tổng kết: CC 10% + GK 30% + CK 60%
        CASE
            WHEN DK.DIEM_CC IS NOT NULL
             AND DK.DIEM_GK IS NOT NULL
             AND DK.DIEM_CK IS NOT NULL
            THEN ROUND(DK.DIEM_CC * 0.1 + DK.DIEM_GK * 0.3 + DK.DIEM_CK * 0.6, 1)
            ELSE NULL
        END AS DIEM_TK
    FROM DANGKY DK
    INNER JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC
    INNER JOIN MONHOC    MH  ON LTC.MAMH = MH.MAMH
    INNER JOIN GIANGVIEN GV  ON LTC.MAGV = GV.MAGV
    WHERE DK.MASV = @MASV AND DK.HUYDANGKY = 0
    ORDER BY LTC.NIENKHOA, LTC.HOCKY, MH.TENMH
END
```

#### `SP_GET_LOPTINCHI_DANGKY` — Lấy danh sách lớp tín chỉ có thể đăng ký
```sql
CREATE PROCEDURE SP_GET_LOPTINCHI_DANGKY
    @MASV     NCHAR(10),
    @NIENKHOA NCHAR(9),
    @HOCKY    INT
AS
BEGIN
    SET NOCOUNT ON
    SELECT
        LTC.MALTC, LTC.MAMH, MH.TENMH,
        LTC.NHOM,
        RTRIM(GV.HO) + ' ' + RTRIM(GV.TEN) AS TENGV,
        K.TENKHOA,
        LTC.SOSVTOITHIEU,
        COUNT(DK2.MASV) AS SOSV_DANGKY,
        CASE WHEN DK_SV.MASV IS NOT NULL THEN 1 ELSE 0 END AS DA_DANGKY
    FROM LOPTINCHI LTC
    INNER JOIN MONHOC    MH  ON LTC.MAMH = MH.MAMH
    INNER JOIN GIANGVIEN GV  ON LTC.MAGV = GV.MAGV
    INNER JOIN KHOA      K   ON LTC.MAKHOA = K.MAKHOA
    LEFT  JOIN DANGKY    DK2 ON LTC.MALTC = DK2.MALTC AND DK2.HUYDANGKY = 0
    LEFT  JOIN DANGKY    DK_SV ON LTC.MALTC = DK_SV.MALTC
                               AND DK_SV.MASV = @MASV
                               AND DK_SV.HUYDANGKY = 0
    WHERE LTC.NIENKHOA = @NIENKHOA
      AND LTC.HOCKY    = @HOCKY
      AND LTC.HUYLOP   = 0
    GROUP BY LTC.MALTC, LTC.MAMH, MH.TENMH, LTC.NHOM,
             GV.HO, GV.TEN, K.TENKHOA,
             LTC.SOSVTOITHIEU, DK_SV.MASV
    ORDER BY MH.TENMH, LTC.NHOM
END
```

---

## 3. Phân Quyền EXECUTE cho các SP Mới

```sql
-- SP dành cho PGV và KHOA (GV nói chung)
GRANT EXECUTE ON SP_GETALL_LOPTINCHI    TO PUBLIC
GRANT EXECUTE ON SP_NHAP_DIEM           TO PUBLIC

-- SP chỉ dành cho PGV
-- (kiểm soát trong app.py, không cần restrict ở DB)
GRANT EXECUTE ON SP_GETALL_KHOA         TO PUBLIC
GRANT EXECUTE ON SP_GETALL_GIANGVIEN    TO PUBLIC
GRANT EXECUTE ON SP_GETALL_SINHVIEN     TO PUBLIC

-- SP dành cho SV (qua tài khoản sv)
GRANT EXECUTE ON SP_DANGKY_LTC          TO [sv]
GRANT EXECUTE ON SP_XEM_PHIEU_DIEM      TO [sv]
GRANT EXECUTE ON SP_GET_LOPTINCHI_DANGKY TO [sv]
```

> Việc kiểm soát PGV vs KHOA được thực hiện tại **tầng app.py** (kiểm tra `session['group']`), không cần phân biệt ở DB vì DB không có cột NHOM.

---

## 4. Thay Đổi `app.py`

### 4.1 Config nhóm PGV

```python
PGV_LOGINS = ['GV01', 'GV05']
```

### 4.2 Gán nhóm sau đăng nhập GV

```python
magv  = row.USER_NAME.strip()
nhom  = 'PGV' if magv in PGV_LOGINS else 'KHOA'
session['group']   = nhom
session['tenkhoa'] = row.TENGROUP.strip()
```

### 4.3 Các route mới theo nhóm

```python
# ---- PGV ONLY ----
@app.route('/khoa')           # Quản lý khoa       → gọi SP_GETALL_KHOA
@app.route('/giangvien')      # Quản lý GV         → gọi SP_GETALL_GIANGVIEN
@app.route('/sinhvien')       # Quản lý SV         → gọi SP_GETALL_SINHVIEN

# ---- PGV + KHOA ----
@app.route('/loptinchi')      # Xem/mở lớp TC      → gọi SP_GETALL_LOPTINCHI
@app.route('/nhapdiem')       # Nhập điểm          → gọi SP_NHAP_DIEM

# ---- SV ONLY ----
@app.route('/dangky')         # Đăng ký LTC        → gọi SP_DANGKY_LTC
@app.route('/phieu_diem')     # Xem phiếu điểm     → gọi SP_XEM_PHIEU_DIEM
```

Mỗi route kiểm tra `session['group']` trước khi xử lý:

```python
@app.route('/khoa')
def quan_ly_khoa():
    if session.get('group') != 'PGV':
        flash('Bạn không có quyền truy cập chức năng này.')
        return redirect(url_for('dashboard'))
    # ... xử lý tiếp
```

---

## 5. Thay Đổi `dashboard.html`

```html
{% if group == 'PGV' %}
    <a href="/khoa"       class="menu-item">🏛️ Quản lý Khoa</a>
    <a href="/lop"        class="menu-item">📋 Quản lý Lớp CN</a>
    <a href="/giangvien"  class="menu-item">👨‍🏫 Quản lý Giảng Viên</a>
    <a href="/sinhvien"   class="menu-item">👨‍🎓 Quản lý Sinh Viên</a>
    <a href="/monhoc"     class="menu-item">📖 Quản lý Môn Học</a>
    <a href="/loptinchi"  class="menu-item">🏫 Mở Lớp Tín Chỉ</a>
    <a href="/nhapdiem"   class="menu-item">✏️ Nhập Điểm</a>
    <a href="/baocao"     class="menu-item">📊 Báo Cáo Thống Kê</a>
    <a href="/taikhoan"   class="menu-item">🔑 Tạo Tài Khoản</a>

{% elif group == 'KHOA' %}
    <a href="/loptinchi"  class="menu-item">👁️ Xem Lớp Tín Chỉ</a>
    <a href="/nhapdiem"   class="menu-item">✏️ Nhập Điểm</a>
    <a href="/baocao"     class="menu-item">📊 Báo Cáo Thống Kê</a>

{% else %}
    <a href="/dangky"     class="menu-item">📝 Đăng Ký Lớp Tín Chỉ</a>
    <a href="/phieu_diem" class="menu-item">📄 Phiếu Điểm Cá Nhân</a>
    <a href="/hocphi"     class="menu-item">💰 Thông Tin Học Phí</a>
{% endif %}
```

---

## 6. Tổng Hợp Các File Cần Thay Đổi

| File | Loại thay đổi | Chi tiết |
|---|---|---|
| `setup_login.sql` | **THÊM** SP mới | 6 SP mới + GRANT EXECUTE |
| `app.py` | Sửa | Thêm `PGV_LOGINS`, logic gán nhóm, các route mới |
| `templates/dashboard.html` | Sửa | Phân 3 nhánh menu |
| `templates/*.html` | **THÊM** | Các template cho từng chức năng mới |
| `QLDSV_HTC_utf8.sql` | ❌ Không đụng | — |
| SP cũ | ❌ Không đụng | `SP_DANGNHAP_GV`, `SP_DANGNHAP_SV` giữ nguyên |

---

## 7. Danh Sách SP Mới

| Stored Procedure | Nhóm sử dụng | Mô tả |
|---|---|---|
| `SP_GETALL_KHOA` | PGV | Danh sách tất cả khoa |
| `SP_GETALL_GIANGVIEN` | PGV | Danh sách tất cả giảng viên |
| `SP_GETALL_SINHVIEN` | PGV | Danh sách sinh viên (lọc theo khoa) |
| `SP_GETALL_LOPTINCHI` | PGV + KHOA | Danh sách lớp tín chỉ |
| `SP_NHAP_DIEM` | PGV + KHOA | Cập nhật điểm CC/GK/CK |
| `SP_DANGKY_LTC` | SV | Đăng ký lớp tín chỉ |
| `SP_XEM_PHIEU_DIEM` | SV | Xem điểm cá nhân + tính điểm TK |
| `SP_GET_LOPTINCHI_DANGKY` | SV | Danh sách lớp TC có thể đăng ký |
