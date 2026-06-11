# Kế hoạch Cải thiện UI/UX & Nhập liệu (PLAN_CAITHIEN_UI)

Mục tiêu của kế hoạch này là khắc phục các điểm bất cập trong trải nghiệm người dùng (UX) hiện tại, ngăn tình trạng người dùng nhầm lẫn giữa nút thao tác và tránh nhập liệu rác vào Database.

## Proposed Changes

### 1. Nâng cấp Logic Nhập liệu chung (Áp dụng cho Khoa, Lớp, Giảng viên, Môn học, v.v.)
- Đổi tên các nút để rõ ràng ngữ nghĩa:
    - Nút "Thêm" đổi thành **"＋ Tạo mới"** (Chỉ clear form, sẵn sàng nhận dữ liệu mới).
    - Nút "Ghi" đổi thành **"💾 Lưu dữ liệu"** (Hành động gọi API để lưu vào DB).
- Chức năng phím `Enter`:
    - Ở tất cả các ô nhập trong thẻ form, khi người dùng gõ xong và nhấn phím **Enter**, hệ thống sẽ tự động bắt sự kiện và gọi hàm `ghiDulieu()` để lưu dòng hiện tại.
- Vị trí nút "Làm mới":
    - Di chuyển nút **"🧹 Làm mới form"** (Xóa trắng) rời khỏi thanh công cụ (Toolbar) phía trên, đưa xuống dưới cùng của hộp nhập liệu (Form Card bên dưới). Nhờ đó, người dùng đang nhập bị sai có thể thuận tay click "Làm mới form" ngay dưới chỗ gõ chữ.

---

### 2. Sửa Thông tin nhập Giảng Viên
- Ở mục "Học vị", chuyển từ biến thẻ nhập `input` thành `select` dropdown, với các giá trị:
  - `(Trống)`
  - `Cử nhân`
  - `Kỹ sư`
  - `Thạc sĩ`
  - `Tiến sĩ`
- Ở mục "Học hàm", chuyển từ thẻ `input` thành `select` dropdown, với các giá trị:
  - `(Trống)`
  - `Phó giáo sư`
  - `Giáo sư`
- Thay đổi hàm đưa dữ liệu cũ từ bảng vào form để map chính xác với `<select>` thay vì text box.
