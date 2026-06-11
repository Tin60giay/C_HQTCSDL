# CHANGELOG: Cải thiện Trải nghiệm Giao diện và Nhập liệu

**Ngày thực hiện:** 2026-04-18
**Tình trạng:** Đã hoàn thành

## 📋 Những thay đổi chính

### 1. Đồng bộ hóa Tên nút công cụ (Toolbar)
Tất cả các module (`khoa.html`, `lop.html`, `giangvien.html`, `monhoc.html`) đều đã được đổi thiết kế tên nút nhằm tránh tình trạng user nhầm lẫn thao tác:
- Nút **"＋ Thêm"** đổi thành **"＋ Tạo mới"**: Hành động này chỉ nhầm mục đích xóa trắng/reset form để sẵn sàng tiếp nhận thông tin mới, không gửi dữ liệu tới Backend.
- Nút **"💾 Ghi"** đổi thành **"💾 Lưu dữ liệu"**: Hành động này là hành động chốt và sẽ gửi dữ liệu về DB theo ID tương ứng.
- Đã đưa nút **"🧹 Làm mới form"** (trước đây là Xóa trắng) rời khỏi thanh công cụ và đưa xuống dưới đáy của bảng form nhập liệu. Mục đích giúp thao tác tiện lợi hơn khi đang gõ sai form và muốn xóa toàn bộ form.

### 2. Sự kiện nhấn phím Enter = Lưu Dữ Liệu
- Thêm logic Javascript vào sự kiện khi website được load (`DOMContentLoaded`) cho mọi thẻ `input` và `select` nằm trong phần nhập liệu `.form-grid`. 
- Nếu người dùng nhấn phím **Enter**, hệ thống sẽ tự động bắt lấy (`preventDefault`) và kích hoạt hành động gọi API **"Lưu dữ liệu"** xuống CSDL.

### 3. Thay Đổi Form Giảng Viên
Đã thay đổi 2 trường nhập nội dung cố định thành dạng Component **Select Box**, mục đích chỉ cho người dùng lựa chọn đúng danh sách có sẵn (tránh bị nhập bậy data rác vào hệ thống).
- **Học vị:** Thêm các Option `(Trống)`, `Cử nhân`, `Kỹ sư`, `Thạc sĩ`, `Tiến sĩ`.
- **Học hàm:** Thêm các Option `(Trống)`, `Phó giáo sư`, `Giáo sư`.
- Tinh chỉnh script hiển thị list data (Click vào hàng của table sẽ bind đúng giá trị `<option>` vào `<select>` tương ứng).
