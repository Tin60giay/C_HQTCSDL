# CHANGELOG: Lọc Niên Khóa Thực Tế cho Đăng Ký LTC

**Ngày:** 2026-04-18  
**Phiên bản:** v1.0  
**Liên quan:** `PLAN_SV_NIENKHOA_FILTER.md`

---

## Tóm tắt thay đổi

Thay thế logic sinh niên khóa ngẫu nhiên bằng cách lấy trực tiếp từ bảng `LOPTINCHI`. Trang đăng ký LTC của SV giờ chỉ hiển thị đúng những niên khóa PGV đã mở lớp — không thừa, không thiếu.

---

## Chi tiết thay đổi

### 1. `setup_login.sql` — Thêm SP mới

**`SP_GET_NIENKHOA_CO_LOP`**
```sql
SELECT DISTINCT RTRIM(NIENKHOA) AS NIENKHOA
FROM LOPTINCHI
WHERE HUYLOP = 0
ORDER BY NIENKHOA
```
- Không đụng DB gốc (không ALTER TABLE, không INSERT/DELETE)
- Cấp `GRANT EXECUTE ON SP_GET_NIENKHOA_CO_LOP TO [sv]`

---

### 2. `app.py` — Thêm helper function

**`get_nienkhoa_co_lop()`** (thêm mới, không xóa `get_nienkhoa_list()`)
- Gọi `EXEC SP_GET_NIENKHOA_CO_LOP`
- Trả danh sách `['2024-2025', '2025-2026', ...]`
- Fallback trả `[]` nếu lỗi kết nối

**Route `/dangky` (GET):**
- Trước: `nienkhoa_list=get_nienkhoa_list()` (sinh năm tự động)
- Sau: `nienkhoa_list=get_nienkhoa_co_lop()` (chỉ năm có LTC thực tế)

---

### 3. `templates/dangky.html` — Sửa layout filter bar

- **Bỏ:** ô nhập tay niên khóa (`<input id="fNK">` dạng text)
- **Gộp:** Niên khóa + Học kỳ về cùng 1 hàng ngang (`flex-direction: row`)
- **Thêm:** Cảnh báo vàng khi `nienkhoa_list` rỗng (chưa có LTC nào được mở)
- **Sửa:** Thông báo lỗi JS từ "nhập" → "chọn" niên khóa

---

## Tác động

| Module | Bị ảnh hưởng | Ghi chú |
|---|---|---|
| Trang `/dangky` (SV) | ✅ Có | Dropdown niên khóa gọn hơn |
| Trang `/loptinchi` (PGV) | ❌ Không | Vẫn dùng `get_nienkhoa_list()` |
| Trang `/nhapdiem` (PGV/KHOA) | ❌ Không | Vẫn dùng `get_nienkhoa_list()` |
| Dữ liệu DB | ❌ Không | Chỉ đọc, không ghi |
