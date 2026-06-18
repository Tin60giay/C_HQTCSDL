# Kế hoạch triển khai: Chức năng Tạo Tài Khoản Giảng Viên

Chức năng "Tạo tài khoản" sẽ cho phép cấp tài khoản đăng nhập SQL Server cho một giảng viên chưa có tài khoản, đồng thời gán Nhóm quyền (`PGV` hoặc `KHOA`).

> [!WARNING]
> **Yêu cầu review**:
> - Hệ thống hiện tại đang sử dụng danh sách `PGV_LOGINS` (cứng trong `app.py`) để phân quyền. Để hỗ trợ chọn "Nhóm quyền" động trên form mà không làm ảnh hưởng (hoặc sửa đổi) các cột của Database, tôi đề xuất tạo các Database Role trong SQL Server (`PGV` và `KHOA`). Tuy nhiên hệ thống login Python vẫn sẽ giữ tính tương thích ngược với `PGV_LOGINS`. Bạn có đồng ý hướng tiếp cận sử dụng Database Roles cho quyền hạn không?
> - Form trong ảnh minh họa có cả nút **"Xóa tài khoản"**. Hiện tại, tôi sẽ tập trung vào chức năng **Tạo tài khoản** bằng stored procedure. Nếu bạn cũng muốn thực hiện chức năng Xóa, tôi sẽ thêm procedure `SP_XOATAIKHOAN`. Bạn có muốn triển khai cả Xóa ngay lập tức không?

## Proposed Changes

### 1. Database (SQL Server / `setup_login.sql`)

Tôi sẽ nối thêm các SP và Role mới vào cuối file `setup_login.sql` để không phá vỡ cấu trúc cũ:
#### [MODIFY] [setup_login.sql](file:///f:/A_HQTCSDL/New/20042026/C_HQTCSDL/setup_login.sql)
- Thêm script tạo Database Roles nếu chưa có: `CREATE ROLE PGV`, `CREATE ROLE KHOA`.
- Thêm Procedure **`SP_TAOLOGIN`**:
  - Tham số: `@LGNAME`, `@PASS`, `@USERNAME`, `@ROLE`.
  - Logic: Kiểm tra trùng tên Đăng nhập/User. Nếu hợp lệ, gọi `CREATE LOGIN`, `CREATE USER`, cấp các quyền truy cập hệ thống cơ bản (`GRANT SELECT`, `GRANT EXECUTE` như cấu hình cũ), và gọi `sp_addrolemember` để đưa User vào Role được chọn.
- Thêm Procedure **`SP_XOALOGIN`** (nếu triển khai chức năng xóa):
  - Logic: Xóa User khỏi Database Role, xóa User khỏi Database và cuối cùng Drop Login.

---

### 2. Backend (Python)

#### [MODIFY] [app.py](file:///f:/A_HQTCSDL/New/20042026/C_HQTCSDL/app.py)
- **Cập nhật Logic Login (`/`)**: Khi login thành công, hệ thống sẽ truy vấn SQL (`sys.database_role_members`) để kiểm tra xem User có thuộc Role `PGV` hay `KHOA` không. Nếu không có (như các GV tạo bằng script cũ), nó vẫn sẽ dùng `PGV_LOGINS` array dự phòng để đảm bảo không lỗi.
- **Tạo Route `/taotaikhoan` (GET)**: Load danh sách Giảng Viên (`SP_GETALL_GIANGVIEN`). Render giao diện `taotaikhoan.html`.
- **Tạo Route `/taotaikhoan/submit` (POST)**: Nhận `LGNAME`, `PASS`, `USERNAME` (Mã GV), `ROLE`. Gọi `EXEC SP_TAOLOGIN`. Trả về JSON thành công hoặc mã lỗi (trùng tên đăng nhập/trùng user).

---

### 3. Frontend (HTML/JS)

#### [NEW] [taotaikhoan.html](file:///f:/A_HQTCSDL/New/20042026/C_HQTCSDL/templates/taotaikhoan.html)
- Xây dựng giao diện giống nguyên mẫu với các input:
  - **Họ tên nhân viên**: Thẻ `<select>` danh sách Giảng viên.
  - **Mã NV**: Thẻ `<input readonly>`. Tự động điền khi thay đổi Họ tên.
  - **Tài khoản**: Thẻ `<input type="text">`.
  - **Mật mã**: Thẻ `<input type="password">`.
  - **Nhóm quyền**: Thẻ `<select>` (PGV, KHOA).
- Viết JavaScript để xử lý API POST tạo mới tài khoản và hiển thị Alert theo phản hồi của Server.

#### [MODIFY] [dashboard.html](file:///f:/A_HQTCSDL/New/20042026/C_HQTCSDL/templates/dashboard.html)
- Bổ sung nút/link "Tạo tài khoản" trên thanh điều hướng sidebar (chỉ dành cho tài khoản có quyền ADMIN hoặc PGV được phép tạo tài khoản - tuy nhiên theo CSDLPT thường thì tài khoản thuộc nhóm nào sẽ chỉ được tạo tài khoản thuộc nhóm đó. Vui lòng làm rõ nếu có giới hạn quyền ai được tạo tk).

## Verification Plan

- Chạy script cập nhật trong SSMS cho `QLDSV_HTC`.
- Dùng tài khoản PGV hiện tại đăng nhập.
- Truy cập tính năng Tạo tài khoản, tạo 1 tài khoản GV mới với quyền KHOA.
- Đăng xuất, đăng nhập lại bằng tài khoản mới vừa tạo -> Kiểm tra xem Sidebar có giới hạn quyền ở mức KHOA đúng không.
- Thử tạo tài khoản bị trùng tên đăng nhập -> Đảm bảo Server bắt lỗi và không crash.
