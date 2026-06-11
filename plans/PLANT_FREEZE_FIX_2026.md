# CHIẾN LƯỢC: SỬA LỖI ĐÓNG BĂNG ĐĂNG KÝ & CHUẨN HÓA UI

Tài liệu này chi tiết hóa cách thức hệ thống sẽ ngăn chặn triệt để các hành vi thay đổi dữ liệu lịch sử và sửa các lỗi giao diện còn tồn đọng.

## 1. Chốt chặn Đăng ký/Hủy lớp tín chỉ (Registration Guard)

Hiện tại, hệ thống mới chỉ đóng băng giao diện danh sách. Điều này dẫn đến việc sinh viên khóa cũ vẫn có thể thực hiện đăng ký hoặc hủy các lớp thuộc niên khóa lịch sử (VD: 2020-2021) thông qua mã hóa API.

- **Giải pháp**: 
    - Tại Backend (`app.py`), trong hai route xử lý đăng ký (`/dangky/dangky`) và hủy (`/dangky/huy`), hệ thống sẽ thực hiện truy vấn Niên khóa của lớp tín chỉ tương ứng.
    - Nếu Niên khóa < 2025, hệ thống sẽ trả ngay kết quả lỗi: **"Không thể thực hiện trên dữ liệu lịch sử đã bị đóng băng."**
    - Điều này đảm bảo tính "bất khả xâm phạm" của dữ liệu quá khứ.

## 2. Loại bỏ đóng băng Giảng viên
- Thực hiện theo yêu cầu: Giảng viên sẽ **không bị đóng băng**. Bạn có thể chỉnh sửa thông tin giảng viên bình thường.

---

## 3. Sửa lỗi Giao diện (UI Fixes)

### 3.1 Sửa lỗi Validation không sáng lại nút bấm
- **Lỗi**: Khi nhập mã trùng (VD: Mã lớp), hệ thống khóa nút (Đúng). Nhưng khi sửa lại cho đúng, nút vẫn mờ (Sai).
- **Khắc phục**: Cập nhật hàm `checkRealtime` trong `history.js`. Ngay khi nhận được phản hồi "Mã hợp lệ" từ Server, hệ thống sẽ tự động gọi `resetValidationState` để phục hồi các nút Sửa/Lưu ngay lập tức.

### 3.2 Tối ưu hóa hiệu ứng "Làm mờ" (Visual Clarity)
- Để tránh việc nút bấm bị khóa trông như đang sáng, tôi sẽ tăng độ mờ và hiệu ứng Grayscale:
  ```css
  .btn:disabled { 
      filter: grayscale(1) !important; 
      opacity: 0.4 !important; 
      cursor: not-allowed !important;
      pointer-events: none;
  }
  ```
- Đảm bảo khi chọn bản ghi lịch sử (có icon 🔒), toàn bộ các nút hành động đều mờ hẳn đi, không cho phép tương tác.

### 3.3 Rà soát trang Quản lý Lớp & Sinh viên
- Kiểm tra lại logic `chonDong` để đảm bảo khi click một lớp cũ, nút "Tạo mới" cũng phải mờ đi cùng các nút khác.

---

## 4. Kế hoạch xác minh (Test Cases)
1. **Đăng ký LTC**: Đăng nhập TK sinh viên khóa 2015 -> Thử tìm và đăng ký lớp năm 2020 -> Phải bị Backend báo lỗi.
2. **Hủy lớp**: Thử hủy một lớp đã học từ năm 2021 -> Phải bị Backend báo lỗi.
3. **Thanh hợp lệ**: Nhập mã trùng -> Nút mờ. Sửa mã -> Nút phải sáng lại ngay.
4. **Giảng viên**: Thử sửa thông tin 1 GV -> Hệ thống phải cho phép thực hiện.
