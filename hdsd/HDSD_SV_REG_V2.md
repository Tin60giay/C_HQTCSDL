# Tài liệu hướng dẫn sử dụng: Module Đăng ký LTC v2

Tài liệu này hướng dẫn kiểm thử các tính năng mới trong bản cập nhật v2.0, tập trung vào ràng buộc môn học và cơ chế khóa UI an toàn.

---

## 1. Kiểm thử Đăng ký LTC (Dành cho Sinh viên)

### Kịch bản 1: Ràng buộc 1 môn / 1 lớp
1. Đăng nhập bằng tài khoản Sinh viên (vd: `N15DCCN001`).
2. Truy cập menu **"Đăng ký Lớp Tín Chỉ"**.
3. Chọn Niên khóa/Học kỳ để hiển thị danh sách lớp.
4. Tìm một môn học có ít nhất 2 lớp tín chỉ (vd: môn A có lớp 01 và lớp 02).
5. Bấm **Đăng ký** lớp 01 -> Một hộp thoại xác nhận hiện lên -> Bấm OK.
6. **Kết quả**:
    - Lớp 01 hiện nút **"Hủy đăng ký"** (xanh lá).
    - Lớp 02 của cùng môn đó, nút "Đăng ký" bị **mờ đi** (disabled).
    - Phía trên bảng tìm kiếm xuất hiện mục **"DANH SÁCH MÔN ĐÃ CHỌN"** chứa lớp 01.

### Kịch bản 2: Hủy đăng ký
1. Tại bảng "DANH SÁCH MÔN ĐÃ CHỌN" hoặc bảng tìm kiếm, bấm nút **"Hủy đăng ký"**.
2. Một hộp thoại xác nhận hiện lên cảnh báo hành động không thể hoàn tác.
3. Bấm OK.
4. **Kết quả**:
    - Lớp đó biến mất khỏi danh sách đã chọn.
    - Trong bảng tìm kiếm, nút của môn đó quay lại trạng thái "Đăng ký" bình thường.

---

## 2. Kiểm thử Khóa UI Toàn cục (Dành cho PGV/Khoa/SV)

Tính năng này áp dụng cho mọi trang nhập liệu (Lớp, Sinh viên, Môn học, Giảng viên...).

### Kịch bản 3: Khóa an toàn khi có lỗi dữ liệu
1. Truy cập trang **"Quản lý Sinh viên"** hoặc **"Quản lý Lớp"**.
2. Chọn một dòng bất kỳ để chỉnh sửa (chế độ UPDATE).
3. Tại ô **Mã sinh viên** hoặc **Mã lớp**, hãy nhập một mã **đã tồn tại** trong hệ thống.
4. Chờ 0.5 giây để hệ thống báo lỗi: `❌ Mã này đã tồn tại!`.
5. **Kết quả**:
    - Nút **"💾 Lưu dữ liệu"** bị mờ.
    - Nút **"🗑 Xóa"** bị mờ.
    - Nút **"＋ Tạo mới"** bị mờ.
    - Nút **"↩ Phục hồi"** bị mờ.
6. Bấm nút **"🧹 Làm mới form"**.
7. **Kết quả**: Form được xóa trắng và các nút chức năng (như Tạo mới) sẽ sáng lại bình thường.

---

## 3. Lưu ý kỹ thuật
- **Confirm Dialog**: Đây là yêu cầu bắt buộc để tránh sinh viên bấm nhầm gây mất slot trong lớp.
- **SQL Updates**: Đảm bảo bạn đã chạy lại file `setup_login.sql` trên SSMS để cập nhật các Stored Procedure mới nhất.
