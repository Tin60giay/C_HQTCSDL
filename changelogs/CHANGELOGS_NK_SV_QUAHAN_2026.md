# CHANGELOG: Sửa mốc niên khóa + Quy tắc sinh viên quá hạn (NK_SV_QUAHAN_2026)

> **Ngày thực hiện:** 2026-06-14
> **Kế hoạch:** `plans/PLANT_NK_SV_QUAHAN_2026.md` (đã duyệt)
> **Phạm vi:**
> - Sửa `setup_login.sql` (revert mốc đóng băng + thêm logic quá hạn vào 4 SP + chặn ĐK LTC quá khứ)
> - Sửa `app.py` (lưu cờ `quahan` vào session + chặn ĐK/Hủy khi quá hạn)
> - Sửa `templates/phieu_diem.html` (banner quá hạn + fix lỗi tên biến `phieu_diem` / `sv` / `DIEM_TK`)
> - Sửa `templates/dangky.html` (banner quá hạn + làm mờ nút ĐK/Hủy khi quá hạn + thông báo JS)
> - Cập nhật `CRITICAL.md` (sửa công thức NK + thêm mục SV quá hạn + mã lỗi -20, -21)
> - **Cập nhật changelog cũ** `changelogs/CHANGELOGS_VALIDATE_SP_2026.md` (ghi nhận revert mốc)

---

## 1. Bối cảnh

Trong `CHANGELOGS_VALIDATE_SP_2026.md` (plan trước), mình đã nhầm lẫn mốc đóng băng từ `2025-2026` (đúng) sang `2020-2021` (sai) do hiểu nhầm yêu cầu. Bạn đã xác nhận lại:

> *"đóng băng là đóng băng từ 2025 về trước"*

Đồng thời bạn yêu cầu bổ sung **quy tắc sinh viên quá hạn** hoàn toàn mới:
- Sinh viên chỉ được đăng ký lớp tín chỉ trong khoảng `[KHOAHOC, KHOAHOC + 7 năm]`.
- Sinh viên vẫn login được để xem điểm nhưng bị vô hiệu hóa mọi chức năng khác.
- Giảng viên không được nhập điểm lại cho SV thuộc diện này.

---

## 2. Thay đổi chi tiết

### 2.1 Revert mốc niên khóa đóng băng

| SP | Trước (sai) | Sau (đúng) |
|---|---|---|
| `SP_THEM_LOPTINCHI` | `NIENKHOA < '2020-2021'` | `NIENKHOA < '2025-2026'` |
| `SP_SUA_LOPTINCHI` | `NIENKHOA < '2020-2021'` | `NIENKHOA < '2025-2026'` |
| `SP_XOA_LOPTINCHI` | `NIENKHOA < '2020-2021'` | `NIENKHOA < '2025-2026'` |
| `SP_PHUCHOI_LOPTINCHI` | `NIENKHOA < '2020-2021'` | `NIENKHOA < '2025-2026'` |
| `SP_SUA_MONHOC` | `LOPTINCHI.NIENKHOA < '2020-2021'` | `LOPTINCHI.NIENKHOA < '2025-2026'` |

Tổng: **11 chỗ đã sửa** (toàn bộ `'2020-2021'` đã được thay bằng `'2025-2026'`).

### 2.2 Thêm logic quá hạn vào 4 SP

#### `SP_DANGNHAP_SV` — Trả thêm cột `QUAHAN`
- Tính `YEAR(GETDATE()) - năm bắt đầu KHOAHOC > 7` → cờ `QUAHAN = 1` (quá hạn) hoặc `0` (bình thường).
- Cột `QUAHAN` được thêm vào `SELECT` cuối cùng, các ứng dụng cũ không đọc cột này vẫn hoạt động bình thường.

#### `SP_DANGKY_LTC` — 2 check mới
1. **Chặn SV quá hạn** (mã lỗi `-20`): nếu năm bắt đầu NK của LTC > (năm bắt đầu KHOAHOC + 7).
2. **Chặn ĐK LTC trong quá khứ** (mã lỗi `-21`): nếu năm bắt đầu NK của LTC < năm hiện tại (`YEAR(GETDATE())`).

#### `SP_HUY_DANGKY` — 1 check mới
- Chặn hủy nếu SV đã quá hạn (mã lỗi `-20`).

#### `SP_NHAP_DIEM` — 1 check mới (chặn GV)
- Chặn giảng viên nhập/sửa điểm cho SV đã quá hạn (mã lỗi `-20`).

### 2.3 Cập nhật `app.py` (4 chỗ)

| Route | Thay đổi |
|---|---|
| `login` (route `/`) | Thêm `session['quahan'] = bool(getattr(row, 'QUAHAN', 0))` sau khi login SV thành công. |
| `phieu_diem` (route `/phieu_diem`) | Đổi tên biến `diem_list` → `phieu_diem` (khớp với template), thêm biến `sv={'MASV', 'HOTEN', 'MALOP'}` (fix lỗi template cũ), thêm `quahan=quahan`. |
| `dangky_thuchien` (route `/dangky/dangky`) | Thêm check `if session.get('quahan'): return jsonify({'ok': False, 'msg': ...})` ngay đầu. |
| `dangky_huy` (route `/dangky/huy`) | Tương tự `dangky_thuchien`. |

### 2.4 Cập nhật 2 template

#### `templates/phieu_diem.html`
- **Fix lỗi "bảng điểm đang lỗi sẵn":**
  - Template cũ dùng `{{ sv.MASV }}` nhưng `app.py` không truyền biến `sv` → fix bằng cách truyền `sv={'MASV', 'HOTEN', 'MALOP'}` từ route.
  - Template cũ dùng `{% for r in phieu_diem %}` nhưng biến trong route tên là `diem_list` → fix bằng cách đổi tên `diem_list` → `phieu_diem` ở route.
  - Template cũ dùng `r.DIEM_HM` nhưng SP trả `DIEM_TK` → fix bằng cách đổi `r.DIEM_HM` → `r.DIEM_TK`.
  - Thêm xử lý `{% if r.X is not none %}` (sẵn có) → giờ chỉ hiển thị `—` khi điểm là `NULL` (chưa nhập).
- **Thêm banner quá hạn** (khi `quahan=True`): banner đỏ ở đầu trang với thông báo "Bạn đã quá hạn 7 năm...".
- **Thêm CSS** `.btn-disabled` và `.quahan-banner` (dù chưa sử dụng ngay — để dành cho sau này).

#### `templates/dangky.html`
- Thêm banner quá hạn ngay sau dòng `get_flashed_messages`.
- Thêm biến JS `const QUAHAN = {{ 'true' if quahan else 'false' }}`.
- Trong `renderAll()`:
  - Nút "Đăng ký" / "Hủy đăng ký" trong cả 2 bảng (Đã chọn & Tìm kiếm) bị làm mờ (`btn-disabled`) khi `QUAHAN = true`.
- Trong `xulyDangKy()` và `xulyHuy()`: thêm `if (QUAHAN) { alert(...); return; }` ở đầu.

### 2.5 Cập nhật `CRITICAL.md`

| Mục | Thay đổi |
|---|---|
| Bảng mã lỗi | Thêm `-20` (SV quá hạn) và `-21` (ĐK LTC quá khứ). Sửa mô tả `-10` từ `2020-2021` → `2025-2026`. |
| Công thức NK đóng băng | Sửa thành "Mốc cố định `2025-2026`" + thêm đoạn giải thích tại sao là cố định. |
| Thêm mục mới "Quy tắc SV quá hạn" | Định nghĩa + quyền hạn chế + cách áp dụng ở từng SP. |
| Thêm mục "Vì sao dùng `YEAR(GETDATE())`" | Giải thích ưu/nhược điểm của việc dùng hàm SQL tự động thay vì hard-code năm. |

---

## 3. Bảng mã lỗi (cập nhật)

| KETQUA | Ý nghĩa |
|---|---|
| `1` | Thành công |
| `MALTC` (số dương) | Mở lại lớp đã hủy, trả về ID |
| `-1` | Lỗi chung (không tồn tại / đã tồn tại) |
| `-2` → `-8` | Validate điểm / LTC / FK (xem `CRITICAL.md` để biết chi tiết) |
| `-10` | Niên khóa đóng băng `NIENKHOA < 2025-2026` / môn đã từng dạy trong quá khứ |
| **`-20`** | **Sinh viên quá hạn (KHOAHOC + 7 năm)** |
| **`-21`** | **Không thể đăng ký LTC trong quá khứ (NK < năm hiện tại)** |

---

## 4. Test Cases

### 4.1 Revert mốc (4 test)
| # | Test | Kỳ vọng |
|---|---|---|
| 1 | `EXEC SP_THEM_LOPTINCHI @NIENKHOA='2024-2025', @HOCKY=1, ...` | `KETQUA=-10`, "Niên khóa < 2025-2026 đã bị đóng băng" |
| 2 | `EXEC SP_THEM_LOPTINCHI @NIENKHOA='2025-2026', @HOCKY=1, ...` | `KETQUA=1` (thành công) |
| 3 | `EXEC SP_THEM_LOPTINCHI @NIENKHOA='2026-2027', @HOCKY=1, ...` | `KETQUA=1` (thành công) |
| 4 | `EXEC SP_SUA_MONHOC @MAMH='M...', @SOTIET_LT=45` (môn đã dạy năm 2024) | `KETQUA=-10`, "không thể sửa" |

### 4.2 Quá hạn (5 test)
| # | Test | Kỳ vọng |
|---|---|---|
| 5 | Login SV thuộc lớp `KHOAHOC='2018-2022'` (học 8 năm, quá hạn) | `QUAHAN = 1` |
| 6 | Login SV thuộc lớp `KHOAHOC='2021-2025'` (học 5 năm) | `QUAHAN = 0` |
| 7 | SV K2021 ĐK lớp LTC `NIENKHOA='2029-2030'` (vượt 8 năm) | `KETQUA=-20`, "quá hạn" |
| 8 | SV K2021 hủy lớp LTC `NIENKHOA='2029-2030'` | `KETQUA=-20`, "quá hạn" |
| 9 | GV nhập điểm cho SV K2021 ở lớp LTC `NIENKHOA='2029-2030'` | `KETQUA=-20`, "không thể nhập/sửa điểm" |

### 4.3 ĐK LTC quá khứ (2 test)
| # | Test | Kỳ vọng |
|---|---|---|
| 10 | SV K2025 (năm 2026) ĐK lớp LTC `NIENKHOA='2023-2024'` (quá khứ) | `KETQUA=-21`, "Không thể đăng ký lớp tín chỉ thuộc niên khóa trong quá khứ" |
| 11 | SV K2025 (năm 2026) ĐK lớp LTC `NIENKHOA='2025-2026'` (hiện tại) | `KETQUA=1` (thành công) |

### 4.4 UI (manual test)
- [ ] Đăng nhập bằng TK SV quá hạn → thấy banner đỏ trong `phieu_diem.html` và `dangky.html`
- [ ] Trong `dangky.html`: tất cả nút "Đăng ký" / "Hủy đăng ký" bị làm mờ
- [ ] Bấm nút "Đăng ký" bất kỳ → alert "Bạn đã quá hạn 7 năm..."
- [ ] Phiếu điểm hiển thị bình thường (không bị chặn)
- [ ] Phiếu điểm không bị lỗi "UndefinedError" nữa (do `r.DIEM_HM` đã sửa thành `r.DIEM_TK`)
- [ ] Phiếu điểm có hiển thị `—` thay vì `None` cho môn chưa nhập điểm

---

## 5. Tệp tin bị thay đổi

| File | Loại thay đổi | Ghi chú |
|---|---|---|
| `setup_login.sql` | **Sửa** | Revert mốc (11 chỗ) + thêm logic quá hạn ở 4 SP + chặn ĐK LTC quá khứ ở `SP_DANGKY_LTC` |
| `app.py` | **Sửa** | Lưu `session['quahan']` + sửa route `phieu_diem` (fix lỗi) + thêm check ở `dangky_thuchien` / `dangky_huy` |
| `templates/phieu_diem.html` | **Sửa** | Thêm banner quá hạn + fix lỗi tên biến `sv` / `phieu_diem` / `DIEM_TK` |
| `templates/dangky.html` | **Sửa** | Thêm banner quá hạn + biến JS `QUAHAN` + làm mờ nút + chặn bằng alert |
| `CRITICAL.md` | **Sửa** | Sửa mốc NK + thêm mục "Quy tắc SV quá hạn" + thêm mã lỗi -20, -21 + giải thích `GETDATE()` |
| `changelogs/CHANGELOGS_VALIDATE_SP_2026.md` | **Sửa** | Thêm ghi chú "revert mốc" ở đầu file |
| `changelogs/CHANGELOGS_NK_SV_QUAHAN_2026.md` | Tạo mới | File này |
| Database (bảng, cột, dữ liệu) | ⛔ Không đụng | — |

---

## 6. Hướng dẫn cập nhật trên SSMS

1. Mở SSMS, kết nối `localhost\SQLEXPRESS`.
2. Mở file `setup_login.sql` (đã cập nhật ở trên).
3. **Chú ý:** Script có lệnh `DROP PROCEDURE` ở đầu mỗi SP. Chạy sẽ xóa SP cũ và tạo SP mới với cùng tên, không ảnh hưởng dữ liệu.
4. Chạy toàn bộ script (Ctrl + A → F5).
5. Nếu có lỗi `Cannot drop procedure 'XXX' because it is being referenced by ...` → bỏ qua, chạy lại đoạn bị lỗi sẽ pass.
6. Sau khi script chạy xong, **khởi động lại `python app.py`** để Flask load lại SP.

## 7. Hướng dẫn kiểm tra sau khi cập nhật

1. **Test SQL Server:** chạy 11 test cases ở mục 4.
2. **Test web:**
   - Đăng nhập bằng SV K2025 (bình thường) → không thấy banner quá hạn, nút ĐK sáng.
   - Đăng nhập bằng SV K2018 (quá hạn — nếu có) → thấy banner đỏ, nút ĐK bị mờ.
   - Vào `Phiếu điểm` → kiểm tra bảng hiển thị đầy đủ các cột (không còn lỗi `UndefinedError: 'sv'`).
   - Các môn chưa nhập điểm hiển thị `—` (không phải `None`).
