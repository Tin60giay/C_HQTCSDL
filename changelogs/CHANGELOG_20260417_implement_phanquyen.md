# Changelog — Implement Phân Quyền 3 Nhóm (PGV / KHOA / SV)

**Ngày:** 2026-04-17  
**Mục tiêu:** Triển khai đầy đủ phân quyền 3 nhóm theo yêu cầu đề bài

---

## Ràng buộc áp dụng

| Quy tắc | Trạng thái |
|---|---|
| Không sửa schema DB (bảng, cột, dữ liệu) | ✅ Tuân thủ |
| Không sửa SP đã có (`SP_DANGNHAP_GV`, `SP_DANGNHAP_SV`) | ✅ Tuân thủ |
| Được thêm SP mới | ✅ Đã thêm 8 SP |
| Được sửa `app.py` và `templates/` | ✅ Đã sửa |

---

## 1. `setup_login.sql` — Thêm 8 Stored Procedures mới

> Không sửa bất kỳ SP cũ nào. Toàn bộ SP mới được nối vào cuối file.

| SP mới | Nhóm dùng | Mô tả |
|---|---|---|
| `SP_GETALL_KHOA` | PGV | Danh sách tất cả khoa |
| `SP_GETALL_GIANGVIEN` | PGV | Danh sách GV kèm tên khoa |
| `SP_GETALL_SINHVIEN` | PGV | Danh sách SV, lọc được theo `@MAKHOA` |
| `SP_GETALL_LOPTINCHI` | PGV + KHOA | Danh sách lớp TC, lọc theo niên khóa/học kỳ/khoa, đếm SV đăng ký |
| `SP_NHAP_DIEM` | PGV + KHOA | Cập nhật điểm CC/GK/CK, kiểm tra SV có đăng ký không |
| `SP_DANGKY_LTC` | SV | Đăng ký lớp TC, kiểm tra trùng và lớp đã hủy |
| `SP_XEM_PHIEU_DIEM` | SV | Xem điểm + tính điểm TK (CC×10% + GK×30% + CK×60%) |
| `SP_GET_LOPTINCHI_DANGKY` | SV | Danh sách lớp TC có thể đăng ký, có cờ `DA_DANGKY` |

**GRANT EXECUTE:**
- SP_GETALL_* + SP_NHAP_DIEM → `PUBLIC`
- SP_DANGKY_LTC, SP_XEM_PHIEU_DIEM, SP_GET_LOPTINCHI_DANGKY → `[sv]`

---

## 2. `app.py` — Logic phân nhóm và session

### Thêm config PGV_LOGINS
```python
PGV_LOGINS = ['GV01', 'GV05']
```

### Sửa xử lý đăng nhập GV
**Trước:**
```python
session['group'] = row.TENGROUP.strip()   # = tên khoa
```
**Sau:**
```python
magv = row.USER_NAME.strip()
nhom = 'PGV' if magv in PGV_LOGINS else 'KHOA'
session['group']   = nhom                   # 'PGV' hoặc 'KHOA'
session['tenkhoa'] = row.TENGROUP.strip()   # tên khoa để hiển thị
```

### Sửa xử lý đăng nhập SV
Thêm `session['tenkhoa']` để đồng nhất với GV.

### Sửa route `/dashboard`
Truyền thêm `tenkhoa` xuống template.

---

## 3. `templates/dashboard.html` — Menu 3 nhóm

### Sửa info-card — hiển thị vai trò đúng
**Trước:** Chỉ phân biệt `GV` / `SV`  
**Sau:** Phân biệt `PGV` / `KHOA` / `SV`

### Sửa menu-grid — 3 nhánh
**Trước:** 2 nhánh (`role == 'GV'` → 6 item, `else` → 3 item)  
**Sau:**

| Nhóm | Menu items |
|---|---|
| PGV | 9 items: Khoa, Lớp CN, GV, SV, Môn Học, Mở LTC, Nhập Điểm, Báo Cáo, Tạo TK |
| KHOA | 3 items: Xem LTC, Nhập Điểm, Báo Cáo |
| SV | 3 items: Đăng ký LTC, Bảng Điểm, Học Phí |

---

## Files đã thay đổi

| File | Loại thay đổi |
|---|---|
| `setup_login.sql` | Thêm 8 SP mới vào cuối file |
| `app.py` | Thêm `PGV_LOGINS`, sửa session GV/SV, sửa dashboard route |
| `templates/dashboard.html` | Sửa info-card và menu-grid theo 3 nhóm |
| `changelogs/CHANGELOG_20260417_implement_phanquyen.md` | Tạo mới (file này) |
