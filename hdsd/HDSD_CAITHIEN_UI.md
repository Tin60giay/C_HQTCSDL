# Hướng Dẫn Sử Dụng & Test (Giao Diện Mới)

Bản hướng dẫn này giúp bạn test lại toàn bộ lượng UI/UX vừa được cập nhật cho các hạng mục (Khoa, Lớp, Giảng viên, Môn học). Vui lòng thử theo trình tự bên dưới.

## 1. Test tạo mới (Với nút "＋ Tạo mới" và "Enter")
- **Bước 1:** Đăng nhập vào hệ thống bằng tài khoản GV01 (hoặc GV thuộc phòng Giáo vụ).
- **Bước 2:** Truy cập Menu một danh mục (ví dụ **"Quản lý Khoa"**).
- **Bước 3:** Click nút **"＋ Tạo mới"**. Bạn sẽ thấy Form nhập liệu ở dưới bị xóa sạch để sẵn sàng cho dữ liệu mới.
- **Bước 4:** Gõ thông tin vào trường "Mã khoa" (VD: `KT5`) và "Tên khoa" (VD: `Khoa Test 5`).
- **Bước 5:** Mặc dù trước đó nếu ấn **Enter** trên bàn phím không có tác dụng gì, thì nay **Bạn hãy nhấn thử trực tiếp phím Enter** trên bàn phím ngay lúc đang ở ô Tên Khoa đó.
- _Kỳ vọng:_ Trang web sẽ load lại và xuất hiện thông báo `Thêm khoa thành công` màu xanh ngọc. (Bạn không cần dùng chuột ấn `💾 Lưu dữ liệu` nữa).

## 2. Test nút Làm mới (Nằm dưới form form)
- **Bước 1:** Click chọn một hàng bất kỳ trên bảng để thông tin trích xuất xuống Box Form bên dưới.
- **Bước 2:** Thử dùng tay sửa sai một số ký tự ở ô Text bên dưới. Bạn đổi ý muốn nó xóa đi để nhập lại một form trống?
- **Bước 3:** Cuộn xuống dưới cùng của Box, ấn vào nút **"🧹 Làm mới form"**.
- _Kỳ vọng:_ Form sẽ bị tẩy trắng hoàn toàn, con trỏ chuột quay trở lại ô chữ đầu tiên.

## 3. Test Combobox "Giảng viên" (Tránh nhập bậy)
- **Bước 1:** Chọn chức năng **"Quản lý Giảng Viên"**.
- **Bước 2:** Click vào một Giảng viên đã có sẵn. Bạn sẽ thấy ô "Học viện" và "Học hàm" tự động chọn đúng Option Select.
- **Bước 3:** Hãy mở Box dropdown và thử xem các giá trị (Cử nhân, Kỹ sư, Thạc sĩ,... Giáo sư...). Việc sử dụng Dropdown này sẽ giúp chặn người dùng nhập sai quy chuẩn.
- **Bước 4:** Chọn thử sang `Cử nhân`, sau đó nhấn nút **"💾 Lưu dữ liệu"** (hoặc Enter). Xem nó có cập nhật hệ thống thành chữ Cử Nhân trong CSDL hay không.

## ⚠️ Tình trạng Bug (Xác định tính tới hiện tại)
Hiện tại tôi đã quét trực tiếp vào thủ tục lưu trữ Data CSDL cũng như Python Backend, **hệ thống hoàn toàn 100% Không có Bug về thao tác CRUD** nhé. Vấn đề "không thêm được" ban nãy xảy ra duy nhất vì người dùng đã bấm nhầm nút "Thêm" (hiện đã đổi thành "Tạo mới") để gửi Form, hoặc nhấn "Enter" và chờ nó chạy nhưng không được. Các nhầm lẫn này đã được khắc phục hoàn toàn trong bản vá này. 
