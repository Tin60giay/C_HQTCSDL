# NHẬT KÝ THAY ĐỔI (CHANGELOGS) - ĐÓNG BĂNG PHASE 4
*Ngày cập nhật: 2026-04-19*

## 🐛 Báo Cáo Tính Năng Mới & Khắc Phục Giao Diện
- **Mở Khóa Nút Làm Mới:** Hoàn trả lại khả năng click cho nút "🧹 Làm mới form" ở mục Quản lý Sinh viên trong các niên khóa bị đóng băng do tính năng này vốn độc lập và an toàn tuyệt đối với CSDL (Chỉ dọn dẹp các Form Value phía UI).
- **Tróc Nã Nút Tạo Mới Tận Gốc Lưới Hành Vi:** Sửa tận gốc file `history.js` bằng cách truyền Biến Cờ Môi Trường Cục Bộ `window.IS_FROZEN_CONTEXT`. Giờ đây, khi bạn bấm xem danh sách của một lớp cũ (như lớp 2015-2016), Trình quản lý trạng thái (`updateActionButtons`) sẽ quét biến số này, nếu là Đồ cổ, Nút Mở Thêm Mới sẽ bị CƯỠNG CHẾ KHÓA DÀI HẠN dù cho hàm có chạy vòng lặp kiểu gì đi chăng nữa.
- **Tiêu Chuẩn Ràng Buộc Cơ Sở Dữ Liệu Real-time (`CRITICAL.md`):** Tích hợp Validation ngầm vào thanh nghe sự kiện `input` trên toàn bộ các Textbox HTML. 
  - Thắt chặt Ranh giới dữ liệu cho các trường hợp: Nhóm Môn (`>= 1`), Học kỳ (`1`, `2`, `3`), Số Sinh Viên Tối Thiểu (`> 0`), Điểm CC/GK/CK (`0` - `10`).
  - **Hệ quả của Ràng buộc:** Khi bạn lỡ cấu hình sai chuẩn (VD: Nhập -3 vào số tiết TH), giao diện lập tức CÓ CẢNH BÁO ĐỎ TẠI CHUẨN Ô. Kê thêm vào đó là chức năng `Khóa Nhốt Cập Nhật Button` tàng hình, làm mờ đi cả dãy thao tác [Lưu], [Tạo mới] ngăn chặn hoàn toàn sai lầm đẩy thẳng dữ liệu rỗng về phía Server.
