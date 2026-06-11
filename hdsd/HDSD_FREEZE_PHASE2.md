# HƯỚNG DẪN KIỂM THỬ GIAI ĐOẠN 2 (HDSD_FREEZE_PHASE2)
*Ngày cập nhật: 2026-04-19*

Để đảm bảo các lỗi đã được sửa triệt để, bạn hãy làm theo hướng dẫn dưới đây để kiểm tra quy trình sử dụng của Hệ thống Đóng băng (Phase 2):

## Các bước chuẩn bị quan trọng
1. **Chạy File SQL (Bắt buộc):**
   Bạn hãy mở SSMS (SQL Server Management Studio), chọn cơ sở dữ liệu `QUANLYDIEM_SV` và tiến hành chạy lệnh của file `setup_login.sql` để cập nhật lỗi liên quan đến Mở lại lớp vừa hủy.
2. Khởi động lại Server: Chạy lại `app.py`. 
3. Đăng nhập với tài khoản PGV (Ví dụ: `PGV01`) để test Quản trị và đăng nhập SV01 để test sinh viên.

---

## 🚀 Kịch bản 1: Kiểm thử khóa giao diện Form (Hard Lock)
1. Trong màn hình **Quản lý Lớp Cử Nhân**, bạn hãy tìm đến một lớp cũ (thuộc niên khóa ví dụ 2020-2024 hoặc <2025). 
2. **Kỳ vọng:** Khi chọn vào lớp học này, thông tin sẽ nhảy lên Form. Bạn sẽ thấy **TẤT CẢ** các ô nhập văn bản và Menu xổ xuống (Khoa) bị đổi thành giao diện nền xám, chữ chìm. Bạn **KHÔNG THỂ** chỉnh sửa (readonly) hay click thay đổi giá trị của bất kỳ box nào. Bấm ra ngoài hoặc bấm `Làm mới form` thì toàn bộ ô nhập sẽ mở khóa lại như cũ.
3. Test tương tự ở phần **Quản lý Sinh Viên**, **Quản lý Môn Học**, và **Mở Lớp Tín Chỉ**. Đảm bảo tất cả thông tin các khóa trước bị lock màn hình chuẩn xác.

## 🚀 Kịch bản 2: Kiểm thử Hỗ trợ mở Lớp và Tùy chỉnh Nút Thêm (Mới)
1. Ở chế độ Quản lý Lớp Cử nhân hoặc Môn học, khi mới vào trang (hoặc sau khi bấm chức năng Làm mới Form) thì **CHỈ CÓ NÚT TẠO MỚI** (Thêm) được làm điểm sáng, Nút **Lưu** sẽ bị bôi mờ đi.
2. Mở trình quản lý **Mở Lớp Tín Chỉ**:
    - **Test nút Tạo Ghi:** Thử nhập dữ liệu cho 1 lớp mới, và bấm **Tạo mới** -> Form sẽ lưu dữ liệu. Chọn lại vào một phần và tự mình bấm **Lưu thay đổi** (Lúc này nút Thêm sẽ tắt để không thể bấm nhầm 2 lần).
    - **Test tính năng Tự động Chọn Khoa Giảng Viên:** Hãy thử chọn vào Giảng viên (vd: `GV01` ở khoa Điện Tử). Bạn sẽ thấy cột `Khoa` ngay lập tức tự động Dropdown về `Điện Tử` đồng bộ. 

## 🚀 Kịch bản 3: Sửa Lỗi Giới Hạn SP Mở Lớp Tín Chỉ
1. Bạn hãy thử mở một lớp tín chỉ mới tinh cho môn "Thiết Kế Đồ Họa", kỳ 2, năm 2026, nhóm 1.
2. Sau khi Tạo xong, ngay lập tức bấm vào lệnh **Hủy Lớp**. (Lúc này lớp đã bị đưa cờ vào HUYLOP = 1).
3. Bây giờ bạn nhấn **Làm mới Form** và nhập **ĐÚNG Y CHANG** (Thiết kế đồ họa, kỳ 2, 2026, nhóm 1, cùng tất cả info khác kể cả giáo viên). Truy vấn **Tạo Mới**.
4. **Kỳ vọng:** Lớp tạo thành công, không còn bị báo Lỗi "Lớp đã tồn tại" cản trở (Lớp cũ vốn chỉ xem chứ không chạy nữa).

## 🚀 Kịch bản 4: Quyền Lợi Hiển Thị Trên Sinh Viên (Student View)
1. Sang tab khác Đăng xuất khỏi hệ thống và thử tài khoản Sinh Viên (Ví dụ: `N15DCCN001` - Khóa 2015).
2. Vào phần Đăng ký lớp tín chỉ, lọc Học Kỳ cũ vào năm 2020-2021 hoặc trước năm 2025. 
3. **Kỳ vọng:** Đối với cả cột Môn Học Hiển Thị Đăng Ký và Phía trên cột Môn Đã Chọn -> tất cả các dòng Class Data sẽ chuyển xám (`Grayscale` UI) đồng thời chuột gắn hình lệnh cấm / dấu gạch (`not-allowed`). Sinh viên không thể thao tác nút "Hủy" hoặc "Đăng ký" tại đây trực quan giao diện.
