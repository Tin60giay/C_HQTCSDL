# HDSD_NHAPDIEM_AV_CTDL_2026 — Hướng dẫn kiểm thử và vận hành các sửa đổi

> Hướng dẫn này mô tả quy trình kiểm thử và vận hành tính năng mới cập nhật liên quan đến Phiếu điểm sinh viên và bộ lọc dropdown nhóm trong trang Nhập điểm.

---

## 1. Yêu cầu môi trường
- Ứng dụng Flask đang chạy (ví dụ cổng `5001`).
- Đã chạy tệp SQL `setup_login.sql` để đồng bộ hóa Stored Procedure mới nhất.

---

## 2. Các bước kiểm thử lỗi Phiếu điểm (Sinh viên N23DCCI079)

### 2.1 Các bước thực hiện
1. Đăng nhập vào trang web dưới quyền **Sinh viên**:
   - Tài khoản: `N23DCCI079`
   - Mật khẩu: `n23dcci079`
2. Chọn mục **Phiếu Điểm** trên thanh điều hướng hoặc truy cập đường dẫn `/phieu_diem`.
3. Kiểm tra bảng danh sách điểm.

### 2.2 Kết quả mong đợi (Expected Results)
- Bảng phiếu điểm chỉ hiển thị các môn học của các lớp tín chỉ **chưa bị hủy** (đang hoạt động).
- Môn **Anh văn (AV)** của học kỳ 1, niên khóa 2025-2026 (nhóm 1) đã bị hủy nên **không được hiển thị**.
- Môn **Cấu trúc dữ liệu & Giải thuật (CTDL)** của học kỳ 1, niên khóa 2025-2026 (nhóm 3) **phải hiển thị bình thường**.

---

## 3. Các bước kiểm thử bộ lọc nhóm (Giảng viên / PGV / KHOA)

### 3.1 Các bước thực hiện
1. Đăng nhập vào trang web dưới quyền **Phòng Giáo Vụ (PGV)** hoặc **Khoa**:
   - Tài khoản: `GV01` (hoặc tài khoản PGV/KHOA bất kỳ)
   - Mật khẩu: `GV01`
2. Đi tới trang **Nhập Điểm** (`/nhapdiem`).
3. Điền/chọn bộ lọc:
   - **Niên khóa**: `2025-2026`
   - **Học kỳ**: `Học kỳ 1`
   - **Môn học**: `Cấu trúc dữ liệu & Giải thuật (CTDL)`
4. Quan sát dropdown **Nhóm**:
   - Hệ thống tự động gọi API lấy danh sách nhóm thực tế và hiển thị hai nhóm: `Nhóm 1` và `Nhóm 3`.
5. Chọn lần lượt từng nhóm:
   - Chọn **Nhóm 3**: Trang web tự động tải và hiển thị danh sách gồm 1 sinh viên là `N23DCCI079 - Nguyễn Thành Vinh` (vì sinh viên Phạm Tuấn quá hạn đã được xóa đăng ký). Giảng viên có thể thực hiện nhập điểm bình thường.
   - Chọn **Nhóm 1**: Trang web tự động tải và hiển thị danh sách trống (`Số SV: 0`) do không có sinh viên nào đăng ký hoạt động ở nhóm này.

---

## 4. Troubleshooting & Lưu ý
- Nếu trang web không tự động tải lại nhóm hoặc không hiển thị sinh viên, hãy thực hiện xoá cache trình duyệt (Ctrl+F5) để đảm bảo trình duyệt tải mã Javascript mới nhất của trang `nhapdiem.html`.
- Hãy chắc chắn rằng database của bạn đã cập nhật SP `SP_XEM_PHIEU_DIEM` bằng cách chạy query trong SSMS hoặc công cụ tương đương.
