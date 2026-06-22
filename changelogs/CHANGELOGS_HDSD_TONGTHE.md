# CHANGELOGS_HDSD_TONGTHE

**Ngày thực hiện:** 2026-04-26  
**Loại thay đổi:** Tài liệu / hướng dẫn test / đánh giá rủi ro  
**Phạm vi:** Không sửa code, không sửa SQL, không sửa schema, không sửa dữ liệu.

## File đã tạo/cập nhật

| File | Lý do |
|---|---|
| `plans/PLANT_HDSD_TONGTHE.md` | Lưu kế hoạch theo quy định trong `CRITICAL.md`. |
| `hdsd/HDSD_TONGTHE.md` | Tạo hướng dẫn tổng thể cách test từng chức năng và đánh giá mức độ hoàn thiện/rủi ro. |
| `changelogs/CHANGELOGS_HDSD_TONGTHE.md` | Ghi lại thay đổi đã thực hiện và lý do. |

## Nội dung chính đã bổ sung

- Hướng dẫn chuẩn bị môi trường test: chạy `setup_login.sql`, chạy `python app.py`, truy cập `http://localhost:5001`.
- Tài khoản mẫu để test: `GV01/GV01`, `GV03/GV03`, `N15DCCN001/123456`.
- Bảng đánh giá các yêu cầu trong `CRITICAL.md` theo trạng thái hiện tại.
- Checklist test chi tiết cho các module: đăng nhập, dashboard, Khoa, Lớp, Sinh viên, Giảng viên, Môn học, Lớp tín chỉ, Đăng ký LTC, Nhập điểm, Phiếu điểm, Tạo tài khoản, Đổi mật khẩu, Lịch sử/Hoàn tác.
- Danh sách điểm nguy cơ cao cần test/fix sau, gồm permission SQL `PUBLIC`, thiếu ràng buộc DB, validation SP, giới hạn dữ liệu của KHOA, history LTC, và dynamic SQL với ký tự đặc biệt.
- Cập nhật lại 3 file tài liệu sang tiếng Việt có dấu để dễ đọc hơn.

## Xác nhận không thay đổi

- Không sửa `app.py`.
- Không sửa `setup_login.sql`.
- Không sửa file HTML/JS/CSS.
- Không tạo, sửa, xóa dữ liệu trong database.
- Không chạy formatter hay migration.
