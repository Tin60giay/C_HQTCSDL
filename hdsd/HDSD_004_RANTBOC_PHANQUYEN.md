# Hướng Dẫn Kiểm Tra Ràng Buộc & Phân Quyền

Tài liệu này hướng dẫn cách test thủ công từng ràng buộc đã được vá trong đợt sửa lỗi này.

> **Lưu ý**: Sau khi cập nhật, bạn cần **đăng xuất và đăng nhập lại** để session ghi nhận `MAKHOA` mới.

---

## 1. Kiểm tra phân quyền KHOA theo khoa

**Mục tiêu**: GV thuộc khoa CNTT chỉ được xem/nhập điểm lớp khoa CNTT.

**Cách test**:
1. Đăng nhập bằng `GV03` (khoa CNTT).
2. Vào trang **Mở Lớp Tín Chỉ** → chỉ thấy lớp của khoa CNTT, không thấy lớp VT.
3. Thử thêm `?makhoa=VT` vào cuối URL → hệ thống tự động reset về CNTT, không hiển thị dữ liệu khoa khác.
4. Vào trang **Nhập Điểm** → chọn môn học của khoa VT → bấm "Bắt đầu" → thông báo "Không tìm thấy lớp tín chỉ".

---

## 2. Kiểm tra validate điểm SP_NHAP_DIEM

**Mục tiêu**: Hệ thống từ chối điểm vi phạm (ngoài 0-10, GK/CK không tròn 0.5).

**Cách test**:
1. Vào trang **Nhập Điểm**, chọn lớp tín chỉ có sinh viên, bấm Bắt đầu.
2. Nhập **Điểm CC = 11** → bấm Ghi Điểm → hệ thống hiển thị thông báo lỗi.
3. Nhập **Điểm GK = 7.3** → bấm Ghi Điểm → bị từ chối (không phải bước 0.5).
4. Nhập **Điểm GK = 7.5** → bấm Ghi Điểm → thành công.

---

## 3. Kiểm tra validate lớp tín chỉ

**Mục tiêu**: SP từ chối dữ liệu sai khi mở/sửa lớp tín chỉ.

**Cách test** (cần tài khoản PGV):
1. Vào **Mở Lớp Tín Chỉ**, bấm Thêm mới.
2. Thử nhập **Học kỳ = 4** → hệ thống báo lỗi "Học kỳ phải từ 1 đến 3".
3. Thử nhập **Nhóm = 0** → báo lỗi "Nhóm phải >= 1".
4. Thử nhập **SV tối thiểu = 0** → báo lỗi.

---

## 4. Kiểm tra unique tên Khoa/Lớp/Môn học

**Mục tiêu**: Không cho phép 2 bản ghi có cùng tên dù khác mã.

**Cách test** (cần tài khoản PGV):
1. Vào **Quản lý Khoa** → Thêm mới khoa với **Tên Khoa** đã tồn tại (ví dụ: "Công nghệ thông tin") → báo "Tên khoa đã tồn tại".
2. Tương tự với **Quản lý Lớp** → thử trùng Tên Lớp.
3. Tương tự với **Quản lý Môn Học** → thử trùng Tên Môn Học.

---

## 5. Kiểm tra lịch sử hoàn tác (MALTC đúng)

**Mục tiêu**: Hoàn tác đúng lớp tín chỉ vừa mở.

**Cách test** (cần tài khoản PGV):
1. Mở **một lớp tín chỉ mới** (chưa từng tồn tại).
2. Nhìn vào **Lịch sử thao tác** → bấm **Hoàn tác** lớp đó.
3. Kiểm tra lớp vừa hoàn tác có biến mất khỏi danh sách không (không hoàn tác nhầm lớp khác có MALTC=1).

---

## 6. Kiểm tra đổi mật khẩu ký tự đặc biệt

**Mục tiêu**: Mật khẩu chứa dấu `'` không gây lỗi SQL.

**Cách test**:
1. Đăng nhập GV → vào **Đổi Mật Khẩu**.
2. Nhập mật khẩu mới: `Test'123` → bấm Xác nhận → không bị lỗi 500.
3. Đăng xuất → đăng nhập lại bằng mật khẩu `Test'123` → thành công.
4. Sau khi xong, đổi lại mật khẩu cũ.

---

## 7. Kiểm tra cập nhật trạng thái Nghỉ Học của Sinh Viên

**Mục tiêu**: PGV có thể đánh dấu Sinh Viên đang nghỉ học.

**Cách test** (cần tài khoản PGV):
1. Vào **Quản lý Sinh Viên** → chọn 1 sinh viên.
2. Tích chọn ô **Đang Nghỉ Học** → bấm **Ghi**.
3. Kiểm tra trong DB hoặc thử đăng nhập bằng tài khoản SV đó → nếu DANGHIHOC=1 thì bị từ chối đăng nhập (SP_DANGNHAP_SV đã có check này).
