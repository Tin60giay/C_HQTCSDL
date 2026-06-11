# HDSD: Kiểm tra Niên khóa & Lớp Tín Chỉ

**Ngày:** 2026-04-18

---

## 1. Kiểm tra Lớp Tín Chỉ — Niên khóa chỉ chọn (không nhập tay)

### Bước test:
1. Vào menu **Lớp Tín Chỉ**
2. Kiểm tra form bên dưới bảng:
   - [ ] Chỉ còn **1 ô chọn** niên khóa (select dropdown), **không còn ô text nhập tay**
   - [ ] Dropdown hiển thị dạng `2023-2024`, `2024-2025`, `2025-2026`... (cách 1 năm)
3. Bấm **＋ Thêm** → select niên khóa reset về `-- Chọn niên khóa --`
4. Chọn 1 dòng trong bảng:
   - [ ] Select niên khóa tự điền đúng giá trị của dòng đó
   - [ ] **Bấm lại vào select vẫn đổi được** (chọn niên khóa khác)
5. Thêm mới 1 lớp TC:
   - [ ] Chọn niên khóa từ dropdown
   - [ ] Điền các trường còn lại, bấm **Ghi** → thành công
6. Sửa 1 lớp TC:
   - [ ] Chọn dòng → đổi niên khóa qua select → bấm **Ghi** → thành công

---

## 2. Kiểm tra Hoàn tác Hủy Lớp Tín Chỉ

1. Chọn 1 lớp TC, bấm **🚫 Hủy lớp** → xác nhận
2. Bấm **🕓 Lịch sử** → tìm hành động "Hủy lớp TC"
3. Bấm **Hoàn tác**:
   - [ ] Thông báo "Phục hồi lớp tín chỉ thành công" (không báo lỗi quyền)
   - [ ] Lớp TC xuất hiện lại trong bảng

---

## 3. Kiểm tra Quản lý Lớp Cử nhân — Khóa học 5 năm

1. Vào menu **Lớp**
2. Bấm vào ô **Khóa học** trong form:
   - [ ] Dropdown gợi ý dạng `2021-2026`, `2022-2027`... (cách 5 năm)
3. Thêm hoặc sửa lớp với khóa học 5 năm → thành công

---

## Các bug đã biết / cần theo dõi
- Nếu database chưa chạy SP `SP_PHUCHOI_LOPTINCHI` trong đúng database `QLDSV_HTC`, hoàn tác vẫn lỗi `Invalid object name`. Cần chạy lại script SQL với `USE [QLDSV_HTC]` ở đầu.
