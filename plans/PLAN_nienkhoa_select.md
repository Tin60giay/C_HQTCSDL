# PLAN: Cải thiện UX chọn Niên khóa trong Lớp Tín Chỉ

**Ngày:** 2026-04-18  
**Phạm vi:** `templates/loptinchi.html`

---

## Vấn đề hiện tại

- Ô niên khóa có **2 control song song**: 1 `<select>` + 1 `<input text>` → rối, khó dùng
- Sau khi chọn 1 dòng trong bảng, niên khóa hiện đúng nhưng **không thể bấm lại vào select để đổi** vì value đã bị set → UX bị kẹt
- Người dùng không biết nên dùng select hay ô text

---

## Ý tưởng đề xuất

### Phương án: Chỉ dùng 1 `<select>` — bỏ ô text nhập tay

**Cách hoạt động:**
- Chỉ còn 1 `<select id="fNK">` với danh sách niên khóa (1 năm: `2021-2022`, `2022-2023`...)
- Mặc định: `-- Chọn niên khóa --`
- Khi chọn dòng trong bảng → select tự set value → **vẫn có thể bấm lại để đổi**
- `getNK()` chỉ đọc từ `fNK.value`

**Ưu điểm:**
- Đơn giản, nhất quán
- Luôn chọn được lại (select không bị "khóa")
- Không cần sync 2 control

**Nhược điểm:**
- Không nhập tự do được (nhưng list đã đủ range)

---

## Thay đổi cần làm

1. Xóa `<input type="text" id="fNK_txt">` trong form thêm/sửa
2. Sửa `<select id="fNK">` — bỏ `onchange` sync sang ô text
3. Sửa `chonDong()` — chỉ set `fNK`, bỏ set `fNK_txt`
4. Sửa `themMoi()` — bỏ reset `fNK_txt`
5. Sửa `phucHoi()` — bỏ set `fNK_txt`
6. Sửa `getNK()` — chỉ đọc `fNK.value`
7. Sửa validate định dạng nếu cần (vẫn giữ YYYY-YYYY check)

---

## Không thay đổi
- Filter niên khóa trên bảng (select lọc) — giữ nguyên
- Logic backend — không đổi
