# CHANGELOGS_LTC_BUGS_2026

> Ngày: 2026-06-18  |  Phạm vi: Sửa 5 lỗi mở lớp tín chỉ + đồng bộ filter toàn hệ thống
> Kế hoạch tham chiếu: `plans/PLANT_LTC_BUGS_2026.md`

---

## Tóm tắt thay đổi

| File | Loại | Mô tả |
|------|------|-------|
| `setup_login.sql` | Sửa SP | `SP_GET_LOPTINCHI_DANGKY`: filter theo khoa SV + phạm vi NK |
| `setup_login.sql` | Sửa SP | `SP_XEM_PHIEU_DIEM`: giới hạn phạm vi NK theo KHOAHOC+7 |
| `setup_login.sql` | Thêm SP | `SP_GET_NIENKHOA_SV`: trả NK theo phạm vi của SV |
| `setup_login.sql` | Thêm SP | `SP_GET_DEFAULT_NK_LTC`: NK mới nhất trong LOPTINCHI |
| `app.py` | Sửa | Route `/loptinchi`: default NK mới nhất |
| `app.py` | Sửa | Route `/dangky`: dùng `SP_GET_NIENKHOA_SV` |
| `app.py` | Thêm helper | `get_default_nk_ltc()`, `get_nienkhoa_for_sv()` |
| `static/history.js` | Sửa | Thêm `applyReadonlyStyle()` và `clearReadonlyStyle()` |
| `static/history.js` | Sửa | `toggleFormLock()` thêm `cursor:not-allowed` |
| `templates/khoa.html` | Sửa | `chonDong`/`xoaTrang`: làm mờ Mã Khoa |
| `templates/lop.html` | Sửa | `chonDong`/`xoaTrang`: làm mờ Mã Lớp (luôn cả khi không frozen) |
| `templates/giangvien.html` | Sửa | `chonDong`/`xoaTrang`: làm mờ Mã GV |
| `templates/monhoc.html` | Sửa | `chonDong`/`xoaTrang`: làm mờ Mã MH (luôn cả khi không frozen) |
| `templates/sinhvien.html` | Sửa | `chonDong`/`xoaTrang`: làm mờ Mã SV (luôn cả khi không frozen) |
| `templates/loptinchi.html` | Sửa | Filter: thêm data-attributes (`data-nk`, `data-hk`, `data-khoa`, `data-text`) + nút "Xem tất cả" |
| `templates/loptinchi.html` | Sửa | `chonDong`: khóa NK/HK/MAMH/MAKHOA khi edit |
| `templates/dangky.html` | Sửa | Auto-select NK đầu tiên + auto-trigger `timLop()` khi load |

---

## 1. Issue 1: Làm mờ trường readOnly

**Vấn đề**: Tất cả 6 trang quản lý đều set `fM.readOnly = true` cho khóa chính khi chọn dòng để sửa, nhưng KHÔNG gọi style làm mờ → user không biết là trường đó không sửa được.

**Nguyên nhân gốc**:
- Hàm `toggleFormLock()` chỉ được gọi khi dữ liệu bị Frozen (đóng băng).
- Khi user chọn dòng bình thường (không Frozen), code chỉ set `readOnly = true` cho `fM` mà không gọi style.

**Cách xử lý**:
- Thêm helper `applyReadonlyStyle(el, isFrozen)` trong `static/history.js` để áp dụng style mờ + readOnly một lần.
- Thêm helper `clearReadonlyStyle(el)` để reset khi tạo mới.
- Cập nhật 6 trang HTML: thay `fM.readOnly = true; fM.style.borderColor = ...` thành `applyReadonlyStyle(fM, isFrozen)`.
- Áp dụng đồng bộ cho: `khoa.html`, `lop.html`, `giangvien.html`, `monhoc.html`, `sinhvien.html`, `loptinchi.html`.

**Kết quả**: Mọi trường khóa chính (Mã Khoa, Mã Lớp, Mã GV, Mã MH, Mã SV) khi chọn dòng đều có nền mờ + chữ xám + cursor not-allowed. Khi nhấn "Làm mới form" → trở về trạng thái bình thường.

---

## 2. Issue 2: Lọc không đồng bộ + không mặc định NK mới nhất

**Vấn đề**:
- `loptinchi.html` gọi `locBang()` filter qua `data-attributes` trên `<tr>`, NHƯNG các `<tr>` KHÔNG CÓ `data-nk`, `data-hk`, `data-khoa` → lọc không hoạt động.
- Khi mở `/loptinchi` không truyền query → hiển thị TẤT CẢ các lớp tín chỉ (kể cả cũ), không focus vào NK mới nhất.

**Cách xử lý**:
- **HTML**: Thêm data-attributes cho mỗi `<tr>` của `loptinchi.html`: `data-nk`, `data-hk`, `data-khoa`, `data-text` (chứa thông tin để tìm kiếm text). Thêm nút "↻ Xem tất cả" để reset filter.
- **Server**: Thêm SP `SP_GET_DEFAULT_NK_LTC` trả về NK lớn nhất có LTC chưa hủy. Trong `app.py` route `/loptinchi`, nếu `request.args.get('nienkhoa')` rỗng → gọi SP lấy NK mới nhất làm mặc định.
- Lấy ý tưởng từ `lop.html` (filter local + query string + reset button).

**Kết quả**:
- Khi mở `/loptinchi`: tự động filter về NK mới nhất có LTC.
- Khi đổi filter (Niên khóa / Học kỳ / Khoa / Tìm kiếm): lọc tức thì trên client.
- Khi nhấn "Xem tất cả": reset toàn bộ filter.

---

## 3. Issue 3: Sửa LTC: không cho sửa NK/HK/MAMH/MAKHOA

**Vấn đề**: Khi PGV chọn 1 dòng LTC để sửa, hiện tại form mở khóa tất cả các trường → user có thể sửa nhầm NK/HK/MAMH/MAKHOA → dễ phá vỡ cấu trúc dữ liệu và các đăng ký liên quan.

**Cách xử lý**:
- Trong `loptinchi.html` hàm `chonDong()`:
  - Nếu Frozen: khóa tất cả (giữ nguyên).
  - Nếu KHÔNG Frozen (edit bình thường): khóa 4 trường định danh `fNK, fHK, fMAMH, fMAKHOA_F` (chỉ cho sửa `fNHOM, fMAGV, fSOSV`).
- Hàm `xoaTrang()` mở khóa tất cả.

**Lý do chỉ cho sửa NHOM/MAGV/SOSV**:
- NHÓM: thay đổi nhóm lớp (chia nhóm lớn thành nhóm nhỏ).
- MAGV: thay đổi giảng viên phụ trách.
- SOSV: điều chỉnh ngưỡng tối thiểu.
- NK/HK/MAMH/MAKHOA là định danh không được phép thay đổi vì ảnh hưởng đến DANGKY (đăng ký), DIEM (điểm), khóa học.

**Kết quả**: Khi chọn 1 LTC để sửa, 4 trường NK/HK/MAMH/MAKHOA tự động bị mờ + disabled, không thể chỉnh. 3 trường NHOM/MAGV/SOSV vẫn sửa được bình thường.

---

## 4. Issue 4: SV chỉ thấy LTC khoa mình

**Vấn đề**: Hiện tại SP `SP_GET_LOPTINCHI_DANGKY` không filter theo khoa → SV khoa CNTT vẫn thấy LTC của khoa Viễn Thông.

**Cách xử lý**:
- Trong SP `SP_GET_LOPTINCHI_DANGKY`: thêm logic lấy `MAKHOA` của SV từ `LOP.MAKHOA` thông qua `SINHVIEN.MALOP` → lưu vào biến `@MAKHOA_SV`.
- Thêm điều kiện `LTC.MAKHOA = @MAKHOA_SV` trong mệnh đề WHERE.

**Kết quả**: SV chỉ thấy các LTC thuộc khoa của mình.

---

## 5. Issue 5: SV chỉ thấy LTC trong phạm vi KHOAHOC → KHOAHOC+7

**Vấn đề**:
- SV khóa 2015-2019 vẫn thấy LTC mở từ 2025-2026 (NK quá khứ so với KHOAHOC).
- SV quá hạn (KHOAHOC + 7) vẫn thấy LTC mở mới 2025-2026.

**Cách xử lý**:
- Trong SP `SP_GET_LOPTINCHI_DANGKY`: thêm biến `@NamBD = năm bắt đầu KHOAHOC` của SV. Tính `@NamKT = @NamBD + 7`. Thêm điều kiện:
  ```sql
  CAST(LEFT(LTC.NIENKHOA, 4) AS INT) BETWEEN @NamBD AND @NamKT
  ```
- Nếu SV chọn NK ngoài phạm vi → trả về rỗng.
- Tương tự trong SP `SP_XEM_PHIEU_DIEM`: thêm cùng điều kiện để SV chỉ xem được điểm đến NK = KHOAHOC + 7.
- Thêm SP mới `SP_GET_NIENKHOA_SV` để dropdown filter của SV chỉ hiển thị các NK thuộc phạm vi `[KHOAHOC, KHOAHOC+7]`.

**Kết quả**:
- SV khóa 2015-2019 (năm bắt đầu 2015): chỉ thấy NK từ 2015-2016 đến 2022-2023.
- SV khóa 2016-2020 (năm bắt đầu 2016): chỉ thấy NK từ 2016-2017 đến 2023-2024.
- SV khóa mới (>= 2019): thấy NK hiện tại.
- SV quá hạn: thấy đến NK = KHOAHOC + 7.
- SV đăng ký vào LTC ngoài phạm vi → bị từ chối (bảo vệ ở SP `SP_DANGKY_LTC` đã có sẵn).

---

## File mới

- `plans/PLANT_LTC_BUGS_2026.md` - Kế hoạch chi tiết
- `changelogs/CHANGELOGS_LTC_BUGS_2026.md` - File này
- `hdsd/HDSD_LTC_BUGS_2026.md` - Hướng dẫn sử dụng / test

---

## File KHÔNG thay đổi

- `QLDSV_HTC.sql` - File tạo CSDL gốc, không đụng vào.
- Toàn bộ cấu trúc bảng (DANGKY, LOPTINCHI, MONHOC, ...) giữ nguyên.
