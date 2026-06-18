# CHANGELOGS_006 — Sửa lỗi giao diện & ràng buộc UI toàn diện
## Ngày: 2026-04-20

---

### 1. `static/history.js`
**Lý do**: Nút Xóa sáng lên sai khi chuyển sang editing mode (trước khi checkCanDelete trả kết quả). Nút Tạo mới sáng sai ở trang Môn Học do biến `selectedMAMH` không được nhận diện.

- `updateActionButtons('editing')`: Đổi `btnXoa.disabled = false` → `btnXoa.disabled = true` (chờ checkCanDelete async)
- `enableSaveOnInputFocus()`: Thêm check biến `selectedMAMH` bên cạnh `sel`
- `resetValidationState()`: Thêm check biến `selectedMAMH` bên cạnh `sel`

---

### 2. `app.py` — Route `/phieu_diem`
**Lý do**: Template `phieu_diem.html` sử dụng biến `sv` (dict) và `phieu_diem` (list), nhưng app.py truyền `diem_list` và chỉ truyền `masv`/`hoten` riêng lẻ → bảng điểm SV luôn trống.

- Truyền biến `sv` dạng dict gồm: MASV, HOTEN, MALOP, NGAYSINH
- Đổi tên biến `diem_list` → `phieu_diem` cho khớp template
- Tính `DIEM_HM` = CC*0.1 + GK*0.3 + CK*0.6 trong Python vì SP trả `DIEM_TK` không đúng mapping

---

### 3. `app.py` — Route `/dangky/loc`
**Lý do**: Nút "Hủy đăng ký" vẫn sáng khi SV đã có điểm → click vào thì lỗi nhưng không dim.

- Thêm trường `CO_DIEM` (boolean) vào response JSON
- Kiểm tra bảng DANGKY: nếu DIEM_CC/DIEM_GK/DIEM_CK != NULL → CO_DIEM = true

---

### 4. `app.py` — Route `/dangky`
**Lý do**: SV khóa 2025-2029 vẫn thấy niên khóa quá khứ (VD: 2024-2025) trong dropdown.

- Lọc niên khóa theo KHOAHOC của lớp SV: chỉ hiển thị NK mà nk_start nằm trong [kh_start, kh_end)

---

### 5. `templates/dangky.html`
**Lý do**: Tương ứng thay đổi #3 — frontend cần dim nút hủy.

- Kiểm tra `ltc.CO_DIEM`: nếu true → nút "Hủy đăng ký" bị disabled + hiển thị badge "📝 Đã có điểm"
- Áp dụng cho cả bảng "Đã chọn" và bảng "Kết quả tìm kiếm"

---

### 6. Tất cả template bảng — Scroll tối đa 10 dòng
**Lý do**: Bảng hiển thị tất cả dòng không giới hạn, giao diện bị tràn khi dữ liệu nhiều.

Các file đã thêm `<div style="max-height:400px; overflow-y:auto;">` bọc quanh `<table>`:
- `templates/khoa.html`
- `templates/lop.html`
- `templates/monhoc.html`
- `templates/giangvien.html`
- `templates/sinhvien.html`
- `templates/loptinchi.html`

---

### 7. `templates/monhoc.html`
**Lý do**: Thiếu `data-text` → hàm `locBang()` không tìm được dòng nào.

- Thêm `data-text="{{ m.MAMH }} {{ m.TENMH }}"` vào mỗi `<tr>`

---

### 8. `templates/loptinchi.html`
**Lý do**: Thiếu `data-nk`, `data-hk`, `data-khoa`, `data-text` → bộ lọc JS không hoạt động.

- Thêm `data-nk`, `data-hk`, `data-khoa`, `data-text` vào mỗi `<tr>`
