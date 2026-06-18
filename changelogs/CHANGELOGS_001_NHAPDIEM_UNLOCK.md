# CHANGELOGS: Fix Form Unlock & Add NhapDiem Filters

## 1. Fix Form Unlock (monhoc.html, lop.html, sinhvien.html)
- **Lý do**: Khi click vào một dòng lịch sử bị đóng băng (frozen), form nhập liệu bị khóa lại. Tuy nhiên, khi bấm nút "Làm mới form" (xoaTrang), hàm JavaScript chỉ mở khóa ô nhập liệu khóa chính (Mã) mà không mở khóa các ô nhập liệu khác.
- **Giải pháp**: Đã bổ sung hàm `toggleFormLock(false, [...danh_sach_id])` vào bên trong hàm `xoaTrang()` tại các file `monhoc.html`, `lop.html`, và `sinhvien.html` để đảm bảo toàn bộ form được mở khóa khi người dùng muốn nhập mới.

## 2. Nâng cấp bộ lọc Nhập Điểm (nhapdiem.html, app.py)
- **Lý do**: Giảng viên cần biết môn học/học kỳ nào đang có lớp thực tế để tiện việc nhập điểm, tránh phải chọn mò các môn không có sinh viên. Đồng thời muốn nhìn thấy thông tin tên giảng viên ở phần chọn Nhóm.
- **Giải pháp**:
  - Tại `app.py`, chỉnh sửa logic của hàm `nhapdiem()` để truy vấn danh sách các lớp tín chỉ thực sự có tồn tại (không bị hủy và có sinh viên đăng ký). Truy vấn kết hợp bảng `LOPTINCHI`, `DANGKY` và `GIANGVIEN` để lấy các thông tin: NIENKHOA, HOCKY, MAMH, NHOM, HO, TEN.
  - Danh sách này được truyền xuống frontend dưới dạng chuỗi JSON `ltc_active_json`.
  - Tại `nhapdiem.html`, thay đổi giao diện bộ lọc Niên khóa, Nhóm thành dạng Combo box (`<select>`).
  - Cập nhật hàm JavaScript `capNhatBoLoc()`:
    - Các dropdown Học kỳ và Môn học: Nếu giá trị nào đang có lớp thực tế (khớp với tổ hợp Niên khóa đang chọn) thì sẽ được highlight màu xanh lá.
    - Các dropdown Niên Khóa và Nhóm: Được tự động lọc chỉ để lại các giá trị có lớp thực tế.
    - Tại mục Nhóm, tự động bổ sung hiển thị tên Giảng viên phụ trách, ví dụ: `1 (GV: Nguyễn Văn A)`.
