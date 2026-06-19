# HDSD_NHAPDIEM_Flicker_Cancel_Khoa_2026 — Hướng dẫn kiểm thử các tính năng sửa đổi mới

> Hướng dẫn này mô tả các bước để kiểm tra hiện tượng nhấp nháy màn hình, tính năng làm mờ nút Hủy đăng ký, và phân quyền khoa cho Giảng viên.

---

## 1. Kiểm thử hiện tượng nhấp nháy khi Ghi điểm (Giảng viên / PGV)
1. Đăng nhập với quyền **Phòng Giáo Vụ** hoặc **Giảng viên** (Ví dụ: `GV01` / mật khẩu `GV01`).
2. Vào trang **Nhập Điểm** (`/nhapdiem`).
3. Chọn bộ lọc: Niên khóa `2025-2026`, Học kỳ `1`, Môn học `Cấu trúc dữ liệu & Giải thuật`, Nhóm `3`.
4. Điền điểm cho sinh viên (nếu trống) và bấm **Ghi điểm**.
5. **Kết quả mong đợi**:
   - Ghi điểm thành công, bảng dữ liệu tự động reload lại điểm số.
   - **Không xảy ra hiện tượng màn hình bị ẩn đi và hiện lại gây nhấp nháy**. Dữ liệu được load ngầm mượt mà.

---

## 2. Kiểm thử nút Hủy đăng ký bị làm mờ (Sinh viên)
1. Đăng nhập dưới quyền **Sinh viên** `N23DCCI079` (mật khẩu `n23dcci079`).
2. Truy cập trang **Đăng ký lớp tín chỉ** (`/dangky`).
3. Chọn Niên khóa `2025-2026`, Học kỳ `1` để xem danh sách lớp đã chọn.
4. **Kịch bản A: Lớp học chưa có điểm**:
   - Kiểm tra cột thao tác của môn **Cấu trúc dữ liệu & Giải thuật (Nhóm 3)**. Nút "Hủy đăng ký" phải có màu xanh và cho phép bấm bình thường (nếu chưa nhập điểm).
5. **Kịch bản B: Lớp học đã bắt đầu nhập điểm**:
   - Đăng nhập tài khoản giảng viên khoa CNTT (`GV03` / `GV03`), vào trang Nhập điểm, ghi điểm cho lớp này.
   - Quay lại tài khoản sinh viên `N23DCCI079` tại trang Đăng ký.
   - **Kết quả mong đợi**:
     - Nút "Hủy đăng ký" của môn học này ở cả bảng *Danh sách đã chọn* và bảng *Kết quả tìm kiếm* **bị làm mờ hoàn toàn** (màu xám, không click được).
     - Rê chuột vào nút hủy đăng ký sẽ hiển thị tooltip thông báo: *"Lớp học đã bắt đầu nhập điểm, không thể hủy đăng ký"*.

---

## 3. Kiểm thử phân quyền khoa cho Giảng viên (Giảng viên)
1. Đăng nhập tài khoản giảng viên thuộc khoa **CNTT** (Ví dụ: `GV03` / `GV03`).
2. Đi tới trang **Nhập Điểm** (`/nhapdiem`).
3. Chọn Niên khóa `2021-2022`, Học kỳ `1`.
4. Chọn môn học **Cấu trúc dữ liệu & Giải thuật (CTDL)**, Nhóm `3` (Đây là lớp tín chỉ thuộc **Khoa VT** - quản lý bởi khoa Viễn thông).
5. Bấm chọn để load lớp học.
6. **Kết quả mong đợi**:
   - Hệ thống hiển thị thông báo lỗi chặn: *"Giảng viên khoa CNTT không được nhập điểm lớp tín chỉ thuộc khoa VT"* và không hiển thị danh sách sinh viên.
7. Hãy thử đăng nhập tài khoản giảng viên khoa **VT** (Ví dụ: `GV04` / `GV04`), lặp lại các bước trên và chọn môn học trên. Kết quả mong đợi: Lớp học được load và hiển thị sinh viên bình thường.
8. Hãy thử đăng nhập tài khoản **PGV** (Ví dụ: `GV01` / `GV01`), thực hiện load lớp học trên. Kết quả mong đợi: Load lớp học bình thường vì PGV được quyền quản lý điểm tất cả các khoa.
