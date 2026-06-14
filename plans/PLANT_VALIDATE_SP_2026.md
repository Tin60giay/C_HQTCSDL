# KẾ HOẠCH: TĂNG CƯỜNG RÀO CHẮN TẦNG BACKEND (SP)

> **Mục tiêu:** Đóng các "lỗ hổng" trong `setup_login.sql` — các ràng buộc trong `CRITICAL.md` hiện **chỉ DB / frontend giữ**, nếu gọi thẳng SP thì vẫn lọt. Kế hoạch này **KHÔNG sửa database**, chỉ sửa các SP hiện có trong `setup_login.sql`.

---

## 0. Tổng quan — Tình trạng hiện tại

Mình đã rà soát toàn bộ ~30 stored procedure trong `setup_login.sql` đối chiếu với `CRITICAL.md`. Kết quả:

- ✅ **Ràng buộc đã chặn tốt**: PK không trùng, FK hợp lệ, không xóa nếu còn ràng buộc con, 1 SV chỉ ĐK 1 lớp/môn, không hủy khi có điểm, chỉ SV `DANGHIHOC=0` mới login.
- ❌ **Ràng buộc CHƯA chặn ở SP** (4 lỗ hổng lớn):

| # | Lỗ hổng | Ràng buộc CRITICAL.md | SP bị ảnh hưởng | Mức độ |
|---|---|---|---|---|
| 1 | **Niên khóa đóng băng** — chỉ Flask chặn, SP không chặn | `NIENKHOA < 2025-2026` không được thêm/sửa/xóa | `SP_THEM/SUA/XOA/PHUCHOI_LOPTINCHI` | 🔴 Cao |
| 2 | **Điểm ngoài khoảng 0–10** | `DIEM_CC/GK/CK ∈ [0,10]`, GK/CK làm tròn 0.5 | `SP_NHAP_DIEM` | 🔴 Cao |
| 3 | **LTC field không hợp lệ** | `HOCKY ∈ [1,3]`, `NHOM ≥ 1`, `SOSVTOITHIEU > 0` | `SP_THEM/SUA_LOPTINCHI` | 🟡 Trung bình |
| 4 | **SOTIET_LT < 30** | Môn học LT phải ≥ 30 tiết (chuẩn PTIT) | `SP_THEM/SUA_MONHOC` | 🟡 Trung bình |

> **Nguyên tắc sửa:** Sửa **nội dung thân SP**, giữ nguyên `CREATE PROCEDURE` header, `GRANT EXECUTE`, output format `KETQUA/THONGBAO`. Có thể dùng cùng pattern `IF ... SELECT -N AS KETQUA, N'...' AS THONGBAO RETURN` đã có sẵn.

---

## 1. Sửa `SP_NHAP_DIEM` — Validate điểm 0..10 + bội số 0.5

### Vấn đề hiện tại
SP chỉ `UPDATE` thẳng, **không validate** khoảng điểm và bội số 0.5. Kẻ xấu gọi thẳng SP có thể nhập `DIEM_CK = 99` hoặc `DIEM_GK = 7.3` (không phải bội số 0.5).

### Code SP sửa lại
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

    -- 0. Kiểm tra sinh viên đã đăng ký lớp này
    IF NOT EXISTS (SELECT 1 FROM DANGKY WHERE MALTC = @MALTC AND MASV = @MASV)
    BEGIN
        SELECT -1 AS KETQUA, N'Sinh viên chưa đăng ký lớp tín chỉ này' AS THONGBAO
        RETURN
    END

    -- 1. Validate DIEM_CC (INT, 0..10)
    IF @DIEM_CC IS NOT NULL AND (@DIEM_CC < 0 OR @DIEM_CC > 10)
    BEGIN
        SELECT -2 AS KETQUA, N'Điểm chuyên cần phải nằm trong khoảng [0, 10]' AS THONGBAO
        RETURN
    END

    -- 2. Validate DIEM_GK (FLOAT, 0..10, bội số 0.5)
    IF @DIEM_GK IS NOT NULL AND (@DIEM_GK < 0 OR @DIEM_GK > 10)
    BEGIN
        SELECT -3 AS KETQUA, N'Điểm giữa kỳ phải nằm trong khoảng [0, 10]' AS THONGBAO
        RETURN
    END
    IF @DIEM_GK IS NOT NULL AND ABS((@DIEM_GK * 2) - ROUND(@DIEM_GK * 2, 0)) > 0.0001
    BEGIN
        SELECT -4 AS KETQUA, N'Điểm giữa kỳ phải là bội số của 0.5' AS THONGBAO
        RETURN
    END

    -- 3. Validate DIEM_CK (FLOAT, 0..10, bội số 0.5)
    IF @DIEM_CK IS NOT NULL AND (@DIEM_CK < 0 OR @DIEM_CK > 10)
    BEGIN
        SELECT -5 AS KETQUA, N'Điểm cuối kỳ phải nằm trong khoảng [0, 10]' AS THONGBAO
        RETURN
    END
    IF @DIEM_CK IS NOT NULL AND ABS((@DIEM_CK * 2) - ROUND(@DIEM_CK * 2, 0)) > 0.0001
    BEGIN
        SELECT -6 AS KETQUA, N'Điểm cuối kỳ phải là bội số của 0.5' AS THONGBAO
        RETURN
    END

    -- 4. UPDATE (giữ nguyên logic cũ)
    UPDATE DANGKY
    SET DIEM_CC = @DIEM_CC,
        DIEM_GK = @DIEM_GK,
        DIEM_CK = @DIEM_CK
    WHERE MALTC = @MALTC AND MASV = @MASV
    SELECT 1 AS KETQUA, N'Nhập điểm thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_NHAP_DIEM TO PUBLIC
GO
```

### Giải thích kỹ thuật
- **Bội số 0.5:** `@DIEM_GK * 2` rồi `ROUND(..., 0)`. Nếu kết quả lệch nhau > 0.0001 → không phải bội số. VD: 7.3 × 2 = 14.6, ROUND = 15 → lệch 0.4 (bị chặn). 7.5 × 2 = 15, ROUND = 15 → lệch 0 (OK).
- **Mã lỗi `-2, -3, -4, -5, -6`** để frontend phân biệt được loại lỗi cụ thể.
- **Không sửa DB**, không đổi tên SP, không đổi parameter list.

---

## 2. Sửa `SP_THEM_LOPTINCHI` — Validate field + đóng băng niên khóa

### Vấn đề hiện tại
SP chỉ check trùng `(NK,HK,MAMH,NHOM)`. Không check `HOCKY ∈ [1,3]`, `NHOM ≥ 1`, `SOSVTOITHIEU > 0`, không check `MAGV/MAMH/MAKHOA` tồn tại, không chặn nếu `NIENKHOA < 2025-2026`.

### Code SP sửa lại
```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_THEM_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_THEM_LOPTINCHI
GO
CREATE PROCEDURE SP_THEM_LOPTINCHI
    @NIENKHOA     NCHAR(9),
    @HOCKY        INT,
    @MAMH         NCHAR(10),
    @NHOM         INT,
    @MAGV         NCHAR(10),
    @MAKHOA       NCHAR(10),
    @SOSVTOITHIEU INT
AS
BEGIN
    SET NOCOUNT ON

    -- [MỚI] 0a. Chặn niên khóa đóng băng (theo CRITICAL.md)
    IF @NIENKHOA < '2025-2026'
    BEGIN
        SELECT -10 AS KETQUA, N'Niên khóa < 2025-2026 đã bị đóng băng, không thể thêm lớp tín chỉ' AS THONGBAO
        RETURN
    END

    -- [MỚI] 0b. Validate HOCKY
    IF @HOCKY < 1 OR @HOCKY > 3
    BEGIN
        SELECT -3 AS KETQUA, N'Học kỳ phải nằm trong khoảng [1, 3]' AS THONGBAO
        RETURN
    END

    -- [MỚI] 0c. Validate NHOM
    IF @NHOM < 1
    BEGIN
        SELECT -4 AS KETQUA, N'Nhóm phải >= 1' AS THONGBAO
        RETURN
    END

    -- [MỚI] 0d. Validate SOSVTOITHIEU
    IF @SOSVTOITHIEU <= 0
    BEGIN
        SELECT -5 AS KETQUA, N'Số SV tối thiểu phải > 0' AS THONGBAO
        RETURN
    END

    -- [MỚI] 0e. Kiểm tra FK tồn tại (báo lỗi thân thiện thay vì để DB ném exception)
    IF NOT EXISTS (SELECT 1 FROM MONHOC    WHERE MAMH  = @MAMH)
    BEGIN
        SELECT -6 AS KETQUA, N'Mã môn học không tồn tại' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM GIANGVIEN WHERE MAGV  = @MAGV)
    BEGIN
        SELECT -7 AS KETQUA, N'Mã giảng viên không tồn tại' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM KHOA      WHERE MAKHOA = @MAKHOA)
    BEGIN
        SELECT -8 AS KETQUA, N'Mã khoa không tồn tại' AS THONGBAO
        RETURN
    END

    -- 1. Kiểm tra trùng (giữ nguyên)
    IF EXISTS (
        SELECT 1 FROM LOPTINCHI
        WHERE NIENKHOA = @NIENKHOA AND HOCKY = @HOCKY
          AND MAMH = @MAMH AND NHOM = @NHOM AND (HUYLOP = 0 OR HUYLOP IS NULL)
    )
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ đã tồn tại (cùng niên khóa, học kỳ, môn, nhóm)' AS THONGBAO
        RETURN
    END

    -- 2. Mở lại lớp đã hủy (giữ nguyên)
    IF EXISTS (
        SELECT 1 FROM LOPTINCHI
        WHERE NIENKHOA = @NIENKHOA AND HOCKY = @HOCKY
          AND MAMH = @MAMH AND NHOM = @NHOM AND HUYLOP = 1
    )
    BEGIN
        UPDATE LOPTINCHI
        SET HUYLOP = 0, MAGV = @MAGV, MAKHOA = @MAKHOA, SOSVTOITHIEU = @SOSVTOITHIEU
        WHERE NIENKHOA = @NIENKHOA AND HOCKY = @HOCKY
          AND MAMH = @MAMH AND NHOM = @NHOM
        DECLARE @UpdatedID INT
        SELECT @UpdatedID = MALTC FROM LOPTINCHI
        WHERE NIENKHOA = @NIENKHOA AND HOCKY = @HOCKY AND MAMH = @MAMH AND NHOM = @NHOM
        SELECT @UpdatedID AS KETQUA, N'Mở lại lớp tín chỉ đã hủy thành công' AS THONGBAO
        RETURN
    END

    -- 3. INSERT (giữ nguyên)
    INSERT INTO LOPTINCHI (NIENKHOA, HOCKY, MAMH, NHOM, MAGV, MAKHOA, SOSVTOITHIEU, HUYLOP)
    VALUES (@NIENKHOA, @HOCKY, @MAMH, @NHOM, @MAGV, @MAKHOA, @SOSVTOITHIEU, 0)
    SELECT 1 AS KETQUA, N'Mở lớp tín chỉ thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_THEM_LOPTINCHI TO PUBLIC
GO
```

### Giải thích
- **Mốc đóng băng `'2025-2026'`** khớp với cấu hình `is_frozen` trong `app.py` (dòng 152 của README).
- **Mã lỗi `-10` cho niên khóa cũ** để frontend dễ phân biệt với lỗi khác.
- Mã lỗi `-1` (trùng) giữ nguyên để không phá vỡ code Flask đang check.

---

## 3. Sửa `SP_SUA_LOPTINCHI` — Validate field + đóng băng

### Code SP sửa lại
```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_SUA_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_SUA_LOPTINCHI
GO
CREATE PROCEDURE SP_SUA_LOPTINCHI
    @MALTC        INT,
    @NIENKHOA     NCHAR(9),
    @HOCKY        INT,
    @MAMH         NCHAR(10),
    @NHOM         INT,
    @MAGV         NCHAR(10),
    @MAKHOA       NCHAR(10),
    @SOSVTOITHIEU INT
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC)
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ không tồn tại' AS THONGBAO
        RETURN
    END

    -- [MỚI] Chặn nếu lớp đang sửa thuộc niên khóa đã đóng băng
    DECLARE @OldNK NCHAR(9)
    SELECT @OldNK = NIENKHOA FROM LOPTINCHI WHERE MALTC = @MALTC
    IF @OldNK < '2025-2026'
    BEGIN
        SELECT -10 AS KETQUA, N'Lớp thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể sửa' AS THONGBAO
        RETURN
    END

    -- [MỚI] Validate các field giống SP_THEM
    IF @HOCKY < 1 OR @HOCKY > 3
    BEGIN SELECT -3 AS KETQUA, N'Học kỳ phải nằm trong khoảng [1, 3]' AS THONGBAO RETURN END
    IF @NHOM < 1
    BEGIN SELECT -4 AS KETQUA, N'Nhóm phải >= 1' AS THONGBAO RETURN END
    IF @SOSVTOITHIEU <= 0
    BEGIN SELECT -5 AS KETQUA, N'Số SV tối thiểu phải > 0' AS THONGBAO RETURN END
    IF NOT EXISTS (SELECT 1 FROM MONHOC    WHERE MAMH  = @MAMH)
    BEGIN SELECT -6 AS KETQUA, N'Mã môn học không tồn tại' AS THONGBAO RETURN END
    IF NOT EXISTS (SELECT 1 FROM GIANGVIEN WHERE MAGV  = @MAGV)
    BEGIN SELECT -7 AS KETQUA, N'Mã giảng viên không tồn tại' AS THONGBAO RETURN END
    IF NOT EXISTS (SELECT 1 FROM KHOA      WHERE MAKHOA = @MAKHOA)
    BEGIN SELECT -8 AS KETQUA, N'Mã khoa không tồn tại' AS THONGBAO RETURN END

    UPDATE LOPTINCHI
    SET NIENKHOA = @NIENKHOA, HOCKY = @HOCKY,
        MAMH = @MAMH, NHOM = @NHOM,
        MAGV = @MAGV, MAKHOA = @MAKHOA,
        SOSVTOITHIEU = @SOSVTOITHIEU
    WHERE MALTC = @MALTC
    SELECT 1 AS KETQUA, N'Cập nhật lớp tín chỉ thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_SUA_LOPTINCHI TO PUBLIC
GO
```

> **Lưu ý quan trọng:** Mình dùng `@OldNK` (niên khóa **cũ** của lớp) để so sánh, không dùng `@NIENKHOA` mới truyền vào. Nếu dùng `@NIENKHOA` thì kẻ xấu có thể "né" bằng cách truyền NK mới là `2025-2026` cho một lớp cũ.

---

## 4. Sửa `SP_XOA_LOPTINCHI` & `SP_PHUCHOI_LOPTINCHI` — Chặn niên khóa

### Vấn đề
Hiện tại cho phép hủy/phục hồi **bất kỳ** lớp tín chỉ nào. Cần chặn thao tác trên niên khóa đã đóng băng.

### `SP_XOA_LOPTINCHI` sửa lại
```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XOA_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_XOA_LOPTINCHI
GO
CREATE PROCEDURE SP_XOA_LOPTINCHI
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC)
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ không tồn tại' AS THONGBAO
        RETURN
    END

    -- [MỚI] Chặn xóa lớp thuộc niên khóa đã đóng băng
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC AND NIENKHOA < '2025-2026')
    BEGIN
        SELECT -10 AS KETQUA, N'Lớp thuộc niên khóa < 2025-2026 đã bị đóng băng' AS THONGBAO
        RETURN
    END

    UPDATE LOPTINCHI SET HUYLOP = 1 WHERE MALTC = @MALTC
    SELECT 1 AS KETQUA, N'Hủy lớp tín chỉ thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_XOA_LOPTINCHI TO PUBLIC
GO
```

### `SP_PHUCHOI_LOPTINCHI` sửa lại
```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_PHUCHOI_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_PHUCHOI_LOPTINCHI
GO
CREATE PROCEDURE SP_PHUCHOI_LOPTINCHI
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC)
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ không tồn tại' AS THONGBAO
        RETURN
    END

    -- [MỚI] Chặn phục hồi lớp thuộc niên khóa đã đóng băng
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC AND NIENKHOA < '2025-2026')
    BEGIN
        SELECT -10 AS KETQUA, N'Lớp thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể phục hồi' AS THONGBAO
        RETURN
    END

    UPDATE LOPTINCHI SET HUYLOP = 0 WHERE MALTC = @MALTC
    SELECT 1 AS KETQUA, N'Phục hồi lớp tín chỉ thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_PHUCHOI_LOPTINCHI TO PUBLIC
GO
```

---

## 5. Sửa `SP_THEM_MONHOC` & `SP_SUA_MONHOC` — Validate SOTIET_LT

### Vấn đề
DB không có CHECK constraint, SP không validate. Hiện frontend (`validateMonHocLT_TH` trong `history.js`) đang chặn nhưng nếu gọi thẳng SP thì vẫn insert được môn có 0 tiết LT.

### `SP_THEM_MONHOC` sửa lại
```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_THEM_MONHOC' AND type = 'P')
    DROP PROCEDURE SP_THEM_MONHOC
GO
CREATE PROCEDURE SP_THEM_MONHOC
    @MAMH       NCHAR(10),
    @TENMH      NVARCHAR(50),
    @SOTIET_LT  INT,
    @SOTIET_TH  INT
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM MONHOC WHERE MAMH = @MAMH)
    BEGIN
        SELECT -1 AS KETQUA, N'Mã môn học đã tồn tại' AS THONGBAO
        RETURN
    END

    -- [MỚI] Validate số tiết
    IF @SOTIET_LT < 30
    BEGIN
        SELECT -2 AS KETQUA, N'Số tiết lý thuyết phải >= 30 (chuẩn PTIT)' AS THONGBAO
        RETURN
    END
    IF @SOTIET_TH < 0
    BEGIN
        SELECT -3 AS KETQUA, N'Số tiết thực hành phải >= 0' AS THONGBAO
        RETURN
    END

    INSERT INTO MONHOC (MAMH, TENMH, SOTIET_LT, SOTIET_TH)
    VALUES (@MAMH, @TENMH, @SOTIET_LT, @SOTIET_TH)
    SELECT 1 AS KETQUA, N'Thêm môn học thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_THEM_MONHOC TO PUBLIC
GO
```

### `SP_SUA_MONHOC` sửa lại
```sql
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_SUA_MONHOC' AND type = 'P')
    DROP PROCEDURE SP_SUA_MONHOC
GO
CREATE PROCEDURE SP_SUA_MONHOC
    @MAMH       NCHAR(10),
    @TENMH      NVARCHAR(50),
    @SOTIET_LT  INT,
    @SOTIET_TH  INT
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM MONHOC WHERE MAMH = @MAMH)
    BEGIN
        SELECT -1 AS KETQUA, N'Môn học không tồn tại' AS THONGBAO
        RETURN
    END

    -- [MỚI] Validate số tiết
    IF @SOTIET_LT < 30
    BEGIN
        SELECT -2 AS KETQUA, N'Số tiết lý thuyết phải >= 30 (chuẩn PTIT)' AS THONGBAO
        RETURN
    END
    IF @SOTIET_TH < 0
    BEGIN
        SELECT -3 AS KETQUA, N'Số tiết thực hành phải >= 0' AS THONGBAO
        RETURN
    END

    -- [MỚI] Nếu môn đã được dùng để mở lớp trong quá khứ → đóng băng không cho sửa tên/số tiết
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MAMH = @MAMH AND NIENKHOA < '2025-2026')
    BEGIN
        SELECT -10 AS KETQUA, N'Môn học đã được dạy trong niên khóa < 2025-2026, không thể sửa' AS THONGBAO
        RETURN
    END

    UPDATE MONHOC
    SET TENMH = @TENMH, SOTIET_LT = @SOTIET_LT, SOTIET_TH = @SOTIET_TH
    WHERE MAMH = @MAMH
    SELECT 1 AS KETQUA, N'Cập nhật môn học thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_SUA_MONHOC TO PUBLIC
GO
```

> **Câu hỏi cần bạn duyệt:** Có chặn luôn `SP_SUA_MONHOC` khi môn đã được dạy trong quá khứ không? Theo tinh thần CRITICAL.md (đóng băng lịch sử), mình đề xuất **CÓ chặn** — nếu cần đổi tên/số tiết, hãy tạo mã môn mới.

---

## 6. File cần thay đổi (tổng hợp)

| File | Loại thay đổi | Số SP bị ảnh hưởng |
|---|---|---|
| `setup_login.sql` | **Sửa** (không xóa, không thêm file mới) | 6 SP: `SP_NHAP_DIEM`, `SP_THEM_LOPTINCHI`, `SP_SUA_LOPTINCHI`, `SP_XOA_LOPTINCHI`, `SP_PHUCHOI_LOPTINCHI`, `SP_THEM_MONHOC`, `SP_SUA_MONHOC` |
| Database | ❌ **Không đụng** | — |
| `app.py` | ❌ **Không đụng** (giữ nguyên logic `is_frozen` hiện có) | — |
| Frontend | ❌ **Không đụng** | — |

---

## 7. Kế hoạch xác minh (Test Cases)

Sau khi áp dụng, mình sẽ verify bằng cách gọi thẳng SP trong SSMS:

| # | Test case | Kỳ vọng |
|---|---|---|
| 1 | `EXEC SP_NHAP_DIEM @MALTC=1, @MASV='N15...', @DIEM_CK=99` | KETQUA = `-5`, thông báo "Điểm cuối kỳ phải nằm trong khoảng [0, 10]" |
| 2 | `EXEC SP_NHAP_DIEM @MALTC=1, @MASV='N15...', @DIEM_GK=7.3` | KETQUA = `-4`, thông báo "phải là bội số của 0.5" |
| 3 | `EXEC SP_THEM_LOPTINCHI @NIENKHOA='2020-2021', @HOCKY=1, ...` | KETQUA = `-10`, thông báo "Niên khóa < 2025-2026 đã bị đóng băng" |
| 4 | `EXEC SP_THEM_LOPTINCHI @NIENKHOA='2025-2026', @HOCKY=5, ...` | KETQUA = `-3`, thông báo "Học kỳ phải nằm trong khoảng [1, 3]" |
| 5 | `EXEC SP_SUA_LOPTINCHI @MALTC=5, @NIENKHOA='2025-2026', @HOCKY=1, ...` (lớp 5 thuộc NK 2020) | KETQUA = `-10`, thông báo "Lớp thuộc niên khóa < 2025-2026 đã bị đóng băng" |
| 6 | `EXEC SP_XOA_LOPTINCHI @MALTC=3` (lớp 3 thuộc NK 2024) | KETQUA = `-10`, thông báo "đã bị đóng băng" |
| 7 | `EXEC SP_THEM_MONHOC @MAMH='M001', @SOTIET_LT=20` | KETQUA = `-2`, thông báo "Số tiết lý thuyết phải >= 30" |
| 8 | `EXEC SP_SUA_MONHOC @MAMH='M001', @SOTIET_LT=45` (môn đã từng dạy năm 2024) | KETQUA = `-10`, thông báo "không thể sửa" |
| 9 | Test happy path: thêm lớp NK=2025-2026, HK=1, NHOM=1, SOSV=10 | KETQUA = `1`, thông báo "Mở lớp tín chỉ thành công" |

---

## 8. Rủi ro & Mitigation

| Rủi ro | Mức độ | Cách giảm |
|---|---|---|
| Số mã lỗi mới (`-2..-10`) có thể xung đột với code Flask đang parse | Thấp | Mình sẽ rà lại `app.py` để xem đang check mã lỗi nào, đảm bảo mã mới không trùng |
| Chặn `SP_SUA_MONHOC` cho môn đã dạy → nếu PGV thật sự cần sửa typo thì không được | Trung bình | Bạn cần duyệt: nếu cho phép, bỏ check `LOPTINCHI` trong `SP_SUA_MONHOC` |
| Performance: thêm query `EXISTS LOPTINCHI` vào mỗi thao tác LTC | Không đáng kể | Bảng LTC thường < 1000 dòng, query < 1ms |

---

## 9. Câu hỏi cần bạn phê duyệt

1. **Mốc đóng băng** dùng `NIENKHOA < '2025-2026'` — khớp với `app.py` — **OK chứ?**
2. **`SP_SUA_MONHOC` có chặn luôn khi môn đã dạy trong quá khứ không?** (Mục 5 đề xuất CÓ chặn)
3. **Mã lỗi mới** (`-2, -3, -4, -5, -6, -10`) — bạn muốn đánh số thế nào? Mặc định mình dùng số âm để không trùng với `KETQUA=1` (thành công) và `KETQUA=MALTC` (id trả về).
4. **Phạm vi sửa:** 6 SP trong mục 6 — có muốn bổ sung thêm SP nào khác không? (Mình thấy các SP CRUD còn lại như `SP_THEM/SUA_LOP`, `SP_THEM/SUA_SV` đã ổn vì DB tự chặn PK/FK/UNIQUE.)

Sau khi bạn duyệt, mình sẽ cập nhật `setup_login.sql` và viết `CHANGELOGS_VALIDATE_SP_2026.md`.
