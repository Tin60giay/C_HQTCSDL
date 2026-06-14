- Database là bất di bất dịch, không được sửa đổi các hàng, cột thuộc tính có sẵn của nó
- Có thể sửa, xóa, thêm hàm, store procedure để phục vụ mục đích truy vấn
- Mọi kế hoạch lên phải lưu dưới tên PLANT_XXX lưu ở thư mục plans chờ tôi duyệt
- Mọi sự thay đổi ở bất cứ chỗ nào bạn đã thực hiện kèm lý do sẽ được ghi vào file CHANGELOGS_XXX lưu vào folder changelogs
- Hướng dẫn test các tính năng mới sẽ được lưu dưới dạng file HDSD_XXX và lưu vào folder hdsd
- Tất cả các thay đổi trong sp phải được thực hiện trong file setup_login.sql không tự ý tạo file sql mới
- Khi sửa/ thêm/ xóa một tính năng thuộc một trang html bất kỳ thì phải check lại toàn bộ trang html đang có để xem tính năng này có đang gặp lỗi tương tự ở các trang html khác hay không và fix toàn bộ



- Nhớ check kỹ các ràng buộc thuộc database dưới đây:

### a. Table Khoa (Khoa)
- MAKHOA (nChar(10)): Primary Key
- TENKHOA (nVarchar(50)): Unique, not NULL

### b. Table Lop (Lớp)
- MALOP (nChar(10)): Primary Key
- TENLOP (nVarchar(50)): Unique, not NULL
- KHOAHOC (nchar(9)): not NULL
- MAKHOA (nChar(10)): FK, not NULL

### c. Table Sinhvien (Sinh viên)
- MASV (nChar(10)): Primary key
- HO (nVarchar(50)): not NULL
- TEN (nVarchar(10)): not NULL
- MALOP (nChar(10)): Foreign Key, not NULL
- PHAI (Bit): Default: false (false: Nam; true: Nữ)
- NGAYSINH (DateTime)
- DIACHI (nVarchar(100))
- DANGHIHOC (Bit): Default: false
- PASSWORD (nVarchar(40)): Default: 123456

### d. Table Monhoc (Môn học)
- MAMH (nChar(10)): Primary key
- TENMH (nVarchar(50)): Unique Key, not NULL
- SOTIET_LT (int): not NULL
- SOTIET_TH (int): not NULL

### e. Table GIANGVIEN (Giảng viên)
- MAGV (nChar(10)): Primary Key
- HO (nvarchar(50)): not NULL
- TEN (nvarchar(10)): not NULL
- HOCVI (nvarchar(20))
- HOCHAM (nvarchar(20))
- CHUYENMON (nvarchar(50))
- MAKHOA (nCHAR(10)): FK, not NULL

### f. Table LOPTINCHI (Lớp tín chỉ)
- MALTC (int): Primary Key (tự động)
- NIENKHOA (nChar(9)): not NULL
- HOCKY (int): not NULL, 1 <= hocky <= 3
- MAMH (nChar(10)): Foreign Key, not NULL
- NHOM (int): not NULL, >= 1
- MAGV (nChar(10)): Foreign Key, not NULL
- MAKHOA (nChar(10)): Foreign Key, not NULL (Ghi chú: lớp tín chỉ do khoa nào quản lý)
- SOSVTOITHIEU (SmallInt): not NULL, > 0
- HUYLOP (bit): Default: false
* Ràng buộc bổ sung: Unique key phối hợp gồm (NIENKHOA + HOCKY + MAMH + NHOM)

### g. Table DANGKY (Đăng ký)
- MALTC (int): Foreign Key, not NULL
- MASV (nChar(10)): Foreign Key, not NULL
- DIEM_CC (int): Điểm từ 0 đến 10
- DIEM_GK (float): Điểm từ 0 đến 10, làm tròn đến 0.5
- DIEM_CK (float): Điểm từ 0 đến 10, làm tròn đến 0.5
- HUYDANGKY (bit): Default: false
* Ràng buộc bổ sung: Primary key phối hợp gồm (MALTC + MASV)

---

## Bảng tổng hợp mã lỗi trả về từ Stored Procedure (KETQUA)

> **Quy ước:** `KETQUA = 1` (hoặc `KETQUA = MALTC` khi mở lại lớp đã hủy) = thành công. Các giá trị âm là mã lỗi. Mỗi SP chỉ trả về **1 dòng** có 2 cột `KETQUA` và `THONGBAO`.

| KETQUA | Ý nghĩa | Stored Procedure áp dụng |
|---|---|---|
| `1` | Thành công | Tất cả SP |
| `MALTC` (số dương) | Mở lại lớp tín chỉ đã hủy, trả về ID | `SP_THEM_LOPTINCHI` |
| `-1` | Lỗi chung (không tồn tại / đã tồn tại / điều kiện không hợp lệ) | Tất cả SP CRUD |
| `-2` | Điểm CC ngoài `[0, 10]` **HOẶC** `SOTIET_LT < 30` | `SP_NHAP_DIEM`, `SP_THEM_MONHOC`, `SP_SUA_MONHOC` |
| `-3` | Điểm GK ngoài `[0, 10]` **HOẶC** `HOCKY` ngoài `[1, 3]` | `SP_NHAP_DIEM`, `SP_THEM_LOPTINCHI`, `SP_SUA_LOPTINCHI` |
| `-4` | Điểm GK không là bội số 0.5 **HOẶC** `NHOM < 1` | `SP_NHAP_DIEM`, `SP_THEM_LOPTINCHI`, `SP_SUA_LOPTINCHI` |
| `-5` | Điểm CK ngoài `[0, 10]` **HOẶC** `SOSVTOITHIEU <= 0` | `SP_NHAP_DIEM`, `SP_THEM_LOPTINCHI`, `SP_SUA_LOPTINCHI` |
| `-6` | Điểm CK không là bội số 0.5 **HOẶC** `MAMH` không tồn tại | `SP_NHAP_DIEM`, `SP_THEM_LOPTINCHI`, `SP_SUA_LOPTINCHI` |
| `-7` | `MAGV` không tồn tại | `SP_THEM_LOPTINCHI`, `SP_SUA_LOPTINCHI` |
| `-8` | `MAKHOA` không tồn tại | `SP_THEM_LOPTINCHI`, `SP_SUA_LOPTINCHI` |
| `-10` | **Niên khóa đóng băng** (`NIENKHOA < 2025-2026`) **HOẶC** môn học đã từng dạy trong quá khứ | `SP_THEM_LOPTINCHI`, `SP_SUA_LOPTINCHI`, `SP_XOA_LOPTINCHI`, `SP_PHUCHOI_LOPTINCHI`, `SP_SUA_MONHOC` |
| `-20` | **Sinh viên quá hạn** (KHOAHOC + 7 năm — vẫn login được, chỉ xem điểm) | `SP_DANGKY_LTC`, `SP_HUY_DANGKY`, `SP_NHAP_DIEM` |
| `-21` | **Không thể đăng ký lớp tín chỉ trong quá khứ** (NK < năm hiện tại) | `SP_DANGKY_LTC` |

### Công thức niên khóa đóng băng (cố định)
- Mốc đóng băng cố định = `2025-2026` → threshold `NIENKHOA < '2025-2026'`.
- Áp dụng cho mọi thao tác INSERT / UPDATE / DELETE / Phục hồi trên bảng `LOPTINCHI`.
- Áp dụng cho UPDATE trên `MONHOC` nếu môn đã từng xuất hiện trong `LOPTINCHI` có `NIENKHOA < '2025-2026'`.

### Quy tắc sinh viên quá hạn (Out-of-range Student)

- **Định nghĩa:** Sinh viên có `YEAR(GETDATE()) - CAST(LEFT(LOP.KHOAHOC, 4) AS INT) > 7`.
- **Quyền hạn chế:**
  - ✅ Vẫn đăng nhập được (cờ `QUAHAN = 1` trong `SP_DANGNHAP_SV`).
  - ✅ Vẫn xem phiếu điểm cá nhân (`SP_XEM_PHIEU_DIEM`).
  - ❌ KHÔNG được đăng ký lớp tín chỉ mới (`SP_DANGKY_LTC` → `-20`).
  - ❌ KHÔNG được hủy đăng ký (`SP_HUY_DANGKY` → `-20`).
- **Quyền hạn chế của giảng viên:**
  - ❌ KHÔNG được nhập điểm / sửa điểm cho SV thuộc diện này (`SP_NHAP_DIEM` → `-20`).
- **Giao diện:** Nút bấm trong trang `dangky.html` bị **làm mờ** (`btn-disabled`), banner cảnh báo vàng hiển thị trong trang `phieu_diem.html` và `dangky.html`.
- **Ràng buộc bổ sung (`SP_DANGKY_LTC`):** Sinh viên không được đăng ký lớp tín chỉ có niên khóa trong quá khứ (NK < năm hiện tại) → mã lỗi `-21`.


### Quy tắc validate điểm (áp dụng cho `SP_NHAP_DIEM`)
- `DIEM_CC`: INT, khoảng `[0, 10]`.
- `DIEM_GK`, `DIEM_CK`: FLOAT, khoảng `[0, 10]`, **bắt buộc là bội số của 0.5** (kiểm tra bằng `ABS(x*2 - ROUND(x*2, 0)) <= 0.0001`).