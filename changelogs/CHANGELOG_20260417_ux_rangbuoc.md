# CHANGELOG — 2026-04-17 — Cập Nhật UX & Ràng Buộc

## Phiên bản: v1.1 · Kế tiếp: CHANGELOG_20260417_nhapdulieu.md

---

## 1. Tính Năng Mới

### 1.1 History Modal — Lịch sử hoàn tác (Undo)
**File mới:** `static/history.js`

- Nút **🕓 Lịch sử** xuất hiện trên toolbar của: Lớp, Sinh Viên, Môn Học, Lớp Tín Chỉ, Nhập Điểm
- Modal hiển thị **10 thao tác gần nhất** trong phiên làm việc (lưu trong session)
- Hỗ trợ hoàn tác (Undo) cho tất cả thao tác CRUD:
  - Thêm Lớp → Undo = Xóa lớp vừa thêm
  - Xóa Lớp → Undo = Khôi phục lại lớp
  - Sửa Lớp → Undo = Phục hồi giá trị cũ
  - Tương tự cho: Sinh Viên, Môn Học, Lớp Tín Chỉ
- **Quan hệ cha–con** được hiển thị dạng cây:
  - Thao tác Sinh Viên thụt lề vào, có chú thích ràng buộc với Lớp
  - Cảnh báo màu vàng khi hành động có thể ảnh hưởng đến dữ liệu con
- Click **Hoàn tác** → xác nhận → gọi `POST /history/undo` → reload trang

**Routes mới trong `app.py`:**
```
GET  /history          — Trả JSON 10 hành động gần nhất
POST /history/undo     — Thực hiện hoàn tác theo index
```

---

### 1.2 Ràng Buộc Nghiệp Vụ Bổ Sung

**Xóa Lớp (`/lop/xoa`):**
- Kiểm tra `SELECT COUNT(*) FROM SINHVIEN WHERE MALOP=?` trước khi xóa
- Nếu còn SV → hiển thị: `"Không thể xóa: lớp X còn N sinh viên."`

**Xóa Môn Học (`/monhoc/xoa`):**
- Kiểm tra bảng `DANGKY JOIN LOPTINCHI` xem có SV đang đăng ký môn này không
- Nếu có → hiển thị: `"Không thể xóa: môn học đang có N sinh viên đã đăng ký."`
- *(SP_XOA_MONHOC đã chặn lớp TC — app.py chặn thêm tầng SV)*

---

### 1.3 Lọc Tức Thì (Không Cần Nút Tìm Kiếm)

| Trang | Bộ lọc tức thì |
|---|---|
| `lop.html` | Dropdown Khoa + ô text (mã/tên lớp) |
| `monhoc.html` | Ô text (mã/tên môn học) |
| `loptinchi.html` | Dropdown Niên khóa + Học kỳ + Khoa + ô text (môn/GV) |
| `dangky.html` | Chọn Niên khóa/HK → tự gọi API sau 400ms debounce |

Tất cả dùng JavaScript lọc DOM trực tiếp — không reload trang.

---

### 1.4 Niên Khóa Gợi Ý Thông Minh

**SP mới:** `SP_GET_ALL_NIENKHOA` — lấy danh sách niên khóa hiện có trong LOPTINCHI

**Helper mới trong `app.py`:** `get_nienkhoa_list()`
- Kết hợp: niên khóa từ DB + sinh tự động từ 2015 đến năm hiện tại + 5
- Không bao giờ trống, luôn có gợi ý hợp lý

**Giao diện:**
- Dropdown `<select>` chọn nhanh niên khóa đã có
- Ô nhập tay bên dưới nếu cần niên khóa chưa tồn tại
- Validate định dạng `YYYY-YYYY` trước khi submit — tránh nhập sai như `2015-2050`

**Áp dụng cho:** `loptinchi.html`, `nhapdiem.html`, `dangky.html`, `lop.html` (khóa học)

---

## 2. Thay Đổi File

| File | Loại thay đổi |
|---|---|
| `static/history.js` | **Tạo mới** — modal lịch sử dùng chung |
| `app.py` | **Sửa** — thêm `push_history()`, `get_nienkhoa_list()`, routes `/history`, `/history/undo`; cập nhật tất cả routes CRUD để ghi history + ràng buộc |
| `setup_login.sql` | **Thêm** — `SP_GET_ALL_NIENKHOA` |
| `templates/lop.html` | **Viết lại** — lọc tức thì, datalist khóa học, nút Lịch sử |
| `templates/monhoc.html` | **Sửa** — lọc tức thì, nút Lịch sử |
| `templates/sinhvien.html` | **Sửa** — nút Lịch sử |
| `templates/loptinchi.html` | **Viết lại** — lọc tức thì 4 chiều, niên khóa select+nhập tay, validate, nút Lịch sử |
| `templates/nhapdiem.html` | **Sửa** — niên khóa select+nhập tay, nút Lịch sử |
| `templates/dangky.html` | **Sửa** — niên khóa select+nhập tay, tự tìm lớp khi đổi filter |

---

## 3. Lưu Ý Triển Khai

> ⚠️ **Cần chạy lại `setup_login.sql` trên SSMS** để tạo `SP_GET_ALL_NIENKHOA`

History chỉ lưu trong **session** (RAM) — mất khi đăng xuất hoặc restart server. Đây là thiết kế cố ý.
