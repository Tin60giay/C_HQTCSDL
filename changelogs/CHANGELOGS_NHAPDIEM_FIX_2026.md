# CHANGELOGS_NHAPDIEM_FIX_2026.md — Nhật ký sửa lỗi logic nhập điểm & hủy đăng ký lớp

## 1. Thông tin chung
- **Ngày thực hiện:** 2026-06-19
- **Phạm vi sửa đổi:** Cập nhật 3 stored procedures (`SP_GET_SINHVIEN_THEO_LTC`, `SP_NHAP_DIEM`, `SP_HUY_DANGKY`) trong file `setup_login.sql`.

## 2. Chi tiết các thay đổi và lý do sửa đổi

### 2.1 Cập nhật `SP_GET_SINHVIEN_THEO_LTC`
- **Sự thay đổi:** Thêm `INNER JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC` và điều kiện `AND (LTC.HUYLOP = 0 OR LTC.HUYLOP IS NULL)`.
- **Lý do:** Khi lớp tín chỉ đã bị hủy (`HUYLOP = 1`), danh sách sinh viên của lớp đó không được phép hiển thị trong form nhập điểm của giảng viên.

### 2.2 Cập nhật `SP_NHAP_DIEM`
- **Sự thay đổi:** Thêm đoạn kiểm tra nếu lớp tín chỉ đã bị hủy (`HUYLOP = 1`) thì chặn không cho nhập/sửa điểm, trả về `KETQUA = -1` và thông báo lỗi.
- **Lý do:** Đảm bảo tính toàn vẹn dữ liệu, không cho phép giảng viên nhập điểm cho các lớp đã bị hủy.

### 2.3 Cập nhật `SP_HUY_DANGKY`
- **Sự thay đổi:** Thay đổi điều kiện kiểm tra điểm của lớp từ mức "sinh viên đó" thành mức "toàn lớp". Cụ thể, kiểm tra xem lớp tín chỉ đó đã được nhập bất kỳ điểm nào (chuyên cần, giữa kỳ, hoặc cuối kỳ) của bất kỳ sinh viên nào chưa. Nếu có, chặn không cho hủy đăng ký, trả về `KETQUA = -2` và thông báo lỗi.
- **Lý do:** Ngăn chặn việc sinh viên hủy lớp sau khi giảng viên đã bắt đầu tiến trình chấm điểm và nhập điểm cho lớp đó. Điều này cũng giúp tránh lỗi các sinh viên đã được chấm điểm bị "biến mất luôn" khỏi danh sách của giảng viên do tự ý hủy lớp.
