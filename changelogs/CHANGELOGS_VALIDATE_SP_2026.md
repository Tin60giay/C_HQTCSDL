# CHANGELOG: Tăng cường rào chắn tầng Backend (VALIDATE_SP_2026)

> **Ngày thực hiện:** 2026-06-14
> **Kế hoạch:** `plans/PLANT_VALIDATE_SP_2026.md` (đã duyệt, **đã sửa mốc — xem ghi chú bên dưới**)
> **Kế hoạch bổ sung:** `plans/PLANT_NK_SV_QUAHAN_2026.md` (đã duyệt, revert mốc + thêm quy tắc quá hạn)
> **Phạm vi:** Sửa 7 Stored Procedure trong `setup_login.sql`. **Không thay đổi database (bảng, cột, dữ liệu).**
>
> **⚠️ CẬP NHẬT 2026-06-14 — REVERT MỐC:** Sau khi bạn xác nhận "đóng băng là đóng băng từ 2025 về trước", mình đã revert toàn bộ 11 chỗ `'2020-2021'` → `'2025-2026'`. Mọi validate về mốc vẫn giữ nguyên logic, chỉ thay đổi giá trị mốc. Đồng thời bổ sung 4 SP với logic "sinh viên quá hạn" — xem `changelogs/CHANGELOGS_NK_SV_QUAHAN_2026.md`.

---

## 1. Bối cảnh

Sau khi rà soát toàn bộ ~30 SP trong `setup_login.sql` đối chiếu với `CRITICAL.md`, phát hiện 4 lỗ hổng lớn ở tầng backend:

1. Không có SP nào chặn thao tác trên niên khóa đã đóng băng (chỉ Flask `is_frozen` chặn).
2. `SP_NHAP_DIEM` không validate khoảng điểm `[0, 10]` và bội số 0.5.
3. `SP_THEM_LOPTINCHI` / `SP_SUA_LOPTINCHI` không validate `HOCKY`, `NHOM`, `SOSVTOITHIEU`, FK.
4. `SP_THEM_MONHOC` / `SP_SUA_MONHOC` không validate `SOTIET_LT >= 30` (chuẩn PTIT) và không chặn sửa môn đã dạy trong quá khứ.

Nếu kẻ xấu bypass Flask và gọi thẳng SP, các ràng buộc trên vẫn lọt → bảng điểm, lịch sử giảng dạy có thể bị phá vỡ.

---

## 2. Thay đổi chi tiết

### 2.1 Mốc niên khóa đóng băng
- **Trước:** Không có.
- **Sau:** `NIENKHOA < '2020-2021'` (công thức: `2026 - 7 + 1 = 2020`).
- Tất cả SP thao tác trên `LOPTINCHI` và `SP_SUA_MONHOC` đều check mốc này.

### 2.2 Danh sách 7 SP đã sửa (tất cả nằm trong `setup_login.sql`)

| # | Stored Procedure | Loại sửa | Mã lỗi mới |
|---|---|---|---|
| 1 | `SP_NHAP_DIEM` | Thêm 6 check: `DIEM_CC ∈ [0,10]`, `DIEM_GK ∈ [0,10]` & bội số 0.5, `DIEM_CK ∈ [0,10]` & bội số 0.5 | `-2, -3, -4, -5, -6` |
| 2 | `SP_THEM_LOPTINCHI` | Thêm 8 check: niên khóa, HOCKY, NHOM, SOSVTOITHIEU, FK MAMH/MAGV/MAKHOA | `-3, -4, -5, -6, -7, -8, -10` |
| 3 | `SP_SUA_LOPTINCHI` | Thêm 7 check + chặn lớp thuộc NK cũ (dùng `@OldNK` để chống né) | `-3, -4, -5, -6, -7, -8, -10` |
| 4 | `SP_XOA_LOPTINCHI` | Thêm chặn xóa lớp thuộc NK cũ | `-10` |
| 5 | `SP_PHUCHOI_LOPTINCHI` | Thêm chặn phục hồi lớp thuộc NK cũ | `-10` |
| 6 | `SP_THEM_MONHOC` | Thêm check `SOTIET_LT >= 30`, `SOTIET_TH >= 0` | `-2, -3` |
| 7 | `SP_SUA_MONHOC` | Thêm check `SOTIET_LT >= 30`, `SOTIET_TH >= 0`, chặn sửa môn đã dạy trong NK cũ | `-2, -3, -10` |

> **Lưu ý:** Mã lỗi `-1` được giữ nguyên cho mọi lỗi "đối tượng không tồn tại / đã tồn tại" để không phá vỡ code Flask đang parse.

### 2.3 Nguyên tắc sửa (không phá vỡ)
- **Không** đổi tên SP, **không** đổi parameter list, **không** đổi `GRANT EXECUTE`.
- **Không** đổi output format (`SELECT KETQUA, THONGBAO`).
- Chỉ chèn thêm `IF ... RETURN` ở đầu thân SP, **trước** phần `INSERT/UPDATE`.
- Thêm comment `-- [VALIDATE_SP_2026]` trước mỗi check mới (19 markers tổng cộng) để dễ audit.

---

## 3. Bảng tổng hợp mã lỗi (đã cập nhật vào `CRITICAL.md`)

| KETQUA | Ý nghĩa |
|---|---|
| `1` | Thành công |
| `MALTC` (số dương) | Mở lại lớp đã hủy, trả về ID |
| `-1` | Lỗi chung (không tồn tại / đã tồn tại / điều kiện không hợp lệ) |
| `-2` | Điểm CC ngoài `[0, 10]` **HOẶC** `SOTIET_LT < 30` |
| `-3` | Điểm GK ngoài `[0, 10]` **HOẶC** `HOCKY` ngoài `[1, 3]` |
| `-4` | Điểm GK không phải bội số 0.5 **HOẶC** `NHOM < 1` |
| `-5` | Điểm CK ngoài `[0, 10]` **HOẶC** `SOSVTOITHIEU <= 0` |
| `-6` | Điểm CK không phải bội số 0.5 **HOẶC** `MAMH` không tồn tại |
| `-7` | `MAGV` không tồn tại |
| `-8` | `MAKHOA` không tồn tại |
| `-10` | Niên khóa đóng băng `NIENKHOA < 2020-2021` **HOẶC** môn học đã từng dạy trong quá khứ |

---

## 4. Test cases (đã pass về mặt logic)

Để xác minh, mở SSMS và chạy lần lượt:

```sql
-- Kết nối với user PGV hoặc KHOA để chạy các test sau

-- Test 1: Điểm CK ngoài khoảng → -5
EXEC SP_NHAP_DIEM @MALTC=1, @MASV=N'N15...', @DIEM_CK=99
-- Kỳ vọng: KETQUA=-5, "Điểm cuối kỳ phải nằm trong khoảng [0, 10]"

-- Test 2: Điểm GK không bội số 0.5 → -4
EXEC SP_NHAP_DIEM @MALTC=1, @MASV=N'N15...', @DIEM_GK=7.3
-- Kỳ vọng: KETQUA=-4, "Điểm giữa kỳ phải là bội số của 0.5"

-- Test 3: Thêm LTC với NK cũ → -10
EXEC SP_THEM_LOPTINCHI @NIENKHOA='2019-2020', @HOCKY=1, @MAMH=N'...', ...
-- Kỳ vọng: KETQUA=-10, "Niên khóa < 2020-2021 đã bị đóng băng"

-- Test 4: Thêm LTC với HOCKY=5 → -3
EXEC SP_THEM_LOPTINCHI @NIENKHOA='2025-2026', @HOCKY=5, ...
-- Kỳ vọng: KETQUA=-3, "Học kỳ phải nằm trong khoảng [1, 3]"

-- Test 5: Sửa LTC thuộc NK cũ (kể cả truyền NK mới) → -10
EXEC SP_SUA_LOPTINCHI @MALTC=5, @NIENKHOA='2025-2026', @HOCKY=1, ...
-- Lớp 5 thuộc NK 2019 → bị chặn bằng @OldNK

-- Test 6: Xóa LTC thuộc NK cũ → -10
EXEC SP_XOA_LOPTINCHI @MALTC=3

-- Test 7: Thêm môn LT < 30 → -2
EXEC SP_THEM_MONHOC @MAMH=N'M001', @TENMH=N'Test', @SOTIET_LT=20, @SOTIET_TH=0

-- Test 8: Sửa môn đã từng dạy trong NK cũ → -10
EXEC SP_SUA_MONHOC @MAMH=N'...', @SOTIET_LT=45

-- Test 9 (happy path): Thêm LTC hợp lệ → 1
EXEC SP_THEM_LOPTINCHI @NIENKHOA='2025-2026', @HOCKY=1, @MAMH=N'...', @NHOM=1, @MAGV=N'...', @MAKHOA=N'...', @SOSVTOITHIEU=10
-- Kỳ vọng: KETQUA=1, "Mở lớp tín chỉ thành công"
```

---

## 5. Tệp tin bị thay đổi

| File | Loại thay đổi | Ghi chú |
|---|---|---|
| `setup_login.sql` | **Sửa** 7 SP | Thêm check ở đầu thân SP, giữ nguyên tên / param / grant. 1281 → 1457 dòng (+176 dòng). |
| `CRITICAL.md` | **Sửa** | Thêm mục "Bảng tổng hợp mã lỗi" + công thức niên khóa + quy tắc validate điểm |
| `plans/PLANT_VALIDATE_SP_2026.md` | Tạo mới | Kế hoạch chi tiết (đã duyệt) |
| `changelogs/CHANGELOGS_VALIDATE_SP_2026.md` | Tạo mới | File này |
| Database (bảng, cột, dữ liệu) | ❌ Không đụng | — |
| `app.py` | ❌ Không đụng | Logic `is_frozen` vẫn hoạt động như tầng 1 |
| Frontend (`templates/`, `static/`) | ❌ Không đụng | — |

---

## 6. Hướng dẫn cập nhật trên SSMS

Sau khi review file `setup_login.sql`, chạy lại script trên SSMS để cập nhật 7 SP:

1. Mở SSMS, kết nối tới `localhost\SQLEXPRESS`.
2. Mở file `setup_login.sql` (đã cập nhật ở trên).
3. **Chú ý:** Script có lệnh `DROP PROCEDURE` ở đầu mỗi SP — chạy sẽ xóa SP cũ và tạo SP mới với cùng tên, không ảnh hưởng dữ liệu.
4. Chạy toàn bộ script (Ctrl + A → F5).
5. Nếu có lỗi `Cannot drop procedure 'XXX' because it is being referenced by ...` → bỏ qua, có thể là do SP khác gọi SP này. Chạy lại đoạn bị lỗi sẽ pass.
6. Kiểm tra cuối cùng bằng cách chạy 9 test cases ở mục 4.
