# Kế hoạch sửa hoàn tác, nhập điểm và tài khoản

## Mục tiêu
- Sửa lỗi hoàn tác báo thành công giả khi stored procedure trả `KETQUA <= 0`.
- Cho phép hoàn tác đúng thao tác mở lớp tín chỉ mới bằng cách xóa vật lý lớp tín chỉ nếu chưa có đăng ký.
- Cập nhật cây lịch sử để chặn hoàn tác cha khi còn thao tác con phụ thuộc, đặc biệt quan hệ giảng viên -> lớp tín chỉ.
- Đồng bộ kiểm tra điểm ở UI, route Flask và stored procedure: điểm CC là số nguyên 0-10, điểm GK/CK theo bước 0.5.
- Giảm lỗi dynamic SQL khi tạo/xóa login hoặc đổi mật khẩu với tên/mật khẩu có ký tự đặc biệt.

## Phạm vi
- Sửa `app.py`, `static/history.js`, `templates/nhapdiem.html`, `setup_login.sql`.
- Tạo/sửa stored procedure, không sửa dữ liệu mẫu đang có.
- Chưa thu hẹp toàn bộ `GRANT EXECUTE TO PUBLIC`; phần này cần một kế hoạch phân quyền riêng để tránh làm hỏng đăng nhập hiện tại.

## Cách làm
- `history/undo` chỉ xóa lịch sử sau khi SP trả thành công.
- Thêm `SP_HOANTAC_THEM_LOPTINCHI` trong `setup_login.sql`.
- Khi mở LTC, lưu thêm `magv`, `mamh`, `makhoa`, `nienkhoa`, `hocky`, `nhom` vào history để nhận diện phụ thuộc.
- Cập nhật validation điểm trên giao diện và server.
- Dùng `QUOTENAME` cho identifier trong SP tạo/xóa login; escape `]` khi đổi mật khẩu GV.
