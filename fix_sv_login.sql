USE [QLDSV_HTC]
GO

-- ============================================================
-- FIX: SP_DANGNHAP_SV — thêm cột MALOP, TENLOP vào kết quả trả về
-- Lý do: Flask app cần MALOP để lưu session['malop'] cho SV
-- ============================================================
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_DANGNHAP_SV' AND type = 'P')
    DROP PROCEDURE SP_DANGNHAP_SV
GO

CREATE PROCEDURE SP_DANGNHAP_SV
    @MASV     NCHAR(10),
    @PASSWORD NVARCHAR(40)
AS
BEGIN
    SET NOCOUNT ON
    SELECT 
        SV.MASV                                          AS USER_NAME,
        RTRIM(SV.HO) + N' ' + RTRIM(SV.TEN)             AS HOTEN,
        K.TENKHOA                                        AS TENGROUP,
        RTRIM(SV.MALOP)                                  AS MALOP,
        RTRIM(L.TENLOP)                                  AS TENLOP
    FROM SINHVIEN SV
    INNER JOIN LOP  L ON SV.MALOP  = L.MALOP
    INNER JOIN KHOA K ON L.MAKHOA  = K.MAKHOA
    WHERE SV.MASV      = @MASV 
      AND SV.PASSWORD  = @PASSWORD
      AND SV.DANGHIHOC = 0
END
GO

GRANT EXECUTE ON SP_DANGNHAP_SV TO [sv]
GO

PRINT N'[OK] SP_DANGNHAP_SV da duoc cap nhat (them MALOP, TENLOP)'
GO

-- ============================================================
-- CẤP QUYỀN EXECUTE cho user [sv] trên các SP cần thiết
-- (chạy lại để đảm bảo đủ quyền)
-- ============================================================
GRANT EXECUTE ON SP_GET_LOPTINCHI_DANGKY TO [sv]
GO
GRANT EXECUTE ON SP_DANGKY_LTC          TO [sv]
GO
GRANT EXECUTE ON SP_XEM_PHIEU_DIEM      TO [sv]
GO
GRANT EXECUTE ON SP_GET_THONGTIN_SV     TO [sv]
GO
GRANT EXECUTE ON SP_GET_ALL_NIENKHOA    TO [sv]
GO
GRANT SELECT ON [dbo].[LOPTINCHI]       TO [sv]
GO
GRANT SELECT ON [dbo].[MONHOC]          TO [sv]
GO
GRANT SELECT ON [dbo].[GIANGVIEN]       TO [sv]
GO
GRANT SELECT ON [dbo].[DANGKY]          TO [sv]
GO
GRANT INSERT ON [dbo].[DANGKY]          TO [sv]
GO
GRANT UPDATE ON [dbo].[DANGKY]          TO [sv]
GO

PRINT N'[OK] Da cap quyen day du cho user [sv]'
GO

-- ============================================================
-- KIỂM TRA: Thử đăng nhập SV mẫu (N15DCCN001, password rỗng '')
-- ============================================================
-- EXEC SP_DANGNHAP_SV 'N15DCCN001', ''
-- Kết quả mong đợi: 1 dòng với USER_NAME, HOTEN, TENGROUP, MALOP, TENLOP
GO
