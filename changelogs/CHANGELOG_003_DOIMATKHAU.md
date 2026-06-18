# Thay Đổi Hệ Thống: Tính năng Đổi Mật Khẩu

## 1. Database (`setup_login.sql`)
- **Tạo SP_SV_DOIMATKHAU**: Bổ sung Stored Procedure để hỗ trợ riêng cho Sinh viên việc đổi mật khẩu. SP này nhận vào `MASV`, `OLDPASS`, `NEWPASS`, tiến hành đối chiếu `OLDPASS` để xác thực, nếu khớp sẽ thực thi lệnh `UPDATE SINHVIEN SET PASSWORD = @NEWPASS`.
- **Giảng viên**: Không tạo thêm SP vì tận dụng tính năng bảo mật native của hệ quản trị SQL Server (`ALTER LOGIN ... WITH PASSWORD ... OLD_PASSWORD`).

## 2. Backend (`app.py`)
- **Bổ sung API `/doimatkhau` (GET)**: Render giao diện trang đổi mật khẩu (`doimatkhau.html`).
- **Bổ sung API `/doimatkhau/submit` (POST)**:
  - Nếu `session['group'] == 'SV'`: Gọi thủ tục `SP_SV_DOIMATKHAU` để cập nhật mật khẩu trong Database.
  - Nếu `session['group']` là Giảng viên (`PGV`/`KHOA`): Sử dụng SQL Server Authentication để đối chiếu mật khẩu cũ và cấp lệnh đổi cấu hình đăng nhập trên cấp độ Server mà không can thiệp vào các Table.
- Đồng thời cập nhật lại Session lưu trữ nếu đổi thành công để tránh lỗi mất phiên.

## 3. Frontend
- **Tạo giao diện `doimatkhau.html`**: Form độc lập có thiết kế Dark Mode (mã màu #0a0a0a và #c01920) đồng bộ với các trang khác. Giao diện bao gồm ô Mật khẩu cũ, Mật khẩu mới, Xác nhận mật khẩu và có tính năng Bật/Tắt hiển thị ký tự (Icon Mắt).
- **Cập nhật Menu Dashboard (`dashboard.html`)**:
  - Gỡ bỏ liên kết chức năng chưa phát triển: "Báo Cáo Thống Kê" (đối với Giảng Viên) và "Thông Tin Học Phí" (đối với Sinh Viên).
  - Thay thế bằng liên kết "🔑 Đổi Mật Khẩu" ở tất cả các tài khoản.
