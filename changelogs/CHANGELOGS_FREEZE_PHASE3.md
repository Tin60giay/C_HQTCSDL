# NHẬT KÝ THAY ĐỔI (CHANGELOGS) - ĐÓNG BĂNG PHASE 3
*Ngày cập nhật: 2026-04-19*

## 🐛 Sửa lỗi nghiêm trọng (Hotfixes)
- **HTML Bảng Sinh Viên:** Sửa lại cấu trúc giao diện `sinhvien.html`. Đồng bộ cột "Ngày Sinh", "Địa Chỉ" chuẩn xác ở Header và Body. Cập nhật sửa ID `fNGAYSINH` thành ID thật `fNGAY` trong mảng chạy hàm `toggleFormLock` để Ngày Sinh được bảo vệ đúng cách.
- **Sửa Lỗi Đảo ngược Giới tính:** Sửa cú pháp Jinja từ `<Nữ nếu 1> thay cho <Nam>` ở Cột Giới Tính để đồng bộ kết quả `0: Nam, 1: Nữ`.
- **Ngăn chặn Cấu trúc "Xuyên Thời Không":** Frontend đã bị chặn hiển thị lệnh `Tạo mới` nếu Lớp đang mở thuộc năm cũ. Đồng thời Backend (`app.py`) đã chặn cứng các endpoint `/sinhvien/them`, `/lop/them`, và `/loptinchi/them` nếu dữ liệu gửi lên mang thông số đóng băng `<2025`.
- **Database Unique Key Violation:** Xử lý triệt để lỗi SQL Server bằng cách thiết kế lại Stored Procedure `SP_THEM_LOPTINCHI`. Nếu bạn đang tạo lớp nhưng trùng thông tin của lớp đã xóa/hủy trước đó (`HUYLOP = 1`), lệnh `INSERT` sẽ nhường chỗ cho lệnh `UPDATE LOPTINCHI SET HUYLOP = 0` nhằm tái khôi phục (undelete) lớp đó mà không vi phạm Constraint.
