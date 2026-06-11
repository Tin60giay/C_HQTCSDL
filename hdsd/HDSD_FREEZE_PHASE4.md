# HƯỚNG DẪN KIỂM THỬ QUY TRÌNH BAO BỌC RỦI RO & RÀNG BUỘC CSDL (HDSD_PHASE4)
*Ngày cập nhật: 2026-04-19*

Để đảm bảo các quy tắc Database mới (Dựa theo `CRITICAL.md`) được thực thi chính xác và giao diện Sinh Viên vận hành chuẩn chỉ, mời bạn thực hiện quy trình sau (BẮT BUỘC BẤM CTRL + F5 ĐỂ XÓA CACHE CHƯƠNG TRÌNH JS CŨ):

## 🚀 Kịch bản 1: Kiểm thử Nút "Làm Mới Form" và Nút "Tạo Mới" Sinh Viên
1. Đăng nhập vào phần Quản lý Sinh viên với tài khoản PGV.
2. Tại bảng Niên khóa, chọn một Lớp Cử Nhân thuộc năm **2015-2016** (Diện Cũ - Đã Đóng Băng).
3. **Kỳ vọng giao diện:** Nút bấm `＋ Tạo mới` sẽ mang bộ quần áo mờ tịt (Gray Scale) ngay từ đầu. Dù bạn có bấm vào đâu trên thanh Form hay Lịch sử, `Tạo Mới` VĨNH VIỄN KHÔNG ĐƯỢC MỞ KHÓA nếu bạn vẫn ở lớp này.
4. **Kỳ vọng với nút Làm Mới:** Bên cạnh sự ảm đạm của nút Tạo mới, nút *🧹 Làm mới form* nằm ở đuôi danh sách sẽ vẫn hiển thị bình thường. Bấm vào nút này để chắc chắn form vẫn bị xóa trắng bình thường (Vì nó vô hại với dữ liệu SQL).

## 🚀 Kịch bản 2: Vượt Giới Hạn Logic Số Liệu Form Mẫu
1. Vào phân khu mở **Môn Học** hoặc **Lớp tín chỉ**. 
2. Tạo mới một Lớp Tín Chỉ hoặc một Môn Học. Cố gắng giả lập việc thao tác số liệu vi phạm bảng luật lệ `CRITICAL.md`.
3. **Bài thi vi phạm 1:** Mục *Nhóm*, thay vì nhập `1`, bạn gõ phím Backspace xóa về `0`.
   - Ngay khoảnh khắc bạn thả tay khỏi phím (`input` sự kiện), ngay dưới hộp Nhóm sẽ thò ra đuôi Cảnh Báo màu đỏ: *❌ Nhóm môn học tối thiểu là 1.*
   - **HIỆU ỨNG LIÊN HOÀN:** Các nút chức năng trọng yếu (Tạo Mới / Ghi Nhận) sẽ bị sập nguồn (Hiệu ứng mờ đục và không cho Click) NGAY LẬP TỨC. 
4. **Bài thi vi phạm 2:** Sang khu Đăng Ký và Nhập Thử Mục *Điểm CK* vượt cao tầng `11`, bạn cũng sẽ bị ăn chặn Tương Tự với dòng chữ *❌ Điểm số cấu thành phải từ 0 - 10.*
5. **Kỳ vọng sửa sai:** Thử sửa `Nhóm` thành `2` trở lại. Lời cảnh báo sẽ bay màu, và **Các Nút Tạo Mới/Lưu sẽ đồng loạt bừng sáng lại ngay tắp lự.** Bảo vệ bạn hoàn hảo khỏi các chướng ngại dội Form.
