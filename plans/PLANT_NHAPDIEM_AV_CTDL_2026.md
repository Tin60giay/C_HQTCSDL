# PLANT_NHAPDIEM_AV_CTDL_2026 — Sửa lỗi Phiếu điểm (lớp đã hủy) & Bộ lọc Nhập điểm môn CTDL

> Ngày: 2026-06-19  |  Phạm vi: Sửa `SP_XEM_PHIEU_DIEM` (`setup_login.sql`), `app.py`, và `nhapdiem.html`
> Tham chiếu: `CRITICAL.md`

---

## 1. Yêu cầu từ user

1. **Phiếu điểm sinh viên N23DCCI079 vẫn hiện lớp Anh văn (AV) đã hủy**:
   - Lớp Anh văn nhóm 1 (`MALTC = 14`) đã bị hủy (`HUYLOP = 1`). Tuy nhiên, trong phiếu điểm cá nhân của sinh viên, lớp này vẫn hiện ra.
   - Cần ẩn các lớp học đã bị hủy (`HUYLOP = 1`) khỏi phiếu điểm của sinh viên.
2. **Giảng viên lọc đúng khóa để nhập điểm môn Cấu trúc dữ liệu & Giải thuật (CTDL) thì không thấy sinh viên nào**:
   - Hiện tại, sinh viên `N23DCCI079` đăng ký học môn CTDL ở Nhóm 3 (`MALTC = 13`).
   - Giao diện nhập điểm (`nhapdiem.html`) hiện tại có trường Nhóm là ô nhập số (mặc định là `1`). Khi giảng viên vào trang nhập điểm, hệ thống mặc định lọc Nhóm 1 (chưa có sinh viên active), dẫn đến danh sách trống. Giảng viên không biết/không thấy Nhóm 3 để chọn.
   - Giải pháp: Chuyển trường nhập Nhóm thành thẻ `<select>` dropdown. Khi giảng viên chọn Niên khóa, Học kỳ, Môn học, hệ thống sẽ tự động gọi API lấy danh sách các Nhóm thực tế đang mở (chưa bị hủy) của môn học đó và đổ vào dropdown. Giảng viên chỉ cần chọn nhóm hiển thị trong dropdown để nhập điểm.

---

## 2. Thiết kế thay đổi

### 2.1 Cơ sở dữ liệu (setup_login.sql)
- **Sửa `SP_XEM_PHIEU_DIEM`**:
  Thêm điều kiện loại bỏ các lớp đã bị hủy:
  ```sql
  AND (LTC.HUYLOP = 0 OR LTC.HUYLOP IS NULL)
  ```

### 2.2 Backend (app.py)
- **Thêm API `/nhapdiem/nhom_list`** (POST):
  - Nhận vào: `nienkhoa`, `hocky`, `mamh`.
  - Thực hiện câu truy vấn:
    ```sql
    SELECT DISTINCT NHOM FROM LOPTINCHI
    WHERE NIENKHOA = ? AND HOCKY = ? AND MAMH = ? AND HUYLOP = 0
    ORDER BY NHOM
    ```
  - Trả về: danh sách các Nhóm (ví dụ `[1, 3]`).

### 2.3 Giao diện (templates/nhapdiem.html)
- **Cập nhật HTML**:
  Thay thế input `fNHOM` dạng số thành select element:
  ```html
  <div class="fg"><label>Nhóm</label>
      <select id="fNHOM" onchange="batDau()" style="min-width:80px;"></select>
  </div>
  ```
- **Cập nhật JS**:
  - Thêm hàm `taiNhomList()` để fetch danh sách nhóm từ server mỗi khi Niên khóa (`fNK`), Học kỳ (`fHK`), hoặc Môn học (`fMAMH`) thay đổi.
  - Sau khi nạp các nhóm vào dropdown, tự động gọi `batDau()` để tải danh sách sinh viên của nhóm đầu tiên.
  - Thêm sự kiện `DOMContentLoaded` để gán Niên khóa mặc định (lấy giá trị cuối cùng trong datalist - thường là niên khóa mới nhất như `2025-2026`) và kích hoạt `taiNhomList()`.

---

## 3. Các file sẽ sửa đổi

| File | Hành động | Mô tả |
|------|-----------|-------|
| [setup_login.sql](file:///f:/A_HQTCSDL/C_HQTCSDL/setup_login.sql) | [MODIFY] | Cập nhật `SP_XEM_PHIEU_DIEM` để ẩn lớp tín chỉ bị hủy. |
| [app.py](file:///f:/A_HQTCSDL/C_HQTCSDL/app.py) | [MODIFY] | Thêm endpoint `/nhapdiem/nhom_list` trả về danh sách nhóm của môn học trong học kỳ/niên khóa. |
| [templates/nhapdiem.html](file:///f:/A_HQTCSDL/C_HQTCSDL/templates/nhapdiem.html) | [MODIFY] | Đổi input Nhóm thành dropdown select động + tự động load dữ liệu. |
| [plans/PLANT_NHAPDIEM_AV_CTDL_2026.md](file:///f:/A_HQTCSDL/C_HQTCSDL/plans/PLANT_NHAPDIEM_AV_CTDL_2026.md) | [NEW] | Kế hoạch này. |

---

## 4. Kế hoạch kiểm thử (Verification Plan)

### Kiểm thử thủ công (Manual Verification)
1. **Kiểm tra phiếu điểm SV N23DCCI079**:
   - Truy cập trang xem điểm của sinh viên `N23DCCI079`.
   - Kết quả mong muốn: Lớp Anh văn (`AV`, Nhóm 1) không còn hiển thị trong danh sách. Lớp Cấu trúc dữ liệu & Giải thuật (`CTDL`, Nhóm 3) vẫn hiển thị bình thường.
2. **Kiểm tra bộ lọc nhập điểm**:
   - Đăng nhập với quyền PGV hoặc KHOA (ví dụ `PGV` hoặc `KHOA`).
   - Vào trang nhập điểm, chọn Niên khóa: `2025-2026`, Học kỳ: `Học kỳ 1`, Môn học: `Cấu trúc dữ liệu & Giải thuật (CTDL)`.
   - Kết quả mong muốn: Dropdown Nhóm tự động hiển thị hai lựa chọn `1` và `3`.
   - Chọn Nhóm `3`: bảng điểm hiển thị 2 sinh viên (`Phạm Tuấn` và `Nguyễn Thành Vinh`).
   - Chọn Nhóm `1`: bảng điểm hiển thị danh sách trống (Số SV: 0).
