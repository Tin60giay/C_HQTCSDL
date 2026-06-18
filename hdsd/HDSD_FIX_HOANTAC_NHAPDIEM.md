# HDSD test sửa hoàn tác, nhập điểm và tài khoản

## Chuẩn bị
- Chạy app: `python app.py`.
- Mở `http://localhost:5001`, không mở trực tiếp file HTML bằng `file:///`.
- Tài khoản test nhanh: `GV01/GV01` cho PGV, `GV03/GV03` cho KHOA.
- Dữ liệu test nên dùng mã bắt đầu bằng `TEST_` để dễ dọn.

## Test hoàn tác giảng viên và lớp tín chỉ

### Trường hợp 1: Hoàn tác đúng thứ tự
Điều kiện trước:
- Đăng nhập `GV01/GV01`.
- Có sẵn môn học và khoa để mở lớp tín chỉ.

Bước test:
1. Vào Giảng viên, thêm GV test, ví dụ `TESTGV01`, khoa `CNTT`.
2. Vào Lớp tín chỉ, mở một LTC mới cho `TESTGV01`, niên khóa từ `2025-2026` trở lên, học kỳ `1`, nhóm nên chọn số ít dùng như `99`.
3. Mở Lịch sử.
4. Bấm hoàn tác thao tác `Thêm GV TESTGV01` trước.
5. Kết quả mong đợi: UI chặn vì còn thao tác con `Mở lớp TC`.
6. Hoàn tác thao tác `Mở lớp TC` trước.
7. Hoàn tác tiếp `Thêm GV TESTGV01`.

Kết quả mong đợi:
- LTC vừa tạo bị xóa vật lý nếu chưa có đăng ký.
- Sau đó GV test xóa được.
- Lịch sử chỉ mất mục nào đã hoàn tác thành công.

Dọn dữ liệu:
- Nếu bước hoàn tác thành công thì không cần dọn thêm.
- Nếu LTC đã có đăng ký, hủy/không dùng mã test đó và kiểm tra theo trường hợp 2.

### Trường hợp 2: LTC đã có đăng ký
Bước test:
1. Tạo GV test và mở LTC test.
2. Cho sinh viên đăng ký LTC đó.
3. Thử hoàn tác thao tác mở LTC.

Kết quả mong đợi:
- Hệ thống báo không thể hoàn tác vì lớp đã có đăng ký hoặc lịch sử điểm.
- Lịch sử vẫn giữ mục hoàn tác, không báo thành công giả.
- Đây là đúng theo toàn vẹn dữ liệu: một lớp tín chỉ đã phát sinh đăng ký không nên bị xóa vật lý.

## Test nhập điểm

Điều kiện trước:
- Đăng nhập `GV01/GV01` hoặc `GV03/GV03`.
- Có LTC đã có sinh viên đăng ký.

Bước test:
1. Vào Nhập điểm.
2. Chọn niên khóa, học kỳ, môn học, nhóm rồi bấm Bắt đầu.
3. Nhập `7.5` vào điểm CC.
4. Nhập `7.3` vào điểm GK hoặc CK.
5. Sửa lại CC thành số nguyên, ví dụ `8`; GK/CK thành bước 0.5, ví dụ `7.5`, `8`.
6. Bấm Ghi điểm.

Kết quả mong đợi:
- CC `7.5` bị viền đỏ và khóa nút Ghi điểm.
- GK/CK `7.3` bị viền đỏ và khóa nút Ghi điểm.
- Dữ liệu hợp lệ mới cho ghi.
- Nếu một dòng sai lọt lên server, server rollback toàn bộ và báo lỗi, không commit nửa chừng.

## Test phân quyền KHOA khi ghi điểm

Bước test:
1. Đăng nhập `GV03/GV03`.
2. Vào Nhập điểm, chọn lớp thuộc khoa của GV03: tải được danh sách SV.
3. Thử sửa request bằng DevTools để gửi `maltc` của khoa khác vào `/nhapdiem/ghidiem`.

Kết quả mong đợi:
- Route từ chối ghi điểm ngoài khoa và không commit dữ liệu.

## Test tạo/xóa tài khoản với ký tự đặc biệt

Bước test:
1. Tạo một GV test chưa có tài khoản.
2. Vào Tạo tài khoản.
3. Tạo login cho GV test với mật khẩu có dấu nháy đơn, ví dụ `Abc'123!`.
4. Đăng nhập thử bằng tài khoản đó.
5. Xóa tài khoản test rồi xóa GV test.

Kết quả mong đợi:
- Tạo login không lỗi do dấu nháy trong mật khẩu.
- Tên login/user được bọc bằng `QUOTENAME`, giảm lỗi do ký tự đặc biệt trong identifier.
