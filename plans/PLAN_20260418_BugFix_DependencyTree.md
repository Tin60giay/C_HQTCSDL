# Kế hoạch Thực hiện: Phục hồi / Sửa lỗi và Cây Undo Mới

Dựa trên các vướng mắc bạn vừa ghi nhận, tôi xin đưa ra cách giải quyết kỹ thuật như sau để chốt nghiệm thu hoàn hảo nhất:

## 1. Chỉnh sửa CSS màu Nút bị Đóng Băng
- Quét qua tất cả 5 file `.html` (Khoa, Lớp, SinhVien, GiangVien, MonHoc).
- Sửa lại bộ thẻ CSS mặc định, thêm thuộc tính `btn:disabled` với nền `màu xám` (#52525b) và chữ xám nhạt, đổi con trỏ chuột thành hình cấm (Not-allowed). Giao diện sẽ hoàn toàn thân thiện khi nút Ghi bị khóa.

## 2. Fix Bug: Disable nút Lưu chuyển sang Edit Mode
- **Nguyên nhân:** Khi bạn gõ sai mã lúc Thêm, hệ thống báo đỏ + Khóa Nút. Nhưng ngay sau đó bạn lại bấm tay chuột lên 1 dòng trên Bảng Lưới để Sửa, hàm `chonDong()` tuy đã điền dữ liệu xong nhưng lại "quên" dọn dẹp dòng cảnh báo đỏ và "quên" bật lại nút Ghi cho bạn.
- **Giải pháp:** Sửa đổi logic các hàm `chonDong()`, `themMoi()` và `xoaTrang()` trên toàn bộ các file. Mỗi khi chuyển sang chế độ Sửa, hệ thống sẽ tự động gỡ mác báo lỗi mã trùng và thả xích (Enable) liên tức khắc cho nút `[💾 Lưu dữ liệu]`.

## 3. Realtime Validation cho Môn Học (Tiết TH, Tiết LT)
- Ở `monhoc.html`, bổ sung sự kiện bóp cò ngay (oninput) vào hai ô:
   - `Tiết Lý Thuyết`: Báo lỗi Tức_Thời nếu số nhập vào `< 30` (Màu đỏ: Phải >= 30).
   - `Tiết Thực Hành`: Báo lỗi Tức_Thời nếu số nhập vào `< 0` (Màu đỏ: Không được âm).
- Đồng bộ hóa với nút Ghi, nếu hai ô Text này vi phạm quy tắc, nút Ghi sẽ biến thành màu xám ngay lập tức. Dữ liệu sẽ 100% hợp lệ trước khi được đút vào Database.

## 4. Rombak Lịch sử (Cây Folder Thực Thụ & Khắc Nhu Cầu Từng Bước)
Tôi sẽ phá vỡ logic cũ (Hover làm tối loạt và bắt Undo Multi) để code lại theo chuẩn bạn muốn:

- **Giao diện Folders Cây:** Tôi sẽ lọc toàn bộ dữ liệu trả về từ server, tự phát hiện mối "quan hệ Cha - Con" bằng thuật toán:
   - Nếu trong 10 thao tác có Hành động `[Sửa/Thêm Sinh viên X]` và có hành động `[Thêm Lớp Y]` mà X thuộc về Lớp Y. Thì hành động Sinh Viên sẽ được dời vào NẰM GỌN TRONG 1 THƯ MỤC CỦA LỚP Y.
- **Validation Khóa Cha:** Bất cứ khi nào bạn nhấn nút `Hoàn tác` ngay tại Folder Cha (VD: *Thêm Lớp* ở lần 7). Mã JS sẽ kiểm tra có rễ/con bám không. Nếu có, báo thẳng ngay: *"❌ Không thể hoàn tác hành động này vì đang có các hành động con (Bước 8: Thêm sinh viên A) cản trở. Vui lòng hoàn tác bước 8 trước."*.
- Vứt bỏ chế độ Multi-Undo do không còn thích hợp. Mỗi nút Undo giờ đây hoạt động Đơn Tuyến và kiểm tra Con/Cha an toàn tuyệt đối.
