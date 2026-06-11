- Database là bất di bất dịch, không được sửa đổi các hàng, cột thuộc tính có sẵn của nó
- Có thể sửa, xóa, thêm hàm, store procedure để phục vụ mục đích truy vấn
- Mọi kế hoạch lên phải lưu dưới tên PLANT_XXX lưu ở thư mục plans chờ tôi duyệt
- Mọi sự thay đổi ở bất cứ chỗ nào bạn đã thực hiện kèm lý do sẽ được ghi vào file CHANGELOGS_XXX lưu vào folder changelogs
- Hướng dẫn test các tính năng mới sẽ được lưu dưới dạng file HDSD_XXX và lưu vào folder hdsd
- Tất cả các thay đổi trong sp phải được thực hiện trong file setup_login.sql không tự ý tạo file sql mới
- Khi sửa/ thêm/ xóa một tính năng thuộc một trang html bất kỳ thì phải check lại toàn bộ trang html đang có để xem tính năng này có đang gặp lỗi tương tự ở các trang html khác hay không và fix toàn bộ
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