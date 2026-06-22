# HDSD_LTC_BUGS_2026 — Hướng dẫn kiểm thử 5 lỗi mở lớp tín chỉ & filter

> Ngày: 2026-06-18  |  Phạm vi test: 5 issue đã sửa trong `CHANGELOGS_LTC_BUGS_2026.md`

---

## Bước 0: Cài đặt

1. Chạy lại `setup_login.sql` trên SSMS để cập nhật 2 SP cũ + tạo 2 SP mới:
   ```sql
   -- Mở SSMS, kết nối QLDSV_HTC, mở file setup_login.sql
   -- Nhấn F5 (Execute)
   ```
2. Khởi động lại `app.py`:
   ```bash
   python app.py
   ```
3. Mở trình duyệt: http://localhost:5001

---

## Test 1: Làm mờ trường readOnly (Issue 1)

### Test 1.1 - Khoa
1. Login PGV (`PGV` / `pgv`).
2. Vào **🏛️ Quản lý Khoa**.
3. Click vào 1 dòng bất kỳ (VD: `CNTT`).
4. **Kỳ vọng**: ô "Mã khoa" có nền mờ xám, chữ mờ, cursor not-allowed. Không thể gõ/sửa.
5. Click **Làm mới form**.
6. **Kỳ vọng**: ô "Mã khoa" trở lại bình thường (có thể gõ).

### Test 1.2 - Lớp
1. Vào **📋 Quản lý Lớp Cử Nhân**.
2. Click vào 1 dòng bất kỳ (VD: `D15CQCP01`).
3. **Kỳ vọng**: ô "Mã Lớp" mờ + readOnly. Các ô khác (Tên Lớp, Khóa Học, Khoa) sáng bình thường.
4. Click **Làm mới form** → mọi ô trở lại sáng.

### Test 1.3 - Giảng viên
1. Vào **👨‍🏫 Quản lý Giảng Viên**.
2. Click 1 dòng (VD: `GV01`).
3. **Kỳ vọng**: ô "Mã GV" mờ + readOnly.

### Test 1.4 - Môn học
1. Vào **📖 Quản lý Môn Học**.
2. Click 1 dòng (VD: `CTDL`).
3. **Kỳ vọng**: ô "Mã môn học" mờ + readOnly.

### Test 1.5 - Sinh viên
1. Vào **👨‍🎓 Quản lý Sinh Viên** → chọn 1 lớp (VD: `D15CQCP01`).
2. Click 1 dòng SV (VD: `N15DCCN001`).
3. **Kỳ vọng**: ô "Mã SV" mờ + readOnly. Các ô khác sáng.

---

## Test 2: Lọc mở lớp tín chỉ - filter đồng bộ + NK mới nhất (Issue 2)

### Test 2.1 - Mặc định NK mới nhất
1. Login PGV.
2. Vào **🏫 Mở Lớp Tín Chỉ** (URL: `/loptinchi`).
3. **Kỳ vọng**: Bộ lọc "Niên khóa" tự động chọn **NK mới nhất hiện có trong LOPTINCHI** (hiện tại: `2021-2022`).
4. **Kỳ vọng**: Bảng chỉ hiển thị các LTC thuộc NK đó.

### Test 2.2 - Lọc theo Học kỳ
1. Đổi dropdown "Học kỳ" → "Học kỳ 2".
2. **Kỳ vọng**: Bảng lập tức chỉ hiển thị các LTC của Học kỳ 2.

### Test 2.3 - Lọc theo Khoa
1. Đổi dropdown "Khoa" → "Viễn Thông".
2. **Kỳ vọng**: Bảng chỉ hiển thị LTC thuộc khoa Viễn Thông.

### Test 2.4 - Tìm kiếm
1. Gõ "CTDL" vào ô "Tìm mã MH / GV".
2. **Kỳ vọng**: Bảng lọc chỉ hiển thị các LTC có mã MH hoặc tên GV chứa "CTDL".

### Test 2.5 - Xem tất cả
1. Nhấn nút **↻ Xem tất cả**.
2. **Kỳ vọng**: Tất cả filter reset, bảng hiển thị TẤT CẢ LTC (bao gồm cả đã đóng băng + còn hạn).

### Test 2.6 - Kết hợp filter
1. Chọn NK = `2021-2022`, Học kỳ = 1, Khoa = `CNTT`, tìm "GV01".
2. **Kỳ vọng**: Bảng lọc đúng theo cả 4 điều kiện AND.

---

## Test 3: Khóa NK/HK/MAMH/MAKHOA khi sửa LTC (Issue 3)

1. Vào **🏫 Mở Lớp Tín Chỉ** với vai trò PGV.
2. Chọn NK = `2021-2022` để hiện các LTC không bị đóng băng.
3. Click vào 1 dòng LTC (VD: `MALTC=1`, môn `CTDL`).
4. **Kỳ vọng**: 4 trường "Niên khóa", "Học kỳ", "Môn học", "Khoa" đều mờ + disabled (không sửa được). 3 trường "Nhóm", "Giảng viên", "SV tối thiểu" sáng bình thường.
5. Thử đổi "Nhóm" từ 1 → 2 → nhấn **💾 Ghi thay đổi**.
6. **Kỳ vọng**: Cập nhật thành công, NHÓM thay đổi nhưng các trường khác giữ nguyên.

### Test 3.1 - LTC Frozen vẫn khóa tất cả
1. Click vào 1 dòng LTC có icon 🔒 (NK < 2025-2026).
2. **Kỳ vọng**: Tất cả 7 trường đều mờ + disabled. Nút "Ghi thay đổi" bị disable.

### Test 3.2 - Tạo mới → mở khóa tất cả
1. Sau khi sửa xong, click **🧹 Làm mới form**.
2. **Kỳ vọng**: Tất cả 7 trường sáng trở lại, có thể nhập liệu mới.

---

## Test 4: SV chỉ thấy LTC khoa mình (Issue 4)

### Test 4.1 - SV khoa CNTT
1. Đăng xuất, login lại với SV khoa CNTT: `N15DCCN001` / `123` (password mặc định).
2. Vào **📝 Đăng ký Lớp Tín Chỉ**.
3. Chọn NK = `2021-2022`, Học kỳ = 1.
4. **Kỳ vọng**: Chỉ thấy LTC thuộc khoa CNTT (mã `CNTT`). KHÔNG thấy LTC khoa Viễn Thông.

### Test 4.2 - SV khoa Viễn Thông
1. Đăng xuất, login SV khoa VT: `N15DCVT001` / `123`.
2. Vào **📝 Đăng ký Lớp Tín Chỉ**.
3. Chọn NK = `2021-2022`, Học kỳ = 2.
4. **Kỳ vọng**: Chỉ thấy LTC khoa Viễn Thông (nếu có).

### Test 4.3 - SV quá hạn + khoa CNTT
1. SV `N15DCCN001` thuộc khóa `2015-2019` → tính đến 2026 đã quá hạn (11 năm).
2. Vào **📝 Đăng ký Lớp Tín Chỉ**.
3. **Kỳ vọng**: Hiển thị banner cảnh báo vàng "Tài khoản của bạn đã quá hạn...".
4. Tất cả nút "Đăng ký" bị mờ + disabled.

---

## Test 5: SV chỉ thấy LTC từ KHOAHOC → KHOAHOC+7 (Issue 5)

### Test 5.1 - SV khóa 2015 (quá hạn 7 năm)
1. Login SV `N15DCCN001` (KHOAHOC = `2015-2019` → năm bắt đầu 2015 → năm KT = 2022).
2. Vào **📝 Đăng ký Lớp Tín Chỉ**.
3. **Kỳ vọng**: Dropdown Niên khóa chỉ hiển thị từ `2015-2016` đến `2022-2023` (nếu có LTC thuộc khoa CNTT trong khoảng này).
4. **KHÔNG** thấy NK `2023-2024`, `2024-2025`, `2025-2026`.

### Test 5.2 - SV khóa 2016 (còn hạn)
1. Login SV `N16DCVT001` (KHOAHOC = `2016-2020` → năm bắt đầu 2016 → năm KT = 2023).
2. Vào **📝 Đăng ký Lớp Tín Chỉ**.
3. **Kỳ vọng**: Dropdown NK từ `2016-2017` đến `2023-2024` (nếu có LTC khoa VT).

### Test 5.3 - Phiếu điểm giới hạn phạm vi
1. Login SV `N15DCCN001`.
2. Vào **📄 Bảng Điểm Cá Nhân**.
3. **Kỳ vọng**: Nếu SV có điểm ở NK `2025-2026` (giả sử) → KHÔNG hiển thị. Chỉ hiển thị điểm đến NK `2022-2023`.

### Test 5.4 - Cố tình gọi API vượt phạm vi
1. Mở DevTools (F12) → tab Console.
2. Trong trang đăng ký, gõ:
   ```js
   fetch('/dangky/loc', {method: 'POST', headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({nienkhoa: '2025-2026', hocky: 1, masv: 'N15DCCN001'})})
       .then(r => r.json()).then(d => console.log(d));
   ```
3. **Kỳ vọng**: Trả về `data.list = []` (rỗng) vì NK `2025-2026` ngoài phạm vi `[2015, 2022]`.

---

## Test 6: Đăng ký thành công (regression test - đảm bảo không phá luồng cũ)

1. Tạo mới 1 LTC trong NK `2025-2026` (PGV) — vì dữ liệu mẫu chỉ có `2021-2022` nên cần tạo thêm.
2. Tạo 1 SV khóa 2025 (KHOAHOC = `2025-2029`) thuộc khoa CNTT.
3. Login SV này → vào đăng ký.
4. **Kỳ vọng**: Thấy NK `2025-2026`, có thể đăng ký thành công.

---

## Test 7: Thoái lui đầy đủ (regression test - đảm bảo các chức năng cũ vẫn chạy)

1. Tạo mới 1 LTC → Undo → LTC bị hủy → Undo → LTC hoạt động lại.
2. Sửa 1 LTC → Undo → giá trị trở về ban đầu.
3. Sửa lớp (LOP) → Undo → trở về ban đầu.
4. **Kỳ vọng**: Tất cả Undo hoạt động bình thường.

---

## Lưu ý quan trọng

- **Database gốc không bị sửa**: Chỉ có 2 SP cũ được sửa nội bộ (`SP_GET_LOPTINCHI_DANGKY`, `SP_XEM_PHIEU_DIEM`) và 2 SP mới được tạo. KHÔNG đụng vào bảng nào.
- **Backup trước khi chạy**: Dù rule đã rõ ràng, vẫn nên backup database trước khi chạy lại `setup_login.sql`.
- **Nếu test fail**: Mở DevTools → Console xem lỗi JS. Mở SSMS chạy tay từng SP để xem lỗi SQL.
