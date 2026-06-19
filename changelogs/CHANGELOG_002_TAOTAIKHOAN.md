# Thay Đổi Cấu Trúc Database và Code: Tạo Tài Khoản Giảng Viên

## 1. Database (setup_login.sql)
- **Thêm Script tạo Role**: Thêm lệnh `CREATE ROLE PGV` và `CREATE ROLE KHOA` để giải quyết việc phân quyền cho tài khoản đăng nhập mà không cần tác động đến cấu trúc các bảng dữ liệu gốc.
- **Bổ sung SP_TAOLOGIN**: Thủ tục này tự động kiểm tra trùng lặp Login/User. Sau đó tạo Login với mật khẩu mặc định (hoặc nhập từ giao diện), tạo User và cấp các quyền SELECT, EXECUTE vào các bảng/SP cho giảng viên.
- **Bổ sung SP_XOALOGIN**: Thủ tục gỡ bỏ User khỏi Role, thu hồi User và xóa luôn Login.

## 2. Backend (app.py)
- **Cập nhật hàm Đăng nhập (`login`)**:
  - Gốc: Sử dụng danh sách cứng `PGV_LOGINS` để chia nhóm quyền.
  - Mới: Thêm truy vấn SQL để kiểm tra User đó có thuộc Database Role (`PGV` hoặc `KHOA`) không. Nếu có, nhận quyền theo Role. Nếu không (GV cũ chưa được đưa vào Role), tiếp tục sử dụng `PGV_LOGINS` để tương thích.
- **Bổ sung Route mới**:
  - `/taotaikhoan` (GET): Gọi `SP_GETALL_GIANGVIEN` để nạp danh sách giảng viên, render file `taotaikhoan.html`.
  - `/taotaikhoan/submit` (POST): Nhận API POST từ trình duyệt, gọi SP `SP_TAOLOGIN` và trả lời JSON thông báo thành công hoặc trùng lặp.
  - `/taotaikhoan/delete` (POST): Gọi SP `SP_XOALOGIN` để xóa tài khoản.

## 3. Frontend
- **Bổ sung `taotaikhoan.html`**: Giao diện độc lập tương thích với thiết kế Dark Mode hiện tại, hỗ trợ combo box động tự nhảy Mã GV.
- **Sửa `dashboard.html`**: Thay thế thẻ `<a>` có href rỗng (`#`) bằng đường dẫn `/taotaikhoan` cho liên kết "Tạo Tài Khoản" trong menu của Nhóm PGV.
- **Cập nhật Logic UI Buttons**: 
  - Thêm logic vô hiệu hóa (làm mờ) nút "Tạo tài khoản" và "Xóa tài khoản" khi chưa chọn giảng viên.
  - Vô hiệu hóa nút "Tạo tài khoản" nếu GV đã có tài khoản.
  - Vô hiệu hóa nút "Xóa tài khoản" nếu GV đang có ràng buộc (đang được phân công dạy Lớp tín chỉ).
- **Cập nhật Backend chặn xóa tài khoản**: Thêm logic `SELECT TOP 1 1 FROM LOPTINCHI WHERE MAGV = ?` vào API `/taotaikhoan/delete` để chặn việc xóa nếu GV đang dạy Lớp tín chỉ, đảm bảo tính toàn vẹn dữ liệu.
