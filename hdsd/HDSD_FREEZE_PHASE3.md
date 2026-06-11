# HƯỚNG DẪN KIỂM THỬ QUY TRÌNH BAO BỌC RỦI RO (HDSD_PHASE3)
*Ngày cập nhật: 2026-04-19*

Để đảm bảo các lỗi nguy hiểm vừa tìm được không còn tái phát, xin hãy làm đúng theo các bài kiểm tra thực tế (Regression Test) dưới đây:

## TRƯỚC TIÊN BẠN PHẢI CHẠY LẠI SQL
**Do hệ CSDL có thay đổi lớn bên trong quy trình Mở Lớp**, hãy truy cập Microsoft SQL Server Management Studio (SSMS), kéo thả toàn bộ tệp `setup_login.sql` vào màn hình chạy query, bôi đen tất cả (Ctrl+A), và nhấn Execute (F5). Khởi động lại trang web.

---

## 🚀 Kịch bản 1: Kiểm thử Data Bảng Sinh Viên và Form Ngày Sinh
1. Đăng nhập vào Quản lý Sinh viên (Tài khoản PGV). 
2. **Kỳ vọng giao diện:** Cột `Ngày Sinh` và `Địa chỉ` sẽ được chuyển về đúng trật tự. Giới tính `1` giờ sẽ hiện là `Nữ`, `0` hiện là `Nam`. 
3. Thử click thẳng vào một lớp thuộc Năm Học 2015-2016 (Đóng băng).
4. **Kỳ vọng Tính Năng:** Tại Khu vực Nhập Form bên dưới, hộp Ngày Sinh `fNGAY` đã bị bôi viền xám đen, và `disabled` không bấm vào phần chọn lịch (Calendar) được nữa. (Trước đó nó đã bị lọt lưới).

## 🚀 Kịch bản 2: Kiểm thử Hack Xuyên Thời Gian (Tạo mới ở lớp đóng băng)
1. Trong mục Quản lý Lớp hoặc Sinh Viên: Bấm chọn vào Lớp `N15DCCN1` (Niên khóa 2015 - Đóng Băng). 
2. **Kỳ vọng Tính Năng Nút Bấm:** Hãy nhìn xuống Toolbar bên dưới - nút `Tạo Mới` (Thêm) đã bị phai viền thành màu xám và **không thể nhận Click**. (Bảo vệ phía UI Frontend).
3. **Kỳ vọng Backend (Dev):** Dù cho ai đó dùng Postman cố tình ép lệnh HTTP POST gửi danh sách sinh viên lên API `/sinhvien/them` vào mã lớp này thì Backend sẽ báo thẻ rỗng (False) kèm "Lỗi: Không thể thêm vào kỳ đóng băng". (Bảo vệ phía Backend).

## 🚀 Kịch bản 3: Sửa lỗi Unique Constraint Lớp Tín Chỉ đã Hủy
1. Vào Quản lý Lớp Tín Chỉ. Chọn năm học mở mạng là **2025-2026**, **Kỳ 2**.
2. Hãy **Tạo Mới** một lớp: Chọn môn *CTDL và Giải thuật*, Nhóm 3. Điền thông tin GV, v.v..
3. Tạo xong, lớp mới xuất hiện. Click chọn vào lớp đó -> Nhấn **🚫 Hủy lớp**. 
4. Xác nhận Hủy thành công (Form reset).
5. Ngay bây giờ, bạn hãy điền lại **Y CHANG** Thông tin: Môn *CTDL và Giải thuật*, Nhóm 3 (Cùng GV, số SV,...). Tiếp tục nhấn **Tạo Mới**.
6. **Kỳ vọng Database:** Bạn sẽ thấy lệnh Tạo mới **Chạy Thành Công**. SP SQL sẽ phát hiện thông tin bạn cung cấp trùng với thông tin của một dữ liệu "Đã Hủy Tạm Thời", và thay vì cố bóp chèn lên Unique Key (Sinh ra lỗi 2627), SQL Tự động chạy lệnh Update mở khóa `HUYLOP = 0` tái sử dụng nó.
7. Bạn cũng **vẫn có thể** Click vào nó và Hủy lại lần 2 bình thường, do nó không hề rơi vào khóa thời không (2025 > 2024).
