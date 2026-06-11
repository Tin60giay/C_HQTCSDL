# CHANGELOG — 2026-04-17 — Triển Khai Nhập Liệu (3.2)

## Tổng Quan
Triển khai đầy đủ 6 chức năng nhập liệu theo yêu cầu mục 3.2, hoàn thiện hệ thống phân quyền 3 nhóm PGV/KHOA/SV.

---

## Thay Đổi

### setup_login.sql — Thêm 17 Stored Procedures mới

| SP | Mô tả |
|---|---|
| SP_GET_ALL_MONHOC | Lấy toàn bộ danh sách môn học |
| SP_THEM_MONHOC | Thêm môn học mới |
| SP_SUA_MONHOC | Cập nhật thông tin môn học |
| SP_XOA_MONHOC | Xóa môn học |
| SP_GET_DSLOP | Lấy danh sách lớp cử nhân (lọc theo khoa) |
| SP_THEM_LOP | Thêm lớp cử nhân |
| SP_SUA_LOP | Cập nhật lớp cử nhân |
| SP_XOA_LOP | Xóa lớp cử nhân |
| SP_GET_DSSV | Lấy danh sách sinh viên theo lớp |
| SP_GET_THONGTIN_SV | Lấy thông tin 1 sinh viên theo MASV |
| SP_THEM_SV | Thêm sinh viên |
| SP_SUA_SV | Cập nhật thông tin sinh viên |
| SP_XOA_SV | Xóa sinh viên |
| SP_THEM_LOPTINCHI | Mở lớp tín chỉ mới |
| SP_SUA_LOPTINCHI | Cập nhật thông tin lớp tín chỉ |
| SP_XOA_LOPTINCHI | Hủy lớp tín chỉ (HUYLOP=1) |
| SP_GET_SINHVIEN_THEO_LTC | Lấy DS sinh viên + điểm của 1 lớp TC |

### app.py — Thêm routes và helpers

**Helpers mới:**
- `require_group(*groups)` — decorator kiểm tra quyền theo nhóm
- `login_required` — decorator kiểm tra đăng nhập

**Routes mới:**
- `GET/POST /monhoc`, `/monhoc/them`, `/monhoc/ghi`, `/monhoc/xoa`
- `GET/POST /lop`, `/lop/them`, `/lop/ghi`, `/lop/xoa`
- `GET /sinhvien`, `GET /sinhvien/<malop>`, `POST /sinhvien/them`, `/sinhvien/ghi`, `/sinhvien/xoa`
- `GET/POST /loptinchi`, `/loptinchi/them`, `/loptinchi/ghi`, `/loptinchi/xoa`
- `GET /nhapdiem`, `POST /nhapdiem/batdau` (AJAX JSON), `POST /nhapdiem/ghidiem`
- `GET /dangky`, `POST /dangky/loc` (AJAX), `POST /dangky/dangky` (AJAX)
- `GET /phieu_diem`

### Templates mới tạo

| File | Chức năng |
|---|---|
| `templates/lop.html` | CRUD Lớp Cử Nhân |
| `templates/sinhvien.html` | SubForm 2 cấp: Lớp → Sinh Viên |
| `templates/monhoc.html` | CRUD Môn Học |
| `templates/loptinchi.html` | Quản lý Lớp Tín Chỉ (PGV ghi/xóa, KHOA chỉ xem) |
| `templates/nhapdiem.html` | Nhập điểm AJAX — tự tính HM |
| `templates/dangky.html` | Đăng ký LTC — AJAX, badge Đã đăng ký |
| `templates/phieu_diem.html` | Phiếu điểm sinh viên |

### templates/dashboard.html — Cập nhật href

Thay thế `href="#"` bằng URL thực:
- PGV: `/lop`, `/sinhvien`, `/monhoc`, `/loptinchi`, `/nhapdiem`
- KHOA: `/loptinchi`, `/nhapdiem`
- SV: `/dangky`, `/phieu_diem`

---

## Phân Quyền

| Chức năng | PGV | KHOA | SV |
|---|---|---|---|
| Quản lý Lớp | ✅ | ❌ | ❌ |
| Quản lý Sinh Viên | ✅ | ❌ | ❌ |
| Quản lý Môn Học | ✅ | ❌ | ❌ |
| Mở/Hủy Lớp TC | ✅ | 👁 Xem | ❌ |
| Nhập Điểm | ✅ | ✅ | ❌ |
| Đăng ký LTC | ❌ | ❌ | ✅ |
| Xem Phiếu Điểm | ❌ | ❌ | ✅ |

---

## Ghi Chú Kỹ Thuật

- Không thay đổi schema database (TUYỆT ĐỐI)
- Không sửa SP cũ — chỉ thêm SP mới
- PGV/KHOA phân biệt qua `PGV_LOGINS` list trong `app.py` (không có cột DB)
- AJAX dùng `fetch()` + JSON response `{ok, msg, ...}`
- Điểm HM tính client-side realtime + server-side khi ghi
