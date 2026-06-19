# CHANGELOGS_NHAPDIEM_Flicker_Cancel_Khoa_2026 — Nhật ký sửa đổi Flicker, Làm mờ Hủy đăng ký & Phân quyền khoa cho Giảng viên

> Ngày: 2026-06-19  |  Lý do thay đổi: Khắc phục hiện tượng nháy màn hình khi ghi điểm, tự động làm mờ nút hủy đăng ký của sinh viên khi môn học đã có điểm, và bổ sung ràng buộc chỉ cho phép giảng viên thuộc khoa nào nhập điểm cho lớp tín chỉ thuộc khoa đó.

---

## 1. Danh sách các file thay đổi

| STT | File | Loại thay đổi | Chi tiết thay đổi |
|---|---|---|---|
| 1 | `setup_login.sql` | Cập nhật SP | - Sửa `SP_NHAP_DIEM` thêm kiểm tra vai trò `PGV` thông qua `IS_ROLEMEMBER('PGV')` và so sánh khoa của giảng viên (`GIANGVIEN.MAKHOA`) với khoa quản lý lớp tín chỉ (`LOPTINCHI.MAKHOA`).<br>- Sửa `SP_GET_LOPTINCHI_DANGKY` để trả thêm cột `DA_NHAP_DIEM` (1 nếu lớp đã có điểm của bất kỳ sinh viên nào, ngược lại 0). |
| 2 | `app.py` | Cập nhật logic | - Route `/dangky/loc`: Bổ sung đọc cột `DA_NHAP_DIEM` từ kết quả truy vấn và trả về JSON.<br>- Route `/nhapdiem/batdau`: Kiểm tra phân quyền khoa, nếu không phải PGV thì so sánh khoa giảng viên trong session và khoa của lớp tín chỉ, báo lỗi nếu không khớp. |
| 3 | `templates/dangky.html` | Cập nhật giao diện | Trong hàm `renderAll()`, kiểm tra thuộc tính `ltc.DA_NHAP_DIEM == 1` để làm mờ nút "Hủy đăng ký" (thêm thuộc tính `disabled`, class `btn-disabled` và hiển thị tooltip thích hợp). |
| 4 | `templates/nhapdiem.html` | Cập nhật giao diện | - Thêm tham số `showSpinner = true` cho hàm `batDau()`. Nếu `showSpinner` là `false`, không ẩn bảng điểm hay hiển thị spinner.<br>- Cập nhật hàm `ghiDiem()` gọi `batDau(false)` sau khi ghi điểm thành công để reload ngầm dữ liệu, loại bỏ hiện tượng nhấp nháy màn hình. |

---

## 2. Nhật ký thay đổi cụ thể

### 2.1 Cập nhật Stored Procedure `SP_NHAP_DIEM` trong `setup_login.sql`
Thêm kiểm tra phân quyền khoa giảng viên bằng cách so sánh khoa:
```sql
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

### 2.2 Cập nhật Stored Procedure `SP_GET_LOPTINCHI_DANGKY` trong `setup_login.sql`
Tính toán cờ `DA_NHAP_DIEM` dựa trên sự tồn tại của bất kỳ điểm số nào đã nhập cho lớp tín chỉ:
```sql
        CASE WHEN EXISTS (
            SELECT 1 FROM DANGKY DK3
            WHERE DK3.MALTC = LTC.MALTC
              AND (DK3.DIEM_CC IS NOT NULL OR DK3.DIEM_GK IS NOT NULL OR DK3.DIEM_CK IS NOT NULL)
        ) THEN 1 ELSE 0 END AS DA_NHAP_DIEM
```

### 2.3 Ràng buộc phân quyền khoa trong `/nhapdiem/batdau` (`app.py`)
Ngăn chặn hiển thị sinh viên nếu giảng viên khoa khác truy cập:
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
