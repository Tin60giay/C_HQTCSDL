# TÀI LIỆU QUY TẮC NGHIỆP VỤ (BUSINESS RULES)
## CÁC CHỨC NĂNG CRUD & UNDO (MÔN HỌC & LỚP TÍN CHỈ)
---

> **LƯU Ý KHI THI VẤN ĐÁP:** Giảng viên sẽ hỏi những câu cực kỳ thực tế để kiểm tra xem bạn có hiểu cơ sở dữ liệu và quy trình nghiệp vụ đào tạo hay không, hay chỉ code chạy được là xong. Tài liệu này cung cấp chi tiết các điều kiện kiểm tra (validation) và lý do thực tế của chúng.

---

## PHẦN I: QUẢN LÝ MÔN HỌC (SUBJECT MANAGEMENT)

### 1. Thao tác CRUD (Thêm, Sửa, Xóa)

#### A. Thêm mới Môn học
* **Điều kiện kiểm tra:**
  1. Mã môn học không được để trống và không được trùng với môn học đã có.
  2. Tên môn học không được để trống và không được trùng với môn học đã có.
  3. Số tiết lý thuyết (`SOTIET_LT`) phải `>= 0` và số tiết thực hành (`SOTIET_TH`) phải `>= 0`.
  4. Tổng số tiết (`SOTIET_LT + SOTIET_TH`) phải lớn hơn `0`.
* **Giải thích thực tế (Vấn đáp):** Môn học không thể có tổng số tiết bằng 0 (vì như vậy không có nội dung giảng dạy). Tên môn học phải độc nhất để tránh gây nhầm lẫn trong chương trình đào tạo của sinh viên.

#### B. Sửa (Ghi) Môn học
* **Điều kiện kiểm tra:**
  1. Môn học muốn sửa phải tồn tại trong hệ thống.
  2. Tên môn học mới không được trùng với tên của môn học khác.
  3. Số tiết lý thuyết, thực hành mới phải `>= 0`.
  4. **Ràng buộc đặc biệt (Cực kỳ quan trọng):** Nếu môn học **đang được sử dụng trong bất kỳ Lớp tín chỉ nào có sinh viên đăng ký học hoặc có điểm số**:
     * **KHÔNG ĐƯỢC PHÉP** thay đổi Số tiết lý thuyết (`SOTIET_LT`) và Số tiết thực hành (`SOTIET_TH`).
     * **CHỈ ĐƯỢC PHÉP** thay đổi Tên môn học (nhằm mục đích sửa lỗi chính tả).
* **Giải thích thực tế (Vấn đáp):** Nếu một môn học đã mở lớp và sinh viên đã học/đang học, việc thay đổi số tiết sẽ trực tiếp làm sai lệch cấu trúc tín chỉ và số giờ lên lớp của sinh viên trong quá khứ/hiện tại, ảnh hưởng tới việc xét tốt nghiệp và học phí. Do đó, chỉ được sửa tên môn học nếu ghi nhận sai sót chữ viết, tuyệt đối khóa số tiết.

#### C. Xóa Môn học
* **Điều kiện kiểm tra:**
  * Môn học chỉ được phép xóa khi **chưa từng được sử dụng để mở bất kỳ Lớp tín chỉ nào** trong hệ thống (dù lớp tín chỉ đó đang hoạt động hay đã bị hủy).
* **Giải thích thực tế (Vấn đáp):** Nếu môn học đã được sử dụng trong bảng `LOPTINCHI`, việc xóa môn học sẽ vi phạm ràng buộc khóa ngoại (Foreign Key Constraint) trong Cơ sở dữ liệu, dẫn tới lỗi hệ thống. Về nghiệp vụ, môn học đã đưa vào kế hoạch mở lớp thì không thể xóa bỏ khỏi danh mục môn học đào tạo để bảo toàn lịch sử dữ liệu.

---

### 2. Thao tác Hoàn tác (Undo) Môn học

| Hành động gốc | Thao tác hoàn tác | Điều kiện để thực hiện Undo thành công (Nút Undo sáng) | Lý do bị chặn (Nút Undo mờ đi) |
| :--- | :--- | :--- | :--- |
| **Thêm môn học** (`THEM_MH`) | Xóa môn học vừa thêm | Môn học hiện tại chưa bị sử dụng ở bất kỳ Lớp tín chỉ nào. | Môn học đã được đưa vào Lớp tín chỉ (vi phạm khóa ngoại). |
| **Xóa môn học** (`XOA_MH`) | Thêm lại môn học đã xóa | Mã môn học và Tên môn học cũ chưa bị người khác tạo mới lại trong hệ thống. | Mã môn học hoặc tên môn học đã tồn tại lại trong DB. |
| **Sửa môn học** (`SUA_MH`) | Khôi phục lại tên và số tiết cũ | Môn học tồn tại; tên môn học cũ không trùng với môn khác. Nếu thông tin cũ có đổi số tiết, môn học phải chưa phát sinh đăng ký. | Tên cũ bị trùng môn khác, hoặc môn học đã có SV đăng ký học (nếu hoàn tác số tiết). |

---
---

## PHẦN II: MỞ LỚP TÍN CHỈ (CREDIT CLASS OPENING)

### 1. Thao tác CRUD (Thêm, Sửa, Xóa/Hủy)

#### A. Thêm mới Lớp tín chỉ (Mở lớp)
* **Điều kiện kiểm tra:**
  1. Niên khóa phải đúng định dạng `YYYY-YYYY` (ví dụ: `2025-2026`).
  2. Học kỳ phải nằm trong khoảng từ `1` đến `3`.
  3. Môn học (`MAMH`) và Giảng viên (`MAGV`) phải tồn tại trong danh mục tương ứng.
  4. Số sinh viên tối thiểu (`SOSVTOITHIEU`) phải lớn hơn `0`.
  5. Tổ hợp `(NIENKHOA, HOCKY, MAMH, NHOM)` của lớp học đang hoạt động (`HUYLOP = 0`) không được trùng lặp.
* **Giải thích thực tế (Vấn đáp):** Mỗi môn học trong một học kỳ chỉ có thể chia làm các Nhóm khác nhau (Nhóm 1, Nhóm 2,...). Không thể tồn tại hai lớp học của cùng một môn, trong cùng một học kỳ, cùng niên khóa mà lại có chung một số Nhóm (vì sẽ gây nhầm lẫn lịch học, phòng học và bảng điểm).

#### B. Sửa (Ghi) Lớp tín chỉ
* **Điều kiện kiểm tra:**
  1. Lớp tín chỉ phải tồn tại.
  2. **Trường hợp đã nhập điểm (Chặt chẽ nhất):** Nếu lớp học đã có điểm số (`DIEM_CC`, `DIEM_GK` hoặc `DIEM_CK` khác NULL) của bất kỳ sinh viên nào, **CẤM SỬA TUYỆT ĐỐI** mọi thông tin của lớp tín chỉ.
  3. **Trường hợp đã có sinh viên đăng ký (chưa có điểm):**
     * **KHÔNG ĐƯỢC PHÉP sửa đổi:** Môn học (`MAMH`), Niên khóa (`NIENKHOA`), Học kỳ (`HOCKY`), Nhóm (`NHOM`), Khoa (`MAKHOA`).
     * **ĐƯỢC PHÉP sửa đổi:** 
       * Giảng viên (`MAGV`): Để phục vụ nghiệp vụ thay đổi giảng viên đứng lớp đột xuất.
       * Số sinh viên tối thiểu (`SOSVTOITHIEU`): Nhưng số mới phải `>=` số lượng sinh viên hiện tại đã đăng ký vào lớp này.
* **Giải thích thực tế (Vấn đáp):** 
  * Nếu đã nhập điểm, lớp học đã hoàn thành hoặc đang kết thúc. Thay đổi thông tin sẽ phá vỡ tính toàn vẹn của bảng điểm và kết quả học tập của sinh viên.
  * Nếu đã có sinh viên đăng ký, việc đổi Môn học/Niên khóa/Học kỳ/Nhóm sẽ làm thay đổi hoàn toàn kế hoạch học tập của sinh viên (sinh viên đăng ký môn A nhóm 1 tự dưng bị chuyển sang môn B nhóm 2). Số SV tối thiểu không được nhỏ hơn số SV thực tế đang đăng ký vì lớp không thể có giới hạn tối thiểu thấp hơn số lượng người thực tế đã tham gia.

#### C. Biến động Lớp tín chỉ: "Xóa vĩnh viễn" vs "Hủy lớp" vs "Mở lại lớp"
Hệ thống phân chia rõ ràng các trạng thái biến động dựa trên tương tác thực tế của sinh viên:
1. **Xóa vĩnh viễn (Xóa vật lý - DELETE):**
   * **Điều kiện:** Lớp tín chỉ hoàn toàn **chưa có sinh viên nào đăng ký** (`SOSV_DANGKY = 0`).
   * **Nghiệp vụ:** Đây là lớp rác tạo nhầm do lỗi nhập liệu của Giáo vụ, chưa phát sinh giao dịch, cho phép xóa sạch khỏi hệ thống.
2. **Hủy lớp (Hủy logic - UPDATE HUYLOP = 1):**
   * **Điều kiện:** Lớp tín chỉ **đã có sinh viên đăng ký** nhưng **chưa nhập bất kỳ cột điểm nào**.
   * **Nghiệp vụ:** Lớp không đủ số lượng sinh viên tối thiểu hoặc giảng viên gặp sự cố. Lớp bị chuyển sang trạng thái "Đã hủy" (hiển thị mờ xám trong danh sách) để lưu vết lịch sử đăng ký, tránh xóa mất dữ liệu học tập của sinh viên.
3. **Mở lại lớp (Khôi phục hoạt động - UPDATE HUYLOP = 0):**
   * **Điều kiện:** Lớp tín chỉ đang bị hủy (`HUYLOP = 1`) và không bị trùng tổ hợp `(Môn, Nhóm, HK, NK)` với một lớp đang hoạt động khác.
   * **Nghiệp vụ:** Khôi phục lại trạng thái giảng dạy bình thường cho lớp tín chỉ đã bị hủy nhầm trước đó.

---

### 2. Thao tác Hoàn tác (Undo) Lớp tín chỉ

| Hành động gốc | Thao tác hoàn tác | Điều kiện để thực hiện Undo thành công (Nút Undo sáng) | Lý do bị chặn (Nút Undo mờ đi) |
| :--- | :--- | :--- | :--- |
| **Mở lớp TC** (`THEM_LTC`) | Xóa vật lý lớp tín chỉ | Lớp tín chỉ tồn tại và chưa có bất kỳ sinh viên nào đăng ký vào lớp này. | Lớp đã phát sinh sinh viên đăng ký học (bảo toàn dữ liệu đăng ký). |
| **Xóa vĩnh viễn lớp TC** (`XOA_VINH_VIEN_LTC`) | Tạo lại lớp tín chỉ đã xóa | Mã lớp tín chỉ và tổ hợp môn học/giáo viên chưa bị ai tạo mới đè lên. | Trùng khóa chính hoặc trùng tổ hợp lớp đang hoạt động khác. |
| **Hủy lớp TC** (`XOA_LTC`) | Mở lại lớp tín chỉ (`HUYLOP = 0`) | Lớp tín chỉ tồn tại ở trạng thái hủy. Tổ hợp `(NK, HK, MH, Nhóm)` của lớp này không trùng với bất kỳ lớp đang hoạt động nào khác trong DB. Giảng viên và Môn học cũ phải còn tồn tại. | Trùng tổ hợp với một lớp đang hoạt động khác (do trong lúc hủy, người khác đã tạo lớp mới trùng nhóm), hoặc giảng viên/môn học đã bị xóa khỏi danh mục. |
| **Sửa lớp TC** (`SUA_LTC`) | Khôi phục lại thông tin cũ | Lớp tín chỉ tồn tại. Nếu hoàn tác thông tin cốt lõi, lớp phải chưa có đăng ký. Nếu khôi phục giảng viên/số SV, lớp phải chưa có điểm. Các đối tượng tham chiếu cũ phải còn tồn tại. | Lớp đã có SV đăng ký học (đối với hoàn tác môn/nhóm/học kỳ/niên khóa) hoặc lớp đã được nhập điểm. |

---
---

## PHẦN III: DANH SÁCH LỊCH SỬ THAO TÁC (HISTORY LIST)

Hệ thống duy trì tối đa **10 hành động gần nhất** cho mỗi phiên làm việc (session). Khi người dùng mở bảng lịch sử:
1. **Kiểm tra Realtime:** Backend sẽ quét qua 10 hành động này, thực thi các câu lệnh `SELECT` kiểm tra database tương ứng với bảng điều kiện ở trên.
2. **Khóa UI trực quan:**
   * Nếu thỏa mãn điều kiện: Nút **Hoàn tác** sẽ sáng, cho phép click để thực hiện khôi phục.
   * Nếu không thỏa mãn: Nút **Hoàn tác** sẽ bị mờ đi (disabled). Một dòng cảnh báo màu đỏ dạng `⚠️ Không thể hoàn tác: [Lý do]` sẽ hiển thị ngay bên dưới hành động đó, đồng thời hiển thị tooltip giải thích chi tiết khi di chuột qua để người dùng biết chính xác tại sao nút bị mờ.

---
---

## PHẦN IV: CỘT TRẠNG THÁI (STATUS COLUMN) TRỰC QUAN

Hệ thống bổ sung cột **Trạng thái** dạng Badge màu sắc trên giao diện HTML nhằm tăng trải nghiệm người dùng và tính chuyên nghiệp của sản phẩm:

### 1. Đối với Môn học (`monhoc.html`):
* **Đã dạy (Khóa) 🔒** (Màu xám/vàng): Môn học đã phát sinh lớp tín chỉ trong quá khứ hoặc hiện tại. Số tiết lý thuyết và thực hành đã bị khóa không cho phép thay đổi.
* **Chưa giảng dạy ✨** (Màu xanh ngọc): Môn học hoàn toàn mới, giáo vụ có toàn quyền sửa đổi mọi thông tin hoặc xóa bỏ.

### 2. Đối với Lớp tín chỉ (`loptinchi.html`):
* **Đã khóa 🔒** (Màu xám tối): Lớp học thuộc niên khóa cũ trước 2025. Dữ liệu lịch sử, không cho phép chỉnh sửa.
* **Đã hủy 🚫** (Màu đỏ mờ): Lớp đã bị hủy hoạt động, dòng hiển thị mờ đi và có tùy chọn mở lại lớp.
* **Đã có điểm 📝** (Màu cam sáng): Lớp đã bắt đầu nhập điểm số cho sinh viên, bị khóa cứng mọi thông tin.
* **Đủ điều kiện ✅** (Màu xanh dương): Lớp đang mở, chưa có điểm và số lượng sinh viên đăng ký đã đạt hoặc vượt mức tối thiểu để giảng dạy.
* **Chờ đăng ký ⏳** (Màu xanh lá): Lớp đang mở, chưa có điểm nhưng số lượng sinh viên đăng ký hiện tại chưa đủ điều kiện tối thiểu để mở lớp.
