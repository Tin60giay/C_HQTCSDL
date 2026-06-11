# CHANGELOG: Đóng Băng Dữ Liệu 2026 & Hoàn Thiện UI

Tài liệu này ghi nhận các thay đổi quan trọng để chuyển đổi hệ thống sang chu kỳ 2026 và cải thiện trải nghiệm người dùng.

## 1. Hệ thống Đóng băng Dữ liệu (Historical Freeze)

### Cơ chế kỹ thuật
- **Backend (`app.py`)**: 
    - Bổ sung hàm `is_frozen(year_str)` để nhận diện dữ liệu trước năm 2025.
    - Cập nhật logic `get_nienkhoa_list` và `get_khoahoc_list` để chỉ sinh năm từ 2025 trở đi.
    - Thêm các chốt chặn (guards) tại các route UPDATE và DELETE. Nếu dữ liệu thuộc diện đóng băng, hệ thống sẽ trả về lỗi `flash` và chặn ghi vào DB.
- **SQL (`setup_login.sql`)**: 
    - Thêm `SP_CHECK_MONHOC_HISTORY` để kiểm tra lịch sử giảng dạy của môn học.

### Quy tắc nghiệp vụ mới
- **Sinh viên & Lớp**: Khóa toàn bộ các bản ghi thuộc niên khóa < 2025.
- **Môn học**: Khóa các môn học đã từng xuất hiện trong danh sách Lớp tín chỉ của các năm trước 2025.
- **Giảng viên**: Giữ nguyên khả năng chỉnh sửa, nhưng dữ liệu quá khứ vẫn bảo toàn tên Khoa cũ thông qua cột `MAKHOA` trong bảng `LOPTINCHI`.

---

## 2. Cải thiện Logic Giao diện (UI Standardization)

### Sửa lỗi Logic Nút bấm (`static/history.js`)
- **Khóa nút Tạo mới (Add Button Lock)**: Khi người dùng click chọn một dòng trong bảng, nút "Tạo mới" sẽ bị disabled. Điều này ngăn chặn việc vô tình thêm trùng hoặc nhầm lẫn giữa Sửa và Thêm.
- **Phục hồi trạng thái (Button Restore)**: Sửa lỗi các nút không sáng lại sau khi người dùng đã xóa nội dung vi phạm ràng buộc (VD: xóa mã trùng).
- **Làm mới form**: Nút "Làm mới form" giờ đây sẽ đặt lại toàn bộ trạng thái UI về `idle`, mở lại nút "Tạo mới".

### Hiển thị trực quan
- **Biểu tượng khóa (🔒)**: Hiển thị bên cạnh các mã bản ghi bị đóng băng để người dùng dễ dàng nhận biết.
- **Hiệu ứng dòng (Frozen row)**: Các dòng dữ liệu cũ sẽ có màu chữ mờ hơn và nền tối hơn.

---

## 3. Các tệp tin bị thay đổi
- `app.py`: Cập nhật logic backend và guards.
- `setup_login.sql`: Thêm SP bổ trợ.
- `static/history.js`: Sửa lỗi điều phối trạng thái nút.
- `templates/monhoc.html`, `templates/lop.html`, `templates/sinhvien.html`, `templates/loptinchi.html`: Cập nhật UI và logic chọn dòng.
