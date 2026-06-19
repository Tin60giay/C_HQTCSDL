# PLANT_NHAPDIEM_FIX_2026 — Sửa lỗi nhập điểm & Hủy lớp đăng ký

> Ngày: 2026-06-19  |  Phạm vi: Sửa `SP_GET_SINHVIEN_THEO_LTC` + `SP_NHAP_DIEM` + `SP_HUY_DANGKY` trong `setup_login.sql`
> Tham chiếu: `CRITICAL.md`

---

## 1. Yêu cầu từ user

1. **Lớp bị hủy không hiển thị sinh viên trong phần nhập điểm**: Khi lớp tín chỉ bị hủy (`LOPTINCHI.HUYLOP = 1`), sinh viên đã đăng ký lớp đó không được hiển thị trong phần nhập điểm.
2. **Chặn sinh viên hủy lớp sau khi giảng viên đã nhập điểm cho lớp đó**: Sinh viên không được hủy đăng ký (`SP_HUY_DANGKY` trả lỗi) nếu lớp đó đã được nhập điểm cho bất kỳ sinh viên nào.
3. **Giữ nguyên và cho phép cập nhật điểm**: Đảm bảo điểm số sau khi ghi điểm vẫn hiển thị đầy đủ và có thể cập nhật.

---

## 2. Thiết kế thay đổi

### 2.1 Sửa `SP_GET_SINHVIEN_THEO_LTC` (setup_login.sql)
*   Thêm `INNER JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC`
*   Thêm điều kiện lọc `LTC.HUYLOP = 0` (hoặc `LTC.HUYLOP IS NULL`) để đảm bảo không trả về danh sách sinh viên của lớp đã bị hủy.

### 2.2 Sửa `SP_NHAP_DIEM` (setup_login.sql)
*   Chặn không cho nhập điểm nếu lớp đã bị hủy (`LOPTINCHI.HUYLOP = 1`). Trả về mã lỗi `-1` và thông báo thích hợp.

### 2.3 Sửa `SP_HUY_DANGKY` (setup_login.sql)
*   Thay đổi điều kiện chặn hủy đăng ký: thay vì chỉ kiểm tra điểm của sinh viên đó, ta kiểm tra xem lớp tín chỉ đó đã có bất kỳ đầu điểm nào của bất kỳ sinh viên nào chưa (`DIEM_CC IS NOT NULL OR DIEM_GK IS NOT NULL OR DIEM_CK IS NOT NULL`).
*   Nếu có đầu điểm, trả về mã lỗi `-2` và thông báo lỗi tương ứng.

---

## 3. Các file sẽ sửa đổi

| File | Hành động | Mô tả |
|------|-----------|-------|
| `setup_login.sql` | Sửa | Cập nhật định nghĩa của 3 stored procedures: `SP_GET_SINHVIEN_THEO_LTC`, `SP_NHAP_DIEM`, `SP_HUY_DANGKY`. |
| `plans/PLANT_NHAPDIEM_FIX_2026.md` | Tạo mới | Kế hoạch này. |
| `changelogs/CHANGELOGS_NHAPDIEM_FIX_2026.md` | Tạo mới | Nhật ký các thay đổi thực tế. |
| `hdsd/HDSD_NHAPDIEM_FIX_2026.md` | Tạo mới | Hướng dẫn kiểm thử và tái hiện lỗi. |
