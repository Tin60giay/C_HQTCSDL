# HDSD_NHAPDIEM_RETAIN_2026.md — Hướng dẫn test

> Ngày: 2026-06-18  |  Phạm vi: Test chức năng Giữ form + Xem NK cũ

---

## 1. Chuẩn bị

1. **Restart Flask** (nếu chưa): mở terminal và chạy `python app.py` ở thư mục gốc.
2. **Restart SQL**: chạy lại `setup_login.sql` trong SSMS để cập nhật `SP_NHAP_DIEM`.
3. Đăng nhập với tài khoản **PGV** (VD: `PGV01` / `ptit@2026`).

---

## 2. Test case 1 — Giữ form khi ghi điểm thành công

**Mục đích**: Sau khi ghi điểm thành công, form KHÔNG bị xóa, KHÔNG bị redirect.

### Bước thực hiện
1. Vào **📝 Nhập Điểm**.
2. Chọn `Niên khóa: 2025-2026` (hoặc NK hiện tại).
3. Chọn `Học kỳ: 1`, `Môn học: <môn có SV đăng ký>`, `Nhóm: 1`.
4. Bảng SV hiện ra → nhập điểm CC/GK/CK (VD: `8 / 7.5 / 9`).
5. Click **💾 Ghi điểm**.

### Kết quả mong đợi
- ✅ Banner xanh: `Ghi điểm thành công cho X/X sinh viên`.
- ✅ Bảng SV **VẪN CÒN NGUYÊN** với các giá trị đã nhập.
- ✅ Filter NK/HK/MH/NHOM vẫn được giữ.
- ✅ URL KHÔNG đổi (không redirect).

### Ghi chú
- Sau khi ghi thành công, FE gọi lại `batDau()` để lấy dữ liệu mới nhất từ server (đảm bảo đồng bộ).

---

## 3. Test case 2 — Ghi điểm có lỗi, giữ dữ liệu đã nhập

**Mục đích**: Khi 1 SV lỗi (VD: điểm ngoài [0,10] hoặc NK frozen), KHÔNG xóa dữ liệu.

### Bước thực hiện
1. Sau test case 1, **ghi điểm mới** với dòng SV1: CC=8, GK=7.5, CK=9.
2. **Cố tình** nhập dòng SV2: CC=15 (ngoài phạm vi 0-10).
3. Click **💾 Ghi điểm**.

### Kết quả mong đợi
- ❌ Banner đỏ: `Lưu thành công X/Y sinh viên. 1 lỗi:` + chi tiết `SV2: Điểm chuyên cần phải nằm trong khoảng [0, 10]`.
- ✅ Dữ liệu các dòng khác **VẪN ĐƯỢC LƯU** thành công.
- ✅ Dòng SV2 giữ nguyên giá trị 15 trong input → user sửa lại rồi ghi tiếp.
- ✅ Form không bị xóa.

### Ghi chú
- Validation 0-10 ở FE (`tinhHM()`) sẽ **cảnh báo viền đỏ** ngay khi user nhập → nhưng nếu user vẫn gửi thì BE vẫn reject.

---

## 4. Test case 3 — Không cho sửa điểm LTC thuộc NK đã đóng băng

**Mục đích**: Khi chọn LTC thuộc NK < 2025-2026, form bị khóa hoàn toàn.

### Bước thực hiện
1. Vào **📝 Nhập Điểm**.
2. Chọn `Niên khóa: 2024-2025` (hoặc NK cũ bất kỳ < 2025).
3. Chọn `Học kỳ`, `Môn học`, `Nhóm` tương ứng với LTC đã có trong DB (xem qua **Mở lớp tín chỉ** trước để biết LTC nào có).
4. Bảng SV hiện ra với điểm đã có sẵn (nếu có).

### Kết quả mong đợi
- 🔒 **Banner đỏ** ở đầu bảng: `Lớp tín chỉ thuộc niên khóa < 2025-2026 đã bị đóng băng. Chỉ xem, không thể sửa điểm.`
- 🔒 Info bar có thêm tag: `🔒 Đã đóng băng (NK cũ)`.
- 🔒 Tất cả ô input **bị disable + làm mờ** (background đậm hơn, chữ xám, cursor not-allowed).
- 🔒 Nút **💾 Ghi điểm** bị disable (mờ + không click được).
- ✅ User vẫn có thể xem điểm đã nhập trước đó.

### Test trực tiếp từ SP
- Nếu user cố tình bypass FE → gọi `EXEC SP_NHAP_DIEM <MALTC cũ>, <MASV>, ...` sẽ trả về:
  ```
  KETQUA = -10
  THONGBAO = N'Lớp tín chỉ thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể nhập/sửa điểm'
  ```

---

## 5. Test case 4 — Mở lớp tín chỉ xem được NK quá khứ

**Mục đích**: PGV/KHOA vào `/loptinchi` thấy được các LTC của NK cũ.

### Bước thực hiện
1. Vào **📚 Mở Lớp Tín Chỉ**.
2. Mở dropdown **Niên khóa**.

### Kết quả mong đợi
- ✅ Danh sách NK chứa **TẤT CẢ** các NK có LTC (kể cả `2020-2021`, `2021-2022`, ...).
- ✅ Chọn NK cũ → bảng hiển thị LTC tương ứng.
- ✅ Nếu LTC cũ: dòng bị làm mờ + tag `🔒 Đóng băng` (logic từ PLANT_LTC_BUGS_2026 trước đó).

---

## 6. Test case 5 — Bộ lọc nhập điểm cho thấy NK cũ

**Mục đích**: Dropdown NK trong Nhập Điểm cũng hiển thị NK cũ.

### Bước thực hiện
1. Vào **📝 Nhập Điểm**.
2. Click vào ô **Niên khóa** (datalist).

### Kết quả mong đợi
- ✅ Gợi ý hiển thị tất cả NK có LTC (kể cả cũ).
- ✅ Nếu không có NK cũ trong DB → chỉ hiện NK hiện tại + tương lai.

---

## 7. Test case 6 — Đăng ký của SV KHÔNG bị ảnh hưởng

**Mục đích**: Đảm bảo SV vẫn chỉ thấy NK trong phạm vi khóa học (từ PLANT_LTC_BUGS_2026 trước đó).

### Bước thực hiện
1. Đăng nhập với tài khoản **SV** (VD: `SV001`).
2. Vào **📋 Đăng Ký Lớp Tín Chỉ**.

### Kết quả mong đợi
- ✅ Dropdown NK chỉ chứa NK trong phạm vi `[KHOAHOC, KHOAHOC+7]` của SV.
- ✅ KHÔNG bị ảnh hưởng bởi thay đổi mới này (helper `get_nienkhoa_for_sv` vẫn được dùng).

---

## 8. Kết quả cuối cùng

| Test | Mục đích | Pass/Fail |
|------|----------|-----------|
| 1 | Ghi điểm thành công → giữ form | ☐ |
| 2 | Có lỗi → giữ dữ liệu + hiện chi tiết | ☐ |
| 3 | NK cũ → form bị khóa + banner 🔒 | ☐ |
| 4 | Mở lớp TC → thấy NK cũ | ☐ |
| 5 | Nhập điểm → NK cũ hiển thị | ☐ |
| 6 | SV vẫn thấy NK theo khóa học | ☐ |

**Ghi chú cuối**:
- Nếu user refresh trang sau khi ghi → form sẽ trở về trạng thái ban đầu (filter trống), bảng SV trống. Đây là hành vi bình thường (giống các webapp khác).
- Để tránh mất dữ liệu khi ghi nhầm → SP `SP_NHAP_DIEM` vẫn UPDATE chứ không xóa → user có thể ghi lại với giá trị đúng.
