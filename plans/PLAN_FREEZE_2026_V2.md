# CHIẾN LƯỢC: ĐÓNG BĂNG DỮ LIỆU 2026 & CHUẨN HÓA UI

Tài liệu này chi tiết hóa cách thức hệ thống sẽ bảo vệ dữ liệu cũ và tối ưu hóa luồng tương tác của người dùng.

## 1. Nguyên tắc Đóng băng (Historical Freeze)

Hệ thống xác định mốc thời gian an toàn là Niên khóa **2025-2026**.

### 1.1 Môn học (Subjects)
- **Ràng buộc**: Môn học nào đã được sử dụng để mở lớp tín chỉ trong quá khứ (trước niên khóa 2025) sẽ bị đóng băng hồ sơ.
- **Tại sao?**: Để đảm bảo tính toàn vẹn của bằng cấp và bảng điểm của các sinh viên khóa cũ. Nếu sửa tên môn học cũ, bảng điểm của sinh viên đã tốt nghiệp có thể bị sai lệch.
- **Giải pháp**: Nếu cần thay đổi nội dung môn học cho khóa mới, hãy tạo một mã môn học mới.

### 1.2 Sinh viên & Lớp (Students & Cohorts)
- **Ràng buộc**: Tất cả sinh viên thuộc các lớp mà khóa học bắt đầu trước 2025 (VD: 2021-2025) sẽ ở trạng thái Read-only.
- **Thao tác**: Không cho phép Sửa thông tin cá nhân hoặc Xóa khỏi hệ thống.

### 1.3 Giảng viên (Teachers)
- **Đặc trưng**: Giảng viên được phép sửa thông tin bình thường.
- **Bảo toàn lịch sử**: Khi một giảng viên chuyển khoa, thông tin tại các lớp tín chỉ cũ họ đã dạy vẫn sẽ hiển thị đúng Khoa của lớp đó tại thời điểm đó (do DB lưu `MAKHOA` tại từng lớp tín chỉ).

---

## 2. Chuẩn hóa Giao diện (UI Standardization)

### 2.1 Khắc phục lỗi khóa nút (Bug Fix)
- **Hiện tượng**: Khi nhập mã trùng, các nút bị mờ nhưng không sáng lại khi xóa nội dung lỗi.
- **Giải pháp**: Cập nhật hàm `resetValidationState` trong `history.js` để trả các nút về trạng thái hoạt động bình thường ngay khi lỗi được xử lý hoặc khi bấm "Làm mới form".

### 2.2 Chế độ Chọn dòng (Selection Mode)
- **Yêu cầu**: Khi người dùng click chọn một dòng trong bảng (để Xem/Sửa/Xóa):
    1. Điền dữ liệu vào form.
    2. Vô hiệu hóa nút **"Tạo mới"** (vì form đang chứa dữ liệu cũ, chỉ được phép Cập nhật hoặc Xóa).
    3. Nút "Tạo mới" chỉ được bật lại sau khi người dùng bấm **"Làm mới form"** (xóa trắng các trường nhập liệu).

---

## 3. Cập nhật Bộ lọc Dropdown
- Danh sách Niên khóa (LTC, Đăng ký) bắt đầu từ: **2025-2026**.
- Danh sách Khóa học (Lớp) bắt đầu từ: **2025-2029**.

---

## 4. Kế hoạch xác minh
1. **Kiểm tra Môn học**: Thử sửa 1 môn học từng được dạy năm 2024 -> Phải bị chặn.
2. **Kiểm tra UI**: 
   - Click chọn 1 sinh viên -> Nút "Tạo mới" phải mờ đi.
   - Nhập mã SV trùng -> All buttons mờ -> Xóa đi -> All buttons phải sáng lại.
3. **Kiểm tra Dropdown**: Mở màn hình đăng ký LTC -> Năm học đầu tiên phải là 2025-2026.
