# Hướng Dẫn Sử Dụng Chức Năng Tạo Tài Khoản

Chức năng Tạo Tài Khoản dùng để cấp quyền đăng nhập vào phần mềm quản lý điểm tín chỉ cho các giảng viên chưa có tài khoản. Tài khoản sau khi tạo sẽ được liên kết trực tiếp với Database SQL Server để phân quyền.

## 1. Yêu cầu quyền hạn
Chỉ các tài khoản thuộc nhóm quyền **PGV** (Phòng Giáo Vụ) mới có thể nhìn thấy nút chức năng và có quyền truy cập vào màn hình "Tạo Tài Khoản". Giảng viên khoa (KHOA) hoặc Sinh viên sẽ không thấy mục này.

## 2. Cách Tạo Tài Khoản
1. Tại màn hình Dashboard (Màn Hình Chính), nhấn vào ô **🔑 Tạo Tài Khoản** ở danh sách Menu Chức Năng.
2. Trên màn hình Tạo Tài Khoản:
   - **Họ tên nhân viên**: Chọn tên của Giảng viên mà bạn muốn cấp tài khoản. Hệ thống sẽ tự động điền `Mã NV` tương ứng vào ô bên cạnh.
   - **Tài khoản**: Nhập tên đăng nhập mong muốn (Không được chứa khoảng trắng hoặc ký tự đặc biệt lạ). Thông thường có thể đặt giống Mã NV.
   - **Mật mã**: Nhập mật khẩu.
   - **Nhóm quyền**:
     - `PGV`: Cấp quyền Quản lý của Phòng Giáo Vụ (Quản trị viên hệ thống).
     - `KHOA`: Cấp quyền Giảng viên thông thường (Chỉ được xem lớp tín chỉ, nhập điểm).
3. Nhấn nút **"Tạo tài khoản"** màu đỏ. Hệ thống sẽ báo xanh nếu tạo thành công, hoặc báo đỏ nếu Tên tài khoản đã tồn tại / Giảng viên này đã có tài khoản.

## 3. Cách Xóa Tài Khoản
Nếu bạn muốn thu hồi quyền truy cập của một giảng viên:
1. Tại màn hình Tạo Tài Khoản, chọn lại tên Giảng Viên đó.
2. Nếu Giảng viên đã có tài khoản, hệ thống sẽ tự động điền Tên đăng nhập và Nhóm quyền, đồng thời vô hiệu hóa (làm mờ) nút Tạo tài khoản.
3. Nhấn nút **"Xóa tài khoản"**. Hệ thống sẽ gỡ bỏ hoàn toàn quyền hạn và tài khoản đăng nhập của người đó ra khỏi Database.

**Lưu ý quan trọng (Ràng buộc dữ liệu):**
- Nút "Tạo tài khoản" và "Xóa tài khoản" sẽ bị làm mờ nếu bạn chưa chọn giảng viên.
- Bạn **KHÔNG THỂ** xóa tài khoản của những giảng viên đang được phân công dạy Lớp tín chỉ. Trong trường hợp này, nút "Xóa tài khoản" sẽ bị làm mờ để bảo vệ toàn vẹn dữ liệu, và hệ thống sẽ hiển thị thông báo lỗi màu đỏ.
