# 📋 Hướng Dẫn Test Chức Năng — Quản Lý Sinh Viên

> **Phiên bản:** v4 (cập nhật 2026-04-18)  
> **Áp dụng cho:** Module `/sinhvien` — tài khoản nhóm **PGV**  
> **URL ứng dụng:** `http://localhost:5000`

---

## 🔐 Điều kiện trước khi test

| Mục | Yêu cầu |
|---|---|
| Tài khoản | Đăng nhập bằng tài khoản thuộc nhóm **PGV** (ví dụ: `GV01` / mật khẩu tương ứng) |
| Dữ liệu | Phải có ít nhất **1 lớp** trong hệ thống (xem trang `/lop`) |
| Server | Flask app đang chạy tại `localhost:5000` |

---

## 🗂️ Cấu trúc Sub-Form 2 Cấp

Trang Sinh viên sử dụng **Sub-Form 2 cấp**:

```
Cấp 1: Danh sách Lớp (panel bên trái)
         ↓ Click chọn lớp
Cấp 2: Danh sách Sinh viên của lớp đó (panel bên phải)
```

---

## ✅ CÁC KỊCH BẢN TEST

---

### TC-SV-01: Truy cập trang Sinh viên

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Đăng nhập bằng tài khoản PGV | Chuyển vào Dashboard |
| 2 | Click vào menu **"Sinh viên"** | Mở trang `/sinhvien` |
| 3 | Quan sát giao diện | Hiển thị **panel trái** (danh sách lớp) và **panel phải** (chờ chọn lớp) |
| 4 | Kiểm tra trạng thái nút | `Tạo mới`, `Xóa`, `Lưu dữ liệu`, `Phục hồi` đều **mờ** (disabled) |

> [!NOTE]
> Trang không hiển thị sinh viên cho đến khi bạn click chọn một lớp ở panel trái.

---

### TC-SV-02: Chọn lớp để xem danh sách sinh viên

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Click vào một lớp trong danh sách bên trái (ví dụ: `D15CQCP01`) | Lớp được đánh dấu bằng viền đỏ |
| 2 | Quan sát panel phải | Tải danh sách sinh viên của lớp đó |
| 3 | Kiểm tra tiêu đề panel phải | Hiển thị: `Sinh viên lớp: D15CQCP01` |
| 4 | Kiểm tra trạng thái nút | Nút `Tạo mới` sáng lên, các nút khác vẫn mờ |

---

### TC-SV-03: Thêm sinh viên mới (Tạo mới = INSERT trực tiếp)

> [!IMPORTANT]
> Quy trình: Điền đầy đủ form → Bấm **"＋ Tạo mới"**. Nút này luôn thực hiện INSERT.

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Chọn lớp `D15CQCP01` ở panel trái | Panel phải hiển thị SV thuộc lớp |
| 2 | Nhập `Mã SV`: `TEST001` | Hệ thống kiểm tra real-time: hiện `✅ Mã hợp lệ.` |
| 3 | Nhập `Họ`: `Nguyễn Văn` | — |
| 4 | Nhập `Tên`: `Test` | — |
| 5 | Chọn `Giới tính`: Nam (0) | — |
| 6 | Nhập `Địa chỉ`: `Quận 9` *(tuỳ chọn)* | — |
| 7 | Nhập `Ngày sinh`: `2000-01-01` *(tuỳ chọn)* | — |
| 8 | Kiểm tra `Mã lớp SV` đã tự điền chưa | Phải là `D15CQCP01` |
| 9 | **Bấm nút "＋ Tạo mới"** | Trang reload, sinh viên `TEST001` xuất hiện trong danh sách |
| 10 | Quan sát flash message | `✅ Thêm thành công.` hoặc thông báo của SP |

---

### TC-SV-04: Validation — Trùng mã sinh viên

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Nhập `Mã SV` = `N15DCCN001` (đã tồn tại) | Sau 500ms hiện `❌ Mã này đã tồn tại!` |
| 2 | Ô nhập có viền đỏ | Đúng |
| 3 | Thử bấm nút bất kỳ | Tất cả nút bị **mờ hoàn toàn** (disabled) |
| 4 | Xóa mã và nhập mã mới hợp lệ | Thông báo lỗi biến mất, nút hoạt động trở lại |

---

### TC-SV-05: Validation — Thiếu thông tin bắt buộc

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Để trống ô `Mã SV` | — |
| 2 | Bấm **"＋ Tạo mới"** | Alert: `Vui lòng nhập Mã SV, Họ và Tên.` |
| 3 | Nhập `Mã SV` nhưng để trống `Họ` | — |
| 4 | Bấm **"＋ Tạo mới"** | Alert tương tự |

---

### TC-SV-06: Nút Lưu — Chỉ mờ mặc định, sáng khi click ô nhập

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Mở trang, chưa làm gì | Nút `Lưu dữ liệu` **mờ** |
| 2 | Click vào ô `Họ` hoặc bất kỳ ô nào trong form | Nút `Lưu dữ liệu` **sáng lên** |
| 3 | Không chọn dòng nào, bấm `Lưu dữ liệu` | Alert: `Vui lòng chọn một sinh viên trong danh sách để cập nhật.` |

---

### TC-SV-07: Cập nhật thông tin sinh viên (Lưu = UPDATE)

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Click chọn sinh viên `TEST001` trong bảng | Form tự điền đầy đủ thông tin; nút `Lưu` sáng, nút `Xóa` sáng/mờ tùy ràng buộc |
| 2 | Sửa `Địa chỉ` thành `Quận 1` | — |
| 3 | **Bấm nút "💾 Lưu dữ liệu"** | Trang reload, địa chỉ đã cập nhật thành `Quận 1` |
| 4 | Flash message | `✅ Cập nhật thành công.` |

---

### TC-SV-08: Phục hồi dữ liệu (Hoàn tác thay đổi trên form)

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Click chọn sinh viên `TEST001` | Form điền sẵn |
| 2 | Sửa `Họ` thành `Sai Họ` | — |
| 3 | **Bấm "↩ Phục hồi"** | `Họ` quay về giá trị ban đầu của SV đang chọn |
| 4 | Kiểm tra | Không có thay đổi gì được lưu vào DB |

---

### TC-SV-09: Xóa sinh viên (Không có ràng buộc)

> [!CAUTION]
> Chỉ có thể xóa sinh viên **chưa đăng ký lớp tín chỉ** nào. Nếu đã đăng ký, nút Xóa sẽ mờ.

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Click chọn sinh viên `TEST001` (vừa tạo, chưa đăng ký LTC) | Nút `Xóa` sáng |
| 2 | **Bấm "🗑 Xóa"** | Xuất hiện hộp thoại xác nhận: `Xóa sinh viên "TEST001"?` |
| 3 | Bấm **OK** | Trang reload, `TEST001` không còn trong danh sách |
| 4 | Flash message | `✅ Xóa thành công.` |

---

### TC-SV-10: Kiểm tra ràng buộc xóa — SV đã đăng ký LTC

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Click chọn sinh viên `N15DCCN001` (đã có đăng ký LTC) | Nút `Xóa` **mờ** (disabled) |
| 2 | Hover chuột vào nút Xóa | Tooltip: `Không thể xóa vì dữ liệu đang có ràng buộc con.` |
| 3 | Thử bấm vào nút Xóa | Không phản hồi gì (đã bị vô hiệu hóa) |

---

### TC-SV-11: Làm mới form (Xóa trang)

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Đang có sinh viên được chọn | Form hiển thị dữ liệu |
| 2 | **Bấm "🧹 Làm mới form"** | Form xóa trắng toàn bộ |
| 3 | Không có dòng nào được chọn | Đúng |
| 4 | Nút `Lưu dữ liệu` | Trở về trạng thái **mờ** |
| 5 | Nút `Xóa` | **Mờ** |

---

### TC-SV-12: Lịch sử thao tác

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Thực hiện thêm/sửa/xóa một số sinh viên | — |
| 2 | **Bấm "🕓 Lịch sử"** | Modal lịch sử mở ra |
| 3 | Kiểm tra danh sách | Hiển thị các thao tác gần nhất, sắp xếp theo nhánh |
| 4 | Thử bấm "Hoàn tác" một thao tác | Trang reload, dữ liệu trở về trước thao tác đó |

---

### TC-SV-13: Chuyển đổi giữa các lớp

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Click lớp `D15CQCP01` | Danh sách SV của lớp đó hiển thị |
| 2 | Click lớp khác, ví dụ `D15CQIS01` | Danh sách cập nhật sang SV của lớp `D15CQIS01` |
| 3 | Kiểm tra tiêu đề | Tiêu đề cập nhật theo lớp đang chọn |
| 4 | Form bên phải | **Reset trắng**, không còn SV cũ |

---

### TC-SV-14: Thêm sinh viên vào lớp khác lớp đang xem

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Chọn lớp `D15CQCP01` | Đang xem SV lớp này |
| 2 | Thay đổi `Mã lớp SV` trong form thành `D15CQIS01` | — |
| 3 | Nhập đầy đủ thông tin SV mới | — |
| 4 | Bấm **"＋ Tạo mới"** | Sinh viên được tạo **và gán vào lớp `D15CQIS01`** |
| 5 | Kiểm tra | Trang chuyển sang danh sách lớp `D15CQIS01` và hiển thị SV mới |

---

## ❌ Các trường hợp lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Tất cả nút mờ sau khi gõ mã | Trùng mã hoặc validation lỗi | Xóa/sửa mã trong ô nhập |
| Nút Xóa luôn mờ | SV đã đăng ký lớp tín chỉ | Hủy đăng ký trước ở module Đăng ký LTC |
| Bấm Tạo mới không làm gì | Chưa nhập đủ Mã SV, Họ, Tên | Nhập đầy đủ ba trường bắt buộc |
| Lưu dữ liệu không làm gì | Chưa click chọn dòng từ bảng | Click chọn dòng trước khi Lưu |
| Flash message đỏ sau INSERT | Stored Procedure báo lỗi DB | Đọc nội dung thông báo để xác định nguyên nhân |

---

## 📌 Dữ liệu test tham khảo

```
Mã SV mới hợp lệ để test: TEST001 → TEST005
Lớp có sẵn:   D15CQCP01  (Công nghệ phần mềm 2015)
               D15CQIS01  (Hệ thống thông tin 2015)
               D15CQMT01  (Mạng máy tính 2015)
SV đã có chú ý: N15DCCN001 (đã đăng ký LTC → không xóa được)
```

---

*File này được tạo tự động bởi Antigravity AI — 2026-04-18*
