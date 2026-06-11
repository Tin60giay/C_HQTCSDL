# HƯỚNG DẪN KIỂM THỬ: ĐÓNG BĂNG DỮ LIỆU & LOGIC UI 2026

Tài liệu này hướng dẫn bạn cách kiểm tra các tính năng đóng băng dữ liệu và các cải tiến về giao diện vừa được triển khai.

## 1. Kiểm tra tính năng Đóng băng (Data Freeze)

### Môn học (Subjects)
- **Kịch bản**: Tìm một môn học đã từng được dạy trong quá khứ (VD: Cấu trúc dữ liệu). 
- **Kết quả mong đợi**: 
    - Có icon 🔒 bên cạnh mã môn học.
    - Khi click vào dòng đó, các nút "Lưu dữ liệu" và "Xóa" phải bị mờ.
    - Ở ô nhập mã, sẽ có cảnh báo: "Dữ liệu lịch sử đã bị đóng băng".
- **Thử nghiệm**: Cố gắng đổi tên môn học này và bấm Lưu -> Giao diện phải chặn hoặc Backend phải báo lỗi.

### Sinh viên & Lớp (Students & Classes)
- **Kịch bản**: Vào mục Quản lý Lớp, tìm các lớp thuộc khóa học cũ (VD: Khóa 2021-2025).
- **Kết quả mong đợi**: Icon 🔒 xuất hiện. Không thể sửa Niên khóa hoặc Tên lớp.
- **Sinh viên**: Tương tự, sinh viên thuộc các lớp cũ sẽ không thể sửa thông tin cá nhân.

---

## 2. Kiểm tra bộ lọc Dropdown (Filters)
- **Kịch bản**: Mở trang Quản lý Lớp hoặc Lớp Tín Chỉ. Xem danh sách dropdown Niên khóa hoặc Khóa học.
- **Kết quả mong đợi**: Danh sách chỉ bắt đầu từ mốc **2025-2026** (đối với Niên khóa) hoặc **2025-2029** (đối với Khóa học). Các năm cũ (2015-2024) không còn xuất hiện để chọn khi tạo mới.

---

## 3. Kiểm tra Logic Nút bấm UI (UI Improvements)

### Chế độ khóa nút Tạo mới (Add Button Lock)
- **Bước 1**: Bấm vào một dòng bất kỳ trong bảng để chọn bản ghi.
- **Bước 2**: Quan sát nút **"＋ Tạo mới"**.
- **Kết quả**: Nút này phải bị mờ đi (disabled). Lúc này bạn chỉ có thể Cập nhật hoặc Xóa dòng hiện tại.
- **Bước 3**: Bấm nút **"🧹 Làm mới form"**.
- **Kết quả**: Nút "Tạo mới" phải sáng lại bình thường.

### Sửa lỗi Phục hồi nút sau khi lỗi (Validation Fix)
- **Bước 1**: Thử nhập một mã bản ghi trùng (VD: nhập Mã môn học đã tồn tại).
- **Bước 2**: Các nút sẽ bị mờ hết (Đúng).
- **Bước 3**: Xóa nội dung vừa nhập hoặc bấm "Làm mới form".
- **Kết quả**: Các nút phải được phục hồi trạng thái (sáng lại) ngay lập tức, không còn bị kẹt trạng thái mờ như trước.

---

## 4. Kiểm tra lịch sử Giảng viên
- **Kịch bản**: Sửa Khoa của một Giảng viên trong mục Quản lý Giảng viên. 
- **Bước 2**: Quay lại trang Lớp Tín Chỉ, xem một lớp cũ mà giảng viên đó từng dạy.
- **Kết quả**: Tên Khoa hiển thị tại lớp cũ đó phải là Khoa cũ (lúc mở lớp), không bị thay đổi theo Khoa hiện tại của giảng viên.
