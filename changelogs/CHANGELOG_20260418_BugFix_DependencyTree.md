# CHANGELOG: Dependencies Tree & Workflow Logic Hotfix

**Ngày cập nhật:** 2026-04-18
**Hạng mục:** Gỡ rối (Debug) và Chỉnh lý Workflow.

## Nội dung cập nhật
### 1. Phác thảo Màu Sắc "Disable" (Tất cả Module)
- Nút "Lưu dữ liệu" `[btn]` hiện giờ khi đã bị vô hiệu hóa sẽ sở hữu nền `#52525b` (Màu nhôm xám) thay vì trơ nguyên màu đỏ như phiên bản lỗi lúc trước.

### 2. Gỡ bỏ trói buộc Button khi Edit (Chế độ Sửa)
- **Vá Bug:** Hành vi click chuột chọn 1 hàng dưới bảng Data để xem/sửa giờ đây sẽ kích hoạt hàm phụ `resetValidationState(inputId)`.
- Hàm phụ này thay mặt bạn dọn sạch sẽ các câu từ cảnh cáo trùng lắp đỏ rực do viết sai trên màn hình lúc nãy, và Mở Xích (Enable) lại Nút `Lưu Dữ liệu` sẵn sàng nhập cuộc.

### 3. Constraints Validation trên Form Môn Học
- Bổ sung quy định theo Format Tiên Quyết: Tiết Lý thuyết phải `>= 30`, và Tiết Thực Hành `Không được Tồn tại Số Âm`.
- Mã Javascript sẽ gác cổng tự động theo Realtime (`oninput`). Nếu tay bạn lỡ đẩy số sai, hộp thoại text sẽ phủ màu Đỏ Cảnh Hình lên Form.

### 4. Thu Hồi Lịch Sử Liên Kết Thư Mục 
- Vứt bỏ chức năng Click 1 nút Xóa Nhiều Nút kiểu Stack Array (Vì nguy hiểm Constraint FK Database).
- Phục dựng lại Undo theo dạng Thư Mục Thực Thụ.
- Khi Click Nút "Lịch sử": Sẽ check xem có 1 Đối tượng Cha (VD Lớp) nào vừa đẻ 1 Đối Tượng Con Mới (VD Sinh viên) không? Lúc này SV sẽ lùi vào làm nhánh con trực tiếp của Lớp.
- Nếu bạn muốn "Hoàn tác Lớp": **Block Khóa Chặt 100% kèm Text Chặn Lỗi** yêu cầu rạch ròi phải làm sạch Lớp trước bằng cách Undo Thao Tác Chèn Con kia đi thì mới cho phép Trảm Cha. Rất chặt chẽ và an toàn!
