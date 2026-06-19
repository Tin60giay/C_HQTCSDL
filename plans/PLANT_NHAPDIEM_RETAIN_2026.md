# PLANT_NHAPDIEM_RETAIN_2026 — Giữ form nhập điểm + cho xem NK cũ

> Ngày: 2026-06-18  |  Phạm vi: Sửa `SP_NHAP_DIEM` + `app.py` + `nhapdiem.html`
> Tham chiếu: Kế hoạch trước `plans/PLANT_LTC_BUGS_2026.md`

---

## 1. Yêu cầu từ user

1. **Giữ form sau khi ghi điểm**: Hiện tại `ghiDiem()` POST thẳng → redirect về `/nhapdiem` (mất filter, phải nhập lại NK/HK/MH/NHOM). Cần đổi sang **AJAX** để giữ nguyên form, chỉ hiển thị thông báo thành công.
2. **Không cho sửa điểm lớp có NK quá khứ**: Hiện `SP_NHAP_DIEM` chỉ chặn "quá hạn SV" (KHOAHOC+7), chưa chặn "NK đóng băng" (< 2025-2026). Cần thêm check.
3. **Mở lớp tín chỉ cho xem NK quá khứ**: PGV/KHOA vào `/loptinchi` và `/nhapdiem` phải thấy được các NK cũ (đã đóng băng) để xem. Hiện tại `get_nienkhoa_list()` chỉ lấy NK ≥ 2025.

---

## 2. Phân tích code hiện tại

### 2.1 `SP_NHAP_DIEM` (setup_login.sql:326)
- Đã có check "quá hạn" với mã lỗi `-20`.
- **Thiếu**: check "NK < 2025-2026" → nên thêm mã lỗi `-10` (theo convention đã có trong bảng lỗi).

### 2.2 Route `/nhapdiem` (app.py:1306)
- Truyền `nienkhoa_list=get_nienkhoa_list()` — chỉ chứa NK ≥ 2025.
- **Cần**: thêm NK cũ để PGV/KHOA có thể filter xem.

### 2.3 Route `/nhapdiem/batdau` (app.py:1330)
- Query trực tiếp `LOPTINCHI` theo NK → vẫn hoạt động nếu user gõ NK cũ (không filter ở đây).
- Tuy nhiên cần trả thêm `IS_FROZEN` để FE biết có cho sửa điểm hay không.

### 2.4 Route `/nhapdiem/ghidiem` (app.py:1368)
- POST thẳng → redirect → mất form.
- **Cần**: chuyển sang nhận JSON, trả JSON. Gộp lỗi thành 1 response.

### 2.5 `nhapdiem.html`
- `<form action="/nhapdiem/ghidiem">` + submit truyền thống.
- **Cần**: bỏ `<form>`, dùng AJAX `fetch` để không reload.

---

## 3. Thiết kế thay đổi

### 3.1 Sửa `SP_NHAP_DIEM`
Thêm ngay sau check quá hạn:
```sql
-- [PLANT_NHAPDIEM_RETAIN_2026] Chặn nếu LTC thuộc NK đã đóng băng (< 2025-2026)
IF @NamNK_ND IS NOT NULL AND @NamNK_ND < 2025
BEGIN
    SELECT -10 AS KETQUA,
           N'Lớp tín chỉ thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể nhập/sửa điểm' AS THONGBAO
    RETURN
END
```

### 3.2 Thêm helper `get_all_nienkhoa_ltc()` (app.py)
Lấy TẤT CẢ NK có LTC (kể cả cũ), trả về list các chuỗi `YYYY-YYYY`.
```python
def get_all_nienkhoa_ltc():
    """Lấy tất cả niên khóa thực tế trong LOPTINCHI (kể cả đã đóng băng)."""
    conn, _ = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC SP_GET_ALL_NIENKHOA")
        return [r[0].strip() for r in cursor.fetchall() if r[0]]
    except:
        return []
    finally:
        conn.close()
```

### 3.3 Sửa route `/nhapdiem`
- Đổi `get_nienkhoa_list()` → `get_all_nienkhoa_ltc()`.

### 3.4 Sửa route `/nhapdiem/batdau`
- Trả thêm `is_frozen` (bool) cho FE biết.
- Sắp xếp theo NK cũ → mới để PGV thấy được lịch sử.

### 3.5 Sửa route `/nhapdiem/ghidiem`
- Nhận JSON: `maltc`, `masv_list`, `diem_cc/gk/ck_list`.
- Trả JSON: `ok`, `success_count`, `errors[]`.
- Không redirect.

### 3.6 Sửa `nhapdiem.html`
- Bỏ `<form>`, dùng `<div id="tbodyDiem">` + `fetch()` AJAX.
- Hàm `ghiDiem()`: gom dữ liệu, gọi AJAX, hiển thị kết quả.
- Khi ghi thành công: hiển thị "✅ Đã lưu X/X SV thành công" + **giữ nguyên form**.
- Khi có lỗi (VD: NK frozen): hiển thị banner đỏ + **KHÔNG xóa dữ liệu đã nhập**.
- Nếu LTC frozen: disable tất cả input + btnGhi (chỉ cho xem).
- Khi load lại sau khi ghi: gọi lại `batDau()` để cập nhật giá trị mới nhất từ server.

---

## 4. File cần sửa

| File | Hành động |
|------|-----------|
| `setup_login.sql` | Sửa `SP_NHAP_DIEM` thêm check frozen NK |
| `app.py` | Thêm `get_all_nienkhoa_ltc()` |
| `app.py` | Sửa route `/nhapdiem` (dùng helper mới) |
| `app.py` | Sửa route `/nhapdiem/batdau` (trả `is_frozen`) |
| `app.py` | Sửa route `/nhapdiem/ghidiem` (JSON in/out) |
| `templates/nhapdiem.html` | Sửa `ghiDiem()` → AJAX; xử lý `is_frozen`; giữ form |
| `plans/PLANT_NHAPDIEM_RETAIN_2026.md` | Tạo mới |
| `changelogs/CHANGELOGS_NHAPDIEM_RETAIN_2026.md` | Tạo mới |
| `hdsd/HDSD_NHAPDIEM_RETAIN_2026.md` | Tạo mới |

---

## 5. Rủi ro & giảm thiểu

- **R1**: AJAX không gửi form → mất validation HTML5 mặc định → em sẽ validate phía client (đã có `tinhHM()`).
- **R2**: User đóng tab giữa chừng → mất dữ liệu chưa lưu (giống trước). Có thể thêm `beforeunload` warning nếu có thay đổi chưa lưu (optional, không bắt buộc).
- **R3**: Số lượng lỗi lớn nếu 1 SV fail → trả mảng `errors` để hiển thị chi tiết từng dòng.

---

## 6. Thứ tự thực hiện

1. Sửa `SP_NHAP_DIEM` (thêm check frozen).
2. Thêm helper + sửa 3 route trong `app.py`.
3. Sửa `nhapdiem.html` (AJAX + xử lý frozen).
4. Ghi CHANGELOG + HDSD.
