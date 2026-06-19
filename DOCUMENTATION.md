# TÀI LIỆU KỸ THUẬT, LÝ THUYẾT & HƯỚNG DẪN PHÁT TRIỂN (COMPREHENSIVE GUIDE)
**Dự án: Hệ thống Quản lý Điểm Sinh Viên Hệ Tín Chỉ (QLDSV_HTC)**

Tài liệu này được soạn thảo đặc biệt không chỉ như một sổ tay bảo trì (maintenance manual) mà còn là một **giáo trình học tập (learning resource)**. Nó giải thích cặn kẽ *tại sao* hệ thống được thiết kế như vậy (lý thuyết) và *làm thế nào* để can thiệp vào mã nguồn (thực hành).

---

## MỤC LỤC
1. [Lý Thuyết: Kiến trúc Tổng quan & Triết lý Thiết kế](#1-lý-thuyết-kiến-trúc-tổng-quan--triết-lý-thiết-kế)
2. [Lý Thuyết: Cơ chế Phân Quyền & Bảo Mật Cơ Sở Dữ Liệu](#2-lý-thuyết-cơ-chế-phân-quyền--bảo-mật-cơ-sở-dữ-liệu)
3. [Lý Thuyết & Thực Hành: Cơ chế Đóng Băng Dữ Liệu (Frozen Data)](#3-lý-thuyết--thực-hành-cơ-chế-đóng-băng-dữ-liệu-frozen-data)
4. [Lý Thuyết & Thực Hành: Real-time API & Validation Bất Đồng Bộ](#4-lý-thuyết--thực-hành-real-time-api--validation-bất-đồng-bộ)
5. [Lý Thuyết & Thực Hành: Lịch Sử Thao Tác & Hoàn Tác (Command Pattern)](#5-lý-thuyết--thực-hành-lịch-sử-thao-tác--hoàn-tác-command-pattern)
6. [Lý Thuyết & Thực Hành: Stored Procedures (SP) & Xử lý Giao dịch](#6-lý-thuyết--thực-hành-stored-procedures-sp--xử-lý-giao-dịch)
7. [Hướng Dẫn Modifying: Cách Sửa Từng Chức Năng Cốt Lõi](#7-hướng-dẫn-modifying-cách-sửa-từng-chức-năng-cốt-lõi)
8. [Xử lý Sự Cố Thường Gặp (Troubleshooting)](#8-xử-lý-sự-cố-thường-gặp-troubleshooting)

---

## 1. Lý Thuyết: Kiến trúc Tổng quan & Triết lý Thiết kế

Hệ thống được xây dựng theo mô hình **Client-Server** truyền thống nhưng kết hợp với **AJAX** để tăng tính tương tác.

### 1.1 Các Tầng (Layers) của Hệ thống:
- **Presentation Layer (Frontend):** Sử dụng HTML, CSS (Vanilla) và Javascript thuần (Vanilla JS). Nhiệm vụ của tầng này là vẽ giao diện (được render sẵn bằng Jinja2 từ Flask) và phản hồi lại thao tác của người dùng ngay lập tức (hiển thị lỗi, khóa nút).
- **Application Layer (Backend):** Sử dụng Python (Flask). Đóng vai trò là cầu nối (Controller). Nó nhận Request, kiểm tra phiên đăng nhập (Session), và gọi xuống Database. Backend này **cố tình giữ rất mỏng** (Thin Controller), không chứa nhiều logic nghiệp vụ.
- **Data Layer (Database):** Microsoft SQL Server. Đây là "bộ não" thực sự của hệ thống. Gần như 100% logic nghiệp vụ (Kiểm tra điểm, kiểm tra trùng lặp, ràng buộc khoa) đều nằm ở đây thông qua các **Stored Procedures**.

### 1.2 Triết lý "Zero-Schema Modification"
Hệ thống tuân thủ nghiêm ngặt nguyên tắc: **Không thay đổi cấu trúc bảng (Table Schema)**. Mọi tính năng mới, ràng buộc mới đều được giải quyết bằng cách nâng cấp đoạn code bên trong các Stored Procedures (SPs). Điều này giúp Database luôn tương thích với các ứng dụng cũ hoặc các báo cáo đã viết từ trước.

---

## 2. Lý Thuyết: Cơ chế Phân Quyền & Bảo Mật Cơ Sở Dữ Liệu

Đa số các ứng dụng web hiện đại dùng 1 tài khoản SQL duy nhất (ví dụ: `sa`) để kết nối DB, và phân quyền bằng Code (JWT, Session). **Tuy nhiên, hệ thống này làm ngược lại!** Nó sử dụng **Double-Authentication (Xác thực kép)**.

### 2.1 Đối với Giảng Viên (PGV / KHOA)
- **Lý thuyết:** Khi một giảng viên được tạo tài khoản (VD: `GV01`), hệ thống gọi lệnh `CREATE LOGIN [GV01]`. Nghĩa là bản thân SQL Server biết đến sự tồn tại của giảng viên này.
- **Cơ chế hoạt động:** 
  1. Giảng viên nhập User/Pass trên web.
  2. Flask dùng chính User/Pass đó để mở kết nối qua `pyodbc`.
  3. Nếu Pass sai, SQL Server sẽ từ chối kết nối ngay lập tức -> Đăng nhập thất bại.
  4. Nếu Pass đúng, SQL Server trả về kết nối. Giảng viên `GV01` đã đăng nhập thành công.
- **Tại sao phải làm vậy?** Để bảo mật tuyệt đối ở tầng Data. Dù ai đó hack được code Backend, họ cũng không thể query dữ liệu của Khoa khác nếu Database Role của họ chỉ là `KHOA`. Mọi truy vấn (SELECT, EXEC) đều bị SQL Server kiểm tra quyền dựa trên Login hiện tại.

### 2.2 Đối với Sinh Viên
- Sinh viên không có Login SQL riêng (vì số lượng SV quá lớn, tạo Login sẽ làm phình DB).
- Thay vào đó, bảng `SINHVIEN` chứa mật khẩu Plain-text. Sinh viên đăng nhập bằng cách Flask sử dụng một tài khoản SQL Server proxy tên là `sv` để gọi hàm `SP_DANGNHAP_SV`.

---

## 3. Lý Thuyết & Thực Hành: Cơ chế Đóng Băng Dữ Liệu (Frozen Data)

### 3.1 Lý thuyết: Tại sao cần Đóng Băng?
Trong giáo dục, dữ liệu của các năm học cũ (khóa cũ) là **bất khả xâm phạm**. Nếu một môn học của năm 2015 bị sửa đổi tên hoặc số tiết, nó sẽ làm hỏng bảng điểm đã in của sinh viên khóa đó. Cơ chế Đóng Băng (Freeze) sinh ra để ngăn chặn bất kỳ ai (kể cả PGV) chỉnh sửa dữ liệu của những năm trước một cột mốc nhất định.

### 3.2 Cơ chế hoạt động (Luồng chạy)
1. **Tại `app.py`:** Hàm `is_frozen(khoahoc_or_nienkhoa)` được định nghĩa. Nó trích xuất năm từ chuỗi (VD: "2021-2022" -> 2021). Nếu năm `< 2025`, nó trả về `True`.
2. **Tại API/Render:** Khi query danh sách Lớp/Môn/SV, Backend gọi hàm này và gán một cờ `IS_FROZEN` vào từng dòng dữ liệu (Row).
3. **Tại Frontend (Jinja2):** HTML kiểm tra `{% if l.IS_FROZEN %}` để render ra một cái icon ổ khóa `🔒`.
4. **Tại Frontend (Javascript):** Khi user click vào dòng bị đóng băng, hàm `chonDong()` sẽ đọc cờ `isFrozen`. Nếu `True`, nó gọi `toggleFormLock(true)` để tô xám toàn bộ input, và gọi `updateActionButtons('error')` để làm mờ nút Ghi/Hủy.

### 3.3 Hướng dẫn Tùy chỉnh (Thực hành)
- **Đổi mốc thời gian:** Mở `app.py`, tìm hàm `is_frozen()`. Đổi `LIMIT_YEAR = 2025` thành `2026` hoặc năm bạn muốn.
- **Bỏ đóng băng hoàn toàn:** Trong hàm `is_frozen()`, chỉ cần `return False` ở ngay dòng đầu tiên. Toàn bộ hệ thống sẽ được mở khóa.

---

## 4. Lý Thuyết & Thực Hành: Real-time API & Validation Bất Đồng Bộ

### 4.1 Lý thuyết: Validation Bất Đồng Bộ (Async Validation) là gì?
Khi người dùng đang gõ mã số (VD: Mã Lớp `D15CQCP01`), hệ thống không đợi họ bấm "Ghi" mới báo lỗi trùng mã. Nó báo lỗi ngay lập tức. Điều này được thực hiện bằng cách gửi các Request ngầm (AJAX/Fetch) lên server trong nền (Background).

### 4.2 Các API quan trọng trong hệ thống
Hệ thống xây dựng 2 API cốt lõi trong `app.py`:
1. **`/api/check_exists`**: Dùng khi **Thêm mới**. JS gửi mã đang gõ lên. Backend query xem mã đó đã có trong DB chưa. Trả về `True` (Đã tồn tại -> Báo lỗi đỏ) hoặc `False` (Hợp lệ -> Báo xanh).
2. **`/api/can_delete`**: Dùng khi **Chọn dòng**. Khi user click vào một Lớp/Môn, ta cần biết nút "Xóa/Hủy" có được bật hay không. Nếu Lớp đã có Sinh Viên, DB sẽ cấm xóa. Để tránh việc user bấm Xóa rồi mới báo lỗi, JS sẽ gọi ngầm API này. Nếu API trả về `False`, nút Xóa sẽ bị mờ đi ngay lập tức.

### 4.3 Hướng dẫn Tùy chỉnh (Thực hành)
**Ví dụ: Sửa điều kiện Hủy Lớp Tín Chỉ (API can_delete)**
Mặc định hệ thống chặn không cho hủy lớp tín chỉ nếu **đã có sinh viên được nhập điểm**.
1. **Mở `app.py`**, tìm route `@app.route('/api/can_delete')`.
2. Ở phần `elif target == 'loptinchi':`, bạn sẽ thấy câu SQL: 
   `SELECT COUNT(*) FROM DANGKY WHERE MALTC=? AND (DIEM_CC IS NOT NULL...)`
3. Nếu bạn muốn khắt khe hơn: "Cứ có sinh viên đăng ký là CẤM hủy" -> Sửa câu SQL thành: 
   `SELECT COUNT(*) FROM DANGKY WHERE MALTC=?`
4. **Mở `templates/loptinchi.html`**, tìm hàm `chonDong()`. Bạn sẽ thấy dòng `checkCanDelete('loptinchi', maltc);`. Đây chính là "cò súng" kích hoạt việc gọi API khi người dùng click chuột.

---

## 5. Lý Thuyết & Thực Hành: Lịch Sử Thao Tác & Hoàn Tác (Command Pattern)

### 5.1 Lý thuyết: Command Pattern
Tính năng Hoàn tác (Undo) được thiết kế theo mẫu thiết kế Command Pattern. Mỗi khi user thực hiện một hành động (Insert/Update/Delete), hệ thống không chỉ thực thi nó mà còn "đóng gói" toàn bộ thông tin của hành động đó vào một bộ nhớ tạm (Session).
- **Hành động Gốc:** Thêm Lớp (Mã: L01, Tên: Lớp 1)
- **Hành động Hoàn tác (Anti-action):** Xóa Lớp (Mã: L01)

### 5.2 Cơ chế Cây Ràng Buộc (Dependency Tree)
Nếu User Thêm Lớp (A), sau đó Thêm Sinh Viên (B) vào Lớp đó. 
Hệ thống không cho phép User Undo (A) trước, vì nếu Xóa Lớp (A) thì Sinh Viên (B) sẽ bị mất dữ liệu cha, gây lỗi DB.
- **Frontend `history.js`** sẽ tự động phân tích: Sinh viên B có cùng `malop` với Lớp A -> Suy ra B là "Con" của A. Nó vẽ B thụt lề dưới A và cấm bấm Undo A cho đến khi Undo B.

### 5.3 Hướng dẫn Thêm một tính năng Hoàn Tác mới (Thực hành)
1. **Ghi nhận lịch sử (app.py):** Ở route xử lý (VD: `/khoa/them`), sau khi gọi SP_THEM thành công, gọi lệnh:
   ```python
   push_history('THEM_KHOA', f'Đã thêm khoa {makhoa}', {'makhoa': makhoa, 'tenkhoa': tenkhoa})
   ```
2. **Định nghĩa Anti-action (app.py):** Ở hàm `history_undo()`, thêm nhánh:
   ```python
   elif atype == 'THEM_KHOA':
       cursor.execute("EXEC SP_XOA_KHOA ?", (d['makhoa'],))
       msg = f"Đã hoàn tác: Xóa khoa {d['makhoa']}"
   ```
3. **Cập nhật Giao diện (static/history.js):** 
   - Tìm biến `HISTORY_ICON` và thêm icon cho hành động của bạn: `THEM_KHOA: '➕'`.
   - Tìm biến `keyMap` trong hàm `openHistory()` và khai báo khóa chính: `'THEM_KHOA': 'makhoa'`. Thuật toán sẽ dùng chữ `makhoa` này để tìm các hành động con (VD: Thêm Lớp) để nhóm chúng lại thành cây.

---

## 6. Lý Thuyết & Thực Hành: Stored Procedures (SP) & Xử lý Giao dịch

### 6.1 Lý thuyết
Hầu hết lập trình viên hiện đại dùng ORM (như Entity Framework, SQLAlchemy) để thao tác DB. Tuy nhiên, hệ thống này dùng **Stored Procedure 100%**.
- **Ưu điểm:** Tốc độ cực nhanh, chống SQL Injection tự nhiên, bảo mật logic (Người dùng có quyền EXECUTE SP nhưng không có quyền gõ lệnh DELETE trực tiếp vào Table).
- **Quy ước chuẩn của SP trong dự án:** Mọi SP thao tác dữ liệu đều phải tuân thủ chuẩn trả về 2 cột: `KETQUA` (Số nguyên) và `THONGBAO` (Chuỗi chuỗi tiếng Việt).
  - `KETQUA = 1` hoặc `> 0`: Thành công (thường trả về cả ID vừa tạo).
  - `KETQUA < 0`: Thất bại do lỗi nghiệp vụ (VD: Trùng mã, điểm sai, lỗi ràng buộc).

### 6.2 Hướng dẫn thực hành: Thêm Validation trong SP
**Ví dụ: Sửa SP_NHAP_DIEM để chặn nhập điểm Âm.**
1. Mở file `setup_login.sql`, tìm `CREATE PROCEDURE SP_NHAP_DIEM`.
2. Bạn sẽ thấy đoạn code:
   ```sql
   IF @DIEM_CC IS NOT NULL AND (@DIEM_CC < 0 OR @DIEM_CC > 10)
   BEGIN SELECT -2 AS KETQUA, N'Điểm CC phải từ 0-10' AS THONGBAO RETURN END
   ```
3. Bạn có thể dễ dàng chèn thêm quy tắc. VD: Sinh viên phải có điểm CC >= 5 mới được nhập điểm GK:
   ```sql
   IF @DIEM_GK IS NOT NULL AND @DIEM_CC < 5
   BEGIN SELECT -99 AS KETQUA, N'Chưa đạt điểm CC, cấm nhập GK' AS THONGBAO RETURN END
   ```
4. Lưu ý: Sau khi sửa `setup_login.sql`, bạn **phải** chạy lại file này vào SQL Server (Xem phần 8. Troubleshooting).

---

## 7. Hướng Dẫn Modifying: Cách Sửa Từng Chức Năng Cốt Lõi

Để thêm/sửa một chức năng, hãy luôn ghi nhớ luồng đi của dữ liệu: 
**Database (SP) -> Backend (Route) -> Frontend (HTML Form) -> AJAX (JS)**.

### 7.1 Sửa Logic Đăng ký Môn Học (Sinh Viên)
**Mục tiêu:** Sinh viên có thể đăng ký nhiều lớp tín chỉ của CÙNG 1 môn học (Học song song).
1. **Mở `setup_login.sql`**, tìm `SP_DANGKY_LTC`.
2. Tìm và XÓA (hoặc comment) đoạn kiểm tra trùng `MAMH`:
   ```sql
   IF EXISTS (
       SELECT 1 FROM DANGKY D JOIN LOPTINCHI LTC ON D.MALTC = LTC.MALTC
       WHERE D.MASV = @MASV AND LTC.MAMH = @MAMH AND D.MALTC <> @MALTC
   )
   ```
3. Khởi chạy lại script SQL. Hệ thống sẽ ngay lập tức cho phép SV đăng ký nhiều lớp cùng môn.

### 7.2 Phân Quyền Bắt Buộc (Scoping Khoa)
**Mục tiêu:** Đảm bảo Giảng viên khoa CNTT không thể dùng thủ thuật URL để xem hoặc nhập điểm lớp tín chỉ của khoa VT.
1. **Tại `app.py` (Hàm login):** Khi GV đăng nhập, hệ thống query cột `MAKHOA` từ bảng `GIANGVIEN` và lưu cứng vào `session['makhoa']`.
2. **Tại Route (Ví dụ `/loptinchi`):** 
   ```python
   if session.get('group') == 'KHOA':
       mk = session.get('makhoa', '') # ÉP BUỘC DÙNG KHOA CỦA SESSION
   else:
       mk = request.args.get('makhoa') # Cho phép PGV tự chọn
   ```
Nếu muốn thêm trang mới (VD: Báo Cáo), bạn **bắt buộc** phải copy đoạn code ép `session['makhoa']` này vào để rào quyền.

---

## 8. Xử lý Sự Cố Thường Gặp (Troubleshooting)

### 8.1 Lỗi "Mã lỗi font: Chữ tiếng Việt biến thành dấu ? hoặc ký tự lạ"
- **Lý thuyết:** Khi bạn dùng lệnh `sqlcmd` để nạp SP vào DB, nếu file `.sql` là chuẩn UTF-8 nhưng **không có chữ ký BOM (Byte Order Mark)**, SQL Server sẽ đọc file bằng bảng mã mặc định của Windows (cp1252), khiến chữ Tiếng Việt bị mã hóa sai (Mojibake). Khi Flask query lên lại, nó đọc nguyên xi cục Mojibake đó hiển thị ra web.
- **Cách fix:** 
  1. Mở file `setup_login.sql` bằng Notepad -> Save As -> Bấm Encoding chọn **UTF-8 with BOM**.
  2. Dùng lệnh có cờ `-f 65001` (Ép UTF-8):
     `sqlcmd -S localhost\SQLEXPRESS -d QLDSV_HTC -E -C -f 65001 -i setup_login.sql`

### 8.2 Tài khoản bất đồng bộ ("Login đã tồn tại" nhưng UI bảo chưa có)
- **Triệu chứng:** Nút "Tạo tài khoản" bị mờ. Bấm "Xóa tài khoản" báo lỗi.
- **Nguyên nhân:** Có thể do quản trị viên vào thẳng SSMS xóa User nhưng quên xóa Login. Hoặc do script `setup_login.sql` (có vòng lặp tự động cấp Login cho toàn bộ GV) đã chạy ngầm và tạo tài khoản mà bạn không biết.
- **Cách fix triệt để:** 
  1. Mở SQL Server Management Studio (SSMS).
  2. Mở mục **Security -> Logins**, xóa Login của GV đó.
  3. Mở mục **Databases -> QLDSV_HTC -> Security -> Users**, xóa User của GV đó.
  4. Lên Web thao tác lại từ đầu.

### 8.3 Nút Ghi/Xóa bị xám không bấm được dù đã chọn dòng
- **Nguyên nhân 1:** Dòng dữ liệu bạn bấm vào có cờ `IS_FROZEN = True` (Khóa học cũ). Hệ thống khóa UI để bảo vệ data.
- **Nguyên nhân 2:** API `/api/can_delete` bị lỗi hoặc đang trả về `False`. Mở DevTools (F12) -> Tab Network -> Click vào dòng -> Xem API `can_delete` có báo Status 200 và trả về `{"can_delete": true}` hay không.
- **Cách ép mở khóa (Không khuyến khích):** Mở Chrome DevTools (F12) -> Console -> Gõ `updateActionButtons('editing'); btnXoa.disabled = false;`. Nhưng hãy nhớ, kể cả khi bạn hack được nút trên UI, **Backend và DB vẫn sẽ chặn lại** nếu dữ liệu vi phạm ràng buộc! Đây là sức mạnh của triết lý Fail-Fast Backend Validation.
