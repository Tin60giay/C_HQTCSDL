# KẾ HOẠCH: NIÊN KHÓA ĐÓNG BĂNG (2025) + QUY TẮC SINH VIÊN QUÁ HẠN

> **Mục tiêu:** Sửa lại mốc đóng băng (đã lệch sang `2020-2021` do nhầm lẫn ở plan trước) về đúng `2025-2026`, đồng thời bổ sung cơ chế **"Sinh viên quá hạn"** — vẫn login được để xem điểm, nhưng bị vô hiệu hóa toàn bộ chức năng khác; giảng viên cũng không được nhập điểm lại cho SV thuộc diện này.
>
> **Kế hoạch trước (nộp bổ sung):** `plans/PLANT_VALIDATE_SP_2026.md` — đã sửa `setup_login.sql` với mốc sai `2020-2021`. Plan này sẽ **revert** về `2025-2026` và thêm logic mới.

---

## 0. Bối cảnh & Nguyên nhân sửa

Trong plan trước (`PLANT_VALIDATE_SP_2026.md` câu hỏi 1), mình đã hỏi bạn về mốc đóng băng. Bạn trả lời:

> *"Hiện nay là năm 2026 - tức là niên khóa đóng băng phải - đi 7 cho 1. - ok"*

Mình đã hiểu nhầm thành **mốc đóng băng = `2026 - 7 + 1 = 2020`**, dẫn đến thay `2025-2026` → `2020-2021` trong 11 chỗ. Theo thông báo mới nhất, bạn xác nhận:

> *"đóng băng là đóng băng từ 2025 về trước"*

→ **Mốc đóng băng đúng = `2025-2026`** (giống với hàm `is_frozen` trong `app.py` đang dùng).

Ngoài ra, bạn bổ sung một quy tắc **Sinh viên quá hạn** hoàn toàn mới:
- Sinh viên chỉ được đăng ký lớp tín chỉ thuộc khoảng `[KHOAHOC, KHOAHOC + 7 năm]`.
- Nếu vượt quá → vẫn login xem điểm nhưng **vô hiệu hóa toàn bộ chức năng**.
- Giảng viên **không được nhập điểm lại** cho SV thuộc diện này.

---

## 1. Định nghĩa & Thuật ngữ

### 1.1 Niên khóa đóng băng (Frozen Year)
- **Mốc:** `NIENKHOA < '2025-2026'`
- **Áp dụng cho:** Mọi thao tác INSERT / UPDATE / DELETE / Phục hồi trên bảng `LOPTINCHI`; thao tác UPDATE trên `MONHOC` (nếu môn đã từng dạy trong NK đã đóng băng).
- **Không áp dụng cho:** Login, xem phiếu điểm, xem thông tin cá nhân.

### 1.2 Sinh viên quá hạn (Out-of-range Student)
- **Định nghĩa:** Sinh viên có niên khóa hiện tại **lớn hơn** `LOP.KHOAHOC + 7 năm`.
  - `LOP.KHOAHOC` là khóa học của lớp sinh viên đang học (chuỗi `nChar(9)` dạng `YYYY-YYYY`, ví dụ `'2021-2025'`).
  - Lấy **năm bắt đầu** = 4 ký tự đầu của `KHOAHOC` → cộng 7.
  - **Niên khóa tối đa SV được ĐK** = năm bắt đầu + 7. Nếu năm bắt đầu = 2021 → tối đa `2028-2029`.
- **Áp dụng cho:**
  - `SP_DANGKY_LTC`: chặn đăng ký lớp có `NIENKHOA > (năm bắt đầu KHOAHOC + 7 năm)`.
  - `SP_NHAP_DIEM`: chặn giảng viên nhập điểm cho SV thuộc diện này (xem cách tính chi tiết ở mục 3.3).
- **Không áp dụng cho:**
  - Login (`SP_DANGNHAP_SV` vẫn cho vào).
  - Xem phiếu điểm (`SP_XEM_PHIEU_DIEM` vẫn trả về dữ liệu).
  - App **vô hiệu hóa toàn bộ nút bấm** khác (theo yêu cầu).

### 1.3 So sánh hai khái niệm (dễ nhầm)

| Tiêu chí | Niên khóa đóng băng | SV quá hạn |
|---|---|---|
| Đối tượng | Mọi thao tác lên `LOPTINCHI` cũ | SV thuộc lớp có `KHOAHOC` cũ |
| Mốc so sánh | `NIENKHOA < 2025-2026` | `LTC.NIENKHOA > (LOP.KHOAHOC + 7 năm)` |
| Ai bị ảnh hưởng | Cả PGV, KHOA, SV | SV thuộc khóa cũ |
| Hậu quả | Từ chối thao tác hoàn toàn | Vô hiệu hóa UI nhưng vẫn xem điểm |

---

## 2. Công thức tính cụ thể (SQL)

### 2.1 Trích "năm bắt đầu" từ `KHOAHOC`
```sql
-- KHOAHOC = '2021-2025' → 2021
DECLARE @NamBD INT = CAST(LEFT(L.KHOAHOC, 4) AS INT)
```

### 2.2 Trích "năm bắt đầu" từ `NIENKHOA` của LTC
```sql
-- NIENKHOA = '2028-2029' → 2028
DECLARE @NamNK INT = CAST(LEFT(LTC.NIENKHOA, 4) AS INT)
```

### 2.3 Công thức "vượt quá 7 năm"
```sql
-- Nếu @NamNK > (@NamBD + 7) thì SV thuộc lớp này đã quá hạn với lớp tín chỉ đó
DECLARE @QuaHan BIT = CASE WHEN @NamNK > (@NamBD + 7) THEN 1 ELSE 0 END
```

**Ví dụ minh họa:**
- SV K2021 (`KHOAHOC='2021-2025'`, năm BD = 2021) → được ĐK lớp từ NK `2021-2022` đến NK `2028-2029`. Lớp NK `2029-2030` trở đi → quá hạn.
- SV K2025 (`KHOAHOC='2025-2029'`, năm BD = 2025) → được ĐK lớp từ NK `2025-2026` đến NK `2032-2033`. Lớp NK `2033-2034` trở đi → quá hạn.

---

## 3. Thay đổi chi tiết trong `setup_login.sql`

### 3.1 Revert mốc đóng băng (11 chỗ)
Thay toàn bộ `'2020-2021'` → `'2025-2026'`. Áp dụng cho 5 SP:
- `SP_THEM_LOPTINCHI`
- `SP_SUA_LOPTINCHI`
- `SP_XOA_LOPTINCHI`
- `SP_PHUCHOI_LOPTINCHI`
- `SP_SUA_MONHOC`

> Thay đổi này **hoàn tác phần sai** của plan cũ, không thêm logic mới.

### 3.2 Sửa `SP_DANGNHAP_SV` — Trả thêm cột `QUAHAN`

```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_DANGNHAP_SV' AND type = 'P')
    DROP PROCEDURE SP_DANGNHAP_SV
GO
CREATE PROCEDURE SP_DANGNHAP_SV
    @MASV     NCHAR(10),
    @PASSWORD NVARCHAR(40)
AS
BEGIN
    SET NOCOUNT ON

    -- Tính số năm đã học của SV so với lớp
    DECLARE @KhoaHocNBD INT
    DECLARE @QuaHan BIT = 0

    SELECT @KhoaHocNBD = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    -- Nếu năm hiện tại (lấy theo GETDATE() hoặc cố định năm 2026) > (năm bắt đầu + 7) thì quá hạn
    -- Công thức: năm hiện tại - năm bắt đầu > 7
    IF @KhoaHocNBD IS NOT NULL
       AND (YEAR(GETDATE()) - @KhoaHocNBD) > 7
        SET @QuaHan = 1

    SELECT 
        SV.MASV                                         AS USER_NAME,
        RTRIM(SV.HO) + N' ' + RTRIM(SV.TEN)            AS HOTEN,
        K.TENKHOA                                       AS TENGROUP,
        RTRIM(SV.MALOP)                                 AS MALOP,
        RTRIM(L.TENLOP)                                 AS TENLOP,
        @QuaHan                                         AS QUAHAN
    FROM SINHVIEN SV
    INNER JOIN LOP  L ON SV.MALOP  = L.MALOP
    INNER JOIN KHOA K ON L.MAKHOA  = K.MAKHOA
    WHERE SV.MASV      = @MASV 
      AND SV.PASSWORD  = @PASSWORD
      AND SV.DANGHIHOC = 0
END
GO
GRANT EXECUTE ON SP_DANGNHAP_SV TO [sv]
GO
```

**Giải thích:**
- Cột `QUAHAN` trả về `1` nếu SV đã học quá 7 năm (tính theo năm hiện tại `YEAR(GETDATE())`).
- Mình dùng `YEAR(GETDATE())` thay vì hard-code `2026` để hệ thống tự cập nhật theo thời gian.
- App sẽ lưu `session['quahan']` rồi dựa vào đó vô hiệu hóa UI.

### 3.3 Sửa `SP_DANGKY_LTC` — Chặn SV quá hạn

```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_DANGKY_LTC' AND type = 'P')
    DROP PROCEDURE SP_DANGKY_LTC
GO
CREATE PROCEDURE SP_DANGKY_LTC
    @MASV  NCHAR(10),
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    
    DECLARE @MAMH NCHAR(10), @NK NVARCHAR(9), @HK INT
    SELECT @MAMH = MAMH, @NK = NIENKHOA, @HK = HOCKY 
    FROM LOPTINCHI WHERE MALTC = @MALTC AND HUYLOP = 0

    -- 1. Kiểm tra lớp có tồn tại và chưa bị hủy
    IF @MAMH IS NULL
    BEGIN
        SELECT -2 AS KETQUA, N'Lớp tín chỉ không tồn tại hoặc đã bị hủy' AS THONGBAO
        RETURN
    END

    -- 2. [MỚI] Kiểm tra SV quá hạn: niên khóa LTC > (KHOAHOC năm bắt đầu + 7)
    DECLARE @KhoaHocNBD INT
    DECLARE @NamNK INT
    DECLARE @QuaHan BIT = 0
    
    SELECT @KhoaHocNBD = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV
    
    SET @NamNK = CAST(LEFT(@NK, 4) AS INT)
    
    IF @KhoaHocNBD IS NOT NULL AND @NamNK > (@KhoaHocNBD + 7)
        SET @QuaHan = 1

    IF @QuaHan = 1
    BEGIN
        SELECT -20 AS KETQUA, N'Bạn đã quá thời hạn đăng ký (vượt quá KHOAHOC + 7 năm). Chỉ có thể xem điểm.' AS THONGBAO
        RETURN
    END

    -- 3. Kiểm tra trùng môn học trong cùng học kỳ/niên khóa
    IF EXISTS (
        SELECT 1 FROM DANGKY DK
        JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC
        WHERE DK.MASV = @MASV 
          AND LTC.MAMH = @MAMH 
          AND LTC.NIENKHOA = @NK 
          AND LTC.HOCKY = @HK
          AND (DK.HUYDANGKY = 0 OR DK.HUYDANGKY IS NULL)
    )
    BEGIN
        SELECT -1 AS KETQUA, N'Bạn đã đăng ký một lớp khác cho môn học này rồi' AS THONGBAO
        RETURN
    END

    -- 4. Thực hiện đăng ký
    IF EXISTS (SELECT 1 FROM DANGKY WHERE MASV = @MASV AND MALTC = @MALTC)
    BEGIN
        UPDATE DANGKY SET HUYDANGKY = 0 WHERE MASV = @MASV AND MALTC = @MALTC
    END
    ELSE
    BEGIN
        INSERT INTO DANGKY (MALTC, MASV, HUYDANGKY) VALUES (@MALTC, @MASV, 0)
    END

    SELECT 1 AS KETQUA, N'Đăng ký thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_DANGKY_LTC TO [sv]
GO
```

**Mã lỗi mới: `-20`** cho "quá hạn" (theo bảng mã lỗi ở `CRITICAL.md`).

### 3.4 Sửa `SP_NHAP_DIEM` — Chặn GV nhập điểm cho SV quá hạn

```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_NHAP_DIEM' AND type = 'P')
    DROP PROCEDURE SP_NHAP_DIEM
GO
CREATE PROCEDURE SP_NHAP_DIEM
    @MALTC   INT,
    @MASV    NCHAR(10),
    @DIEM_CC INT   = NULL,
    @DIEM_GK FLOAT = NULL,
    @DIEM_CK FLOAT = NULL
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM DANGKY WHERE MALTC = @MALTC AND MASV = @MASV)
    BEGIN
        SELECT -1 AS KETQUA, N'Sinh viên chưa đăng ký lớp tín chỉ này' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] [QUA_HAN_SP_2026] Kiểm tra SV quá hạn (KHOAHOC + 7 năm)
    DECLARE @KhoaHocNBD INT
    DECLARE @NamNK INT
    DECLARE @QuaHan BIT = 0
    
    SELECT @KhoaHocNBD = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    SELECT @NamNK = CAST(LEFT(LTC.NIENKHOA, 4) AS INT)
    FROM LOPTINCHI LTC
    WHERE LTC.MALTC = @MALTC

    IF @KhoaHocNBD IS NOT NULL AND @NamNK > (@KhoaHocNBD + 7)
        SET @QuaHan = 1

    IF @QuaHan = 1
    BEGIN
        SELECT -20 AS KETQUA, N'Sinh viên đã quá hạn (KHOAHOC + 7 năm), không thể nhập/sửa điểm' AS THONGBAO
        RETURN
    END

    -- ... (giữ nguyên 6 check validate điểm như plan trước: -2, -3, -4, -5, -6)
    -- ... (giữ nguyên UPDATE)
END
GO
GRANT EXECUTE ON SP_NHAP_DIEM TO PUBLIC
GO
```

> **Lưu ý:** Logic check quá hạn được **chèn ngay sau** check tồn tại đăng ký, **trước** 6 check validate điểm. Mã lỗi `-20` giống `SP_DANGKY_LTC` cho thống nhất.

### 3.5 Sửa `SP_XEM_PHIEU_DIEM` — Cho phép xem điểm kể cả khi quá hạn
**Không sửa gì** — SP này vẫn trả về dữ liệu bình thường. App sẽ dựa vào `session['quahan']` để quyết định hiển thị thế nào (xem mục 4.2).

### 3.6 Sửa `SP_HUY_DANGKY` — Chặn SV quá hạn hủy đăng ký
```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_HUY_DANGKY' AND type = 'P')
    DROP PROCEDURE SP_HUY_DANGKY
GO
CREATE PROCEDURE SP_HUY_DANGKY
    @MASV  NCHAR(10),
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    
    -- [QUA_HAN_SP_2026] Chặn hủy nếu SV đã quá hạn
    DECLARE @KhoaHocNBD INT
    DECLARE @NamNK INT
    DECLARE @QuaHan BIT = 0
    
    SELECT @KhoaHocNBD = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV
    
    SELECT @NamNK = CAST(LEFT(LTC.NIENKHOA, 4) AS INT)
    FROM LOPTINCHI LTC
    WHERE LTC.MALTC = @MALTC

    IF @KhoaHocNBD IS NOT NULL AND @NamNK > (@KhoaHocNBD + 7)
        SET @QuaHan = 1

    IF @QuaHan = 1
    BEGIN
        SELECT -20 AS KETQUA, N'Bạn đã quá hạn, không thể hủy đăng ký' AS THONGBAO
        RETURN
    END

    IF NOT EXISTS (SELECT 1 FROM DANGKY WHERE MASV = @MASV AND MALTC = @MALTC AND (HUYDANGKY = 0 OR HUYDANGKY IS NULL))
    BEGIN
        SELECT -1 AS KETQUA, N'Bạn chưa đăng ký lớp này hoặc đã hủy rồi' AS THONGBAO
        RETURN
    END

    IF EXISTS (SELECT 1 FROM DANGKY WHERE MASV = @MASV AND MALTC = @MALTC AND (DIEM_CC IS NOT NULL OR DIEM_GK IS NOT NULL OR DIEM_CK IS NOT NULL))
    BEGIN
        SELECT -2 AS KETQUA, N'Không thể hủy: Môn học đã có đầu điểm' AS THONGBAO
        RETURN
    END

    UPDATE DANGKY SET HUYDANGKY = 1 WHERE MASV = @MASV AND MALTC = @MALTC
    SELECT 1 AS KETQUA, N'Hủy đăng ký thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_HUY_DANGKY TO [sv]
GO
```

---

## 4. Thay đổi chi tiết trong `app.py`

### 4.1 Lưu `quahan` vào session khi đăng nhập SV
```python
# Trong route /login_sv (chỗ gọi SP_DANGNHAP_SV)
row = cursor.fetchone()
quahan = bool(row.QUAHAN) if hasattr(row, 'QUAHAN') else False
session['quahan'] = quahan
```

### 4.2 Trang `phieu_diem.html` — Hiển thị banner cảnh báo nếu quá hạn
```html
{% if session.get('quahan') %}
<div class="alert alert-warning">
    <strong>⚠️ Tài khoản của bạn đã quá hạn 7 năm kể từ khóa học.</strong>
    Bạn chỉ có thể xem phiếu điểm. Mọi chức năng khác đã bị vô hiệu hóa.
</div>
{% endif %}
```

### 4.3 Vô hiệu hóa menu/route cho SV quá hạn
Có 2 cách, mình đề xuất **cách 1** (đơn giản hơn):

**Cách 1 — Filter ở Flask (`app.py`):**
```python
@app.before_request
def check_quahan():
    if session.get('quahan') and request.endpoint in ['dangky', 'huy_dangky', 'thong_tin_sv', 'doi_mat_khau']:
        flash('Tài khoản của bạn đã quá hạn, không thể sử dụng chức năng này.')
        return redirect(url_for('phieu_diem'))
```

**Cách 2 — Filter ở HTML (`dashboard.html`):**
```html
{% if not session.get('quahan') %}
    <a href="/dangky" class="menu-item">📝 Đăng Ký Lớp Tín Chỉ</a>
    <a href="/thongtincanhan" class="menu-item">👤 Thông Tin Cá Nhân</a>
    <a href="/doimatkhau" class="menu-item">🔑 Đổi Mật Khẩu</a>
{% endif %}
<a href="/phieu_diem" class="menu-item">📄 Phiếu Điểm Cá Nhân</a>  <!-- luôn hiển thị -->
```

> **Đề xuất:** Làm **cả 2 cách** để chắc chắn — Cách 1 chặn ở backend (an toàn), Cách 2 ẩn menu ở frontend (gọn gàng).

### 4.4 Route nhập điểm (PGV/KHOA) — chặn ngay từ backend
```python
# Trong route /nhapdiem/submit
# Trước khi gọi SP_NHAP_DIEM, kiểm tra quá hạn
# (Tuy SP_NHAP_DIEM đã chặn ở mục 3.4, nhưng kiểm tra trước giúp trả message thân thiện hơn)
```

> Mình sẽ **không thêm** đoạn này vì SP đã chặn rồi (defense in depth). Nếu bạn muốn có thể bổ sung.

---

## 5. Cập nhật `CRITICAL.md`

### 5.1 Sửa dòng "Công thức niên khóa đóng băng"
**Trước (sai):**
```
- Mốc đóng băng = `(Năm hiện tại - 7 + 1) = 2020` → threshold `NIENKHOA < '2020-2021'`.
```

**Sau (đúng):**
```
- Mốc đóng băng cố định = `2025-2026` → threshold `NIENKHOA < '2025-2026'`.
- Áp dụng cho mọi thao tác INSERT / UPDATE / DELETE / Phục hồi trên bảng `LOPTINCHI`.
- Áp dụng cho UPDATE trên `MONHOC` nếu môn đã từng xuất hiện trong `LOPTINCHI` có `NIENKHOA < '2025-2026'`.
```

### 5.2 Thêm mục mới: "Quy tắc sinh viên quá hạn"
```
### Quy tắc sinh viên quá hạn (Out-of-range Student)

- **Định nghĩa:** Sinh viên có `YEAR(GETDATE()) - CAST(LEFT(LOP.KHOAHOC, 4) AS INT) > 7`.
- **Quyền hạn chế:**
  - ✅ Vẫn đăng nhập được.
  - ✅ Vẫn xem phiếu điểm cá nhân.
  - ❌ KHÔNG được đăng ký lớp tín chỉ mới.
  - ❌ KHÔNG được hủy đăng ký.
  - ❌ KHÔNG được sửa thông tin cá nhân / đổi mật khẩu (tùy chọn).
- **Quyền hạn chế của giảng viên:**
  - ❌ KHÔNG được nhập điểm / sửa điểm cho SV thuộc diện này.
- **Áp dụng ở:** `SP_DANGNHAP_SV` (trả về cờ `QUAHAN`), `SP_DANGKY_LTC`, `SP_HUY_DANGKY`, `SP_NHAP_DIEM`.
```

### 5.3 Thêm mã lỗi `-20` vào bảng tổng hợp
| KETQUA | Ý nghĩa | SP |
|---|---|---|
| `-20` | **SV quá hạn** (KHOAHOC + 7 năm) | `SP_DANGKY_LTC`, `SP_HUY_DANGKY`, `SP_NHAP_DIEM` |

---

## 6. File cần thay đổi (tổng hợp)

| File | Loại thay đổi | Số dòng ước tính |
|---|---|---|
| `setup_login.sql` | **Sửa** | 6 SP: `SP_DANGNHAP_SV` (+8 dòng), `SP_DANGKY_LTC` (+20 dòng), `SP_NHAP_DIEM` (+20 dòng), `SP_HUY_DANGKY` (+20 dòng), +revert mốc ở 5 SP cũ (−0 dòng, chỉ đổi chuỗi) |
| `app.py` | **Sửa** | Lưu `quahan` vào session (+3 dòng); thêm `before_request` filter (+8 dòng) |
| `templates/phieu_diem.html` | **Sửa** | Banner cảnh báo (+6 dòng) |
| `templates/dashboard.html` | **Sửa** | Ẩn menu cho SV quá hạn (+5 dòng) |
| `CRITICAL.md` | **Sửa** | Sửa dòng công thức NK + thêm mục "SV quá hạn" + thêm mã `-20` |
| Database | ⛔ **Không đụng** | — |
| `changelogs/CHANGELOGS_VALIDATE_SP_2026.md` | **Sửa** | Ghi nhận việc revert mốc + bổ sung "quá hạn" |
| `changelogs/CHANGELOGS_NK_SV_QUAHAN_2026.md` | **Tạo mới** | Mục 7 dưới đây |

---

## 7. Kế hoạch xác minh (Test Cases)

### 7.1 Revert mốc đóng băng (4 test)
| # | Test | Kỳ vọng |
|---|---|---|
| 1 | `EXEC SP_THEM_LOPTINCHI @NIENKHOA='2024-2025', @HOCKY=1, ...` | KETQUA = `-10`, "Niên khóa < 2025-2026 đã bị đóng băng" |
| 2 | `EXEC SP_THEM_LOPTINCHI @NIENKHOA='2025-2026', @HOCKY=1, ...` | KETQUA = `1` (thành công) |
| 3 | `EXEC SP_THEM_LOPTINCHI @NIENKHOA='2026-2027', @HOCKY=1, ...` | KETQUA = `1` (thành công) |
| 4 | `EXEC SP_SUA_MONHOC @MAMH='M...', @SOTIET_LT=45` (môn đã dạy năm 2024) | KETQUA = `-10`, "không thể sửa" |

### 7.2 Sinh viên quá hạn (6 test)
| # | Test | Kỳ vọng |
|---|---|---|
| 5 | Login SV thuộc lớp `KHOAHOC='2018-2022'` (đã học 8 năm, quá hạn) | Trả về `QUAHAN = 1` |
| 6 | Login SV thuộc lớp `KHOAHOC='2021-2025'` (mới học 5 năm) | Trả về `QUAHAN = 0` |
| 7 | SV K2021 ĐK lớp LTC `NIENKHOA='2028-2029'` (vừa đúng 7 năm) | KETQUA = `1` |
| 8 | SV K2021 ĐK lớp LTC `NIENKHOA='2029-2030'` (vượt 8 năm) | KETQUA = `-20`, "quá hạn" |
| 9 | SV K2021 hủy lớp LTC `NIENKHOA='2029-2030'` | KETQUA = `-20`, "quá hạn" |
| 10 | GV nhập điểm cho SV K2021 ở lớp LTC `NIENKHOA='2029-2030'` | KETQUA = `-20`, "không thể nhập/sửa điểm" |

### 7.3 UI (manual test)
- [ ] Login SV quá hạn → thấy banner cảnh báo vàng trên phiếu điểm
- [ ] Menu "Đăng ký LTC", "Thông tin cá nhân" bị ẩn
- [ ] Truy cập trực tiếp `/dangky` → bị redirect về `/phieu_diem` + flash message
- [ ] Phiếu điểm hiển thị bình thường (không bị chặn)

---

## 8. Rủi ro & Mitigation

| Rủi ro | Mức độ | Cách giảm |
|---|---|---|
| Dùng `YEAR(GETDATE())` → khi sang năm 2027, mốc sẽ tự tăng thêm 1 năm. Có thể gây bất ngờ. | Trung bình | Bạn duyệt: dùng `GETDATE()` (tự động) hay hard-code `2026`? **Mình đề xuất `GETDATE()`** vì thực tế hệ thống chạy nhiều năm, không ai muốn update hàm mỗi năm. |
| Mã lỗi `-20` mới — cần check `app.py` đang parse những mã nào | Thấp | Mình sẽ rà lại `app.py` mục 6 để đảm bảo fallback (`!= 1`) sẽ hiển thị thông báo lỗi đúng |
| Logic `KHOAHOC + 7 năm` dùng `LEFT(KHOAHOC, 4)` — nếu DB có dữ liệu `KHOAHOC` không đúng format (vd: rỗng) thì `CAST(... AS INT)` trả NULL → không trigger quá hạn | Thấp | Có thể thêm `ISNULL(@KhoaHocNBD, 0)` để fallback, nhưng mình sẽ check dữ liệu thực tế trước |
| Frontend hiện không có cơ chế hiển thị banner từ session | Trung bình | Tận dụng pattern có sẵn trong các template (theo `app.py` có thể dùng `flash()`) |

---

## 9. Câu hỏi cần bạn phê duyệt

1. **Mốc đóng băng `'2025-2026'`** đã đúng chưa?
2. **Công thức `YEAR(GETDATE()) - năm bắt đầu KHOAHOC > 7`**: dùng `GETDATE()` tự động (hết 2026 sẽ tự lên 8) hay hard-code `2026`? **Mình đề xuất `GETDATE()`** cho linh hoạt.
3. **SV quá hạn có được xem "Thông tin cá nhân" không?** Hay chỉ xem phiếu điểm? Mình đang đề xuất: **chỉ xem phiếu điểm + đổi mật khẩu** (để tránh khóa tài khoản hoàn toàn). Đổi mật khẩu hay không là tùy bạn.
4. **"Vô hiệu hóa toàn bộ chức năng"** cụ thể là: ẩn menu + chặn route + banner cảnh báo? Hay chỉ cần 1 trong 3? Mình đề xuất **làm cả 3** (defense in depth).
5. **Mã lỗi `-20`** cho quá hạn — OK chứ?
6. **GV có cần bị ẩn menu "Nhập điểm" khi SV lớp đó thuộc diện quá hạn không?** Hay chỉ cần SP chặn? Mình đề xuất **chỉ cần SP chặn** (GV vẫn vào trang nhập điểm được, nhưng khi bấm Lưu thì SP sẽ báo lỗi "SV quá hạn" → tránh GV hoang mang vì sao menu biến mất).

Sau khi bạn duyệt, mình sẽ:
1. Cập nhật `setup_login.sql` (revert mốc + thêm 3 SP mới + 1 SP sửa)
2. Cập nhật `app.py` + 2 template
3. Cập nhật `CRITICAL.md`
4. Viết `changelogs/CHANGELOGS_NK_SV_QUAHAN_2026.md`
5. Cập nhật `changelogs/CHANGELOGS_VALIDATE_SP_2026.md` (ghi nhận việc revert mốc)
