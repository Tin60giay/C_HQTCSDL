# PLANT_HDSD_TONGTHE

**Ngày lập:** 2026-04-26  
**Mục tiêu:** Tạo tài liệu tổng thể hướng dẫn test từng chức năng và đánh giá rủi ro hiện tại của đồ án theo `CRITICAL.md`.

## Phạm vi

- Tạo `hdsd/HDSD_TONGTHE.md`.
- Tạo `changelogs/CHANGELOGS_HDSD_TONGTHE.md`.
- Không sửa `app.py`, template, static JS, SQL, schema hay dữ liệu.

## Nội dung cần có trong HDSD

- Chuẩn bị môi trường test: SQL Server, `setup_login.sql`, `python app.py`, URL `http://localhost:5001`.
- Tài khoản mẫu: `GV01/GV01`, `GV03/GV03`, `N15DCCN001/123456`.
- Bảng đối chiếu yêu cầu trong `CRITICAL.md` với tình trạng hiện tại.
- Danh sách rủi ro cao:
  - `GRANT EXECUTE TO PUBLIC` quá rộng.
  - Thiếu một số ràng buộc DB theo đề bài.
  - SP chưa validate đầy đủ miền điểm/học kỳ/nhóm.
  - KHOA có nguy cơ xem/nhập điểm qua khoa khác.
  - History thêm Lớp tín chỉ có nguy cơ sai `MALTC`.
  - Dynamic SQL có nguy cơ lỗi với ký tự đặc biệt.
- Checklist test chi tiết cho:
  - Đăng nhập và phân quyền.
  - Dashboard.
  - Khoa, Lớp, Sinh viên, Giảng viên, Môn học, Lớp tín chỉ.
  - Đăng ký Lớp tín chỉ.
  - Nhập điểm.
  - Phiếu điểm.
  - Tạo/xóa tài khoản.
  - Đổi mật khẩu.
  - Lịch sử/hoàn tác.

## Cách thức thực hiện

1. Ghi tài liệu tổng thể vào `hdsd/HDSD_TONGTHE.md`.
2. Ghi changelog vào `changelogs/CHANGELOGS_HDSD_TONGTHE.md`.
3. Kiểm tra file tồn tại và đọc lại các đầu mục chính.
4. Đảm bảo tài liệu không hướng dẫn thao tác sửa trực tiếp database mẫu.

## Tiêu chí hoàn thành

- Có đủ 3 file mới theo đúng thư mục.
- HDSD có đầy đủ test case dương tính và âm tính.
- HDSD nêu rõ các điểm nguy cơ cao cần ưu tiên test/fix.
- Changelog ghi rõ chỉ thay đổi tài liệu.
