# Hệ Thống QLDSV - Quản Lý Điểm Sinh Viên Hệ Tín Chỉ

**Trường:** Học viện Công nghệ Bưu chính Viễn thông (PTIT)  
**Database:** `QLDSV_HTC`  
**Phiên bản hiện tại:** v2.0 (Phase 4 - Freeze Historical Data & Realtime Validation)

Đây là ứng dụng Web quản trị cơ sở dữ liệu chuyên nghiệp được xây dựng trên Flask và SQL Server. Hệ thống cung cấp cơ chế bảo mật xác thực kép (Application Role + DB Security) và giao diện Single-Page Layout tối ưu UX.

---

## 🏗️ 1. Cấu Trúc File & Vai Trò Cốt Lõi

Toàn bộ logic nghiệp vụ được dàn đều qua các tệp tin với sự phân tách trách nhiệm rõ ràng. Nếu bạn muốn **Sửa tính năng nào, hãy nhìn vào file tương ứng dưới đây**:

- **`app.py`**: Trái tim của Backend. Chứa tất cả routing (URL), khởi tạo kết nối DB (`pyodbc`), phân quyền đăng nhập (`PGV`, `KHOA`, `SV`), xử lý try/catch cho các giao dịch CSDL (Commit/Rollback).
- **`CRITICAL.md`**: Hiến pháp của hệ thống. File tài liệu quy định mọi giới hạn cứng (Bounds) của CSDL (Ví dụ: Năm 2025 là năm chốt sổ, Điểm tối đa là 10, Học kỳ nằm từ 1-3...).
- **`setup_login.sql`**: Chứa toàn bộ các Stored Procedures (SP). Bất cứ lúc nào thêm chức năng liên quan đến việc thống kê, cập nhật đa bảng thì thêm SP vào đây.
- **`static/history.js`**: **Bộ não của Frontend!!** File này chứa toàn bộ các hệ thống tương tác phức tạp nhất của UI, từ khóa nút (Disable buttons) đến kiểm tra dữ liệu theo thời gian thực (Realtime Validation). Thay vì viết JS rải rác, tất cả đều được nén ở đây.

---

## 🛠️ 2. Từ Điển Hàm / Chức Năng Đặc Biệt (Tra Cứu Nhanh)

Dưới đây là danh sách các hàm ma thuật được áp dụng trong hệ thống, giúp bạn dễ dàng chỉnh sửa khi hệ thống thay đổi yêu cầu.

### A. Tầng Backend (Trong file `app.py`)

1. **`get_db_connection(login, password)`**  
   - Chức năng: Khởi tạo kết nối đến SQL Server bằng chính tài khoản Server của người dùng chứ không xài chung (Bảo mật tầng SQL).
   
2. **`is_frozen(nienkhoa_hoac_khoahoc)`**  
   - Chức năng: Thuật toán rào chắn Lịch Sử. Xác định xem năm được ném vào có nhỏ hơn niên khóa hiện hành (2025) hay không. Nếu `True`, toàn bộ các hành động `Thêm/Xóa/Sửa` trên dữ liệu đó sẽ bị chặn đứng tại máy chủ.

3. **`@app.route('/api/can_delete')`** *(Dependency Tree Checker)*  
   - Chức năng: Chạy ngầm kiểm tra xem một bản ghi (Ví dụ: 1 Lớp) có chứa các bản ghi con (Sinh viên) hay không để bật/tắt nút Xóa trên giao diện, ngăn chặn lỗi khóa ngoại (Foreign Key Constraint Error) ngay cả trước khi người dùng kịp bấm.

4. **`@app.route('/api/check_exists')`**  
   - Chức năng: API check trùng lặp ID (Khóa chính). Khi gõ mã lớp hoặc mã môn, API này báo về ngay để UI tô viền màu đỏ.

### B. Tầng Frontend (Trong file `static/history.js`)

1. **`updateActionButtons(state)`**  
   - Chức năng: Máy trạng thái (State Machine) của toàn bộ các Nút Bấm (`Tạo mới`, `Ghi Dữ Liệu`, `Xóa`, `Phục hồi`). 
   - Tham số trạng thái: 
     - `'idle'`: Không chọn gì (Nút thêm sáng, nút ghi mờ).
     - `'adding'`: Đang nhập dữ liệu mới.
     - `'editing'`: Đã click vào grid chuẩn bị sửa.
     - `'error'`: Vi phạm quy tắc (Tất cả các nút bị phong ấn).
     
2. **`toggleFormLock(lock_boolean, [field_ids])`**  
   - Chức năng: Khóa (readonly) hàng loạt thẻ Input/Select. Rất hữu ích khi chọn một dòng dữ liệu đang bị Đóng Băng (`IS_FROZEN_CONTEXT`), mọi ô chữ sẽ tự động chìm xuống xám xịt.

3. **`enableSaveOnInputFocus()`**  
   - Chức năng: Một con "mắt thần". Nó rà soát tất cả mọi ô nhập liệu (Input). Bất cứ lúc nào có sự thay đổi (Gõ chữ, đổi số), nó sẽ báo hiệu cho nút **Lưu Dữ liệu** sáng lên. Đồng thời tích hợp kiểm tra luật lệ cơ bản (Tránh số âm < 0).

4. **`checkRealtime(inputId, table)`**  
   - Chức năng: Kích hoạt Delay 500ms (Debounce) gọi lên `api/check_exists` để xem mã có ai nhập chưa. Được móc vào ngay lúc khởi động `DOMContentLoaded`.

### C. Logic Ở Các File `HTML` Cụ Thể

1. **`lop.html` - Hàm `comboOpen()`**  
   - Chức năng: Được tạo ra để chèn ép tính năng tự động lọc của trình duyệt. Nó ép Input Box xổ thẳng 100% danh sách Niên Khóa ra khi Click vào thay vì giấu đi.
   
2. **`nhapdiem.html` - Hàm `batDau()` & `tinhHM()`**  
   - Chức năng: 
     - `batDau()`: Tự động Tải (Auto Reload) lưới điểm Sinh viên dựa trên API Fetch mà không làm chớp màn hình. 
     - `tinhHM()`: Check bảo kê điểm số. Quét xem có ai nhập điểm < 0 hoặc > 10 không. Nếu có, bôi đỏ ô TextBox, khóa vĩnh viễn nút Ghi Điểm.

3. **`monhoc.html` - Hàm `validateMonHocLT_TH()`**  
   - Chức năng: Check chéo Logic giữa Tiết Lý Thuyết (Bắt buộc >= 30) và Thực hành (>=0) trước khi mở khóa cho phép đi tiếp.

---

## 🔒 3. Quyền Hạn User và Database

Cơ chế phân quyền của hệ thống trải dài suốt dọc Backend tới Hệ Quản Trị CSDL:

| Phân Vùng | Database (Tên Đăng Nhập) | Giao diện | Thuộc logic file nào | 
|---|---|---|---|
| **PGV (Giáo vụ)** | `GV01`, `GV02` | Toàn quyền thao tác trên mọi màn hình. | `app.py` (Lấy động từ Database Role `PGV`) |
| **KHOA (Khoa)** | `GV03`, `GV04`, `GV05`, ... | Chỉ xem, không được tạo lớp mới, được quyền lên điểm. | `app.py` (Lấy động từ Database Role `KHOA`) |
| **SV (Sinh viên)** | `sv` / (mật khẩu dùng chung: `123`) | Cấp độ tài khoản DB được thắt chặt. Xác thực tài khoản riêng rẽ dựa trên mã (Ví dụ `N15DCCN001`) qua Procedure. | `SP_DANGNHAP_SV` trong `setup_login.sql` |

---

## 🚢 4. Hướng Dẫn Run Code Nhanh

**Bước 1:** Bật kết nối nội bộ
1. Đảm bảo SQL Server đang chạy `localhost\SQLEXPRESS`.
2. Script cần chạy (nếu là máy mới): `QLDSV_HTC.sql` (Cấu trúc), `QLDSV_HTC_utf8.sql` (Dữ liệu), và BẮT BUỘC có `setup_login.sql` (Các hàm Logic).

**Bước 2:** Bật Terminal chạy App
```bash
python app.py
# Mở ở http://localhost:5001
```

**Bước 3:** Đăng nhập Testing
- PGV: `GV01` / `GV01`
- Khoa: `GV02` / `GV02`
- Sinh viên: `N15DCQT001` / *(để trống - mk default)* 

> **Lưu ý Quan Trọng Khi Phát Triển:** Viết code frontend cập nhật JS rất dễ bị dính Cache của Trình Duyệt. Nếu bạn mới sửa xong file `history.js` mà load web không có gì suy xuyển, bắt buộc bấm tổ hợp phím **`CTRL + F5`** (Hoặc Xóa bộ đệm) để trải nghiệm giao diện phiên bản mới nhất.

---
_Đây là tài liệu được sinh ra với mục đích dẫn đường (Map) cho quy trình phát triển tương lai. Update Date: 2026_
