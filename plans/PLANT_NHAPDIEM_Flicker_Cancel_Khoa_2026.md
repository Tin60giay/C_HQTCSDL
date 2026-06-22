# PLANT_NHAPDIEM_Flicker_Cancel_Khoa_2026 — Sửa lỗi nhấp nháy, Làm mờ Hủy đăng ký & Ràng buộc khoa cho Giảng viên nhập điểm

> Ngày: 2026-06-19  |  Phạm vi: Sửa `SP_NHAP_DIEM` và `SP_GET_LOPTINCHI_DANGKY` (`setup_login.sql`), `app.py`, `dangky.html` và `nhapdiem.html`
> Tham chiếu: `CRITICAL.md`

---

## 1. Yêu cầu từ user

1. **Hiện tượng nhấp nháy màn hình khi Ghi điểm**:
   - Khi click "Ghi điểm" thành công, hệ thống gọi `batDau()` để reload lại dữ liệu. Trong `batDau()`, bảng điểm bị ẩn đi (`display = 'none'`) và spinner hiển thị trước khi bảng hiển thị lại. Điều này làm màn hình bị nhấp nháy khó chịu.
   - Giải pháp: Thêm tham số `showSpinner = true` cho hàm `batDau()`. Khi reload sau khi ghi điểm, truyền `showSpinner = false` để cập nhật ngầm dữ liệu mà không ẩn bảng điểm hay hiện spinner.
2. **Làm mờ nút Hủy đăng ký của sinh viên khi lớp đã có điểm**:
   - Hiện tại, sinh viên bị chặn hủy đăng ký ở mức database/SP (`SP_HUY_DANGKY`) khi lớp đã có điểm của bất kỳ sinh viên nào, nhưng trên giao diện nút "Hủy đăng ký" vẫn hiện màu xanh cho phép bấm.
   - Giải pháp:
     - Cập nhật `SP_GET_LOPTINCHI_DANGKY` để trả thêm cột `DA_NHAP_DIEM` (1 nếu lớp đã được nhập điểm cho bất kỳ SV nào, ngược lại 0).
     - Cập nhật API `/dangky/loc` để trả thêm thuộc tính này.
     - Cập nhật `dangky.html` để làm mờ nút "Hủy đăng ký" (thêm class `btn-disabled` và `disabled`, hiển thị tooltip giải thích) khi `ltc.DA_NHAP_DIEM == 1`.
3. **Ràng buộc phân quyền khoa cho Giảng viên**:
   - Chỉ giảng viên thuộc khoa X mới được nhập điểm cho lớp tín chỉ thuộc khoa X (ví dụ giảng viên khoa CNTT chỉ được nhập điểm cho lớp tín chỉ CNTT). PGV được quyền nhập điểm cho tất cả các khoa.
   - Giải pháp:
     - Cập nhật `SP_NHAP_DIEM`: Kiểm tra nếu tài khoản đang thực thi (`SYSTEM_USER`) không thuộc role `PGV` (`IS_ROLEMEMBER('PGV') = 0`) và có thông tin trong bảng `GIANGVIEN`, so sánh khoa quản lý lớp tín chỉ và khoa của giảng viên. Nếu không khớp, trả về lỗi `-1` kèm thông báo chặn.
     - Cập nhật backend `app.py` tại `/nhapdiem/batdau`: Nếu `session['group'] != 'PGV'`, so sánh `session['khoa']` (khoa của giảng viên) và khoa quản lý lớp tín chỉ. Nếu không trùng khớp, trả về lỗi chặn hiển thị danh sách sinh viên.

---

## 2. Thiết kế thay đổi chi tiết

### 2.1 Cơ sở dữ liệu (setup_login.sql)

#### Sửa `SP_NHAP_DIEM` (Bổ sung check khoa giảng viên)
```sql
    -- [PLANT_NHAPDIEM_Flicker_Cancel_Khoa_2026] Ràng buộc chỉ giảng viên khoa X được nhập điểm cho lớp tín chỉ khoa X
    -- Bỏ qua kiểm tra nếu user là thành viên role PGV
    IF IS_ROLEMEMBER('PGV') = 0
    BEGIN
        DECLARE @MAKHOA_GV NCHAR(10) = NULL
        SELECT @MAKHOA_GV = MAKHOA FROM GIANGVIEN WHERE MAGV = RTRIM(SYSTEM_USER)
        
        IF @MAKHOA_GV IS NOT NULL
        BEGIN
            DECLARE @MAKHOA_LTC NCHAR(10) = NULL
            SELECT @MAKHOA_LTC = MAKHOA FROM LOPTINCHI WHERE MALTC = @MALTC
            
            IF @MAKHOA_GV <> @MAKHOA_LTC
            BEGIN
                SELECT -1 AS KETQUA, N'Giảng viên khoa ' + RTRIM(@MAKHOA_GV) + N' không được phép nhập điểm cho lớp tín chỉ thuộc khoa ' + RTRIM(@MAKHOA_LTC) AS THONGBAO
                RETURN
            END
        END
    END
```

#### Sửa `SP_GET_LOPTINCHI_DANGKY` (Trả thêm cột `DA_NHAP_DIEM`)
*   Thêm cột `DA_NHAP_DIEM`:
    ```sql
    CASE WHEN EXISTS (
        SELECT 1 FROM DANGKY DK3
        WHERE DK3.MALTC = LTC.MALTC
          AND (DK3.DIEM_CC IS NOT NULL OR DK3.DIEM_GK IS NOT NULL OR DK3.DIEM_CK IS NOT NULL)
    ) THEN 1 ELSE 0 END AS DA_NHAP_DIEM
    ```

### 2.2 Backend (app.py)

#### Sửa `/dangky/loc`
- Đọc thuộc tính `DA_NHAP_DIEM` từ kết quả truy vấn và trả về JSON:
  ```python
  'DA_NHAP_DIEM': getattr(r, 'DA_NHAP_DIEM', 0)
  ```

#### Sửa `/nhapdiem/batdau`
- Thêm kiểm tra so sánh khoa nếu không phải PGV:
  ```python
  group = session.get('group')
  if group != 'PGV':
      user_khoa = session.get('khoa', '').strip().upper()
      cursor.execute("SELECT MAKHOA FROM LOPTINCHI WHERE MALTC=?", (maltc,))
      ltc_khoa_row = cursor.fetchone()
      ltc_khoa = ltc_khoa_row[0].strip().upper() if ltc_khoa_row else ''
      if user_khoa != ltc_khoa:
          return jsonify({'ok': False, 'msg': f'Giảng viên khoa {user_khoa} không được nhập điểm lớp tín chỉ thuộc khoa {ltc_khoa}'})
  ```

### 2.3 Giao diện (dangky.html & nhapdiem.html)

#### Sửa `dangky.html`
- Kiểm tra `ltc.DA_NHAP_DIEM == 1` trong hàm `renderAll()`.
- Làm mờ nút Hủy đăng ký nếu điều kiện thỏa mãn:
  ```javascript
  const isGraded = ltc.DA_NHAP_DIEM == 1;
  ...
  // Làm mờ khi đã có điểm nhập
  ```

#### Sửa `nhapdiem.html`
- Cập nhật hàm `batDau(showSpinner = true)`:
  - Nếu `showSpinner` là `false`, không ẩn `diemTable` và không hiện `spinner`.
- Cập nhật hàm `ghiDiem()`:
  - Khi lưu điểm thành công, gọi `batDau(false)` để tránh nhấp nháy màn hình.

---

## 3. Các file sẽ sửa đổi

| File | Hành động | Mô tả |
|------|-----------|-------|
| [setup_login.sql](file:///f:/A_HQTCSDL/C_HQTCSDL/setup_login.sql) | [MODIFY] | Cập nhật `SP_NHAP_DIEM` và `SP_GET_LOPTINCHI_DANGKY`. |
| [app.py](file:///f:/A_HQTCSDL/C_HQTCSDL/app.py) | [MODIFY] | Cập nhật logic phân quyền khoa và trả thuộc tính `DA_NHAP_DIEM`. |
| [templates/dangky.html](file:///f:/A_HQTCSDL/C_HQTCSDL/templates/dangky.html) | [MODIFY] | Làm mờ nút Hủy đăng ký khi lớp học đã bắt đầu nhập điểm. |
| [templates/nhapdiem.html](file:///f:/A_HQTCSDL/C_HQTCSDL/templates/nhapdiem.html) | [MODIFY] | Khắc phục hiện tượng nhấp nháy khi lưu điểm thành công. |
| [plans/PLANT_NHAPDIEM_Flicker_Cancel_Khoa_2026.md](file:///f:/A_HQTCSDL/C_HQTCSDL/plans/PLANT_NHAPDIEM_Flicker_Cancel_Khoa_2026.md) | [NEW] | Kế hoạch này. |

---

## 4. Kế hoạch kiểm thử (Verification Plan)

### Kiểm thử tự động / SQL
- Kiểm tra `SP_GET_LOPTINCHI_DANGKY` trả về đúng cờ `DA_NHAP_DIEM`.
- Kiểm tra `SP_NHAP_DIEM` dưới quyền giảng viên CNTT (`GV03`) đối với lớp của khoa VT (ví dụ `MALTC = 4` có `MAKHOA = VT`): kết quả trả về phải báo lỗi.

### Kiểm thử thủ công
1. **Kiểm tra nhấp nháy khi Ghi điểm**:
   - Đăng nhập quyền PGV/KHOA, chọn một lớp và ghi điểm.
   - Kết quả mong muốn: Dữ liệu được ghi và cập nhật thành công, màn hình không bị ẩn bảng điểm hay nháy trắng.
2. **Kiểm tra nút Hủy đăng ký bị làm mờ**:
   - Đăng nhập tài khoản sinh viên `N23DCCI079` xem danh sách lớp đã chọn.
   - Nhập điểm cho lớp đó từ giảng viên.
   - Kiểm tra lại giao diện sinh viên: Nút "Hủy đăng ký" phải được làm mờ và hiển thị tooltip thích hợp.
3. **Kiểm tra phân quyền khoa cho giảng viên**:
   - Đăng nhập tài khoản `GV03` (Khoa CNTT), thử load danh sách lớp tín chỉ của khoa khác. Hệ thống phải báo lỗi và chặn.
   - Thử nhập điểm lớp khoa khác trực tiếp thông qua API hoặc SQL. SQL phải trả về mã lỗi chặn khoa.
