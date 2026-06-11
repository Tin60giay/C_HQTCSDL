# NHẬT KÝ THAY ĐỔI (CHANGELOGS) - ĐÓNG BĂNG PHASE 2
*Ngày cập nhật: 2026-04-19*

## 🚀 Tính năng mới (New Features)
- **Hard Lock Form (Khóa cứng Form):** Thêm tính năng tự động khóa (Disable và Readonly) đối với toàn bộ các ô nhập (TextBox, ComboBox) ở trang Quản lý Lớp, Sinh Viên, Môn Học, Lớp tín chỉ khi người dùng click vào một bản ghi thuộc diện đóng băng (niên khóa < 2025). Gắn cờ xám để phân biệt trạng thái xem dữ liệu.
- **Auto-select Khoa cho Giảng viên:** Cập nhật trang Mở lớp tín chỉ để trường "Khoa" tự động update giá trị tương ứng với Khoa của "Giảng viên" vừa được chọn.

## 🐛 Sửa lỗi (Bug Fixes)
- **Sửa Lỗi Add/Edit bị kẹt nhau (UI Logic):** Sửa lỗi trong `history.js` khiến người dùng không thể tạo dữ liệu mới do nút "Tạo mới" luôn bị làm mờ và "Lưu đổi" luôn tự động bật. Logic mới tách bạch hoàn toàn chức năng Thêm mới (khi Làm mới form) và Ghi (khi Chọn dòng).
- **Sửa lỗi Trùng Lớp khi Hủy Lớp:** Thay đổi `SP_THEM_LOPTINCHI` trong `setup_login.sql` chặn lỗi "Lớp tín chỉ đã tồn tại" khi người dùng cố mở lại lớp tín chỉ đã lưu trước đây nhưng trạng thái bị hủy (`HUYLOP=1`). 
- **Đóng băng Form Đăng ký Tín Chỉ Sinh Viên:** Hiển thị vô hiệu hóa hoàn toàn đối với các phím bấm chức năng "Hủy đăng ký" và "Đăng ký" của các lớp tín chỉ thuộc niên khoa < 2025.

## 🛠 Thay đổi kỹ thuật (Technical Changes)
- **Cập nhật `history.js`**: Bổ sung hàm `toggleFormLock` và tái cấu trúc `updateActionButtons` lấy trạng thái từ `window.sel` thay vì `dataset.formActive`.
- **Cập nhật `app.py`**: Truyền `IS_FROZEN: is_frozen(...)` xuống template của route `/lop`, `/sinhvien/<malop>`, và route JSON `/dangky/loc` để frontend có cờ kiểm tra đóng băng.
- **Cập nhật Giao diện**: Gắn hàm `toggleFormLock` vào hàm `chonDong` trong `lop.html`, `sinhvien.html`, `monhoc.html`, `loptinchi.html`. Sắp xếp lại HTML Nút bấm và bổ sung Attribute mới (`data-khoa`) vào options giảng viên của trang `loptinchi.html`. Tùy chỉnh Disable Button hiển thị ở HTML trang `dangky.html`.
