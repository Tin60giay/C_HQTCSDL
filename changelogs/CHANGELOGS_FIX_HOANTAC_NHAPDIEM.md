# Changelog sửa hoàn tác, nhập điểm và tài khoản

## Thay đổi
- `app.py`
  - `/history/undo` kiểm tra `KETQUA`; nếu SP thất bại thì rollback, trả lỗi và giữ lịch sử.
  - Hoàn tác `THEM_LTC` gọi `SP_HOANTAC_THEM_LOPTINCHI` thay vì chỉ set `HUYLOP = 1`.
  - History của thao tác mở LTC lưu thêm thông tin liên kết với GV, môn học, khoa.
  - `/nhapdiem/ghidiem` kiểm tra điểm ở server, rollback toàn bộ nếu có một dòng lỗi, và chặn KHOA ghi điểm ngoài khoa.
  - Đổi mật khẩu GV escape dấu `]` trong tên login trước khi ghép dynamic SQL.
  - Tạo tài khoản xử lý thêm mã lỗi role không hợp lệ.

- `static/history.js`
  - Thêm bảng quan hệ phụ thuộc: khoa -> lớp/GV/LTC, lớp -> SV, môn học -> LTC, GV -> LTC.
  - Chặn hoàn tác thao tác cha khi thao tác con mới hơn còn tồn tại trong lịch sử phiên.

- `templates/nhapdiem.html`
  - Điểm CC dùng `step="1"`.
  - Điểm GK/CK dùng `step="0.5"`.
  - Nút ghi điểm bị khóa khi điểm sai miền hoặc sai bước.

- `setup_login.sql`
  - Thêm `SP_HOANTAC_THEM_LOPTINCHI`.
  - Sửa `SP_TAOLOGIN` và `SP_XOALOGIN` dùng `QUOTENAME`.
  - Chặn role ngoài `PGV`, `KHOA` khi tạo login.

## Cập nhật DB đang chạy
- Đã tạo/cập nhật trực tiếp trên DB `QLDSV_HTC`: `SP_HOANTAC_THEM_LOPTINCHI`, `SP_TAOLOGIN`, `SP_XOALOGIN`.
- Không sửa dòng dữ liệu mẫu.

## Kiểm tra đã chạy
- `python -m py_compile app.py check_roles.py check_sp.py`
- `node --check static/history.js`
- Test route `/history/undo`: SP trả lỗi thì HTTP 400, `ok=false`, lịch sử vẫn còn.
- Test route `/nhapdiem/ghidiem`: điểm GK `7.3` bị chặn và redirect không lỗi.

## Rủi ro còn lại
- Nhiều SP cũ vẫn đang `GRANT EXECUTE TO PUBLIC`; cần kế hoạch riêng để chuyển sang quyền theo role `PGV`, `KHOA`, `sv` và test lại toàn bộ đăng nhập/phân quyền.
