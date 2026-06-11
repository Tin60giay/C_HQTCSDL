# CHANGELOG: Cải thiện UX Niên khóa trong Lớp Tín Chỉ

**Ngày:** 2026-04-18  
**Phiên bản:** —

---

## Thay đổi

### `templates/loptinchi.html`
- **Xóa** `<input type="text" id="fNK_txt">` (ô nhập tay niên khóa)
- **Xóa** `onchange` sync từ select sang input text trên `<select id="fNK">`
- **Sửa placeholder** select: `-- Chọn hoặc nhập --` → `-- Chọn niên khóa --`
- **Sửa JS `getNK()`**: chỉ đọc `fNK.value`, bỏ logic ưu tiên ô text
- **Sửa JS `chonDong()`**: bỏ `set('fNK_txt', nk)`
- **Sửa JS `themMoi()`**: bỏ `set('fNK_txt', '')`
- **Sửa JS `phucHoi()`**: bỏ `set('fNK_txt', orig.nk)`
- **Sửa thông báo lỗi**: "Vui lòng chọn hoặc nhập niên khóa" → "Vui lòng chọn niên khóa"

### `app.py`
- **`get_nienkhoa_list()`**: sinh niên khóa cách **1 năm** (`YYYY-(YYYY+1)`) thay vì 5 năm
- **Thêm `get_khoahoc_list()`**: sinh khóa học cách **5 năm** (`YYYY-(YYYY+5)`) cho lớp cử nhân
- **Route `/lop`**: truyền thêm `khoahoc_list=get_khoahoc_list()` vào template

### `templates/lop.html`
- `datalist#khoahocList` đổi sang dùng `khoahoc_list` (5 năm) thay vì `nienkhoa_list`

### `setup_login.sql`
- Thêm SP `SP_PHUCHOI_LOPTINCHI`: set `HUYLOP=0`, có `GRANT EXECUTE TO PUBLIC`
- Sửa hoàn tác `XOA_LTC` trong `app.py`: dùng `EXEC SP_PHUCHOI_LOPTINCHI` thay vì `UPDATE` trực tiếp (fix lỗi quyền 42000)

---

## Lý do
- Niên khóa lớp tín chỉ là khoảng 1 năm học, không phải 5 năm
- Khóa học lớp cử nhân mới là 5 năm
- UX select + input text song song gây khó dùng và bug không chọn lại được
