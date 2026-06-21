# CHANGELOGS_NHAPDIEM_AV_CTDL_2026 — Nhật ký sửa đổi Phiếu điểm (lớp đã hủy) & Bộ lọc Nhập điểm môn CTDL

> Ngày: 2026-06-19  |  Lý do thay đổi: Sửa lỗi lớp học đã hủy vẫn hiện trong phiếu điểm sinh viên N23DCCI079; đồng thời tối ưu hóa bộ lọc nhóm trên giao diện nhập điểm để tự động lọc và hiển thị danh sách nhóm thực tế thay vì nhập số thủ công.

---

## 1. Danh sách các file thay đổi

| STT | File | Loại thay đổi | Chi tiết thay đổi |
|---|---|---|---|
| 1 | `setup_login.sql` | Cập nhật SP | Sửa `SP_XEM_PHIEU_DIEM` thêm điều kiện lọc `AND (LTC.HUYLOP = 0 OR LTC.HUYLOP IS NULL)` để loại bỏ các lớp học đã bị hủy khỏi phiếu điểm của sinh viên. |
| 2 | `app.py` | Thêm API mới | Thêm route `/nhapdiem/nhom_list` (POST) dùng để lấy danh sách các nhóm môn học của lớp tín chỉ hợp lệ (chưa bị hủy) tương ứng học kỳ/niên khóa được chọn. |
| 3 | `templates/nhapdiem.html` | Cập nhật giao diện | Chuyển ô nhập nhóm `fNHOM` (dạng số nhập tay) thành select dropdown; tích hợp hàm JS `taiNhomList()` để load động danh sách nhóm qua AJAX; thiết lập tự động điền niên khóa hợp lệ mới nhất và kích hoạt load dữ liệu khi tải xong trang (`DOMContentLoaded`). |

---

## 2. Nhật ký thay đổi cụ thể

### 2.1 Cập nhật Stored Procedure `SP_XEM_PHIEU_DIEM`
Thực hiện thêm điều kiện loại trừ các lớp đã bị hủy (`LTC.HUYLOP = 1`) trong câu lệnh SELECT của SP:
```sql
ALTER PROCEDURE SP_XEM_PHIEU_DIEM
    @MASV NCHAR(10)
AS
BEGIN
    ...
    SELECT
        ...
    FROM DANGKY DK
    INNER JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC
    INNER JOIN MONHOC    MH  ON LTC.MAMH  = MH.MAMH
    INNER JOIN GIANGVIEN GV  ON LTC.MAGV  = GV.MAGV
    WHERE DK.MASV = @MASV
      AND (DK.HUYDANGKY = 0 OR DK.HUYDANGKY IS NULL)
      AND (LTC.HUYLOP = 0 OR LTC.HUYLOP IS NULL) -- [PLANT_NHAPDIEM_AV_CTDL_2026] Ẩn lớp bị hủy
      AND (@NamBD IS NULL OR CAST(LEFT(LTC.NIENKHOA, 4) AS INT) BETWEEN @NamBD AND @NamKT)
    ORDER BY LTC.NIENKHOA, LTC.HOCKY, MH.TENMH
END
```

### 2.2 Bổ sung API `/nhapdiem/nhom_list` trong `app.py`
API này cho phép giao diện frontend truy vấn các nhóm thực tế của một môn học:
```python
@app.route('/nhapdiem/nhom_list', methods=['POST'])
@require_group('PGV', 'KHOA')
def nhapdiem_nhom_list():
    data = request.get_json(silent=True) or request.form
    nienkhoa = (data.get('nienkhoa', '') or '').strip()
    hocky = data.get('hocky', '')
    mamh = (data.get('mamh', '') or '').strip().upper()
    conn, _ = get_db()
    if not conn:
        return jsonify({'ok': False, 'msg': 'Không thể kết nối DB'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT NHOM FROM LOPTINCHI WHERE NIENKHOA=? AND HOCKY=? AND MAMH=? AND HUYLOP=0 ORDER BY NHOM",
            (nienkhoa, int(hocky), mamh)
        )
        nhom_list = [r[0] for r in cursor.fetchall()]
        return jsonify({'ok': True, 'nhom_list': nhom_list})
    ...
```

### 2.3 Chuyển trường nhập nhóm thành dropdown trong `nhapdiem.html`
- Chuyển `<input type="number">` thành `<select id="fNHOM">`.
- Viết hàm `taiNhomList()` để thực hiện gọi API lấy nhóm, nạp vào dropdown và tự động gọi `batDau()` để hiển thị danh sách sinh viên của nhóm đầu tiên.
- Khởi tạo trang: tự động điền niên khóa mới nhất chưa bị khóa (ví dụ `2025-2026`) vào ô Niên khóa khi tải trang.

### 2.4 Dữ liệu mẫu (Theo yêu cầu trực tiếp từ user)
- Xóa bản ghi đăng ký của sinh viên quá hạn `N15DCCN004` khỏi các lớp tín chỉ thuộc niên khóa `2025-2026` (`MALTC = 9` và `MALTC = 13`) khỏi bảng `DANGKY` để tránh hiển thị sai lệch trong phần nhập điểm.
