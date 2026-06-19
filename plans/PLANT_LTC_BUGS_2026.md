# PLANT_LTC_BUGS_2026 — Kế hoạch sửa 5 lỗi mở lớp tín chỉ & lọc đồng bộ

> Ngày: 2026-06-18  |  Phạm vi: **không sửa DB gốc**, chỉ sửa/thêm SP trong `setup_login.sql`,
> sửa `app.py` (route + filter mặc định), sửa các file HTML trong `templates/`.
> Lưu ý: tất cả các thay đổi về SP phải nằm trong `setup_login.sql` (rule 6).

---

## 1. Tổng quan các lỗi cần xử lý

| # | Lỗi | File chính | Hướng xử lý |
|---|-----|------------|-------------|
| 1 | Trường `readOnly` (Mã GV, MAMH, MAGV...) không bị làm mờ | `*.html` | Dùng `toggleFormLock(true, …)` cho **mọi** trường readOnly khi đang chọn dòng để sửa. Áp dụng đồng bộ cho 6 trang. |
| 2 | Chức năng lọc LTC chưa đồng bộ + không tự chọn NK mới nhất | `loptinchi.html`, `app.py` | Lấy ý tưởng từ `lop.html` (filter local + query string). Khi mở `/loptinchi` mặc định chọn NK lớn nhất có LTC (chưa hủy). |
| 3 | Trong sửa LTC: không khóa cứng HOCKY / MAMH / NIENKHOA / MAKHOA | `loptinchi.html` | Khi `chonDong` ở chế độ edit, gọi `toggleFormLock(true, ['fNK','fHK','fMAMH','fMAKHOA_F'])`. Khi tạo mới → mở lại. |
| 4 | SV khoa nào chỉ thấy LTC của khoa đó | `setup_login.sql` (`SP_GET_LOPTINCHI_DANGKY`), `app.py` | SP lấy thêm `@MAKHOA_SV` filter, truyền từ session `tenkhoa` / query `SP_GET_THONGTIN_SV`. |
| 5 | SV chỉ thấy LTC từ `KHOAHOC` của mình (quá hạn 7 năm thì giới hạn tới NK = KHOAHOC+7) | `setup_login.sql`, `app.py` | Trong SP lọc: chỉ trả về LTC có `NIENKHOA >= KHOAHOC_SV`. Nếu quá hạn thì lấy `MAX(NIENKHOA) <= KHOAHOC_SV + 7`. Nếu không quá hạn thì giới hạn tới `KHOAHOC_SV + 7` (sinh viên còn hạn cũng chỉ xem được đến hạn 7 năm, tương tự `phieu_diem`). |

---

## 2. Thiết kế Stored Procedure mới / sửa

### 2.1 Sửa `SP_GET_LOPTINCHI_DANGKY` (CHỈ SỬA NỘI BỘ — không phá rule)
Thêm:
- Lấy `KHOAHOC` của SV từ `SINHVIEN → LOP`.
- Lấy năm bắt đầu `KHOAHOC` (`@NamBD`).
- Tính `QUAHAN = (YEAR(GETDATE()) - @NamBD) > 7`.
- Lấy `MAKHOA` của SV từ `LOP.MAKHOA`.
- Lọc:
  - `LTC.MAKHOA = @MAKHOA_SV` (chỉ thấy LTC thuộc khoa mình)
  - `LTC.NIENKHOA >= @NK_MIN` (NK_MIN = @NamBD)
  - Nếu quá hạn: `LTC.NIENKHOA <= @NamBD+7`; ngược lại cũng giới hạn tới `+7` (sinh viên còn hạn tối đa nhìn tới hạn cuối).
- Trả thêm cột `QUAHAN` (BIT) để FE dùng hiển thị banner nếu cần.

```sql
ALTER PROCEDURE SP_GET_LOPTINCHI_DANGKY
    @MASV NCHAR(10),
    @NIENKHOA NCHAR(9),
    @HOCKY INT
AS
BEGIN
    SET NOCOUNT ON
    DECLARE @NamBD INT
    DECLARE @MAKHOA_SV NCHAR(10)
    DECLARE @QUAHAN BIT = 0

    SELECT @NamBD = CAST(LEFT(L.KHOAHOC, 4) AS INT), @MAKHOA_SV = L.MAKHOA
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    IF @NamBD IS NOT NULL AND (YEAR(GETDATE()) - @NamBD) > 7
        SET @QUAHAN = 1

    ;WITH LTC_LOC AS (
        SELECT LTC.*,
               CASE WHEN LTC.NIENKHOA < CONVERT(NCHAR(9), CONCAT(@NamBD, '-', @NamBD+1))
                    OR LTC.NIENKHOA > CONVERT(NCHAR(9), CONCAT(@NamBD+7, '-', @NamBD+8))
                    THEN 0 ELSE 1 END AS IN_RANGE
        FROM LOPTINCHI LTC
        WHERE LTC.NIENKHOA = @NIENKHOA AND LTC.HOCKY = @HOCKY
          AND LTC.HUYLOP = 0
          AND LTC.MAKHOA = @MAKHOA_SV
    )
    SELECT LTC.MALTC, LTC.MAMH, MH.TENMH, LTC.NHOM,
           RTRIM(GV.HO)+' '+RTRIM(GV.TEN) AS TENGV,
           K.TENKHOA, LTC.SOSVTOITHIEU,
           COUNT(DK2.MASV) AS SOSV_DANGKY,
           CASE WHEN DK_SV.MASV IS NOT NULL THEN 1 ELSE 0 END AS DA_DANGKY,
           @QUAHAN AS QUAHAN,
           0 AS IS_FROZEN
    FROM LTC_LOC LTC
    INNER JOIN MONHOC MH ON LTC.MAMH = MH.MAMH
    INNER JOIN GIANGVIEN GV ON LTC.MAGV = GV.MAGV
    INNER JOIN KHOA K ON LTC.MAKHOA = K.MAKHOA
    LEFT JOIN DANGKY DK2 ON LTC.MALTC = DK2.MALTC
        AND (DK2.HUYDANGKY = 0 OR DK2.HUYDANGKY IS NULL)
    LEFT JOIN DANGKY DK_SV ON LTC.MALTC = DK_SV.MALTC
        AND DK_SV.MASV = @MASV
        AND (DK_SV.HUYDANGKY = 0 OR DK_SV.HUYDANGKY IS NULL)
    WHERE LTC.IN_RANGE = 1
    GROUP BY LTC.MALTC, LTC.MAMH, MH.TENMH, LTC.NHOM, GV.HO, GV.TEN, K.TENKHOA,
             LTC.SOSVTOITHIEU, DK_SV.MASV
    ORDER BY MH.TENMH, LTC.NHOM
END
```

**Lưu ý rule 6**: Theo `Critical.md` rule gốc, mọi SP phải nằm trong `setup_login.sql`. Theo phê duyệt của user, **được phép sửa trực tiếp các SP cũ** (không cần tạo V2) vì:
- `SP_GET_LOPTINCHI_DANGKY`: không có nơi nào khác gọi → sửa thẳng.
- `SP_XEM_PHIEU_DIEM`: cũng chỉ app.py gọi → sửa thẳng.

### 2.2 Sửa `SP_GETALL_LOPTINCHI` (PGV)
KHÔNG cần sửa. Chỉ cần app.py default NK = MAX(NIENKHOA) trong LOPTINCHI khi user mở `/loptinchi` không truyền query.

### 2.2 Thêm `SP_GET_NIENKHOA_SV`
Lấy danh sách niên khóa thực tế mà SV được phép thấy (dựa trên KHOAHOC và quá hạn).

```sql
CREATE PROCEDURE SP_GET_NIENKHOA_SV
    @MASV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    DECLARE @NamBD INT
    DECLARE @MAKHOA_SV NCHAR(10)
    DECLARE @QUAHAN BIT = 0

    SELECT @NamBD = CAST(LEFT(L.KHOAHOC, 4) AS INT), @MAKHOA_SV = L.MAKHOA
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    IF @NamBD IS NOT NULL AND (YEAR(GETDATE()) - @NamBD) > 7
        SET @QUAHAN = 1

    DECLARE @NamKT INT = @NamBD + 7

    SELECT DISTINCT RTRIM(LTC.NIENKHOA) AS NIENKHOA
    FROM LOPTINCHI LTC
    WHERE LTC.HUYLOP = 0
      AND LTC.MAKHOA = @MAKHOA_SV
      AND CAST(LEFT(LTC.NIENKHOA, 4) AS INT) BETWEEN @NamBD AND @NamKT
    ORDER BY NIENKHOA
END
GRANT EXECUTE ON SP_GET_NIENKHOA_SV TO [sv]
```

### 2.3 Sửa `SP_GET_LOPTINCHI_DANGKY` (CHỈ sửa nội bộ — user cho phép)
- Lấy `KHOAHOC` của SV từ `SINHVIEN → LOP`.
- Lấy năm bắt đầu `KHOAHOC` (`@NamBD`).
- Tính `QUAHAN = (YEAR(GETDATE()) - @NamBD) > 7`.
- Lấy `MAKHOA` của SV từ `LOP.MAKHOA`.
- Lọc:
  - `LTC.MAKHOA = @MAKHOA_SV` (chỉ thấy LTC thuộc khoa mình)
  - `CAST(LEFT(LTC.NIENKHOA,4) AS INT) BETWEEN @NamBD AND @NamBD+7` (chỉ thấy LTC trong phạm vi KHOAHOC→KHOAHOC+7).

### 2.5 Thêm `SP_GET_DEFAULT_NK_LTC`
Trả về niên khóa mới nhất hiện có trong LOPTINCHI (chưa hủy). Dùng để default filter trang PGV.

```sql
CREATE PROCEDURE SP_GET_DEFAULT_NK_LTC
AS
BEGIN
    SET NOCOUNT ON
    SELECT TOP 1 RTRIM(NIENKHOA) AS NIENKHOA
    FROM LOPTINCHI
    WHERE HUYLOP = 0
    ORDER BY NIENKHOA DESC
END
GRANT EXECUTE ON SP_GET_DEFAULT_NK_LTC TO PUBLIC
```

---

## 3. Thiết kế `app.py`

### 3.1 Route `/loptinchi`
- Nếu `request.args.get('nienkhoa')` rỗng → gọi `SP_GET_DEFAULT_NK_LTC` để lấy NK mới nhất, set mặc định.
- Truyền `nienkhoa` xuống template để filter preselect.

### 3.2 Route `/dangky`
- Đổi `get_nienkhoa_co_lop()` (lấy tất cả) → `SP_GET_NIENKHOA_SV(session['username'])` (lấy NK thuộc phạm vi của SV).

### 3.3 Route `/dangky/loc`
- Vẫn gọi `SP_GET_LOPTINCHI_DANGKY` (đã sửa để filter khoa + quá hạn).

### 3.4 Route `/phieu_diem`
- Gọi `SP_XEM_PHIEU_DIEM` (đã sửa để filter NK + cờ quá hạn).

---

## 4. Thiết kế HTML

### 4.1. Issue 1: Làm mờ trường readOnly
Áp dụng cho tất cả 6 trang: `khoa.html`, `lop.html`, `giangvien.html`, `monhoc.html`, `sinhvien.html`, `loptinchi.html`.

**Nguyên tắc**: bất cứ khi nào `chonDong` set một trường thành `readOnly = true` (khóa chính) thì đồng thời gọi `toggleFormLock(true, [id])` cho trường đó. CSS từ `history.js` đã có sẵn style cho `readOnly` mờ — chỉ cần thêm class `frozen-readonly` hoặc style trực tiếp.

**Cách làm cụ thể**:
- Trong mỗi `chonDong`, sau khi set `fM.readOnly = true`, gọi thêm:
  ```js
  fM.style.backgroundColor = 'rgba(39, 39, 42, 0.4)';
  fM.style.color = '#52525b';
  fM.style.borderColor = isFrozen ? '#fca5a5' : '#52525b';
  fM.style.cursor = 'not-allowed';
  ```
- Tạo helper `applyReadonlyStyle(el, isFrozen)` trong `history.js` để đồng bộ.

### 4.2. Issue 2: Lọc đồng bộ
- `loptinchi.html`: hiện đang dùng `data-attributes` để filter local (đã có `data-nk`… KHÔNG, đang **thiếu** `data-nk`! Đây là bug). Sửa: thêm `data-nk`, `data-hk`, `data-khoa`, `data-text` vào từng `<tr>` của `loptinchi.html`. Filter giống `lop.html`.
- Thêm nút "Xem tất cả" để reset filter, mặc định chọn NK mới nhất (do server trả về).
- Lấy ý tưởng từ `lop.html`: filter bar gồm Khoa + Tìm mã/tên (chỉ cần 2 filter đơn giản giống `lop.html`).

### 4.3. Issue 3: Khóa NK/HK/MAMH/KHOA khi edit LTC
Trong `loptinchi.html`, sửa `chonDong`:
- Khi `isFrozen` thì khóa tất cả (giữ nguyên).
- Khi KHÔNG frozen (đang edit) → vẫn phải khóa `fNK, fHK, fMAMH, fMAKHOA_F` (vì rule 3).
- Chỉ cho phép sửa `fNHOM, fMAGV, fSOSV`.

```js
function chonDong(row, maltc, nk, hk, mamh, nhom, magv, makhoa, minsv, isFrozen) {
    // ...
    if (isFrozen) {
        toggleFormLock(true, ['fNK','fHK','fMAMH','fNHOM','fMAGV','fMAKHOA_F','fSOSV']);
        updateActionButtons('error');
    } else {
        // Khi edit: khóa 4 trường định danh, chỉ cho phép sửa NHOM/MAGV/SOSV
        toggleFormLock(true, ['fNK','fHK','fMAMH','fMAKHOA_F']);
        toggleFormLock(false, ['fNHOM','fMAGV','fSOSV']);
        updateActionButtons('editing');
    }
    // ...
}
```

Khi `xoaTrang()` → `toggleFormLock(false, [...])` tất cả.

### 4.4. Issue 4: SV chỉ thấy lớp khoa mình
- Trong `app.py` route `/dangky/loc`: gọi `SP_GET_LOPTINCHI_DANGKY` (đã sửa filter theo khoa).

### 4.5. Issue 5: SV chỉ thấy LTC mở từ học kỳ của họ
- Cũng trong `SP_GET_LOPTINCHI_DANGKY` (đã sửa): thêm điều kiện `NIENKHOA` nằm trong `[KHOAHOC, KHOAHOC+7]`.
- Trong `app.py` route `/dangky`: gọi `SP_GET_NIENKHOA_SV(masv)` thay cho `get_nienkhoa_co_lop()`.
- Trong `app.py` route `/phieu_diem`: gọi `SP_XEM_PHIEU_DIEM` (đã sửa filter).

---

## 5. File cần sửa / tạo

| File | Hành động | Lý do |
|------|-----------|-------|
| `setup_login.sql` | Sửa: thêm 2 SP mới (`SP_GET_NIENKHOA_SV`, `SP_GET_DEFAULT_NK_LTC`); sửa `SP_GET_LOPTINCHI_DANGKY`, `SP_XEM_PHIEU_DIEM` | Rule 6 - mọi SP mới phải nằm trong file này. User cho phép sửa SP cũ. |
| `app.py` | Sửa: route `/loptinchi`, `/dangky`, `/dangky/loc`, `/phieu_diem` | Default NK + dùng SP mới |
| `static/history.js` | Sửa: thêm helper `applyReadonlyStyle` | Đồng bộ CSS cho readOnly |
| `templates/loptinchi.html` | Sửa: thêm data-attributes cho filter, khóa NK/HK/MAMH/KHOA khi edit | Issue 1, 2, 3 |
| `templates/lop.html` | Sửa: helper readonly | Issue 1 |
| `templates/khoa.html` | Sửa: helper readonly | Issue 1 |
| `templates/giangvien.html` | Sửa: helper readonly | Issue 1 |
| `templates/monhoc.html` | Sửa: helper readonly | Issue 1 |
| `templates/sinhvien.html` | Sửa: helper readonly | Issue 1 |
| `plans/PLANT_LTC_BUGS_2026.md` | Tạo | Rule 3 |
| `changelogs/CHANGELOGS_LTC_BUGS_2026.md` | Tạo | Rule 4 |
| `hdsd/HDSD_LTC_BUGS_2026.md` | Tạo | Rule 5 |

---

## 6. Thứ tự thực hiện (TODO)

1. Sửa `setup_login.sql` (thêm 4 SP mới, KHÔNG sửa SP cũ).
2. Sửa `app.py` (4 route).
3. Sửa `static/history.js` (thêm helper readonly style).
4. Sửa 6 file HTML.
5. Ghi CHANGELOG + HDSD.

---

## 7. Rủi ro & phương án dự phòng

- **Rủi ro 1**: SV đăng nhập khi KHOAHOC là NULL → SP sẽ trả về rỗng (an toàn).
- **Rủi ro 2**: Filter NK mới nhất trả về chuỗi 'YYYY-YYYY' có space → dùng `RTRIM` trong SP và `strip()` trong app.py.
- **Rủi ro 3**: `SP_GET_LOPTINCHI_DANGKY` cũ đã có trong plan trước — chỉ sửa nội bộ, không đổi chữ ký để tương thích ngược.
