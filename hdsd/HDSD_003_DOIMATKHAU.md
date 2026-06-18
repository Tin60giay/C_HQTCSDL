# Hướng Dẫn Sử Dụng Tính Năng Đổi Mật Khẩu

Tính năng Đổi mật khẩu giúp nâng cao tính bảo mật cá nhân. Tất cả các vai trò (Quản trị viên PGV, Giảng viên KHOA, và Sinh viên SV) đều có quyền tự thay đổi mật khẩu của chính mình thông qua giao diện hệ thống.

## 1. Truy cập chức năng
Tại màn hình Menu chức năng (Dashboard), bạn bấm vào ô **🔑 Đổi Mật Khẩu**. Hệ thống sẽ chuyển bạn đến giao diện cập nhật bảo mật.

## 2. Cách thức hoạt động
Để đảm bảo người lạ không tự ý đổi mật khẩu khi bạn treo máy, hệ thống yêu cầu xác thực 3 bước nghiêm ngặt:
- **Mật khẩu hiện tại:** Nhập chính xác mật khẩu bạn đang dùng để đăng nhập.
- **Mật khẩu mới:** Nhập mật khẩu bạn muốn đổi.
- **Nhập lại mật khẩu mới:** Đảm bảo phải khớp hoàn toàn với ô Mật khẩu mới để tránh việc bạn bị gõ nhầm (sai chính tả/caplock).

## 3. Các tính năng hỗ trợ
- **Icon Con mắt 👁️:** Khi bạn nhấp chuột vào biểu tượng con mắt ở cuối mỗi ô nhập, hệ thống sẽ hiển thị các dấu `*` thành chữ để bạn dễ dàng kiểm tra xem mình có đang gõ sai mật khẩu hay không.
- **Chuyển hướng tự động:** Khi bạn nhấn "Xác nhận đổi" và hệ thống thông báo "Đổi mật khẩu thành công", phần mềm sẽ tự động đưa bạn về màn hình Dashboard sau 1.5 giây mà không làm gián đoạn (văng) phiên đăng nhập hiện tại.

## LƯU Ý
- Mật khẩu phân biệt rõ chữ hoa và chữ thường.
- Nếu là Giảng Viên, mật khẩu mới của bạn sẽ được ghi thẳng vào Hệ thống bảo mật lõi của SQL Server chứ không nằm trong bảng cơ sở dữ liệu như Sinh Viên. Nếu lỡ quên mật khẩu, hãy nhờ Phòng Giáo Vụ xóa tài khoản và tạo lại tài khoản mới (tất nhiên là với điều kiện tài khoản đó đang không bị ràng buộc tiết dạy).
