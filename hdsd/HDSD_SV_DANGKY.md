# Hướng Dẫn Test: Đăng Ký Lớp Tín Chỉ (Tài khoản Sinh Viên)

**Cập nhật:** 2026-04-18 | **Áp dụng cho:** Module `/dangky` — nhóm **SV**

---

## ⚠️ Điều kiện tiên quyết

### Bước 1 — Chạy script SQL trên SSMS

Mở **SSMS** → kết nối `localhost\SQLEXPRESS` bằng sa → chạy 2 file theo thứ tự:

```
1. setup_login.sql   (tạo/cập nhật tất cả SP, cấp quyền)
2. fix_sv_login.sql  (tùy chọn — chỉ chạy nếu chưa update SP_DANGNHAP_SV)
```

### Bước 2 — Đảm bảo có dữ liệu LTC

PGV phải đã tạo ít nhất 1 lớp tín chỉ trong hệ thống (trang `/loptinchi`).  
Nếu không có LTC nào → trang đăng ký sẽ hiển thị cảnh báo vàng.

### Bước 3 — Tài khoản SV hợp lệ

Sinh viên phải có `PASSWORD` trong bảng `SINHVIEN` và `DANGHIHOC = 0`.

---

## 🔐 Đăng nhập SV

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Mở `http://localhost:5000` | Trang đăng nhập |
| 2 | Chọn vai trò **Sinh Viên** | Hiện form nhập Mã SV + Mật khẩu |
| 3 | Nhập Mã SV (vd: `N15DCCN001`), Mật khẩu | — |
| 4 | Bấm Đăng nhập | Chuyển vào Dashboard SV |
| 5 | Kiểm tra menu | Có `📝 Đăng ký Lớp Tín Chỉ` và `📄 Bảng Điểm Cá Nhân` |

---

## ✅ Test trang Đăng ký Lớp Tín Chỉ

### TC-DK-01: Truy cập trang

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Click **"📝 Đăng ký Lớp Tín Chỉ"** | Mở `/dangky` |
| 2 | Kiểm tra thông tin SV trên đầu trang | Hiển thị đúng `Mã SV`, `Họ tên`, `Lớp` |
| 3 | Kiểm tra dropdown Niên khóa | **Chỉ hiển thị các niên khóa mà PGV đã mở LTC** — không có năm thừa |
| 4 | Dropdown Học kỳ + Niên khóa **cùng 1 hàng ngang** | ✅ |

---

### TC-DK-02: Niên khóa tự động tracking theo LTC thực tế

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Mở trang PGV (`/loptinchi`) kiểm tra có LTC ở niên khóa nào | Ví dụ: `2024-2025` |
| 2 | Đăng nhập SV, vào trang Đăng ký LTC | — |
| 3 | Kiểm tra dropdown Niên khóa | **Chỉ thấy `2024-2025`** (đúng như PGV đã mở) |
| 4 | PGV thêm LTC cho niên khóa `2025-2026` | — |
| 5 | SV reload trang → kiểm tra dropdown | Xuất hiện thêm `2025-2026` |

---

### TC-DK-03: Tìm lớp tín chỉ

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Chọn **Niên khóa** từ dropdown | — |
| 2 | Chọn **Học kỳ** | Tự động tải danh sách LTC (debounce 400ms) |
| 3 | Kiểm tra bảng kết quả | Hiện: MALTC, Môn học (MAMH), Nhóm, Giảng viên, Khoa, Số SV đã ĐK / Tối thiểu |
| 4 | LTC đã đăng ký | Hiển thị badge `✓ Đã đăng ký` thay vì nút |
| 5 | LTC chưa đăng ký | Hiển thị nút `Đăng ký` màu đỏ |

---

### TC-DK-04: Đăng ký lớp tín chỉ

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Tìm LTC chưa đăng ký | Nút `Đăng ký` hiển thị |
| 2 | Bấm **Đăng ký** | Nút chuyển thành `...` (đang xử lý) |
| 3 | Sau 1-2 giây | Nút thay bằng badge `✓ Đã đăng ký` |
| 4 | Reload trang, tìm lại LTC đó | Vẫn hiển thị `✓ Đã đăng ký` |

---

### TC-DK-05: Trường hợp chưa có LTC nào

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | PGV chưa tạo LTC nào | — |
| 2 | SV vào trang Đăng ký LTC | Dropdown Niên khóa **rỗng** |
| 3 | Hiển thị cảnh báo | `⚠️ Chưa có lớp tín chỉ nào được mở. Vui lòng liên hệ Phòng Giáo Vụ.` (màu vàng) |

---

### TC-DK-06: Bảng điểm cá nhân

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Từ Dashboard SV click **"📄 Bảng Điểm Cá Nhân"** | Mở `/phieu_diem` |
| 2 | Kiểm tra danh sách | Hiển thị các môn đã đăng ký kèm điểm CC/GK/CK/TK |
| 3 | Môn chưa có điểm | Ô điểm trống hoặc `—` |

---

## ❌ Lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Đăng nhập SV bị redirect về login | Chưa chạy `setup_login.sql` | Chạy lại file SQL trên SSMS |
| Dropdown Niên khóa rỗng | Chưa có LTC nào trong DB | PGV tạo LTC trước |
| Bấm Đăng ký → lỗi đỏ | SV chưa được cấp quyền INSERT/DANGKY | Chạy lại `setup_login.sql` |
| Thông tin SV sai (Lớp: rỗng) | SP_DANGNHAP_SV cũ chưa có cột MALOP | Chạy lại `setup_login.sql` |
