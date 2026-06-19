# HDSD_006 — Hướng dẫn kiểm tra các tính năng đã sửa

## Ngày: 2026-04-20

---

## 1. Kiểm tra bảng có thanh cuộn (tối đa 10 dòng)

**Các trang**: Khoa, Lớp, Môn Học, Giảng Viên, Sinh Viên, Lớp Tín Chỉ

1. Đăng nhập với tài khoản GV thuộc nhóm PGV
2. Truy cập lần lượt từng trang quản lý
3. **Kỳ vọng**: Nếu bảng có > 10 dòng, bảng sẽ hiển thị thanh cuộn dọc, không tràn ra ngoài

---

## 2. Kiểm tra nút Xóa không sáng sai

**Các trang**: Khoa, Lớp, Môn Học, Giảng Viên, Sinh Viên

1. Đăng nhập PGV → vào trang Quản lý Lớp
2. Click chọn một lớp **đang có sinh viên** (ví dụ: D15CQCP01-N)
3. **Kỳ vọng**: 
   - Nút **Lưu dữ liệu** sáng lên ✅
   - Nút **Xóa** vẫn **mờ** (do lớp có SV, vi phạm ràng buộc) ✅
   - Nút **Tạo mới** mờ ✅
4. Click chọn một lớp **không có sinh viên** 
5. **Kỳ vọng**: Nút **Xóa** sáng lên ✅

---

## 3. Kiểm tra nút Tạo mới / Lưu ở Môn Học

1. Đăng nhập PGV → vào trang Quản lý Môn Học
2. Click chọn một môn học trong bảng (ví dụ: CTDL)
3. Sửa tên môn học ở form bên dưới
4. **Kỳ vọng**:
   - Nút **Lưu dữ liệu** sáng ✅
   - Nút **Tạo mới** mờ ✅ (vì đang ở chế độ editing, không phải adding)
5. Click **Làm mới form** → bấm vào ô Mã MH → gõ mã mới
6. **Kỳ vọng**: Nút **Tạo mới** sáng ✅, nút **Lưu** mờ ✅

---

## 4. Kiểm tra Bảng Điểm Cá Nhân (SV) — IMPORTANT

1. Đăng nhập bằng tài khoản **Sinh Viên** (VD: MASV / password 123456)
2. Vào menu **📄 Bảng Điểm Cá Nhân**
3. **Kỳ vọng**:
   - Hiển thị đúng: Mã SV, Họ tên, Lớp, Ngày sinh
   - Bảng điểm hiển thị các môn đã được nhập điểm
   - Điểm Hệ Mười (HM) = CC*0.1 + GK*0.3 + CK*0.6
   - Điểm HM >= 5: màu xanh | < 5: màu đỏ

---

## 5. Kiểm tra SV không thấy niên khóa quá khứ

1. Đăng nhập SV khóa 2025-2029
2. Vào **Đăng ký Lớp Tín Chỉ**
3. Mở dropdown **Niên khóa**
4. **Kỳ vọng**: Chỉ thấy niên khóa từ 2025-2026 đến 2028-2029 ✅
   - Không thấy 2024-2025 hoặc cũ hơn ❌

---

## 6. Kiểm tra nút Hủy đăng ký bị mờ khi đã có điểm

1. Đăng nhập PGV → Nhập điểm cho một SV ở LTC bất kỳ
2. Đăng nhập SV đó → Đăng ký LTC → chọn niên khóa/HK tương ứng
3. Tìm LTC đã được nhập điểm
4. **Kỳ vọng**:
   - Nút **Hủy đăng ký** bị mờ (disabled) ✅
   - Hiển thị badge **📝 Đã có điểm** bên cạnh ✅
   - Tooltip: "Không thể hủy vì đã được nhập điểm"

---

## 7. Kiểm tra bộ lọc Môn Học hoạt động

1. Vào Quản lý Môn Học
2. Gõ vào ô tìm kiếm một từ khóa (VD: "cấu trúc")
3. **Kỳ vọng**: Chỉ hiển thị các môn chứa từ khóa ✅

---

## 8. Kiểm tra bộ lọc Lớp Tín Chỉ hoạt động

1. Vào Mở Lớp Tín Chỉ
2. Chọn Niên khóa / Học kỳ / Khoa từ các dropdown
3. **Kỳ vọng**: Bảng LTC chỉ hiển thị các dòng khớp filter ✅
