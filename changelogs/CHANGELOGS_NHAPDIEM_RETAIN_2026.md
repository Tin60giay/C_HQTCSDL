# CHANGELOGS_NHAPDIEM_RETAIN_2026.md

> Ngày: 2026-06-18  |  Phạm vi: Giữ form nhập điểm + cho xem NK cũ
> Liên quan: `plans/PLANT_NHAPDIEM_RETAIN_2026.md`

---

## 1. Tổng quan thay đổi

| # | File | Hành động | Mô tả |
|---|------|-----------|--------|
| 1 | `setup_login.sql` | Sửa `SP_NHAP_DIEM` | Thêm block chặn nếu LTC thuộc NK < 2025-2026 (mã lỗi -10) |
| 2 | `app.py` | Thêm helper `get_all_nienkhoa_ltc()` | Lấy TẤT CẢ NK có LTC (kể cả cũ), bỏ filter 2025 |
| 3 | `app.py` | Sửa route `/nhapdiem` | Đổi từ `get_nienkhoa_list()` → `get_all_nienkhoa_ltc()` |
| 4 | `app.py` | Sửa route `/loptinchi` | Đổi từ `get_nienkhoa_list()` → `get_all_nienkhoa_ltc()` |
| 5 | `app.py` | Sửa route `/nhapdiem/batdau` | Trả thêm `is_frozen` để FE biết LTC có bị đóng băng |
| 6 | `app.py` | Sửa route `/nhapdiem/ghidiem` | Nhận JSON, trả JSON, gộp lỗi từng dòng; KHÔNG redirect |
| 7 | `templates/nhapdiem.html` | Sửa `batDau()` | Render input với class `frozen-input` + disabled nếu frozen |
| 8 | `templates/nhapdiem.html` | Sửa `ghiDiem()` | Chuyển sang AJAX, giữ form, gọi lại `batDau()` sau khi lưu |

---

## 2. Chi tiết SQL — `SP_NHAP_DIEM`

**Trước**: Chỉ chặn "quá hạn SV" (`KHOAHOC + 7`).

**Sau**: Thêm check ngay sau block quá hạn:
```sql
-- [PLANT_NHAPDIEM_RETAIN_2026] Chặn nếu LTC thuộc NK đã đóng băng (< 2025-2026)
IF @NamNK_ND IS NOT NULL AND @NamNK_ND < 2025
BEGIN
    SELECT -10 AS KETQUA,
           N'Lớp tín chỉ thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể nhập/sửa điểm' AS THONGBAO
    RETURN
END
```

Mã lỗi: **-10** (đã có sẵn trong bảng mã lỗi tổng - xem CRITICAL.md).

---

## 3. Chi tiết Python — `app.py`

### 3.1 Helper mới `get_all_nienkhoa_ltc()` (sau `get_nienkhoa_for_sv`)
```python
def get_all_nienkhoa_ltc():
    """[PLANT_NHAPDIEM_RETAIN_2026] Lấy TẤT CẢ niên khóa thực tế trong LOPTINCHI
    (kể cả đã đóng băng < 2025) - dùng cho trang Nhập Điểm / Xem LTC.
    """
```
- Tái sử dụng `SP_GET_ALL_NIENKHOA` (đã có sẵn).
- **Khác biệt so với `get_nienkhoa_list()`**: helper cũ lọc `start_year >= 2025` + sinh thêm 2025→hiện tại+1. Helper mới trả nguyên xi từ DB.

### 3.2 Sửa route `/nhapdiem`
Đổi 1 dòng: `nienkhoa_list=get_nienkhoa_list()` → `nienkhoa_list=get_all_nienkhoa_ltc()`.

### 3.3 Sửa route `/loptinchi`
Đổi tương tự: PGV/KHOA giờ thấy được tất cả NK kể cả cũ để xem LTC quá khứ.

### 3.4 Sửa route `/nhapdiem/batdau`
Thêm 7 dòng tính `is_frozen` và trả về JSON:
```python
is_frozen = False
try:
    nk_start = int(nienkhoa.split('-')[0])
    is_frozen = nk_start < 2025
except Exception:
    is_frozen = False
return jsonify({..., 'is_frozen': is_frozen})
```

### 3.5 Sửa route `/nhapdiem/ghidiem`
- Chuyển `request.form` → `request.get_json(silent=True)`.
- Gom tất cả lỗi từ `SP_NHAP_DIEM` (trả về `KETQUA` < 0 + `THONGBAO`) thành mảng `errors[]`.
- Trả JSON: `{ok, success_count, errors, total}`.
- **Không** redirect, **không** flash. Form được giữ nguyên ở FE.
- Commit 1 lần sau khi xử lý tất cả dòng.

---

## 4. Chi tiết Frontend — `nhapdiem.html`

### 4.1 Bỏ `<form>`, dùng `<div id="diemFormWrap">`
- Không còn submit chuyển trang.
- Nút "Ghi điểm" gọi AJAX `fetch('/nhapdiem/ghidiem', {method: 'POST', body: JSON})`.

### 4.2 Thêm biến `currentIsFrozen`
- Lưu trạng thái frozen của LTC hiện tại.
- Khi frozen: disable toàn bộ input + disable nút ghi + show banner 🔒.

### 4.3 Class CSS mới `.frozen-input`
```css
.frozen-input { background: #0e0e0e !important; color: #71717a !important;
                border-color: #2a2a2a !important; cursor: not-allowed !important; }
```

### 4.4 Banner thông báo
- `#frozenBanner`: hiện banner đỏ khi LTC thuộc NK đã đóng băng.
- `#ghiOkBanner`: hiện banner xanh khi ghi thành công toàn bộ.
- `#ghiErrBanner`: hiện banner đỏ khi có lỗi (kèm danh sách SV lỗi).

### 4.5 Hàm `ghiDiem()` mới
```javascript
async function ghiDiem() {
    if (currentIsFrozen) { show frozen banner; return; }
    // Gom dữ liệu từ DOM
    const payload = { maltc, masv_list, diem_cc_list, diem_gk_list, diem_ck_list };
    const res = await fetch('/nhapdiem/ghidiem', { method: 'POST', body: JSON.stringify(payload) });
    const data = await res.json();
    if (data.ok && data.errors.length === 0) {
        // ✅ Thành công: gọi batDau() để reload dữ liệu từ server
        await batDau();
    } else {
        // ⚠ Có lỗi: hiển thị chi tiết, KHÔNG xóa dữ liệu đã nhập
        show errBanner(errors);
    }
}
```

**Đặc điểm quan trọng**:
- ✅ Khi lưu thành công: gọi lại `batDau()` → server trả dữ liệu mới nhất → render lại bảng.
- ✅ Khi có lỗi: KHÔNG xóa form, hiển thị chi tiết từng SV lỗi để user sửa.
- ✅ Khi frozen: nút bị disable, banner hiện, không thể ghi.

---

## 5. Tích hợp với các thay đổi trước

- **PLANT_LTC_BUGS_2026**: Filter NK ≥ 2025 cho `/dangky` SV vẫn giữ (SV chỉ thấy NK trong phạm vi khóa học). Helper mới `get_all_nienkhoa_ltc()` chỉ dùng cho PGV/KHOA trong `/nhapdiem` và `/loptinchi`.
- **Mã lỗi -10**: đã có sẵn trong bảng lỗi, dùng đồng nhất với các SP khác.
- **IS_FROZEN**: tái sử dụng helper `is_frozen()` đã có sẵn ở cả FE (loptinchi.html) và BE (app.py).

---

## 6. File tham chiếu

- `plans/PLANT_NHAPDIEM_RETAIN_2026.md` - Kế hoạch chi tiết
- `hdsd/HDSD_NHAPDIEM_RETAIN_2026.md` - Hướng dẫn test
- `setup_login.sql` - SP_NHAP_DIEM (sửa)
- `app.py` - helper + 3 route (sửa)
- `templates/nhapdiem.html` - AJAX + frozen handling (sửa)
