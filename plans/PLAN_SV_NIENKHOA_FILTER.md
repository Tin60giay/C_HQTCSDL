# PLAN: Lọc Niên Khóa Theo LTC Thực Tế Đang Mở (v2)

**Ngày tạo:** 2026-04-18 — **Cập nhật:** 2026-04-18  
**Trạng thái:** ⏳ Chờ duyệt

---

## Mô tả yêu cầu (đã đơn giản hóa)

Trang **Đăng ký Lớp Tín Chỉ** (nhóm SV) chỉ hiển thị các **niên khóa thực tế đang có lớp tín chỉ được mở** (do PGV tạo), thay vì sinh ra toàn bộ danh sách năm từ code.

> **Logic:** `DISTINCT NIENKHOA FROM LOPTINCHI WHERE HUYLOP = 0`  
> PGV mở lớp nào thì SV thấy niên khóa đó, không thêm gì khác.

Đồng thời sửa layout filter bar thành **1 hàng ngang**.

---

## Quy tắc bất biến

| Ràng buộc | Chi tiết |
|---|---|
| ❌ Không ALTER TABLE | Không sửa cột/hàng nào trong DB gốc |
| ❌ Không INSERT/UPDATE/DELETE dữ liệu | Dữ liệu gốc giữ nguyên 100% |
| ✅ Được thêm SP mới | `SP_GET_NIENKHOA_CO_LOP` |
| ✅ Được sửa SP hiện có | Nếu cần |
| ✅ Được sửa code Python / HTML | `app.py`, `dangky.html` |

---

## Thay đổi cụ thể

### A. `setup_login.sql` — Thêm SP mới

**Tên SP:** `SP_GET_NIENKHOA_CO_LOP`  
**Mục đích:** Trả về danh sách niên khóa thực tế đang có LTC chưa bị hủy

```sql
CREATE PROCEDURE SP_GET_NIENKHOA_CO_LOP
AS
BEGIN
    SET NOCOUNT ON
    SELECT DISTINCT RTRIM(NIENKHOA) AS NIENKHOA
    FROM LOPTINCHI
    WHERE HUYLOP = 0
    ORDER BY NIENKHOA
END
GO
GRANT EXECUTE ON SP_GET_NIENKHOA_CO_LOP TO [sv]
GO
```

---

### B. `app.py` — Thêm helper function

```python
def get_nienkhoa_co_lop():
    """Lấy danh sách niên khóa thực tế đang có LTC (dành cho SV đăng ký)."""
    conn, _ = get_db_connection(SV_SHARED_LOGIN, SV_SHARED_PASSWORD)
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC SP_GET_NIENKHOA_CO_LOP")
        return [r[0].strip() for r in cursor.fetchall()]
    except:
        return []
    finally:
        conn.close()
```

---

### C. `app.py` — Route `/dangky` (GET)

**Thay:** `nienkhoa_list=get_nienkhoa_list()`  
**Thành:** `nienkhoa_list=get_nienkhoa_co_lop()`

---

### D. `templates/dangky.html` — Sửa layout filter bar

**Hiện tại (2 block riêng, Niên khóa có 2 input xếp dọc):**
```
[NIÊN KHÓA]          [HỌC KỲ]
[dropdown]
[input nhập tay]     [dropdown]
```

**Sau khi sửa (1 hàng ngang, chỉ dropdown):**
```
[NIÊN KHÓA: dropdown▼]   [HỌC KỲ: dropdown▼]
```

Bỏ ô nhập tay vì niên khóa đã được backend kiểm soát → chỉ cần chọn từ list.  
Cả 2 nằm cùng hàng `flex-row`, `align-items: flex-end`.

---

## Luồng hoạt động sau khi sửa

```
SV mở trang /dangky
        ↓
Backend gọi SP_GET_NIENKHOA_CO_LOP
        ↓
Trả về: [2024-2025, 2025-2026] (chỉ những NK PGV đã mở LTC)
        ↓
SV chọn Niên khóa + Học kỳ
        ↓
AJAX gọi /dangky/loc → SP_GET_LOPTINCHI_DANGKY (đã có sẵn)
        ↓
Hiển thị danh sách LTC → SV bấm Đăng ký
```

---

## Files thay đổi

| File | Loại thay đổi |
|---|---|
| `setup_login.sql` | Thêm `SP_GET_NIENKHOA_CO_LOP` + GRANT |
| `app.py` | Thêm `get_nienkhoa_co_lop()`, sửa route `/dangky` |
| `templates/dangky.html` | Sửa filter bar 1 hàng, bỏ input nhập tay |

**Sau khi xong sẽ tạo:**
- `changelogs/CHANGELOG_SV_NIENKHOA_FILTER.md`
- `hdsd/HDSD_SV_DANGKY.md`
