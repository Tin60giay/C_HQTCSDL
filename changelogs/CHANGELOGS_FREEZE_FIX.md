# CHANGELOG: Sửa Lỗi Đóng Băng Đăng Ký & Hoàn Thiện Giao Diện

Bản cập nhật này tập trung vào việc vá các lỗ hổng bảo mật về dữ liệu lịch sử và sửa các lỗi trải nghiệm người dùng (UX) vừa phát hiện.

## 1. Bảo mật Backend (Chặn thao tác trên dữ liệu cũ)
- **Đăng ký & Hủy lớp**: Đã chèn logic kiểm tra Niên khóa vào route `/dangky/dangky` và `/dangky/huy`. Hệ thống sẽ chặn đứng mọi nỗ lực đăng ký hoặc hủy lớp thuộc các niên khóa trước **2025**.
- **Thông báo**: Khi vi phạm, sinh viên sẽ nhận được thông báo rõ ràng: "Không thể thực hiện trên niên khóa lịch sử."

## 2. Sửa lỗi Logic Giao diện (UI Fixes)
- **Phục hồi Validation**: Sửa lỗi nút Sửa/Lưu bị kẹt trạng thái mờ sau khi người dùng đã sửa Mã trùng thành mã hợp lệ. Hiện tại, trạng thái nút sẽ được khôi phục ngay lập tức trong thời gian thực.
- **Thoát đóng băng Giảng viên**: Đã xác nhận và đảm bảo không có bất kỳ hạn chế nào đối với việc chỉnh sửa hồ sơ Giảng viên.

## 3. Nâng cấp Hiển thị trực quan
- **Nút bấm Đóng băng**: Cập nhật CSS toàn cục để các nút bị `disabled` (do dữ liệu cũ hoặc lỗi) sẽ tự động kích hoạt hiệu ứng **Grayscale (xám)** và **Opacity 0.4**. Điều này giúp phân biệt rõ rệt giữa nút đang hoạt động và nút bị khóa.
- **Pointer Events**: Các nút bị khóa hiện tại sẽ không nhận bất kỳ tương tác chuột nào, đảm bảo tính an toàn tuyệt đối.

---

## Các tệp tin đã cập nhật
- `app.py`: Thêm chốt chặn bảo mật cho đăng ký/hủy.
- `static/history.js`: Sửa lỗi phục hồi nút và bổ sung CSS làm mờ toàn cục.
