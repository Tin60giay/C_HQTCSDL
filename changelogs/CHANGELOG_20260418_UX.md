# CHANGELOG: Advanced Realtime Validation & History Tree Undo

**Ngày cập nhật:** 2026-04-18
**Người thi hành:** AI Assistant
**Tình trạng:** Hoàn tất. Mọi logic Nghiệp vụ 6 Bước cốt lõi đều được bảo lưu 100%.

## Nội dung thay đổi
### 1. API Auto-Check Trùng Mã (Real-time Validation)
- Thêm Endpont `GET /api/check_exists` vào `app.py`.
- Tích hợp JS `checkRealtime(inputId, typeStr)` vào 5 Layout form chính: Sinh Viên, Giảng Viên, Lớp, Môn Học, Khoa.
- **Tiêu chuẩn UX:** Nếu đang trong chế độ Nhập (Readonly = false), mỗi khi gõ từ bàn phím, hệ thống delay 500ms để kiểm tra dưới Database.
- Khi phát hiện trùng: Chữ mác báo đỏ xuất hiện *"❌ Mã này đã tồn tại!"* và hệ thống sẽ đóng băng (Disable) nút Ghi/Lưu tránh user gửi form rác.

### 2. Multi-Undo Tree Stack (Như Microsoft Word)
- Viết lại toàn bộ hàm `openHistory` trong file `static/history.js`.
- Bổ sung Logic định dạng dạng cây `├─ ` với các nhóm Sinh Viên, giúp mắt người dùng dễ phân biệt cấp bậc Cha - Con so với Lớp hay Khoa.
- Khi Hover chuột vào Action thứ $N$, toàn bộ nền thẻ từ mục $1 \dots N$ được phủ Bôi Đỏ.
- Click chuột một cái, `app.py` sẽ thực thi lệnh trượt (Loop API `POST /history/undo` liên tiếp $N$ lần vào móc trên cùng) giúp thu hồi cùng lúc nhiều thao tác y hệt Undo ở Microsoft Word.
