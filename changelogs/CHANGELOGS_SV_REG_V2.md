# CHANGELOG: Đăng ký LTC v2 & Chuẩn hóa Ràng buộc UI Toàn cục

**Ngày:** 2026-04-18  
**Phiên bản:** v2.0  
**Liên quan:** Nâng cấp trải nghiệm đăng ký cho SV và bảo mật UI.

---

## 1. Module Đăng ký Lớp Tín Chỉ (Sinh viên)

### Ràng buộc nghiệp vụ mới
- **Quy tắc 1 môn / 1 lớp**: Sinh viên chỉ được đăng ký tối đa một lớp cho mỗi môn học trong cùng một học kỳ.
- **Tự động làm mờ (Gray-out)**: Khi đã đăng ký một lớp của môn X, tất cả các nút "Đăng ký" của các lớp khác cùng môn X sẽ bị vô hiệu hóa kèm thông báo giải thích.
- **Hủy đăng ký**: Thay thế Badge tĩnh bằng nút **"Hủy đăng ký"** (màu xanh lá). Sinh viên có thể rút tên khỏi lớp nếu chưa có đầu điểm.

### Cải tiến giao diện
- **Danh sách môn đã chọn**: Thêm một phân mục riêng biệt phía trên kết quả tìm kiếm, hiển thị tóm tắt các môn học đã đăng ký thành công.
- **Xác nhận thao tác**: Bổ sung hộp thoại xác nhận (Confirm) cho cả hành động Đăng ký và Hủy đăng ký để tránh nhầm lẫn.
- **Phản hồi thời gian thực**: Khi thực hiện thao tác, toàn bộ nút chức năng sẽ tạm thời bị khóa để tránh spam request.

---

## 2. Chuẩn hóa Ràng buộc UI Toàn cục (Toàn hệ thống)

### Cơ chế Khóa an toàn (Strict Lock)
- **Vấn đề**: Trước đây khi có lỗi validation (nhập mã trùng, sai định dạng), chỉ nút "Lưu" bị khóa, người dùng vẫn có thể bấm "Tạo mới" hoặc "Xóa" gây lỗi hệ thống.
- **Giải pháp**: Cập nhật `static/history.js`. Bây giờ, khi phát hiện bất kỳ lỗi ràng buộc dữ liệu nào:
    - **Vô hiệu hóa toàn bộ**: Nút "Tạo mới", "Lưu dữ liệu", "Xóa", "Phục hồi" đều bị làm mờ.
    - **Ngoại lệ**: Nút **"🧹 Làm mới form"** luôn được giữ nguyên để sinh viên/giáo vụ có thể xóa trắng dữ liệu và bắt đầu lại.

---

## 3. Thay đổi kỹ thuật (Backend & SQL)

- **SQL**: 
    - Cập nhật `SP_DANGKY_LTC` (v3): Thêm logic check trùng `MAMH` ở mức database.
    - Bổ sung `SP_HUY_DANGKY`: Xử lý logic rút tên (ngăn hủy nếu đã có điểm).
- **Backend (app.py)**: 
    - Thêm route `@app.route('/dangky/huy')` xử lý gọi SP hủy.
