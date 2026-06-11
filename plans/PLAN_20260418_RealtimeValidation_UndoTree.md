# Kế hoạch Thực hiện: Tính năng Nâng cao (Realtime Validation & Undo Tree)

Dựa trên yêu cầu của bạn, các chức năng cơ bản của 6 module (Lớp, Sinh viên, Môn học, Mở LTC, Đăng ký LTC, Nhập điểm) **cơ bản đã được đáp ứng đầy đủ và áp dụng đúng logic Database, phân quyền PGV/Khoa/SV.** 

Tôi sẽ tập trung khắc phục và nâng cấp **2 Bug/Tính năng UX mới** mà bạn vừa chỉ định:

## 1. Phát hiện mã trùng lặp tự động (Realtime Validation)
**Ý tưởng:** Không cần bấm "Lưu dữ liệu" hay "Enter" mới biết mã bị trùng. Ngay khi bạn đang gõ, hệ thống sẽ chớp nhoáng (debounce 500ms) kiểm tra dưới CSDL và báo ngay dưới ô Textbox nếu mã đã có người xài.

**Thực hiện:**
1. **Backend (`app.py`):** Tạo thêm 1 API nội bộ `GET /api/check_exists?table=...&id=...`. API này sẽ truy vấn `SELECT COUNT(*)` xuống CSDL.
2. **Frontend (`khoa.html`, `lop.html`, `giangvien.html`, `monhoc.html`, `sinhvien.html`):**
   - Áp dụng một thẻ `div` nhỏ tàng hình ngay dưới ô input Mã (Mã khoa, Mã lớp, Mã GV, v.v.).
   - Khi gõ phím (`oninput`), JS sẽ gọi API và hiển thị chữ đỏ: *"❌ Mã này đã tồn tại!"* hoặc chữ xanh *"✅ Mã hợp lệ"*.
   - Khóa nút "💾 Lưu dữ liệu" tạm thời nếu mã đang bị trùng.

## 2. Nâng cấp Lịch sử Hoàn tác (Cấu trúc Cây & Multi-Undo như Word)
**Ý tưởng:** Trong Microsoft Word, khi bạn bấm mũi tên Undo, một danh sách rủ xuống. Nếu bạn trượt chuột xuống mục số 5, nó bôi đen cả 5 mục và cho phép hoàn tác "Undo 5 Actions" cùng lúc. Chữ "Cấu trúc cây" có nghĩa là chúng ta sẽ gom nhóm (group) các hành động liên quan tới nhau (VD: Sinh viên A và B vừa thêm vào Lớp X sẽ được thụt lề gom chung dưới thẻ nhánh của Lớp X).

**Thực hiện (`static/history.js`):**
1. **Giao diện Tree-Node:** Quy hoạch lại UI danh sách lịch sử. Tự động nhận diện các hành động có chung một gốc (ví dụ chung `malop` hoặc `makhoa`) và sắp xếp thụt lề thành các cây (Ví dụ: 🗂 Dự án lớp D15CQCP01 -> ├─ Thêm sinh viên A -> └─ Thêm sinh viên B).
2. **Cơ chế Multi-Undo:** 
   - Thêm hiệu ứng Hover: khi rê chuột vào mục thứ `N` từ trên xuống, TẤT CẢ các mục từ `1` đến `N` sẽ được bôi màu đánh dấu (highlight).
   - Đổi nút 'Hoàn tác' thành cục bộ: Khi click vào vị trí đó, nó sẽ hiển thị *"Hoàn tác 3 hành động"*. 
   - Về logic code, nó sẽ gửi lệnh `Undo` liên tiếp 3 lần xuống `/history/undo`.
