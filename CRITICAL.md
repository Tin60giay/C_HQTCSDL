- Database là bất di bất dịch, không được sửa đổi các hàng, cột thuộc tính có sẵn của nó
- Có thể sửa, xóa, thêm hàm, store procedure để phục vụ mục đích truy vấn
- Mọi kế hoạch lên phải lưu dưới tên PLANT_XXX lưu ở thư mục plans chờ tôi duyệt
- Mọi sự thay đổi ở bất cứ chỗ nào bạn đã thực hiện kèm lý do sẽ được ghi vào file CHANGELOGS_XXX lưu vào folder changelogs
- Hướng dẫn test các tính năng mới sẽ được lưu dưới dạng file HDSD_XXX và lưu vào folder hdsd
- Tất cả các thay đổi trong sp phải được thực hiện trong file setup_login.sql không tự ý tạo file sql mới
- Khi sửa/ thêm/ xóa một tính năng thuộc một trang html bất kỳ thì phải check lại toàn bộ trang html đang có để xem tính năng này có đang gặp lỗi tương tự ở các trang html khác hay không và fix toàn bộ
- Phải code dựa theo nguyên tắc: Vi phạm ràng buột thì trước hết làm mờ nút của chức năng đó trước -> sau khi sửa đúng thì mới làm sáng nút bấm lại, đã vi phạm ràng buộc thì tốt nhất nên làm mờ toàn bộ nút bấm cho an toàn
- Nhớ check kỹ các ràng buộc thuộc database dưới đây:

Table Khoa {
  MAKHOA  nchar(10)    [pk]
  TENKHOA nvarchar(50) [unique, not null]
}

Table Lop {
  MALOP   nchar(10)    [pk]
  TENLOP  nvarchar(50) [unique, not null]
  KHOAHOC nchar(9)     [not null]
  MAKHOA  nchar(10)    [not null, ref: > Khoa.MAKHOA]
}

Table Sinhvien {
  MASV      nchar(10)     [pk]
  HO        nvarchar(50)  [not null]
  TEN       nvarchar(10)  [not null]
  MALOP     nchar(10)     [not null, ref: > Lop.MALOP]
  PHAI      bit           [default: false, note: 'false: Nam, true: Nữ']
  NGAYSINH  datetime
  DIACHI    nvarchar(100)
  DANGHIHOC bit           [default: false]
  PASSWORD  nvarchar(40)  [default: '123456']
}

Table Monhoc {
  MAMH      nchar(10)    [pk]
  TENMH     nvarchar(50) [unique, not null]
  SOTIET_LT int          [not null]
  SOTIET_TH int          [not null]
}

Table Giangvien {
  MAGV      nchar(10)    [pk]
  HO        nvarchar(50) [not null]
  TEN       nvarchar(10) [not null]
  HOCVI     nvarchar(20)
  HOCHAM    nvarchar(20)
  CHUYENMON nvarchar(50)
  MAKHOA    nchar(10)    [not null, ref: > Khoa.MAKHOA]
}

Table Loptinchi {
  MALTC        int       [pk, increment]
  NIENKHOA     nchar(9)  [not null]
  HOCKY        int       [not null, note: '1 <= HOCKY <= 3']
  MAMH         nchar(10) [not null, ref: > Monhoc.MAMH]
  NHOM         int       [not null, note: '>= 1']
  MAGV         nchar(10) [not null, ref: > Giangvien.MAGV]
  MAKHOA       nchar(10) [not null, ref: > Khoa.MAKHOA]
  SOSVTOITHIEU smallint  [not null, note: '> 0']
  HUYLOP       bit       [default: false]

  indexes {
    (NIENKHOA, HOCKY, MAMH, NHOM) [unique]
  }
}

Table Dangky {
  MALTC     int       [not null, ref: > Loptinchi.MALTC]
  MASV      nchar(10) [not null, ref: > Sinhvien.MASV]
  DIEM_CC   int       [note: '0 đến 10']
  DIEM_GK   float     [note: '0 đến 10, làm tròn đến 0.5']
  DIEM_CK   float     [note: '0 đến 10, làm tròn đến 0.5']
  HUYDANGKY bit       [default: false]

  indexes {
    (MALTC, MASV) [pk]
  }
}

--ĐỀ BÀI:
Yêu cầu: 
   Viết chương trình thực hiện các công việc sau trên từng khoa:
3.1. Đăng nhập:
GIẢNG VIÊN ⚪		SINH VIÊN ⚪
Login     	:
Password	:
Trước khi sinh viên/ giảng viên sử dụng chương trình thì phải đăng ký trước.  Đối với sinh viên thì tất cả sinh viên dùng chung login sv để kết nối, lúc này label Login chuyển thành Mã SV.

3.2. Nhập liệu: gồm các công việc sau
- Nhập danh mục lớp: Form có các chức năng sau Thêm, Xóa, Ghi, Phục hồi, Thoát; Chức năng này do tài khoản thuộc nhóm PGV nhập. Trên từng khoa ta chỉ thấy được danh sách lớp thuộc khoa đó.
- Nhập danh sách sinh viên: dưới dạng SubForm 2 cấp. Yêu cầu: giống như lớp
- Nhập môn học: trên form Nhập môn học có các nút lệnh : Thêm, Xóa,  Ghi, Phục hồi, Thoát. Chức năng này do tài khoản thuộc nhóm PGV nhập
- Mở Lớp tín chỉ: có các chức năng Thêm, Xóa, Ghi, Phục hồi thông tin của lớp tín chỉ. Chức năng này do tài khoản thuộc nhóm PGV nhập
- Đăng ký lớp tín chỉ: user nhập vào mã sinh viên của mình, chương trình tự động in ra các thông tin của sinh viên (họ, tên, mã lớp).  Kế tiếp, user nhập vào Niên khóa, Học kỳ, chương trình sẽ tự động lọc ra các lớp tín chỉ đã mở trong niên khóa, học kỳ đó để sinh viên đăng ký (chưa hủy). Dữ liệu in ra gồm : MAMH, TENMH, nhóm, Hoten GV giảng,  số sv đã đăng ký;  Chức năng này do tài khoản thuộc nhóm SV nhập.
- Nhập điểm:  Điểm thuộc khoa nào thì khoa đó nhập hoặc PGV nhập. User nhập vào Niên khóa, Học kỳ, môn học, nhóm; click nút lệnh Bắt đầu thì chương trình tự động lọc ra các sinh viên có đăng ký trên lớp tín chỉ đó theo dạng sau, sau đó user chỉ nhập điểm vào. 
Điểm hết môn = Điểm CC * 0.1 + Điểm GK*0.3+ ĐCK * 0.6 
 
Mã SV
Họ tên SV
Điểm chuyên cần
Điểm giữa kỳ
Điểm cuối kỳ
Điểm hết môn
(read only)
(read only)
10
5
8
(tự động tính, read only)
3.5. Quản trị:
a. Tạo tài khoản cho người dùng sử dụng phần mềm













    Sau khi nhập điểm thi xong, click nút lệnh ‘Ghi điểm’ thì mới ghi hết điểm về CSDL. 

3.3. Phân quyền: Chương trình có các nhóm : PGV (phòng giáo vụ), KHOA, SV
-  Nếu login thuộc nhóm PGV thì login đó có toàn quyền. Login nhóm này được tạo tài khoản cho nhóm PGV, Khoa.  
-  Nếu login thuộc nhóm Khoa thì ta không cho nhập Khoa, Lớp, Giảng viên, Sinh viên, mở Lớp tín chỉ ; Login này được tạo tài khoản cho nhóm Khoa.
- Nhóm SV : được đăng ký lớp tín chỉ, xem Phiếu điểm của chính mình. Tất cả sinh viên đều dùng chung 1 login đăng nhập.
Chương trình cho phép ta tạo các login, password và cho login này làm việc với quyền hạn tương ứng. Căn cứ vào quyền này khi user login vào hệ thống, ta sẽ biết người đó được quyền làm việc với chức năng tương ứng. 
