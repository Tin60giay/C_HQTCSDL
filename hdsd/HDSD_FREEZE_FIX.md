# HƯỚNG DẪN TEST: SỬA LỖI ĐÓNG BĂNG ĐĂNG KÝ & UI

Tài liệu này hướng dẫn các bước kiểm tra lại các lỗi đã được khắc phục liên quan đến dữ liệu lịch sử và giao diện.

## 1. Kiểm tra Chốt chặn Đăng ký lịch sử
- **Bước 1**: Đăng nhập tài khoản sinh viên (VD: khóa 2015).
- **Bước 2**: Tìm kiếm lớp tín chỉ thuộc năm học cũ (VD: 2020-2021).
- **Bước 3**: Thử bấm nút "Đăng ký" hoặc "Hủy đăng ký" (nếu đã có trong danh sách).
- **Kết quả mong đợi**: Hệ thống báo lỗi ngay tại màn hình: "Không thể đăng ký/hủy lớp thuộc niên khóa lịch sử". Hành động không được ghi vào DB.

## 2. Kiểm tra phục hồi Nút bấm (Real-time Validation)
- **Bước 1**: Vào mục Quản lý Lớp hoặc Sinh viên.
- **Bước 2**: Nhập một Mã đã tồn tại vào ô nhập mã.
- **Quan sát**: Các nút Sửa/Lưu/Xóa phải mờ đi và có thông báo mã trùng (Đúng).
- **Bước 3**: Sửa lại mã đó cho đúng (không trùng) hoặc xóa đi để nhập mã mới.
- **Kết quả mong đợi**: Ngay khi mã trở nên hợp lệ, các nút bấm phải tự động **sáng lại ngay lập tức** mà không cần reload trang hay bấm nút khác.

## 3. Kiểm tra độ hiển thị "Làm mờ" (Visuals)
- **Kịch bản**: Chọn một bản ghi có biểu tượng 🔒 (đã đóng băng).
- **Kết quả mong đợi**: Quan sát các nút chức năng trên toolbar. Chúng phải trông mờ rõ rệt (mờ hơn trước đây) và có màu xám đậm (grayscale). Bạn sẽ thấy rất rõ sự khác biệt giữa nút được dùng và nút bị khóa.

## 4. Kiểm tra Giảng viên
- **Kịch bản**: Vào mục Quản lý Giảng viên.
- **Thử nghiệm**: Sửa thông tin một giảng viên bất kỳ.
- **Kết quả mong đợi**: Hệ thống phải cho phép Lưu thành công, không bị chặn bởi bất kỳ logic đóng băng nào.
