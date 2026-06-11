# Kế Hoạch Implement Chức Năng Nhập Liệu (3.2)

**Ngày lập:** 2026-04-17  
**Trạng thái:** ✅ Đã được duyệt

---

## Context

Hệ thống QLDSV hiện tại đã có:
- Đăng nhập 3 nhóm (PGV / KHOA / SV)
- Dashboard phân quyền menu theo nhóm
- 8 Stored Procedure mới (SP_GETALL_*, SP_NHAP_DIEM, SP_DANGKY_LTC, SP_XEM_PHIEU_DIEM, SP_GET_LOPTINCHI_DANGKY)

Cần triển khai 6 chức năng nhập liệu theo yêu cầu 3.2, thêm folder `hdsd/`, `plans/` để lưu lịch sử, và tạo file HDSD.

---

## Ràng buộc

| Quy tắc | |
|---|---|
| ❌ Không sửa DB schema (bảng, cột, dữ liệu) | Bất di bất dịch |
| ❌ Không sửa SP cũ (`SP_DANGNHAP_GV`, `SP_DANGNHAP_SV`) | Giữ nguyên |
| ✅ Được thêm SP mới vào `setup_login.sql` | |
| ✅ Được sửa `app.py` và `templates/` | |

---

## Phần 1 — SP Mới Thêm vào `setup_login.sql`

### 1.1 SP cho Lớp (LOP) — PGV
| SP | Tham số chính | Mô tả |
|---|---|---|
| `SP_GET_DSLOP` | `@MAKHOA` | DS lớp theo khoa (NULL = tất cả) |
| `SP_THEM_LOP` | MALOP, TENLOP, KHOAHOC, MAKHOA | Thêm lớp mới |
| `SP_SUA_LOP` | MALOP, TENLOP, KHOAHOC, MAKHOA | Cập nhật lớp |
| `SP_XOA_LOP` | `@MALOP` | Xóa lớp (kiểm tra còn SV không) |

### 1.2 SP cho Sinh viên — PGV
| SP | Tham số chính | Mô tả |
|---|---|---|
| `SP_GET_DSSV` | `@MALOP` | DS sinh viên theo lớp |
| `SP_GET_THONGTIN_SV` | `@MASV` | Thông tin 1 SV (dùng cho trang đăng ký LTC) |
| `SP_THEM_SV` | MASV, HO, TEN, PHAI, DIACHI, NGAYSINH, MALOP | Thêm sinh viên |
| `SP_SUA_SV` | MASV, HO, TEN, PHAI, DIACHI, NGAYSINH, MALOP | Cập nhật sinh viên |
| `SP_XOA_SV` | `@MASV` | Xóa sinh viên (kiểm tra đã đăng ký LTC chưa) |

### 1.3 SP cho Môn học — PGV
| SP | Tham số chính | Mô tả |
|---|---|---|
| `SP_GET_ALL_MONHOC` | _(không)_ | Danh sách tất cả môn học |
| `SP_THEM_MONHOC` | MAMH, TENMH, SOTIET_LT, SOTIET_TH | Thêm môn học |
| `SP_SUA_MONHOC` | MAMH, TENMH, SOTIET_LT, SOTIET_TH | Cập nhật môn học |
| `SP_XOA_MONHOC` | `@MAMH` | Xóa môn học (kiểm tra đã có LTC chưa) |

### 1.4 SP cho Lớp tín chỉ — PGV
| SP | Tham số chính | Mô tả |
|---|---|---|
| `SP_THEM_LOPTINCHI` | NIENKHOA, HOCKY, MAMH, NHOM, MAGV, MAKHOA, SOSVTOITHIEU | Mở lớp TC |
| `SP_SUA_LOPTINCHI` | MALTC, NIENKHOA, HOCKY, MAMH, NHOM, MAGV, MAKHOA, SOSVTOITHIEU | Cập nhật |
| `SP_XOA_LOPTINCHI` | `@MALTC` | Hủy lớp TC (set HUYLOP=1) |

### 1.5 SP cho Nhập điểm — PGV + KHOA
| SP | Tham số chính | Mô tả |
|---|---|---|
| `SP_GET_SINHVIEN_THEO_LTC` | `@MALTC` | DS SV + điểm hiện tại của lớp TC |

> `SP_NHAP_DIEM` đã có — gọi lặp từ app.py cho từng dòng khi Ghi điểm

---

## Phần 2 — Routes Mới trong `app.py`

### Helper phân quyền
```python
from functools import wraps

def require_group(*groups):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            if session.get('group') not in groups:
                flash('Bạn không có quyền truy cập chức năng này.')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return wrapped
    return decorator
```

### 2.1 Lớp — PGV only
```
GET  /lop                   Danh sách lớp (lọc theo khoa nếu cần)
POST /lop/them              Thêm lớp
POST /lop/ghi               Ghi/cập nhật lớp
POST /lop/xoa               Xóa lớp
```

### 2.2 Sinh viên — PGV only (SubForm 2 cấp)
```
GET  /sinhvien              Cấp 1: DS lớp để chọn
GET  /sinhvien/<malop>      Cấp 2: DS SV của lớp đó
POST /sinhvien/them         Thêm SV
POST /sinhvien/ghi          Ghi/cập nhật SV
POST /sinhvien/xoa          Xóa SV
```

### 2.3 Môn học — PGV only
```
GET  /monhoc                Danh sách môn học
POST /monhoc/them           Thêm môn học
POST /monhoc/ghi            Ghi môn học
POST /monhoc/xoa            Xóa môn học
```

### 2.4 Lớp tín chỉ — PGV only
```
GET  /loptinchi             DS lớp TC (filter niên khóa/học kỳ)
POST /loptinchi/them        Mở lớp TC
POST /loptinchi/ghi         Ghi lớp TC
POST /loptinchi/xoa         Hủy lớp TC
```

### 2.5 Đăng ký LTC — SV only
```
GET  /dangky                Form đăng ký
POST /dangky/timkiem        AJAX: thông tin SV theo MASV
POST /dangky/loc            AJAX: lọc LTC theo niên khóa + học kỳ
POST /dangky/dangky         Thực hiện đăng ký
```

### 2.6 Nhập điểm — PGV + KHOA
```
GET  /nhapdiem              Form nhập điểm
POST /nhapdiem/batdau       AJAX: load DS SV của lớp TC
POST /nhapdiem/ghidiem      Ghi toàn bộ điểm
```

---

## Phần 3 — Templates Mới

Tất cả kế thừa CSS variables dark theme từ `dashboard.html`.

| Template | Nhóm | Đặc điểm |
|---|---|---|
| `lop.html` | PGV | Bảng + form CRUD, Thêm/Xóa/Ghi/Phục hồi/Thoát |
| `sinhvien.html` | PGV | SubForm 2 cấp: panel lớp trái + bảng SV phải |
| `monhoc.html` | PGV | Bảng + form CRUD |
| `loptinchi.html` | PGV | Bảng + filter niên khóa/học kỳ + form CRUD |
| `dangky.html` | SV | Nhập MASV → hiện thông tin → chọn niên khóa/HK → bảng LTC |
| `nhapdiem.html` | PGV+KHOA | Dropdown filter → Bắt đầu → bảng điểm inline + Ghi điểm |

### Cấu trúc chung CRUD templates
```
[Header: Tên chức năng] [Nút Thoát → /dashboard]
[Toolbar: Thêm | Xóa | Ghi | Phục hồi]
[Bảng dữ liệu — click dòng → highlight + load form]
[Form nhập liệu]
[Flash messages]
```

### `nhapdiem.html` — đặc biệt
```
[Filter: Niên khóa | Học kỳ | Môn học | Nhóm] [Bắt đầu]
---
[Bảng điểm: Mã SV* | Họ tên* | Điểm CC | Điểm GK | Điểm CK | Điểm HM*]
  (* = readonly, Điểm HM = CC×0.1 + GK×0.3 + CK×0.6, tính realtime bằng JS)
[Ghi điểm]
```

### `dangky.html` — đặc biệt
```
[Nhập Mã SV] → [Họ tên | Lớp hiện ra]
[Niên khóa | Học kỳ] → [Bảng LTC: MAMH | Tên MH | Nhóm | Tên GV | Số SV | Trạng thái]
  (DA_DANGKY=1 → badge "Đã đăng ký", DA_DANGKY=0 → nút "Đăng ký")
```

---

## Phần 4 — Cập nhật `dashboard.html`

Gắn `href` thực cho các menu item:

| Nhóm | Menu | href |
|---|---|---|
| PGV | Quản lý Lớp Cử Nhân | `/lop` |
| PGV | Quản lý Sinh Viên | `/sinhvien` |
| PGV | Quản lý Môn Học | `/monhoc` |
| PGV | Mở Lớp Tín Chỉ | `/loptinchi` |
| PGV | Nhập Điểm | `/nhapdiem` |
| KHOA | Xem Lớp Tín Chỉ | `/loptinchi` |
| KHOA | Nhập Điểm | `/nhapdiem` |
| SV | Đăng ký Lớp Tín Chỉ | `/dangky` |
| SV | Bảng Điểm Cá Nhân | `/phieu_diem` |

---

## Phần 5 — Thứ Tự Thực Hiện

1. Tạo folder `hdsd/`, `plans/`
2. Lưu kế hoạch này vào `plans/`
3. Thêm SP mới vào `setup_login.sql`
4. Thêm `require_group()` helper vào `app.py`
5. Implement từng cặp route + template:
   - `/lop` + `lop.html`
   - `/monhoc` + `monhoc.html`
   - `/loptinchi` + `loptinchi.html`
   - `/sinhvien` + `sinhvien.html`
   - `/nhapdiem` + `nhapdiem.html`
   - `/dangky` + `dangky.html`
6. Cập nhật `dashboard.html` — gắn href thực
7. Tạo `hdsd/HDSD_20260417_v1.md`
8. Tạo `changelogs/CHANGELOG_20260417_nhapdulieu.md`
9. Cập nhật `DOCUMENTATION.md`

---

## Files Sẽ Thay Đổi

| File | Loại thay đổi |
|---|---|
| `setup_login.sql` | Thêm ~14 SP mới |
| `app.py` | Thêm helper + ~15 routes |
| `templates/dashboard.html` | Sửa href các menu item |
| `templates/lop.html` | Tạo mới |
| `templates/sinhvien.html` | Tạo mới |
| `templates/monhoc.html` | Tạo mới |
| `templates/loptinchi.html` | Tạo mới |
| `templates/dangky.html` | Tạo mới |
| `templates/nhapdiem.html` | Tạo mới |
| `hdsd/HDSD_20260417_v1.md` | Tạo mới |
| `changelogs/CHANGELOG_20260417_nhapdulieu.md` | Tạo mới |
| `DOCUMENTATION.md` | Cập nhật |
