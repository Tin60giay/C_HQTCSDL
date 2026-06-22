# HDSD_NHAPDIEM_FIX_2026.md — Hướng dẫn kiểm thử lỗi logic nhập điểm & hủy đăng ký lớp

Tài liệu này hướng dẫn cách kiểm thử các logic mới đã sửa đổi liên quan đến việc nhập điểm của giảng viên và việc hủy lớp đăng ký của sinh viên.

---

## 1. Chuẩn bị dữ liệu kiểm thử (SQL)
Để kiểm thử các trường hợp này, chạy script SQL hoặc thực hiện trực tiếp trên SSMS:
- Lớp tín chỉ kiểm thử: `MALTC = 1`.
- Sinh viên kiểm thử: `N15DCCN001`, `N15DCCN002`.

---

## 2. Các kịch bản kiểm thử (Test Cases)

### Kịch bản 1: Lớp bị hủy không hiển thị sinh viên trong phần nhập điểm
1. Đánh dấu lớp tín chỉ `MALTC = 1` là bị hủy:
   ```sql
   UPDATE LOPTINCHI SET HUYLOP = 1 WHERE MALTC = 1;
   ```
2. Gọi SP để lấy danh sách sinh viên:
   ```sql
   EXEC SP_GET_SINHVIEN_THEO_LTC @MALTC = 1;
   ```
   **Kết quả kỳ vọng:** SP không trả về bất kỳ dòng dữ liệu nào (danh sách rỗng).
3. Gọi SP nhập điểm:
   ```sql
   EXEC SP_NHAP_DIEM @MALTC = 1, @MASV = 'N15DCCN001', @DIEM_CC = 10;
   ```
   **Kết quả kỳ vọng:** SP trả về `KETQUA = -1` và thông báo `Lớp tín chỉ đã bị hủy, không thể nhập/sửa điểm`.

4. Phục hồi trạng thái lớp để làm test tiếp theo:
   ```sql
   UPDATE LOPTINCHI SET HUYLOP = 0 WHERE MALTC = 1;
   ```

---

### Kịch bản 2: Sinh viên không thể hủy lớp khi lớp đã được nhập điểm
1. Reset điểm của tất cả sinh viên trong lớp `MALTC = 1` về `NULL` (chưa nhập điểm):
   ```sql
   UPDATE DANGKY SET DIEM_CC = NULL, DIEM_GK = NULL, DIEM_CK = NULL, HUYDANGKY = 0 WHERE MALTC = 1;
   ```
2. Thử hủy đăng ký cho sinh viên `N15DCCN001` khi chưa có điểm:
   ```sql
   EXEC SP_HUY_DANGKY @MASV = 'N15DCCN001', @MALTC = 1;
   ```
   **Kết quả kỳ vọng:** Hủy thành công (`KETQUA = 1`).
   
3. Đăng ký lại cho sinh viên đó:
   ```sql
   UPDATE DANGKY SET HUYDANGKY = 0 WHERE MASV = 'N15DCCN001' AND MALTC = 1;
   ```

4. Tiến hành nhập điểm cho một sinh viên **khác** trong lớp (ví dụ: `N15DCCN002`):
   ```sql
   EXEC SP_NHAP_DIEM @MALTC = 1, @MASV = 'N15DCCN002', @DIEM_CC = 8, @DIEM_GK = 9, @DIEM_CK = 9.5;
   ```
5. Thử hủy đăng ký cho sinh viên `N15DCCN001` (người chưa hề có điểm):
   ```sql
   EXEC SP_HUY_DANGKY @MASV = 'N15DCCN001', @MALTC = 1;
   ```
   **Kết quả kỳ vọng:** SP trả về lỗi `KETQUA = -2` và thông báo `Không thể hủy: Lớp học đã được nhập điểm`.

---

## 3. Khôi phục dữ liệu sau kiểm thử
Chạy câu lệnh sau để khôi phục dữ liệu ban đầu:
```sql
UPDATE DANGKY SET DIEM_CC = NULL, DIEM_GK = NULL, DIEM_CK = NULL, HUYDANGKY = 0 WHERE MALTC = 1;
UPDATE LOPTINCHI SET HUYLOP = 0 WHERE MALTC = 1;
```
