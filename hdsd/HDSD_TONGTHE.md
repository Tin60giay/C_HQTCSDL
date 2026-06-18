# HDSD Tổng Thể - Hướng Dẫn Test Đồ Án QLDSV HTC

**Ngày lập:** 2026-04-26  
**Phạm vi:** Hướng dẫn test tổng thể toàn bộ chức năng hiện có của đồ án Hệ Quản Trị Cơ Sở Dữ Liệu.  
**Căn cứ:** `CRITICAL.md`, `app.py`, `setup_login.sql`, các template trong `templates/`, và kết quả kiểm tra đọc-only trên máy hiện tại.  
**Lưu ý quan trọng:** Tài liệu này chỉ hướng dẫn test và đánh giá rủi ro. Không yêu cầu sửa code, không sửa schema, không sửa dữ liệu mẫu.

---

## 1. Chuẩn Bị Môi Trường Test

### 1.1 Điều kiện trước khi test

| Mục | Giá trị cần có |
|---|---|
| SQL Server | `localhost\SQLEXPRESS` |
| Database | `QLDSV_HTC` |
| Driver | ODBC Driver 17 for SQL Server |
| Python package | `flask`, `pyodbc` |
| File SQL bắt buộc | `setup_login.sql` |
| URL ứng dụng | `http://localhost:5001` |

### 1.2 Khởi tạo SQL

1. Mở SQL Server Management Studio.
2. Kết nối vào `localhost\SQLEXPRESS`.
3. Chạy database gốc nếu máy chưa có DB:
   - `QLDSV_HTC_utf8.sql`
4. Chạy lại file:
   - `setup_login.sql`
5. Đảm bảo không tạo file SQL mới khi cần sửa SP. Theo `CRITICAL.md`, mọi thay đổi SP phải nằm trong `setup_login.sql`.

### 1.3 Chạy ứng dụng

```powershell
cd F:\A_HQTCSDL\New\20042026\C_HQTCSDL
python app.py
```

Mở trình duyệt tại:

```text
http://localhost:5001
```

### 1.4 Tài khoản mẫu để test

| Vai trò | Login | Mật khẩu | Kết quả mong đợi |
|---|---|---|---|
| PGV | `GV01` | `GV01` | Vào Dashboard nhóm Phòng Giáo Vụ |
| KHOA | `GV03` | `GV03` | Vào Dashboard nhóm Giảng Viên Khoa |
| SV | `N15DCCN001` | `123456` | Vào Dashboard Sinh Viên |

Nếu mật khẩu GV đã bị đổi trong quá trình test, cần dùng mật khẩu mới hoặc tạo lại login trong SQL.

### 1.5 Nguyên tắc dữ liệu test

- Không sửa trực tiếp các dòng dữ liệu mẫu bằng SQL.
- Mọi bản ghi test nên đặt tiền tố `TEST_`, `TST`, hoặc giá trị dễ nhận ra.
- Sau mỗi test tạo mới, xóa bằng giao diện nếu không còn ràng buộc con.
- Nếu bản ghi test đã bị ràng buộc, không cố gắng xóa cưỡng bức. Ghi lại tình huống vào kết quả test.

---

## 2. Đánh Giá Hiện Trạng Theo CRITICAL.md

### 2.1 Bảng đối chiếu yêu cầu và trạng thái

| Yêu cầu | Trạng thái hiện tại | Mức độ cần test |
|---|---|---|
| Không sửa database gốc, chỉ thêm/sửa/xóa hàm/SP | Đang tuân thủ về mặt quy trình; SP tập trung trong `setup_login.sql` | Trung bình |
| Đăng nhập Giảng viên | Đã có, xác thực bằng SQL Login và `SP_DANGNHAP_GV` | Trung bình |
| Đăng nhập Sinh viên bằng login chung `sv` | Đã có, SV dùng `sv/123`, xác thực qua `SP_DANGNHAP_SV` | Cao |
| Label Login chuyển thành Mã SV | Đã có trong `login.html` | Thấp |
| PGV quản lý Khoa | Đã có CRUD `/khoa` | Cao |
| PGV quản lý Lớp | Đã có CRUD `/lop` | Cao |
| PGV quản lý Sinh viên dạng SubForm 2 cấp | Đã có `/sinhvien` và `/sinhvien/<malop>` | Cao |
| PGV quản lý Môn học | Đã có CRUD `/monhoc` | Cao |
| PGV mở Lớp tín chỉ | Đã có CRUD/hủy lớp `/loptinchi` | Cao |
| SV đăng ký Lớp tín chỉ | Đã có `/dangky`, lọc theo niên khóa/học kỳ và chống trùng môn | Cao |
| PGV/KHOA nhập điểm | Đã có `/nhapdiem`, tính điểm hết môn | Cao |
| SV xem phiếu điểm của mình | Đã có `/phieu_diem` | Trung bình |
| Quản trị tạo tài khoản | Đã có `/taotaikhoan` | Cao |
| Đổi mật khẩu | Đã có `/doimatkhau` cho GV và SV | Cao |
| Phân quyền PGV/KHOA/SV trên giao diện | Đã có decorator `require_group` và menu riêng | Cao |
| Vi phạm ràng buộc thì làm mờ nút | Đã có ở nhiều trang qua `history.js` và JS riêng | Cao |
| KHOA chỉ thấy dữ liệu khoa mình | Chưa chắc chắn đầy đủ, `/loptinchi` và `/nhapdiem` có nguy cơ xem rộng | Cao |

### 2.2 Phần đã giải quyết tốt

- Các route chính đã tồn tại cho 3 nhóm PGV, KHOA, SV.
- Route-level phân quyền đã chặn nhóm sai vào trang không đúng quyền.
- `setup_login.sql` đã tạo đủ các SP chính cần cho login, CRUD, đăng ký, nhập điểm, phiếu điểm, tạo/xóa login, đổi mật khẩu SV.
- Giao diện có cơ chế làm mờ nút khi chưa chọn dòng, khi có lỗi validation, khi dữ liệu bị đóng băng, hoặc khi bị ràng buộc xóa.
- Có lịch sử thao tác và hoàn tác trong session cho nhiều màn CRUD.
- Kiểm tra đọc-only đã xác nhận:
  - `python -m py_compile app.py check_roles.py check_sp.py test_alter_login.py` không báo lỗi.
  - Role SQL `PGV`, `KHOA` tồn tại.
  - Các SP chính tồn tại trong DB.
  - Route test có kết quả đúng: PGV vào CRUD, KHOA bị chặn CRUD nhập liệu, SV chỉ vào đăng ký/phiếu điểm.

### 2.3 Điểm nguy cơ cao cần test kỹ

| Nguy cơ | Lý do | Cách test nhanh |
|---|---|---|
| `GRANT EXECUTE TO PUBLIC` quá rộng | Nhiều SP CRUD và SP tạo/xóa login đang cấp cho `PUBLIC`; app có chặn route nhưng DB-level permission yếu | Đăng nhập bằng GV KHOA, thử gọi SP bằng script riêng nếu được phép test DB |
| DB thiếu một số ràng buộc trong `CRITICAL.md` | DB hiện chỉ thấy check `SOSVTOITHIEU > 0`; thiếu unique tên khoa/lớp/môn và check điểm/học kỳ/nhóm | Test nhập trùng tên, học kỳ 4, điểm 11, điểm GK 7.3 |
| SP chưa validate điểm 0-10 và bước 0.5 | UI có validate nhưng server/SP có thể vẫn nhận dữ liệu sai nếu bypass UI | Test từ giao diện và ghi chú không được bypass nếu không có yêu cầu |
| KHOA có thể xem/nhập điểm qua khoa khác | Route cho KHOA vào `/loptinchi`, `/nhapdiem` nhưng cần kiểm tra lọc theo khoa | Đăng nhập `GV03`, xem có thấy LTC khoa khác hay không |
| History mở LTC có thể lưu sai `MALTC` | `SP_THEM_LOPTINCHI` chèn mới trả `KETQUA = 1`, không chắc là identity mới | Mở LTC mới, mở lịch sử, thử hoàn tác và kiểm tra đúng lớp vừa mở |
| Dynamic SQL với mật khẩu/login | `ALTER LOGIN` và `SP_TAOLOGIN` ghép chuỗi, dễ lỗi khi mật khẩu có dấu nháy đơn | Test mật khẩu có ký tự đặc biệt như `Abc'123` trong môi trường an toàn |
| Login SV trong UI bắt buộc mật khẩu | SV không thể để trống password do HTML/backend yêu cầu đầy đủ | Dùng mật khẩu `123456` khi test SV |
| Xóa/Hủy dữ liệu bị ràng buộc | Nhiều nút đã mờ đúng nhưng backend vẫn cần chặn | Test xóa lớp có SV, xóa SV có đăng ký, xóa GV đang dạy |

---

## 3. Checklist Test Tổng Thể

### 3.1 Đăng nhập và phân quyền

| Mã test | Điều kiện | Bước thao tác | Dữ liệu | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| AUTH-01 | App đang chạy | Mở `/`, chọn Giảng Viên, đăng nhập | `GV01/GV01` | Vào dashboard PGV, hiện menu quản lý đầy đủ | Đăng xuất |
| AUTH-02 | App đang chạy | Mở `/`, chọn Giảng Viên, đăng nhập | `GV03/GV03` | Vào dashboard KHOA, chỉ có xem LTC, nhập điểm, đổi mật khẩu | Đăng xuất |
| AUTH-03 | App đang chạy | Mở `/`, chọn Sinh Viên, đăng nhập | `N15DCCN001/123456` | Vào dashboard SV, có đăng ký LTC, phiếu điểm, đổi mật khẩu | Đăng xuất |
| AUTH-04 | Đăng nhập PGV | Truy cập `/dangky`, `/phieu_diem` | URL trực tiếp | Bị chuyển về dashboard, có thông báo không có quyền | Không |
| AUTH-05 | Đăng nhập KHOA | Truy cập `/khoa`, `/lop`, `/sinhvien`, `/monhoc`, `/taotaikhoan` | URL trực tiếp | Bị chặn về dashboard | Không |
| AUTH-06 | Đăng nhập SV | Truy cập `/nhapdiem`, `/loptinchi`, `/khoa` | URL trực tiếp | Bị chặn về dashboard | Không |
| AUTH-07 | Chưa đăng nhập | Truy cập `/dashboard` hoặc route bất kỳ | URL trực tiếp | Bị chuyển về trang login | Không |
| AUTH-08 | App đang chạy | Nhập sai mật khẩu | `GV01/sai`, `N15DCCN001/sai` | Không đăng nhập được, hiện thông báo lỗi | Không |

Lỗi cần quan sát:
- SV không nên đăng nhập bằng password rỗng trên UI hiện tại.
- Nhóm của GV phải lấy đúng từ SQL role, không được nhầm PGV/KHOA.

### 3.2 Dashboard

| Mã test | Điều kiện | Bước thao tác | Kết quả mong đợi |
|---|---|---|---|
| DASH-01 | Đăng nhập PGV | Quan sát dashboard | Có menu Khoa, Lớp, Giảng viên, Sinh viên, Môn học, Lớp tín chỉ, Nhập điểm, Đổi mật khẩu, Tạo tài khoản |
| DASH-02 | Đăng nhập KHOA | Quan sát dashboard | Chỉ có Xem Lớp tín chỉ, Nhập điểm, Đổi mật khẩu |
| DASH-03 | Đăng nhập SV | Quan sát dashboard | Chỉ có Đăng ký LTC, Bảng điểm cá nhân, Đổi mật khẩu |
| DASH-04 | Đăng nhập bất kỳ | Bấm Đăng xuất | Session xóa, quay về login; truy cập dashboard lại bị chặn |

### 3.3 Quản lý Khoa - PGV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| KHOA-01 | Đăng nhập PGV | Mở `/khoa` | Không | Danh sách khoa hiển thị, nút Xóa/Ghi mờ khi chưa chọn dòng | Không |
| KHOA-02 | Đăng nhập PGV | Nhập mã và tên, bấm Tạo mới | `TESTK`, `Khoa Test` | Thêm thành công, dòng mới xuất hiện | Xóa `TESTK` |
| KHOA-03 | Đã có `TESTK` | Chọn dòng, sửa tên, bấm Ghi | `Khoa Test Sửa` | Cập nhật thành công | Xóa `TESTK` |
| KHOA-04 | Có khoa không có lớp/GV | Chọn dòng, bấm Xóa | `TESTK` | Xóa thành công | Không |
| KHOA-05 | Khoa có lớp/GV | Chọn khoa đang có ràng buộc | Khoa có lớp/GV mẫu | Nút Xóa mờ hoặc backend báo không thể xóa; không mất dữ liệu | Không |
| KHOA-06 | Đăng nhập PGV | Thử thêm trùng mã | Mã khoa đã có | Nút/validation báo trùng hoặc SP báo lỗi, không chèn trùng | Không |
| KHOA-07 | Đăng nhập PGV | Thử thêm trùng tên khoa | Tên khoa đã có | Cần ghi nhận nguy cơ: DB/SP có thể chưa chặn unique tên | Xóa nếu tạo nhầm |

### 3.4 Quản lý Lớp - PGV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| LOP-01 | Đăng nhập PGV | Mở `/lop` | Không | Bảng lớp hiển thị, có lọc khoa/text, có combo khóa học | Không |
| LOP-02 | Đăng nhập PGV | Lọc theo khoa và text | Từ khóa bất kỳ | Bảng lọc đúng, không reload | Không |
| LOP-03 | Đăng nhập PGV | Thêm lớp mới | `TESTLOP`, `Lop Test`, `2026-2030`, khoa hợp lệ | Thêm thành công | Xóa `TESTLOP` |
| LOP-04 | Có `TESTLOP` | Chọn dòng, sửa tên/khóa học/khoa | Giá trị mới hợp lệ | Cập nhật thành công | Xóa `TESTLOP` |
| LOP-05 | Có lớp rỗng | Chọn dòng, bấm Xóa | `TESTLOP` | Xóa thành công | Không |
| LOP-06 | Lớp có sinh viên | Chọn lớp mẫu có SV | Lớp mẫu | Nút Xóa mờ hoặc backend từ chối; không xóa dữ liệu | Không |
| LOP-07 | Đăng nhập PGV | Nhập khóa học sai định dạng | `2026`, `2026-2029` | Nút Ghi/Tạo phải bị mờ và hiện cảnh báo | Không |
| LOP-08 | Đăng nhập PGV | Chọn lớp khóa học trước 2025 | Lớp cũ nếu có | Form bị khóa, các nút thao tác bị mờ | Không |
| LOP-09 | Đăng nhập PGV | Thử trùng tên lớp | Tên lớp đã có | Ghi nhận nguy cơ nếu hệ thống cho qua | Xóa nếu tạo nhầm |

### 3.5 Quản lý Sinh viên - PGV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| SV-01 | Đăng nhập PGV | Mở `/sinhvien` | Không | Hiện panel lớp bên trái, panel SV bên phải chờ chọn lớp | Không |
| SV-02 | Có danh sách lớp | Click một lớp | Lớp bất kỳ | URL sang `/sinhvien/<malop>`, bảng SV của lớp hiện đúng | Không |
| SV-03 | Đang xem lớp hợp lệ | Thêm SV mới | `TESTSV001`, `Nguyen Van`, `Test`, lớp đang xem | Thêm thành công | Xóa `TESTSV001` nếu chưa đăng ký |
| SV-04 | Có `TESTSV001` | Chọn SV, sửa địa chỉ/giới tính/ngày sinh | Giá trị hợp lệ | Cập nhật thành công | Xóa `TESTSV001` |
| SV-05 | SV chưa đăng ký LTC | Chọn SV, bấm Xóa | `TESTSV001` | Xóa thành công | Không |
| SV-06 | SV đã đăng ký LTC | Chọn SV mẫu | `N15DCCN001` hoặc SV có DK | Nút Xóa bị mờ hoặc backend báo ràng buộc | Không |
| SV-07 | Đăng nhập PGV | Nhập MASV trùng | MASV đã có | Hiện lỗi realtime, tất cả nút thao tác bị mờ | Không |
| SV-08 | Đang xem lớp cũ trước 2025 | Chọn SV thuộc lớp cũ | SV trong lớp cũ | Form bị khóa, nút sửa/xóa bị mờ | Không |
| SV-09 | Đang chọn SV | Sửa form rồi bấm Phục hồi | Giá trị bất kỳ | Form quay về dữ liệu ban đầu, DB chưa đổi | Không |

Lỗi cần quan sát:
- Trường `DANGHIHOC` hiện trong form nhưng route thêm/sửa hiện không ghi thay đổi trạng thái này.
- Nếu chuyển `MALOP` của SV sang lớp khác, cần kiểm tra redirect và danh sách sau khi ghi.

### 3.6 Quản lý Giảng viên - PGV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| GV-01 | Đăng nhập PGV | Mở `/giangvien` | Không | Danh sách GV hiển thị, có lọc theo khoa | Không |
| GV-02 | Đăng nhập PGV | Thêm GV mới | `TESTGV`, khoa hợp lệ, họ/tên hợp lệ | Thêm thành công | Xóa `TESTGV` nếu chưa dạy |
| GV-03 | Có `TESTGV` | Sửa học vị/học hàm/chuyên môn | Giá trị mới | Cập nhật thành công | Xóa `TESTGV` |
| GV-04 | GV chưa dạy LTC | Chọn `TESTGV`, bấm Xóa | `TESTGV` | Xóa thành công | Không |
| GV-05 | GV đang dạy LTC | Chọn GV mẫu đang có LTC | GV trong LOPTINCHI | Nút Xóa mờ hoặc backend báo ràng buộc | Không |
| GV-06 | Đăng nhập PGV | Nhập MAGV trùng | MAGV đã có | Validation báo trùng, nút bị mờ | Không |

Lỗi cần quan sát:
- Tạo GV không tự động tạo login SQL. Nếu cần login, dùng chức năng Tạo tài khoản.

### 3.7 Quản lý Môn học - PGV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| MH-01 | Đăng nhập PGV | Mở `/monhoc` | Không | Danh sách môn hiển thị, có lọc text | Không |
| MH-02 | Đăng nhập PGV | Thêm môn mới | `TESTMH`, `Mon Test`, LT `30`, TH `0` | Thêm thành công | Xóa `TESTMH` nếu chưa có LTC |
| MH-03 | Có `TESTMH` | Sửa tên/số tiết | LT `45`, TH `15` | Cập nhật thành công | Xóa `TESTMH` |
| MH-04 | Môn chưa có LTC | Chọn `TESTMH`, bấm Xóa | `TESTMH` | Xóa thành công | Không |
| MH-05 | Môn đã có LTC/Đăng ký | Chọn môn mẫu | Môn có LTC | Nút Xóa bị mờ hoặc backend báo ràng buộc | Không |
| MH-06 | Đăng nhập PGV | Nhập LT nhỏ hơn 30 hoặc TH âm | LT `10`, TH `-1` | Nút thao tác bị mờ, hiện cảnh báo | Không |
| MH-07 | Đăng nhập PGV | Nhập tên môn trùng | Tên môn đã có | Ghi nhận nguy cơ nếu SP/DB cho qua | Xóa nếu tạo nhầm |
| MH-08 | Chọn môn có lịch sử trước 2025 | Click dòng có khóa | Môn cũ | Form bị khóa, nút thao tác bị mờ | Không |

### 3.8 Mở Lớp Tín Chỉ - PGV và KHOA

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| LTC-01 | Đăng nhập PGV | Mở `/loptinchi` | Không | Hiện bảng LTC, form mở lớp và bộ lọc | Không |
| LTC-02 | Đăng nhập KHOA | Mở `/loptinchi` | Không | Chỉ xem bảng, không thấy toolbar/form chỉnh sửa | Không |
| LTC-03 | Đăng nhập PGV | Lọc theo niên khóa/học kỳ/khoa/text | Giá trị bất kỳ | Bảng lọc đúng trên client | Không |
| LTC-04 | Đăng nhập PGV | Mở LTC mới | NK `2026-2027`, HK `1`, môn hợp lệ, nhóm mới, GV/khoa hợp lệ, min `10` | Thêm thành công, hiện trong bảng | Hủy lớp vừa tạo |
| LTC-05 | Có LTC vừa tạo | Chọn dòng, sửa GV/min SV | Giá trị hợp lệ | Cập nhật thành công | Hủy lớp test |
| LTC-06 | Có LTC test | Chọn dòng, bấm Hủy lớp | `MALTC` test | Lớp bị HUYLOP, không hiện cho SV | Không |
| LTC-07 | Đăng nhập PGV | Thử tạo trùng `(NIENKHOA, HOCKY, MAMH, NHOM)` | Giá trị đã có | SP báo lớp đã tồn tại | Không |
| LTC-08 | Đăng nhập PGV | Nhập HK `4`, nhóm `0`, min `0` | Giá trị sai | UI phải làm mờ nút; nếu backend cho qua thì ghi rủi ro cao | Xóa/hủy nếu tạo nhầm |
| LTC-09 | Đăng nhập PGV | Chọn niên khóa trước 2025 | `2021-2022` nếu có | Form/nút bị khóa hoặc backend từ chối | Không |
| LTC-10 | Đăng nhập KHOA | Quan sát LTC | Không | Cần kiểm tra có bị lộ LTC khoa khác hay không | Không |

Lỗi cần quan sát:
- Sau khi mở LTC mới, mở Lịch sử và thử Hoàn tác. Nếu hoàn tác nhầm lớp #1 hoặc lớp khác, ghi lỗi `History MALTC`.
- KHOA không được có nút tạo/sửa/xóa LTC.

### 3.9 Đăng ký Lớp Tín Chỉ - SV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| DK-01 | Đăng nhập SV | Mở `/dangky` | `N15DCCN001` | Hiện mã SV, họ tên, mã lớp; dropdown niên khóa theo LTC phù hợp | Không |
| DK-02 | Có LTC mở | Chọn niên khóa, học kỳ | `2025-2026`, HK `1` nếu có | Bảng LTC hiện MALTC, môn, nhóm, GV, khoa, số SV đăng ký | Không |
| DK-03 | Có lớp chưa đăng ký | Bấm Đăng ký | LTC chưa đăng ký | Đăng ký thành công, nút đổi trạng thái | Hủy đăng ký nếu chưa có điểm |
| DK-04 | Đã đăng ký một lớp của môn | Thử đăng ký lớp khác cùng môn | Môn đã đăng ký | Nút bị mờ hoặc SP báo đã đăng ký môn này | Hủy nếu cần |
| DK-05 | Đã đăng ký lớp | Bấm Hủy đăng ký | Lớp chưa có điểm | Hủy thành công, có thể đăng ký lại | Không |
| DK-06 | Lớp đã có điểm | Thử hủy đăng ký | Lớp có điểm | Nút Hủy bị mờ hoặc SP báo không thể hủy vì có điểm | Không |
| DK-07 | LTC bị hủy | Tìm theo NK/HK | Lớp HUYLOP=1 | Không hiện cho SV | Không |
| DK-08 | Niên khóa cũ trước 2025 | Tìm và thao tác nếu có | `2021-2022` | Nút thao tác bị mờ hoặc backend từ chối | Không |

Lỗi cần quan sát:
- SV chỉ được đăng ký cho chính mình. Request gửi `masv` trên client không được làm đối tượng thao tác thành SV khác; backend đang lấy `session['username']`, đây là đúng.

### 3.10 Nhập Điểm - PGV và KHOA

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| DIEM-01 | Đăng nhập PGV | Mở `/nhapdiem` | Không | Hiện combobox NK/HK/Môn/Nhóm, có nút Bắt đầu | Không |
| DIEM-02 | Có LTC có SV đăng ký | Chọn lớp và Bắt đầu | Ví dụ `2025-2026`, HK `1`, môn `CTDL`, nhóm `3` nếu có | Bảng SV tải ra, có cột CC/GK/CK/HM | Không |
| DIEM-03 | Bảng điểm đã hiện | Nhập CC/GK/CK | `10`, `5`, `8` | HM tự tính `6.50` | Không |
| DIEM-04 | Bảng điểm đã hiện | Nhập điểm ngoài miền | `11`, `-1` | Ô bị viền đỏ, nút Ghi điểm bị mờ | Sửa lại điểm |
| DIEM-05 | Bảng điểm đã hiện | Nhập điểm thập phân không phải 0.5 | `7.3` | Ghi nhận rủi ro: yêu cầu GK/CK làm tròn 0.5 nhưng UI đang step 0.1 | Sửa lại điểm |
| DIEM-06 | Bảng điểm hợp lệ | Bấm Ghi điểm | Giá trị hợp lệ | Flash ghi điểm thành công, reload vẫn giữ điểm trong DB | Nếu là SV/test, có thể sửa về rỗng nếu cần bằng UI không hỗ trợ rỗng để xóa hết |
| DIEM-07 | Chọn lớp không tồn tại | Bắt đầu | Tổ hợp không có LTC | Hiện thông báo không tìm thấy LTC | Không |
| DIEM-08 | Đăng nhập KHOA | Mở `/nhapdiem`, chọn LTC khoa khác nếu thấy | Giá trị khoa khác | Cần ghi rõ nếu KHOA vẫn xem/nhập được điểm khoa khác | Không |

Lỗi cần quan sát:
- Backend `SP_NHAP_DIEM` hiện chưa chặn điểm ngoài 0-10 nếu request bypass UI.
- Điểm hết môn tính theo công thức `CC*0.1 + GK*0.3 + CK*0.6`; phải chỉ đọc.

### 3.11 Phiếu Điểm - SV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| PD-01 | Đăng nhập SV | Mở `/phieu_diem` | `N15DCCN001` | Hiện thông tin SV và danh sách môn đã đăng ký | Không |
| PD-02 | SV có điểm đầy đủ | Quan sát cột HM | Điểm có CC/GK/CK | HM tính đúng công thức | Không |
| PD-03 | SV có môn chưa nhập điểm | Quan sát bảng | Môn chưa điểm | Điểm trống/không tính HM | Không |
| PD-04 | SV thử truy cập phiếu điểm SV khác | Không có input MASV trên UI | URL `/phieu_diem` | Chỉ hiện phiếu điểm của session hiện tại | Không |

### 3.12 Tạo và Xóa Tài Khoản - PGV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| TK-01 | Đăng nhập PGV | Mở `/taotaikhoan` | Không | Hiện danh sách giảng viên, nút Tạo/Xóa mờ khi chưa chọn | Không |
| TK-02 | Chọn GV chưa có tài khoản | Nhập login, mật khẩu, role | GV test nếu có, login `TESTLOGIN` | Nút Tạo sáng, tạo thành công | Xóa tài khoản test nếu GV không dạy |
| TK-03 | Chọn GV đã có tài khoản | Quan sát form | GV01/GV03 | Ô login/mật khẩu/role bị khóa, nút Tạo mờ, nút Xóa tùy ràng buộc | Không |
| TK-04 | Login bị trùng | Nhập login đã tồn tại | `GV01` | Nút Tạo bị mờ, hiện cảnh báo | Không |
| TK-05 | GV đang dạy LTC | Chọn GV đang dạy | GV có trong LOPTINCHI | Nút Xóa bị mờ, hiện lý do ràng buộc | Không |
| TK-06 | Mật khẩu có dấu nháy đơn | Thử tạo trong môi trường an toàn | `Abc'123` | Có thể lỗi dynamic SQL; ghi nhận rủi ro | Xóa nếu tạo được |

Lỗi cần quan sát:
- `SP_TAOLOGIN` và `SP_XOALOGIN` đang được grant public, cần đưa vào danh sách rủi ro bảo vệ.
- PGV được tạo tài khoản cho PGV/KHOA; KHOA không được vào trang này.

### 3.13 Đổi Mật Khẩu - PGV, KHOA, SV

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| MK-01 | Đăng nhập SV | Mở `/doimatkhau`, nhập sai mật khẩu cũ | `sai` | Báo mật khẩu cũ không chính xác | Không |
| MK-02 | Đăng nhập SV | Đổi mật khẩu đúng | Cũ `123456`, mới `123456_test` | Thành công, quay về dashboard | Đổi lại `123456` |
| MK-03 | Đăng nhập SV | Xác nhận mật khẩu mới không khớp | `abc` và `abcd` | Báo lỗi, nút không ghi | Không |
| MK-04 | Đăng nhập GV | Đổi mật khẩu đúng | `GV03` -> `GV03_test` | Thành công, session không bị văng | Đổi lại `GV03` |
| MK-05 | Đăng nhập GV | Đổi với mật khẩu có dấu nháy | `Abc'123` | Có thể lỗi dynamic SQL; ghi nhận rủi ro | Đổi lại nếu thành công |

Lưu ý:
- Khi test đổi mật khẩu, bắt buộc đổi lại mật khẩu gốc ngay sau khi test để không làm hỏng các test sau.
- Nếu quên mật khẩu GV, cần tạo lại login qua SQL/PGV tùy tình huống.

### 3.14 Lịch sử và Hoàn tác

| Mã test | Điều kiện | Bước thao tác | Dữ liệu gợi ý | Kết quả mong đợi | Dọn dẹp |
|---|---|---|---|---|---|
| HIS-01 | Đăng nhập PGV | Thêm bản ghi test ở `/lop` hoặc `/monhoc` | `TESTLOP`, `TESTMH` | Hành động xuất hiện trong Lịch sử | Hoàn tác/xóa test |
| HIS-02 | Có hành động thêm | Mở Lịch sử, bấm Hoàn tác | Bản ghi vừa thêm | Bản ghi biến mất, trang reload | Không |
| HIS-03 | Sửa bản ghi test | Mở Lịch sử, hoàn tác sửa | `TESTMH` | Giá trị quay về trước khi sửa | Xóa test |
| HIS-04 | Xóa bản ghi test | Hoàn tác xóa | `TESTMH` | Bản ghi được khôi phục | Xóa lại test |
| HIS-05 | Tạo cha-con | Thêm lớp test, thêm SV test vào lớp | `TESTLOP`, `TESTSV001` | Hoàn tác lớp cha bị chặn nếu còn con tồn tại | Xóa/hoàn tác SV trước |
| HIS-06 | Mở LTC mới | Mở Lịch sử, hoàn tác | LTC test | Kiểm tra có hủy đúng lớp vừa mở không; ghi lỗi nếu sai `MALTC` | Hủy lớp test nếu cần |

Lưu ý:
- Lịch sử nằm trong session. Đăng xuất sẽ mất lịch sử.
- Hoàn tác vẫn phải tôn trọng ràng buộc DB; nếu có con phát sinh thì hoàn tác có thể bị chặn.

---

## 4. Checklist Chấp Nhận Sau Khi Test

| Nhóm | Tiêu chí đạt |
|---|---|
| Đăng nhập | 3 nhóm PGV/KHOA/SV đăng nhập đúng, sai mật khẩu bị chặn |
| Phân quyền | Mỗi nhóm chỉ vào đúng route của mình; URL trực tiếp bị chặn |
| Nhập liệu PGV | CRUD Khoa/Lớp/SV/GV/Môn/LTC hoạt động với dữ liệu hợp lệ |
| Ràng buộc UI | Khi sai/trùng/bị đóng băng/bị ràng buộc, nút thao tác phải bị mờ trước |
| Đăng ký SV | SV đăng ký/hủy đúng, không đăng ký trùng môn, không hủy khi đã có điểm |
| Nhập điểm | Tải đúng lớp, tính HM đúng, chặn điểm sai trên UI |
| Phiếu điểm | SV chỉ xem điểm của chính mình |
| Quản trị | PGV tạo/xóa tài khoản đúng ràng buộc; KHOA/SV không vào được |
| Lịch sử | Hoàn tác đúng với bản ghi test, không phá dữ liệu mẫu |

---

## 5. Kết Luận Đánh Giá Nhanh

Đồ án hiện đã có đầy đủ khung chức năng chính theo đề bài: đăng nhập, phân quyền, nhập liệu PGV, đăng ký SV, nhập điểm, phiếu điểm, tạo tài khoản và đổi mật khẩu. Phần cần ưu tiên test kỹ nhất là ranh giới quyền KHOA, ràng buộc điểm/học kỳ/nhóm ở server-side, và các SP đang cấp quyền `PUBLIC`.

Nếu cần sửa sau đợt test, nên tách riêng một plan mới cho:

1. Thu hẹp permission SQL theo role thay vì `PUBLIC`.
2. Bổ sung validation trong SP cho điểm, học kỳ, nhóm, số tiết, unique tên.
3. Giới hạn KHOA chỉ thấy/nhập điểm dữ liệu đúng khoa.
4. Sửa history khi thêm Lớp tín chỉ để lấy đúng `MALTC` identity mới.
