# PLANT_006: Sửa lỗi giao diện & ràng buộc UI toàn diện

## Ngày lập: 2026-04-20
## Trạng thái: Chờ duyệt

---

## 1. Mô tả vấn đề

### 1.1. Bảng danh sách hiển thị tối đa 10 dòng, có thanh cuộn
- Hiện tại tất cả bảng (Lớp, Sinh viên, Khoa, Môn học, Giảng viên, LTC) hiển thị tất cả dòng không giới hạn
- **Yêu cầu**: Mỗi bảng chỉ hiển thị tối đa 10 dòng, nếu hơn phải cuộn chuột

### 1.2. Nút Xóa sáng lên sai khi chỉnh sửa thông tin
- **Vấn đề**: Khi click chọn 1 dòng (editing mode), nút Xóa tự động sáng lên. Nếu dòng đó vi phạm ràng buộc (có dữ liệu con), nút Xóa vẫn bị sáng trước khi API `checkCanDelete` trả kết quả
- **Nguyên nhân**: Hàm `updateActionButtons('editing')` bật nút Xóa = `false` (enabled) ngay lập tức. Sau đó mới gọi `checkCanDelete()` bất đồng bộ → khoảnh khắc giữa 2 lệnh, nút Xóa đã sáng sai
- **Fix**: Khi chuyển sang `editing`, giữ nút Xóa disabled cho đến khi `checkCanDelete` trả về kết quả

### 1.3. Nút Tạo mới sáng lên khi đang ở chế độ Editing (Môn Học)
- **Vấn đề**: Trang Quản lý Môn Học — khi click chọn dòng và sửa thông tin, nút **Tạo mới** sáng lên trong khi nút **Lưu** không hoạt động
- **Nguyên nhân**: Hàm `enableSaveOnInputFocus()` trong `history.js` — khi focus input mà `sel` chưa được nhận dạng (do trang monhoc.html sử dụng biến `selectedMAMH` thay vì `sel`), logic check `typeof sel !== 'undefined'` bị sai → luôn vào nhánh `adding`
- **Fix**: Cập nhật `history.js` kiểm tra cả `sel` và `selectedMAMH` (hoặc normalize biến name)

### 1.4. Lỗi Bảng điểm cá nhân (Sinh viên) - IMPORTANT
- **Vấn đề**: Route `/phieu_diem` truyền `diem_list` nhưng template `phieu_diem.html` sử dụng biến `phieu_diem` → không khớp → bảng luôn hiển thị "Chưa có điểm..."
- Thêm: Template sử dụng `sv.HOTEN`, `sv.MASV`... nhưng app.py không truyền biến `sv` — chỉ truyền `masv` và `hoten` riêng lẻ
- **Fix**: Sửa app.py truyền đúng biến HOẶC sửa template nhận đúng biến

### 1.5. SV lọc được niên khóa quá khứ (not important)
- **Mô tả**: SV khóa 2025-2029 vẫn lọc được LTC ở niên khóa quá khứ (ví dụ 2024-2025)
- **Nguyên nhân**: `get_nienkhoa_co_lop()` trả về tất cả niên khóa có LTC, không lọc theo khóa học của SV
- **Fix**: Backend lọc niên khóa dựa trên KHOAHOC của SV

### 1.6. Nút Hủy đăng ký không mờ khi SV đã có điểm
- **Vấn đề**: Trang đăng ký LTC của SV — khi GV/PGV đã nhập điểm (DIEM_CC / DIEM_GK / DIEM_CK), nút "Hủy đăng ký" vẫn xanh sáng → click vào thì lỗi nhưng nút không disable
- **Fix**: API `/dangky/loc` trả thêm trường `CO_DIEM` — frontend kiểm tra để dim nút hủy

---

## 2. Kế hoạch thay đổi

### File thay đổi:

| File | Thay đổi |
|------|----------|
| `static/history.js` | Fix logic nút Xóa, nút Tạo mới, hỗ trợ biến `selectedMAMH` |
| `templates/khoa.html` | Thêm max-height + scroll cho bảng |
| `templates/lop.html` | Thêm max-height + scroll cho bảng |
| `templates/monhoc.html` | Thêm max-height + scroll, fix data-text thiếu |
| `templates/giangvien.html` | Thêm max-height + scroll cho bảng |
| `templates/sinhvien.html` | Thêm max-height + scroll cho bảng |
| `templates/loptinchi.html` | Thêm max-height + scroll, data-* attributes |
| `templates/dangky.html` | Dim nút hủy nếu SV đã có điểm |
| `templates/phieu_diem.html` | Fix biến template không khớp (sv → từng biến riêng) |
| `app.py` | Fix route `/phieu_diem`, `/dangky/loc` trả thêm `CO_DIEM`, lọc NK cho SV |

### Không thay đổi:
- ❌ Không sửa/xóa/thêm cột/hàng database
- ❌ Không tạo file SQL mới (mọi thay đổi SP nếu có đều trong `setup_login.sql`)

---

## 3. Chi tiết thay đổi

### 3.1. `history.js` — Fix logic nút
```
- updateActionButtons('editing'): Giữ btnXoa.disabled = true mặc định → chờ checkCanDelete re-enable
- enableSaveOnInputFocus(): Check thêm biến selectedMAMH bên cạnh sel
```

### 3.2. Tất cả template bảng — Scroll container
```css
/* Bọc tbody trong div có max-height tương đương ~10 dòng */
.table-scroll { max-height: 400px; overflow-y: auto; }
```

### 3.3. `phieu_diem.html` — Fix biến
```
- sv.MASV → masv
- sv.HOTEN → hoten  
- sv.MALOP → malop
- sv.NGAYSINH → ngaysinh (cần truyền thêm từ app.py)
- phieu_diem → diem_list
```

### 3.4. `dangky.html` — Dim nút hủy khi đã có điểm
```
- API trả thêm field CO_DIEM (boolean)
- Frontend: nếu CO_DIEM=true → nút "Hủy đăng ký" bị disabled + title giải thích
```

### 3.5. `app.py` — Fix phieu_diem route
- Truyền thông tin SV đầy đủ (masv, hoten, malop, ngaysinh)
- Sửa tên biến template `phieu_diem` → `diem_list`

---

## 4. Kiểm thử sau khi thay đổi
- [ ] Kiểm tra tất cả bảng hiển thị ≤10 dòng, cuộn mượt
- [ ] Click chọn dòng → nút Xóa chỉ sáng khi không vi phạm ràng buộc
- [ ] Click chọn dòng trong Môn Học → nút Lưu sáng, nút Tạo mới mờ
- [ ] Đăng nhập SV → Bảng Điểm Cá Nhân hiển thị đúng điểm
- [ ] SV đăng ký LTC → niên khóa quá khứ không hiển thị
- [ ] SV đã có điểm → nút Hủy đăng ký bị mờ
