# CHANGELOG 004 — Ràng Buộc & Phân Quyền Toàn Diện

## 1. Database — Stored Procedures (`setup_login.sql`)

### SP_NHAP_DIEM (v2)
- **Thêm validate DIEM_CC**: phải là số nguyên trong khoảng 0–10.
- **Thêm validate DIEM_GK, DIEM_CK**: phải trong khoảng 0–10 và là bội số của 0.5 (kiểm tra bằng `@DIEM * 2 = FLOOR(@DIEM * 2)`).
- Trả mã lỗi `-2`, `-3`, `-4` tương ứng khi vi phạm.

### SP_THEM_LOPTINCHI (v2)
- **Thêm validate HOCKY**: phải từ 1 đến 3, trả `-5` nếu sai.
- **Thêm validate NHOM**: phải >= 1, trả `-6` nếu sai.
- **Thêm validate SOSVTOITHIEU**: phải > 0, trả `-7` nếu sai.
- **Sửa lỗi SCOPE_IDENTITY**: khi INSERT lớp mới, trả `SCOPE_IDENTITY()` (MALTC thực) thay vì số 1 cố định → sửa lỗi hoàn tác sai lớp trong lịch sử thao tác.
- Trường hợp mở lại lớp đã hủy: vẫn trả đúng MALTC từ DB.

### SP_SUA_LOPTINCHI (v2)
- **Thêm validate HOCKY, NHOM, SOSVTOITHIEU** giống SP_THEM.
- **Thêm check trùng tổ hợp** (NIENKHOA, HOCKY, MAMH, NHOM) loại trừ chính bản ghi đang sửa, trả `-2`.

### SP_THEM_MONHOC, SP_SUA_MONHOC
- Thêm kiểm tra `TENMH` unique: không được trùng tên với môn học khác, trả `-2`.

### SP_THEM_LOP, SP_SUA_LOP
- Thêm kiểm tra `TENLOP` unique: không được trùng tên với lớp khác, trả `-3`.

### SP_THEM_KHOA, SP_SUA_KHOA
- Thêm kiểm tra `TENKHOA` unique: không được trùng tên với khoa khác, trả `-2`.

### SP_SUA_SV (v2)
- **Thêm tham số `@DANGHIHOC BIT = 0`**: cho phép PGV cập nhật trạng thái nghỉ học của sinh viên thông qua giao diện mà không cần truy cập thẳng SSMS.

### SP_TAOLOGIN (fix injection)
- Thêm `DECLARE @PASS_ESCAPED = REPLACE(@PASS, '''', '''''')` trước khi ghép vào câu lệnh `CREATE LOGIN` dynamic SQL, tránh lỗi SQL syntax và nguy cơ SQL injection khi mật khẩu chứa dấu nháy đơn `'`.

---

## 2. Backend — `app.py`

### Hàm `login()` — lưu MAKHOA vào session
- Sau khi đăng nhập thành công với tài khoản Giảng viên, hệ thống query thêm `MAKHOA` từ bảng `GIANGVIEN` và lưu vào `session['makhoa']`.
- Đây là nền tảng để lọc dữ liệu theo khoa cho nhóm KHOA ở các trang sau.

### Route `/loptinchi` — ép filter MAKHOA cho nhóm KHOA
- Nếu `group == 'KHOA'`: bắt buộc dùng `session['makhoa']` làm filter, bỏ qua URL param `?makhoa=`.
- Trước đây GV khoa CNTT có thể xóa `?makhoa=CNTT` khỏi URL để xem lớp của khoa khác.

### Route `/nhapdiem/batdau` — lọc LTC theo khoa cho nhóm KHOA
- Thêm điều kiện `AND (? IS NULL OR LTC.MAKHOA=?)` vào câu truy vấn tìm MALTC.
- Nhóm KHOA chỉ có thể tìm thấy và nhập điểm các lớp tín chỉ thuộc khoa của mình.

### Route `/sinhvien/ghi` — truyền DANGHIHOC
- Đọc thêm field `danghihoc` từ form submit.
- Truyền vào SP_SUA_SV với 8 tham số thay vì 7.

### Route `/doimatkhau/submit` — fix SQL injection
- Thay lệnh `cursor.execute(f"ALTER LOGIN ...")` (f-string dễ bị injection) bằng `sp_executesql` với tham số `@P` và `@O` kiểu `NVARCHAR(200)`.
