# HDSD: Kiểm thử Vá Lỗi & Lịch Sử Thư Mục
## Case 1: Lỗi Giao Diện Disable Lì Lợm
1. Tại **Môn Học** (Hoặc Khoa, GV, Lớp): Bấm nút **"＋ Thêm"** (Mới).
2. Gõ thử Một Mã đã tồn tại (Ví dụ: `KTDH` nếu web có sẵn). 
3. Xem Nút **"Lưu Dữ Liệu"**! So với bản v1 (đỏ chót), thì bây giờ nó đã Xám Khịt và có hình con chuột gạch chéo (`Not Allowed`) chuyên nghiệp.
4. Ngay lúc nút đang màu xám, Bạn lấy chuột Click đúp thử vào dòng chữ Môn KTDH ở cái bảng ở dưới! Lập tức giao diện nhảy sang Mode Edit (Sửa). Chữ Lỗi lúc trước bay sạch bong, Nút Xám kia tự động Bừng Đỏ trở lại sẵn sàng cho bạn Ghi Đè! (Fix hoàn toàn lỗi kẹt Button).

## Case 2: Validation Số Tiết của Môn Học
1. Click **"Tạo Mới Môn Học"**.
2. Ở ô Tiết Thực Hành, thử gõ Số Âm (Ví dụ: `-5` hoặc `-11`). Viền Của Khung Input ngay lập tức Cháy Đỏ lên và Nút Ghi sẽ Bị Xám Khóa Cứng (Bệnh viện). Gõ Lại Thành `0` -> Khung bình thường lại.
3. Ở ô Tiết Lý Thuyết, gõ số `< 30` (Ví dụ 12). Khung Cửa Sổ Báo Động đỏ chét. Đổi Thành 30 trở lên -> Nút Xám Sáng Rực Chờ Lệnh Lưu. Quá tuyệt!

## Case 3: Block Folder Cây Undo
1. Trở ra Menu **Lớp**. Bấm Thêm 1 Lớp Bất Kỳ (Ví dụ ID `CLASS_TEST`).
2. Mở Tab qua bên cửa sổ **Sinh Viên**. Lúc này Menu Lớp đã có `CLASS_TEST`. Hãy bốc 1 em Sinh Viên mới nào đó tống giam vào Lớp này rồi Ghi Lại. Bạn thao tác liên tiếp 2 Lớp + SV vào.
3. Tại bất cứ cửa sổ nào, Bấm Vô Nút **Lịch Sử**.
4. Cây Gia Phả rớt xuống. Hãy để ý hình `├─ [Lớp] ... (Sinh viên)` nằm xép xép ngoan ngoãn chui vào nách thằng Lớp `CLASS_TEST` cực ngầu.
5. Bạn Trỏ tay thẳng vô Chữ `Hoàn Tác` của dòng Lớp Cha! Trình Duyệt Bật Ra Bảng Chữ Chửi Xối Xả: `"❌ Không thể Hoàn Tác Hành Động vì Có Nhánh Con bám vào. Yêu cầu Rút Chốt Mấy Đứa Nhánh Con Trái Bom Đó Rời Đi Trước Tiên"`. Rõ ràng tính năng Quản lý Database Constraits Rào Chắn này hoạt động tốt!
6. Bấm Hoàn Tác cái Thằng Sinh Viên Trái Bom Đó trước tiên thì Nó Chết. 
7. Giờ bấm Hoàn Tác Lên Thằng Lớp Một Lần Nữa -> Ngon Trớn Thành Công! Trang refresh mất tăm cả đám!
