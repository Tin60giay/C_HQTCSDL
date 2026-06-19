USE [QLDSV_HTC]
GO
ALTER DATABASE [QLDSV_HTC] SET TRUSTWORTHY ON
GO
GRANT VIEW DEFINITION TO [public]
GO


USE [master]
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'sv')
BEGIN
    CREATE LOGIN [sv] WITH PASSWORD = N'123', DEFAULT_DATABASE = [QLDSV_HTC], CHECK_POLICY = OFF
    PRINT N'Đã tạo login sv'
END
ELSE
    PRINT N'Login sv đã tồn tại'
GO

USE [QLDSV_HTC]
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'sv')
BEGIN
    CREATE USER [sv] FOR LOGIN [sv]
    PRINT N'Đã tạo user sv trong QLDSV_HTC'
END
GO

-- Cấp quyền cho user 'sv'
GRANT SELECT ON [dbo].[SINHVIEN] TO [sv]
GRANT SELECT ON [dbo].[LOP] TO [sv]
GRANT SELECT ON [dbo].[KHOA] TO [sv]
GO


IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_DANGNHAP_GV' AND type = 'P')
    DROP PROCEDURE SP_DANGNHAP_GV
GO

CREATE PROCEDURE SP_DANGNHAP_GV
    @MAGV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON

    SELECT 
        GV.MAGV AS USER_NAME,
        RTRIM(GV.HO) + ' ' + RTRIM(GV.TEN) AS HOTEN,
        K.TENKHOA AS TENGROUP
    FROM GIANGVIEN GV
    INNER JOIN KHOA K ON GV.MAKHOA = K.MAKHOA
    WHERE GV.MAGV = @MAGV
END
GO

GRANT EXECUTE ON SP_DANGNHAP_GV TO PUBLIC
GO

PRINT N'Đã tạo SP_DANGNHAP_GV'
GO


IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_DANGNHAP_SV' AND type = 'P')
    DROP PROCEDURE SP_DANGNHAP_SV
GO

CREATE PROCEDURE SP_DANGNHAP_SV
    @MASV     NCHAR(10),
    @PASSWORD NVARCHAR(40)
AS
BEGIN
    SET NOCOUNT ON

    -- [QUA_HAN_SP_2026] Tính cờ QUAHAN:
    --   1 = sinh viên đã học quá 7 năm kể từ khóa học
    --   0 = còn trong thời hạn
    -- Công thức: YEAR(GETDATE()) - CAST(LEFT(LOP.KHOAHOC, 4) AS INT) > 7
    DECLARE @KhoaHocNBD INT = NULL
    DECLARE @QuaHan BIT = 0

    SELECT @KhoaHocNBD = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    IF @KhoaHocNBD IS NOT NULL AND (YEAR(GETDATE()) - @KhoaHocNBD) > 7
        SET @QuaHan = 1

    SELECT 
        SV.MASV                                         AS USER_NAME,
        RTRIM(SV.HO) + N' ' + RTRIM(SV.TEN)            AS HOTEN,
        K.TENKHOA                                       AS TENGROUP,
        RTRIM(SV.MALOP)                                 AS MALOP,
        RTRIM(L.TENLOP)                                 AS TENLOP,
        @QuaHan                                         AS QUAHAN
    FROM SINHVIEN SV
    INNER JOIN LOP  L ON SV.MALOP  = L.MALOP
    INNER JOIN KHOA K ON L.MAKHOA  = K.MAKHOA
    WHERE SV.MASV      = @MASV 
      AND SV.PASSWORD  = @PASSWORD
      AND SV.DANGHIHOC = 0
END
GO

GRANT EXECUTE ON SP_DANGNHAP_SV      TO [sv]
GO
GRANT EXECUTE ON SP_GET_THONGTIN_SV  TO [sv]
GO
GRANT EXECUTE ON SP_GET_LOPTINCHI_DANGKY TO [sv]
GO
GRANT EXECUTE ON SP_DANGKY_LTC       TO [sv]
GO
GRANT EXECUTE ON SP_XEM_PHIEU_DIEM   TO [sv]
GO
GRANT EXECUTE ON SP_GET_ALL_NIENKHOA TO [sv]
GO
GRANT SELECT  ON [dbo].[LOPTINCHI]   TO [sv]
GO
GRANT SELECT  ON [dbo].[MONHOC]      TO [sv]
GO
GRANT SELECT  ON [dbo].[GIANGVIEN]   TO [sv]
GO
GRANT SELECT  ON [dbo].[DANGKY]      TO [sv]
GO
GRANT INSERT  ON [dbo].[DANGKY]      TO [sv]
GO
GRANT UPDATE  ON [dbo].[DANGKY]      TO [sv]
GO

PRINT N'Đã tạo SP_DANGNHAP_SV (v2: có MALOP, TENLOP + cấp quyền đầy đủ cho [sv])'
GO

--4
DECLARE @magv NVARCHAR(10)
DECLARE @sql NVARCHAR(MAX)

DECLARE cur_gv CURSOR FOR
    SELECT RTRIM(MAGV) FROM GIANGVIEN

OPEN cur_gv
FETCH NEXT FROM cur_gv INTO @magv

WHILE @@FETCH_STATUS = 0
BEGIN
    IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = @magv)
    BEGIN
        SET @sql = 'CREATE LOGIN [' + @magv + '] WITH PASSWORD = N''' + @magv + ''', DEFAULT_DATABASE = [QLDSV_HTC], CHECK_POLICY = OFF'
        EXEC sp_executesql @sql
        PRINT N'Đã tạo login: ' + @magv
    END
    ELSE
        PRINT N'Login đã tồn tại: ' + @magv

    IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = @magv)
    BEGIN
        SET @sql = 'CREATE USER [' + @magv + '] FOR LOGIN [' + @magv + ']'
        EXEC sp_executesql @sql
    END

    SET @sql = 'GRANT EXECUTE ON SP_DANGNHAP_GV TO [' + @magv + ']'
    EXEC sp_executesql @sql
    SET @sql = 'GRANT SELECT ON [dbo].[GIANGVIEN] TO [' + @magv + ']'
    EXEC sp_executesql @sql
    SET @sql = 'GRANT SELECT ON [dbo].[KHOA] TO [' + @magv + ']'
    EXEC sp_executesql @sql
    SET @sql = 'GRANT SELECT ON [dbo].[LOP] TO [' + @magv + ']'
    EXEC sp_executesql @sql
    SET @sql = 'GRANT SELECT ON [dbo].[SINHVIEN] TO [' + @magv + ']'
    EXEC sp_executesql @sql
    SET @sql = 'GRANT SELECT ON [dbo].[LOPTINCHI] TO [' + @magv + ']'
    EXEC sp_executesql @sql
    SET @sql = 'GRANT SELECT ON [dbo].[DANGKY] TO [' + @magv + ']'
    EXEC sp_executesql @sql
    SET @sql = 'GRANT SELECT ON [dbo].[MONHOC] TO [' + @magv + ']'
    EXEC sp_executesql @sql

    FETCH NEXT FROM cur_gv INTO @magv
END

CLOSE cur_gv
DEALLOCATE cur_gv
GO

PRINT N'=== SETUP HOÀN TẤT ==='
GO

-- ============================================================
-- CÁC STORED PROCEDURE BỔ SUNG (THÊM MỚI - KHÔNG SỬA SP CŨ)
-- ============================================================

-- ------------------------------------------------------------
-- SP_GETALL_KHOA: Lấy danh sách tất cả khoa (dành cho PGV)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GETALL_KHOA' AND type = 'P')
    DROP PROCEDURE SP_GETALL_KHOA
GO
CREATE PROCEDURE SP_GETALL_KHOA
AS
BEGIN
    SET NOCOUNT ON
    SELECT MAKHOA, TENKHOA FROM KHOA ORDER BY MAKHOA
END
GO
GRANT EXECUTE ON SP_GETALL_KHOA TO PUBLIC
GO
PRINT N'Đã tạo SP_GETALL_KHOA'
GO

-- ------------------------------------------------------------
-- SP_GETALL_GIANGVIEN: Lấy danh sách giảng viên (dành cho PGV)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GETALL_GIANGVIEN' AND type = 'P')
    DROP PROCEDURE SP_GETALL_GIANGVIEN
GO
CREATE PROCEDURE SP_GETALL_GIANGVIEN
AS
BEGIN
    SET NOCOUNT ON
    SELECT
        GV.MAGV,
        GV.MAKHOA,
        K.TENKHOA,
        RTRIM(GV.HO) + N' ' + RTRIM(GV.TEN) AS HOTEN,
        GV.HOCVI,
        GV.HOCHAM,
        GV.CHUYENMON
    FROM GIANGVIEN GV
    INNER JOIN KHOA K ON GV.MAKHOA = K.MAKHOA
    ORDER BY GV.MAKHOA, GV.MAGV
END
GO
GRANT EXECUTE ON SP_GETALL_GIANGVIEN TO PUBLIC
GO
PRINT N'Đã tạo SP_GETALL_GIANGVIEN'
GO

-- ------------------------------------------------------------
-- SP_GETALL_SINHVIEN: Lấy danh sách sinh viên (dành cho PGV)
--   @MAKHOA = NULL  → lấy tất cả
--   @MAKHOA = 'CNTT' → lọc theo khoa
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GETALL_SINHVIEN' AND type = 'P')
    DROP PROCEDURE SP_GETALL_SINHVIEN
GO
CREATE PROCEDURE SP_GETALL_SINHVIEN
    @MAKHOA NCHAR(10) = NULL
AS
BEGIN
    SET NOCOUNT ON
    SELECT
        SV.MASV,
        RTRIM(SV.HO) + N' ' + RTRIM(SV.TEN) AS HOTEN,
        SV.PHAI,
        SV.DIACHI,
        SV.NGAYSINH,
        L.MALOP,
        L.TENLOP,
        K.MAKHOA,
        K.TENKHOA,
        SV.DANGHIHOC
    FROM SINHVIEN SV
    INNER JOIN LOP  L ON SV.MALOP  = L.MALOP
    INNER JOIN KHOA K ON L.MAKHOA  = K.MAKHOA
    WHERE (@MAKHOA IS NULL OR K.MAKHOA = @MAKHOA)
    ORDER BY K.MAKHOA, L.MALOP, SV.MASV
END
GO
GRANT EXECUTE ON SP_GETALL_SINHVIEN TO PUBLIC
GO
PRINT N'Đã tạo SP_GETALL_SINHVIEN'
GO

-- ------------------------------------------------------------
-- SP_GETALL_LOPTINCHI: Lấy danh sách lớp tín chỉ (PGV + KHOA)
--   Các tham số đều có thể NULL để lấy tất cả
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GETALL_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_GETALL_LOPTINCHI
GO
CREATE PROCEDURE SP_GETALL_LOPTINCHI
    @NIENKHOA NCHAR(9)  = NULL,
    @HOCKY    INT       = NULL,
    @MAKHOA   NCHAR(10) = NULL
AS
BEGIN
    SET NOCOUNT ON
    SELECT
        LTC.MALTC,
        LTC.NIENKHOA,
        LTC.HOCKY,
        LTC.MAMH,
        MH.TENMH,
        LTC.NHOM,
        LTC.MAGV,
        RTRIM(GV.HO) + N' ' + RTRIM(GV.TEN) AS TENGV,
        LTC.MAKHOA,
        K.TENKHOA,
        LTC.SOSVTOITHIEU,
        LTC.HUYLOP,
        COUNT(DK.MASV) AS SOSV_DANGKY
    FROM LOPTINCHI LTC
    INNER JOIN MONHOC    MH  ON LTC.MAMH   = MH.MAMH
    INNER JOIN GIANGVIEN GV  ON LTC.MAGV   = GV.MAGV
    INNER JOIN KHOA      K   ON LTC.MAKHOA = K.MAKHOA
    LEFT  JOIN DANGKY    DK  ON LTC.MALTC  = DK.MALTC AND (DK.HUYDANGKY = 0 OR DK.HUYDANGKY IS NULL)
    WHERE (@NIENKHOA IS NULL OR LTC.NIENKHOA = @NIENKHOA)
      AND (@HOCKY    IS NULL OR LTC.HOCKY    = @HOCKY)
      AND (@MAKHOA   IS NULL OR LTC.MAKHOA   = @MAKHOA)
      AND LTC.HUYLOP = 0
    GROUP BY LTC.MALTC, LTC.NIENKHOA, LTC.HOCKY,
             LTC.MAMH, MH.TENMH, LTC.NHOM,
             LTC.MAGV, GV.HO, GV.TEN,
             LTC.MAKHOA, K.TENKHOA,
             LTC.SOSVTOITHIEU, LTC.HUYLOP
    ORDER BY LTC.NIENKHOA, LTC.HOCKY, LTC.MAMH, LTC.NHOM
END
GO
GRANT EXECUTE ON SP_GETALL_LOPTINCHI TO PUBLIC
GO
PRINT N'Đã tạo SP_GETALL_LOPTINCHI'
GO

-- ------------------------------------------------------------
-- SP_NHAP_DIEM: Cập nhật điểm CC/GK/CK (PGV + KHOA)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_NHAP_DIEM' AND type = 'P')
    DROP PROCEDURE SP_NHAP_DIEM
GO
CREATE PROCEDURE SP_NHAP_DIEM
    @MALTC   INT,
    @MASV    NCHAR(10),
    @DIEM_CC INT   = NULL,
    @DIEM_GK FLOAT = NULL,
    @DIEM_CK FLOAT = NULL
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM DANGKY WHERE MALTC = @MALTC AND MASV = @MASV)
    BEGIN
        SELECT -1 AS KETQUA, N'Sinh viên chưa đăng ký lớp tín chỉ này' AS THONGBAO
        RETURN
    END

    -- [QUA_HAN_SP_2026] Chặn giảng viên nhập điểm cho SV đã quá hạn
    -- Công thức: năm bắt đầu NK của LTC > (năm bắt đầu KHOAHOC + 7)
    DECLARE @KhoaHocNBD_ND INT = NULL
    DECLARE @NamNK_ND INT = NULL

    SELECT @KhoaHocNBD_ND = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    SELECT @NamNK_ND = CAST(LEFT(LTC.NIENKHOA, 4) AS INT)
    FROM LOPTINCHI LTC
    WHERE LTC.MALTC = @MALTC

    IF @KhoaHocNBD_ND IS NOT NULL AND @NamNK_ND IS NOT NULL AND @NamNK_ND > (@KhoaHocNBD_ND + 7)
    BEGIN
        SELECT -20 AS KETQUA, N'Sinh viên đã quá hạn (KHOAHOC + 7 năm), không thể nhập/sửa điểm' AS THONGBAO
        RETURN
    END

    -- [PLANT_NHAPDIEM_Flicker_Cancel_Khoa_2026] Ràng buộc chỉ giảng viên khoa X được nhập điểm cho lớp tín chỉ khoa X
    -- Bỏ qua kiểm tra nếu user là thành viên role PGV
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

    -- [PLANT_NHAPDIEM_FIX_2026] Chặn nếu lớp đã bị hủy
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC AND HUYLOP = 1)
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ đã bị hủy, không thể nhập/sửa điểm' AS THONGBAO
        RETURN
    END

    -- [PLANT_NHAPDIEM_RETAIN_2026] Chặn nếu LTC thuộc NK đã đóng băng (< 2025-2026)
    IF @NamNK_ND IS NOT NULL AND @NamNK_ND < 2025
    BEGIN
        SELECT -10 AS KETQUA,
               N'Lớp tín chỉ thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể nhập/sửa điểm' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Điểm CC: INT, khoảng [0, 10]
    IF @DIEM_CC IS NOT NULL AND (@DIEM_CC < 0 OR @DIEM_CC > 10)
    BEGIN
        SELECT -2 AS KETQUA, N'Điểm chuyên cần phải nằm trong khoảng [0, 10]' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Điểm GK: FLOAT, khoảng [0, 10]
    IF @DIEM_GK IS NOT NULL AND (@DIEM_GK < 0 OR @DIEM_GK > 10)
    BEGIN
        SELECT -3 AS KETQUA, N'Điểm giữa kỳ phải nằm trong khoảng [0, 10]' AS THONGBAO
        RETURN
    END
    -- [VALIDATE_SP_2026] Điểm GK: phải là bội số của 0.5
    IF @DIEM_GK IS NOT NULL AND ABS((@DIEM_GK * 2) - ROUND(@DIEM_GK * 2, 0)) > 0.0001
    BEGIN
        SELECT -4 AS KETQUA, N'Điểm giữa kỳ phải là bội số của 0.5' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Điểm CK: FLOAT, khoảng [0, 10]
    IF @DIEM_CK IS NOT NULL AND (@DIEM_CK < 0 OR @DIEM_CK > 10)
    BEGIN
        SELECT -5 AS KETQUA, N'Điểm cuối kỳ phải nằm trong khoảng [0, 10]' AS THONGBAO
        RETURN
    END
    -- [VALIDATE_SP_2026] Điểm CK: phải là bội số của 0.5
    IF @DIEM_CK IS NOT NULL AND ABS((@DIEM_CK * 2) - ROUND(@DIEM_CK * 2, 0)) > 0.0001
    BEGIN
        SELECT -6 AS KETQUA, N'Điểm cuối kỳ phải là bội số của 0.5' AS THONGBAO
        RETURN
    END

    UPDATE DANGKY
    SET DIEM_CC = @DIEM_CC,
        DIEM_GK = @DIEM_GK,
        DIEM_CK = @DIEM_CK
    WHERE MALTC = @MALTC AND MASV = @MASV
    SELECT 1 AS KETQUA, N'Nhập điểm thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_NHAP_DIEM TO PUBLIC
GO
PRINT N'Đã tạo SP_NHAP_DIEM'
GO

-- ------------------------------------------------------------
-- ------------------------------------------------------------
-- SP_DANGKY_LTC: Sinh viên đăng ký lớp tín chỉ
-- Quy tắc: 1 sinh viên chỉ được đăng ký tối đa 1 lớp cho 1 môn học trong cùng HK/NK
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_DANGKY_LTC' AND type = 'P')
    DROP PROCEDURE SP_DANGKY_LTC
GO
CREATE PROCEDURE SP_DANGKY_LTC
    @MASV  NCHAR(10),
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    
    DECLARE @MAMH NCHAR(10), @NK NVARCHAR(9), @HK INT
    SELECT @MAMH = MAMH, @NK = NIENKHOA, @HK = HOCKY 
    FROM LOPTINCHI WHERE MALTC = @MALTC AND HUYLOP = 0

    -- 1. Kiểm tra lớp có tồn tại và chưa bị hủy
    IF @MAMH IS NULL
    BEGIN
        SELECT -2 AS KETQUA, N'Lớp tín chỉ không tồn tại hoặc đã bị hủy' AS THONGBAO
        RETURN
    END

    -- 2. [QUA_HAN_SP_2026] Chặn SV quá hạn (YEAR(GETDATE()) - năm bắt đầu KHOAHOC > 7)
    DECLARE @KhoaHocNBD INT = NULL
    DECLARE @NamNK INT = NULL
    DECLARE @QuaHan BIT = 0

    SELECT @KhoaHocNBD = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    SET @NamNK = CAST(LEFT(@NK, 4) AS INT)

    IF @KhoaHocNBD IS NOT NULL AND @NamNK > (@KhoaHocNBD + 7)
        SET @QuaHan = 1

    IF @QuaHan = 1
    BEGIN
        SELECT -20 AS KETQUA, N'Bạn đã quá thời hạn đăng ký (vượt quá KHOAHOC + 7 năm). Chỉ có thể xem điểm.' AS THONGBAO
        RETURN
    END

    -- 3. [QUA_HAN_SP_2026] Chặn đăng ký LTC trong quá khứ (NK < NK hiện tại)
    DECLARE @NamHienTai INT = YEAR(GETDATE())
    IF @NamNK < @NamHienTai
    BEGIN
        SELECT -21 AS KETQUA, N'Không thể đăng ký lớp tín chỉ thuộc niên khóa trong quá khứ.' AS THONGBAO
        RETURN
    END

    -- 4. Kiểm tra trùng môn học trong cùng học kỳ/niên khóa
    IF EXISTS (
        SELECT 1 FROM DANGKY DK
        JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC
        WHERE DK.MASV = @MASV 
          AND LTC.MAMH = @MAMH 
          AND LTC.NIENKHOA = @NK 
          AND LTC.HOCKY = @HK
          AND (DK.HUYDANGKY = 0 OR DK.HUYDANGKY IS NULL)
    )
    BEGIN
        SELECT -1 AS KETQUA, N'Bạn đã đăng ký một lớp khác cho môn học này rồi' AS THONGBAO
        RETURN
    END

    -- 3. Thực hiện đăng ký
    -- Nếu đã từng đăng ký nhưng hủy, thì re-active
    IF EXISTS (SELECT 1 FROM DANGKY WHERE MASV = @MASV AND MALTC = @MALTC)
    BEGIN
        UPDATE DANGKY SET HUYDANGKY = 0 WHERE MASV = @MASV AND MALTC = @MALTC
    END
    ELSE
    BEGIN
        INSERT INTO DANGKY (MALTC, MASV, HUYDANGKY) VALUES (@MALTC, @MASV, 0)
    END

    SELECT 1 AS KETQUA, N'Đăng ký thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_DANGKY_LTC TO [sv]
GO
PRINT N'Đã tạo SP_DANGKY_LTC (v3: 1 lớp/môn)'
GO

-- ============================================================
-- SP_HUY_DANGKY: Sinh viên hủy đăng ký lớp tín chỉ
-- ============================================================
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_HUY_DANGKY' AND type = 'P')
    DROP PROCEDURE SP_HUY_DANGKY
GO
CREATE PROCEDURE SP_HUY_DANGKY
    @MASV  NCHAR(10),
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    
    -- [QUA_HAN_SP_2026] Chặn hủy nếu SV đã quá hạn
    DECLARE @KhoaHocNBD INT = NULL
    DECLARE @NamNK INT = NULL
    DECLARE @QuaHan BIT = 0

    SELECT @KhoaHocNBD = CAST(LEFT(L.KHOAHOC, 4) AS INT)
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    SELECT @NamNK = CAST(LEFT(LTC.NIENKHOA, 4) AS INT)
    FROM LOPTINCHI LTC
    WHERE LTC.MALTC = @MALTC

    IF @KhoaHocNBD IS NOT NULL AND @NamNK IS NOT NULL AND @NamNK > (@KhoaHocNBD + 7)
        SET @QuaHan = 1

    IF @QuaHan = 1
    BEGIN
        SELECT -20 AS KETQUA, N'Bạn đã quá thời hạn, không thể hủy đăng ký. Chỉ có thể xem điểm.' AS THONGBAO
        RETURN
    END

    IF NOT EXISTS (SELECT 1 FROM DANGKY WHERE MASV = @MASV AND MALTC = @MALTC AND (HUYDANGKY = 0 OR HUYDANGKY IS NULL))
    BEGIN
        SELECT -1 AS KETQUA, N'Bạn chưa đăng ký lớp này hoặc đã hủy rồi' AS THONGBAO
        RETURN
    END

    -- [PLANT_NHAPDIEM_FIX_2026] Chỉ cho phép hủy nếu lớp chưa được nhập bất kỳ điểm nào cho bất kỳ sinh viên nào
    IF EXISTS (SELECT 1 FROM DANGKY WHERE MALTC = @MALTC AND (DIEM_CC IS NOT NULL OR DIEM_GK IS NOT NULL OR DIEM_CK IS NOT NULL))
    BEGIN
        SELECT -2 AS KETQUA, N'Không thể hủy: Lớp học đã được nhập điểm' AS THONGBAO
        RETURN
    END

    UPDATE DANGKY SET HUYDANGKY = 1 WHERE MASV = @MASV AND MALTC = @MALTC
    SELECT 1 AS KETQUA, N'Hủy đăng ký thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_HUY_DANGKY TO [sv]
GO
PRINT N'Đã tạo SP_HUY_DANGKY'
GO

-- ------------------------------------------------------------
-- SP_XEM_PHIEU_DIEM: Xem phiếu điểm cá nhân (SV)
--   Tính điểm tổng kết: CC*10% + GK*30% + CK*60%
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XEM_PHIEU_DIEM' AND type = 'P')
    DROP PROCEDURE SP_XEM_PHIEU_DIEM
GO
CREATE PROCEDURE SP_XEM_PHIEU_DIEM
    @MASV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    -- [PLANT_LTC_BUGS_2026] Lấy KHOAHOC để giới hạn phạm vi xem điểm
    DECLARE @NamBD INT = NULL
    DECLARE @MAKHOA_SV NCHAR(10) = NULL

    SELECT @NamBD = CAST(LEFT(L.KHOAHOC, 4) AS INT),
           @MAKHOA_SV = L.MAKHOA
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    DECLARE @NamKT INT = ISNULL(@NamBD, 0) + 7

    SELECT
        LTC.NIENKHOA,
        LTC.HOCKY,
        MH.MAMH,
        MH.TENMH,
        LTC.NHOM,
        RTRIM(GV.HO) + N' ' + RTRIM(GV.TEN) AS TENGV,
        DK.DIEM_CC,
        DK.DIEM_GK,
        DK.DIEM_CK,
        CASE
            WHEN DK.DIEM_CC IS NOT NULL
             AND DK.DIEM_GK IS NOT NULL
             AND DK.DIEM_CK IS NOT NULL
            THEN ROUND(DK.DIEM_CC * 0.1 + DK.DIEM_GK * 0.3 + DK.DIEM_CK * 0.6, 1)
            ELSE NULL
        END AS DIEM_TK,
        CASE WHEN (YEAR(GETDATE()) - @NamBD) > 7 THEN 1 ELSE 0 END AS QUAHAN
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
GO
GRANT EXECUTE ON SP_XEM_PHIEU_DIEM TO [sv]
GO
PRINT N'[PLANT_LTC_BUGS_2026] Đã cập nhật SP_XEM_PHIEU_DIEM (giới hạn phạm vi NK)'
GO

-- ------------------------------------------------------------
-- SP_GET_LOPTINCHI_DANGKY: Danh sách lớp TC SV có thể đăng ký
--   Trả về cờ DA_DANGKY = 1 nếu SV đã đăng ký lớp đó rồi
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_LOPTINCHI_DANGKY' AND type = 'P')
    DROP PROCEDURE SP_GET_LOPTINCHI_DANGKY
GO
CREATE PROCEDURE SP_GET_LOPTINCHI_DANGKY
    @MASV     NCHAR(10),
    @NIENKHOA NCHAR(9),
    @HOCKY    INT
AS
BEGIN
    SET NOCOUNT ON

    -- [PLANT_LTC_BUGS_2026] Lấy khóa học + khoa của SV
    DECLARE @NamBD INT = NULL
    DECLARE @MAKHOA_SV NCHAR(10) = NULL

    SELECT @NamBD = CAST(LEFT(L.KHOAHOC, 4) AS INT),
           @MAKHOA_SV = L.MAKHOA
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    -- Sinh viên chỉ thấy LTC trong phạm vi [KHOAHOC, KHOAHOC+7]
    DECLARE @NamKT INT = ISNULL(@NamBD, 0) + 7
    DECLARE @NamNK_LTC INT = CAST(LEFT(@NIENKHOA, 4) AS INT)

    -- Nếu NK được chọn nằm ngoài phạm vi -> trả về rỗng
    IF @NamBD IS NULL OR @NamNK_LTC < @NamBD OR @NamNK_LTC > @NamKT
    BEGIN
        SELECT TOP 0 CAST(NULL AS INT) AS MALTC, CAST(NULL AS NCHAR(10)) AS MAMH,
               CAST(NULL AS NVARCHAR(50)) AS TENMH, CAST(NULL AS INT) AS NHOM,
               CAST(NULL AS NVARCHAR(50)) AS TENGV, CAST(NULL AS NVARCHAR(50)) AS TENKHOA,
               CAST(NULL AS INT) AS SOSVTOITHIEU, CAST(0 AS INT) AS SOSV_DANGKY,
               CAST(0 AS INT) AS DA_DANGKY, CAST(0 AS BIT) AS QUAHAN, CAST(0 AS INT) AS DA_NHAP_DIEM
        RETURN
    END

    SELECT
        LTC.MALTC,
        LTC.MAMH,
        MH.TENMH,
        LTC.NHOM,
        RTRIM(GV.HO) + N' ' + RTRIM(GV.TEN) AS TENGV,
        K.TENKHOA,
        LTC.SOSVTOITHIEU,
        COUNT(DK2.MASV) AS SOSV_DANGKY,
        CASE WHEN DK_SV.MASV IS NOT NULL THEN 1 ELSE 0 END AS DA_DANGKY,
        CASE WHEN (YEAR(GETDATE()) - @NamBD) > 7 THEN 1 ELSE 0 END AS QUAHAN,
        CASE WHEN EXISTS (
            SELECT 1 FROM DANGKY DK3
            WHERE DK3.MALTC = LTC.MALTC
              AND (DK3.DIEM_CC IS NOT NULL OR DK3.DIEM_GK IS NOT NULL OR DK3.DIEM_CK IS NOT NULL)
        ) THEN 1 ELSE 0 END AS DA_NHAP_DIEM
    FROM LOPTINCHI LTC
    INNER JOIN MONHOC    MH   ON LTC.MAMH   = MH.MAMH
    INNER JOIN GIANGVIEN GV   ON LTC.MAGV   = GV.MAGV
    INNER JOIN KHOA      K    ON LTC.MAKHOA = K.MAKHOA
    LEFT  JOIN DANGKY    DK2  ON LTC.MALTC  = DK2.MALTC
                              AND (DK2.HUYDANGKY = 0 OR DK2.HUYDANGKY IS NULL)
    LEFT  JOIN DANGKY    DK_SV ON LTC.MALTC  = DK_SV.MALTC
                               AND DK_SV.MASV = @MASV
                               AND (DK_SV.HUYDANGKY = 0 OR DK_SV.HUYDANGKY IS NULL)
    WHERE LTC.NIENKHOA = @NIENKHOA
      AND LTC.HOCKY    = @HOCKY
      AND LTC.HUYLOP   = 0
      AND LTC.MAKHOA   = @MAKHOA_SV   -- [PLANT_LTC_BUGS_2026] Chỉ thấy LTC thuộc khoa mình
    GROUP BY LTC.MALTC, LTC.MAMH, MH.TENMH, LTC.NHOM,
             GV.HO, GV.TEN, K.TENKHOA,
             LTC.SOSVTOITHIEU, DK_SV.MASV
    ORDER BY MH.TENMH, LTC.NHOM
END
GO
GRANT EXECUTE ON SP_GET_LOPTINCHI_DANGKY TO [sv]
GO
PRINT N'[PLANT_LTC_BUGS_2026] Đã cập nhật SP_GET_LOPTINCHI_DANGKY (filter theo khoa + phạm vi NK)'
GO

-- ------------------------------------------------------------
-- SP_GET_NIENKHOA_CO_LOP: Danh sách niên khóa thực tế có LTC
--   Dùng cho trang đăng ký LTC của sinh viên — chỉ hiển thị
--   các niên khóa mà PGV đã thực sự mở lớp (HUYLOP = 0).
--   Không sinh dữ liệu giả — dựa 100% vào bảng LOPTINCHI.
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_NIENKHOA_CO_LOP' AND type = 'P')
    DROP PROCEDURE SP_GET_NIENKHOA_CO_LOP
GO
CREATE PROCEDURE SP_GET_NIENKHOA_CO_LOP
AS
BEGIN
    SET NOCOUNT ON
    SELECT DISTINCT RTRIM(NIENKHOA) AS NIENKHOA
    FROM LOPTINCHI
    WHERE HUYLOP = 0
    ORDER BY NIENKHOA
END
GO
GRANT EXECUTE ON SP_GET_NIENKHOA_CO_LOP TO [sv]
GO
PRINT N'Đã tạo SP_GET_NIENKHOA_CO_LOP'
GO

-- ------------------------------------------------------------
-- [PLANT_LTC_BUGS_2026] SP_GET_NIENKHOA_SV
-- Trả về danh sách niên khóa mà SV được phép thấy (trong phạm vi
-- [KHOAHOC, KHOAHOC+7]) và thuộc khoa của SV.
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_NIENKHOA_SV' AND type = 'P')
    DROP PROCEDURE SP_GET_NIENKHOA_SV
GO
CREATE PROCEDURE SP_GET_NIENKHOA_SV
    @MASV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    DECLARE @NamBD INT = NULL
    DECLARE @MAKHOA_SV NCHAR(10) = NULL

    SELECT @NamBD = CAST(LEFT(L.KHOAHOC, 4) AS INT),
           @MAKHOA_SV = L.MAKHOA
    FROM SINHVIEN SV
    INNER JOIN LOP L ON SV.MALOP = L.MALOP
    WHERE SV.MASV = @MASV

    IF @NamBD IS NULL
    BEGIN
        SELECT CAST(NULL AS NCHAR(9)) AS NIENKHOA WHERE 1 = 0
        RETURN
    END

    DECLARE @NamKT INT = @NamBD + 7

    SELECT DISTINCT RTRIM(LTC.NIENKHOA) AS NIENKHOA
    FROM LOPTINCHI LTC
    WHERE LTC.HUYLOP = 0
      AND LTC.MAKHOA = @MAKHOA_SV
      AND CAST(LEFT(LTC.NIENKHOA, 4) AS INT) BETWEEN @NamBD AND @NamKT
    ORDER BY NIENKHOA
END
GO
GRANT EXECUTE ON SP_GET_NIENKHOA_SV TO [sv]
GO
PRINT N'[PLANT_LTC_BUGS_2026] Đã tạo SP_GET_NIENKHOA_SV'
GO

-- ------------------------------------------------------------
-- [PLANT_LTC_BUGS_2026] SP_GET_DEFAULT_NK_LTC
-- Trả về niên khóa mới nhất hiện có trong LOPTINCHI (chưa hủy).
-- Dùng để mặc định filter trang Mở Lớp Tín Chỉ.
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_DEFAULT_NK_LTC' AND type = 'P')
    DROP PROCEDURE SP_GET_DEFAULT_NK_LTC
GO
CREATE PROCEDURE SP_GET_DEFAULT_NK_LTC
AS
BEGIN
    SET NOCOUNT ON
    SELECT TOP 1 RTRIM(NIENKHOA) AS NIENKHOA
    FROM LOPTINCHI
    WHERE HUYLOP = 0
    ORDER BY NIENKHOA DESC
END
GO
GRANT EXECUTE ON SP_GET_DEFAULT_NK_LTC TO PUBLIC
GO
PRINT N'[PLANT_LTC_BUGS_2026] Đã tạo SP_GET_DEFAULT_NK_LTC'
GO

PRINT N'=== TOÀN BỘ SP BỔ SUNG ĐÃ ĐƯỢC TẠO ==='
GO

-- ============================================================
-- SP NHẬP LIỆU (3.2) — THÊM MỚI
-- ============================================================

-- ------------------------------------------------------------
-- SP_GET_ALL_MONHOC: Lấy danh sách tất cả môn học
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_ALL_MONHOC' AND type = 'P')
    DROP PROCEDURE SP_GET_ALL_MONHOC
GO
CREATE PROCEDURE SP_GET_ALL_MONHOC
AS
BEGIN
    SET NOCOUNT ON
    SELECT MAMH, TENMH, SOTIET_LT, SOTIET_TH
    FROM MONHOC
    ORDER BY MAMH
END
GO
GRANT EXECUTE ON SP_GET_ALL_MONHOC TO PUBLIC
GO
PRINT N'Đã tạo SP_GET_ALL_MONHOC'
GO

-- ------------------------------------------------------------
-- SP_THEM_MONHOC: Thêm môn học mới
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_THEM_MONHOC' AND type = 'P')
    DROP PROCEDURE SP_THEM_MONHOC
GO
CREATE PROCEDURE SP_THEM_MONHOC
    @MAMH       NCHAR(10),
    @TENMH      NVARCHAR(50),
    @SOTIET_LT  INT,
    @SOTIET_TH  INT
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM MONHOC WHERE MAMH = @MAMH)
    BEGIN
        SELECT -1 AS KETQUA, N'Mã môn học đã tồn tại' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] SOTIET_LT phải >= 30 (chuẩn PTIT)
    IF @SOTIET_LT < 30
    BEGIN
        SELECT -2 AS KETQUA, N'Số tiết lý thuyết phải >= 30 (chuẩn PTIT)' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] SOTIET_TH phải >= 0
    IF @SOTIET_TH < 0
    BEGIN
        SELECT -3 AS KETQUA, N'Số tiết thực hành phải >= 0' AS THONGBAO
        RETURN
    END

    INSERT INTO MONHOC (MAMH, TENMH, SOTIET_LT, SOTIET_TH)
    VALUES (@MAMH, @TENMH, @SOTIET_LT, @SOTIET_TH)
    SELECT 1 AS KETQUA, N'Thêm môn học thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_THEM_MONHOC TO PUBLIC
GO
PRINT N'Đã tạo SP_THEM_MONHOC'
GO

-- ------------------------------------------------------------
-- SP_SUA_MONHOC: Cập nhật môn học
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_SUA_MONHOC' AND type = 'P')
    DROP PROCEDURE SP_SUA_MONHOC
GO
CREATE PROCEDURE SP_SUA_MONHOC
    @MAMH       NCHAR(10),
    @TENMH      NVARCHAR(50),
    @SOTIET_LT  INT,
    @SOTIET_TH  INT
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM MONHOC WHERE MAMH = @MAMH)
    BEGIN
        SELECT -1 AS KETQUA, N'Môn học không tồn tại' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] SOTIET_LT phải >= 30 (chuẩn PTIT)
    IF @SOTIET_LT < 30
    BEGIN
        SELECT -2 AS KETQUA, N'Số tiết lý thuyết phải >= 30 (chuẩn PTIT)' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] SOTIET_TH phải >= 0
    IF @SOTIET_TH < 0
    BEGIN
        SELECT -3 AS KETQUA, N'Số tiết thực hành phải >= 0' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Nếu môn đã được dùng để mở lớp trong quá khứ → đóng băng không cho sửa
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MAMH = @MAMH AND NIENKHOA < '2025-2026')
    BEGIN
        SELECT -10 AS KETQUA, N'Môn học đã được dạy trong niên khóa < 2025-2026, không thể sửa' AS THONGBAO
        RETURN
    END

    UPDATE MONHOC
    SET TENMH = @TENMH, SOTIET_LT = @SOTIET_LT, SOTIET_TH = @SOTIET_TH
    WHERE MAMH = @MAMH
    SELECT 1 AS KETQUA, N'Cập nhật môn học thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_SUA_MONHOC TO PUBLIC
GO
PRINT N'Đã tạo SP_SUA_MONHOC'
GO

-- ------------------------------------------------------------
-- SP_XOA_MONHOC: Xóa môn học (kiểm tra còn LTC không)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XOA_MONHOC' AND type = 'P')
    DROP PROCEDURE SP_XOA_MONHOC
GO
CREATE PROCEDURE SP_XOA_MONHOC
    @MAMH NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MAMH = @MAMH)
    BEGIN
        SELECT -1 AS KETQUA, N'Không thể xóa: môn học đang có lớp tín chỉ' AS THONGBAO
        RETURN
    END
    DELETE FROM MONHOC WHERE MAMH = @MAMH
    SELECT 1 AS KETQUA, N'Xóa môn học thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_XOA_MONHOC TO PUBLIC
GO
PRINT N'Đã tạo SP_XOA_MONHOC'
GO

-- ------------------------------------------------------------
-- SP_GET_DSLOP: Danh sách lớp (lọc theo khoa)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_DSLOP' AND type = 'P')
    DROP PROCEDURE SP_GET_DSLOP
GO
CREATE PROCEDURE SP_GET_DSLOP
    @MAKHOA NCHAR(10) = NULL
AS
BEGIN
    SET NOCOUNT ON
    SELECT L.MALOP, L.TENLOP, L.KHOAHOC, L.MAKHOA, K.TENKHOA
    FROM LOP L
    INNER JOIN KHOA K ON L.MAKHOA = K.MAKHOA
    WHERE (@MAKHOA IS NULL OR L.MAKHOA = @MAKHOA)
    ORDER BY L.MAKHOA, L.MALOP
END
GO
GRANT EXECUTE ON SP_GET_DSLOP TO PUBLIC
GO
PRINT N'Đã tạo SP_GET_DSLOP'
GO

-- ------------------------------------------------------------
-- SP_THEM_LOP: Thêm lớp mới
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_THEM_LOP' AND type = 'P')
    DROP PROCEDURE SP_THEM_LOP
GO
CREATE PROCEDURE SP_THEM_LOP
    @MALOP    NCHAR(10),
    @TENLOP   NVARCHAR(50),
    @KHOAHOC  NCHAR(9),
    @MAKHOA   NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM LOP WHERE MALOP = @MALOP)
    BEGIN
        SELECT -1 AS KETQUA, N'Mã lớp đã tồn tại' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM KHOA WHERE MAKHOA = @MAKHOA)
    BEGIN
        SELECT -2 AS KETQUA, N'Khoa không tồn tại' AS THONGBAO
        RETURN
    END
    INSERT INTO LOP (MALOP, TENLOP, KHOAHOC, MAKHOA)
    VALUES (@MALOP, @TENLOP, @KHOAHOC, @MAKHOA)
    SELECT 1 AS KETQUA, N'Thêm lớp thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_THEM_LOP TO PUBLIC
GO
PRINT N'Đã tạo SP_THEM_LOP'
GO

-- ------------------------------------------------------------
-- SP_SUA_LOP: Cập nhật lớp
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_SUA_LOP' AND type = 'P')
    DROP PROCEDURE SP_SUA_LOP
GO
CREATE PROCEDURE SP_SUA_LOP
    @MALOP    NCHAR(10),
    @TENLOP   NVARCHAR(50),
    @KHOAHOC  NCHAR(9),
    @MAKHOA   NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM LOP WHERE MALOP = @MALOP)
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp không tồn tại' AS THONGBAO
        RETURN
    END
    UPDATE LOP
    SET TENLOP = @TENLOP, KHOAHOC = @KHOAHOC, MAKHOA = @MAKHOA
    WHERE MALOP = @MALOP
    SELECT 1 AS KETQUA, N'Cập nhật lớp thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_SUA_LOP TO PUBLIC
GO
PRINT N'Đã tạo SP_SUA_LOP'
GO

-- ------------------------------------------------------------
-- SP_XOA_LOP: Xóa lớp (kiểm tra còn SV không)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XOA_LOP' AND type = 'P')
    DROP PROCEDURE SP_XOA_LOP
GO
CREATE PROCEDURE SP_XOA_LOP
    @MALOP NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM SINHVIEN WHERE MALOP = @MALOP)
    BEGIN
        SELECT -1 AS KETQUA, N'Không thể xóa: lớp còn sinh viên' AS THONGBAO
        RETURN
    END
    DELETE FROM LOP WHERE MALOP = @MALOP
    SELECT 1 AS KETQUA, N'Xóa lớp thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_XOA_LOP TO PUBLIC
GO
PRINT N'Đã tạo SP_XOA_LOP'
GO

-- ------------------------------------------------------------
-- SP_GET_DSSV: Danh sách sinh viên theo lớp
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_DSSV' AND type = 'P')
    DROP PROCEDURE SP_GET_DSSV
GO
CREATE PROCEDURE SP_GET_DSSV
    @MALOP NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    SELECT SV.MASV,
           RTRIM(SV.HO) + N' ' + RTRIM(SV.TEN) AS HOTEN,
           SV.HO, SV.TEN, SV.PHAI,
           SV.DIACHI, SV.NGAYSINH,
           SV.MALOP, SV.DANGHIHOC
    FROM SINHVIEN SV
    WHERE SV.MALOP = @MALOP
    ORDER BY SV.MASV
END
GO
GRANT EXECUTE ON SP_GET_DSSV TO PUBLIC
GO
PRINT N'Đã tạo SP_GET_DSSV'
GO

-- ------------------------------------------------------------
-- SP_GET_THONGTIN_SV: Lấy thông tin 1 sinh viên theo MASV
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_THONGTIN_SV' AND type = 'P')
    DROP PROCEDURE SP_GET_THONGTIN_SV
GO
CREATE PROCEDURE SP_GET_THONGTIN_SV
    @MASV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    SELECT SV.MASV,
           RTRIM(SV.HO) + N' ' + RTRIM(SV.TEN) AS HOTEN,
           SV.MALOP,
           L.TENLOP,
           K.MAKHOA,
           K.TENKHOA
    FROM SINHVIEN SV
    INNER JOIN LOP  L ON SV.MALOP  = L.MALOP
    INNER JOIN KHOA K ON L.MAKHOA  = K.MAKHOA
    WHERE SV.MASV = @MASV AND SV.DANGHIHOC = 0
END
GO
GRANT EXECUTE ON SP_GET_THONGTIN_SV TO [sv]
GO
PRINT N'Đã tạo SP_GET_THONGTIN_SV'
GO

-- ------------------------------------------------------------
-- SP_THEM_SV: Thêm sinh viên mới
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_THEM_SV' AND type = 'P')
    DROP PROCEDURE SP_THEM_SV
GO
CREATE PROCEDURE SP_THEM_SV
    @MASV      NCHAR(10),
    @HO        NVARCHAR(50),
    @TEN       NVARCHAR(10),
    @PHAI      BIT,
    @DIACHI    NVARCHAR(100),
    @NGAYSINH  DATE,
    @MALOP     NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM SINHVIEN WHERE MASV = @MASV)
    BEGIN
        SELECT -1 AS KETQUA, N'Mã sinh viên đã tồn tại' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM LOP WHERE MALOP = @MALOP)
    BEGIN
        SELECT -2 AS KETQUA, N'Lớp không tồn tại' AS THONGBAO
        RETURN
    END
    INSERT INTO SINHVIEN (MASV, HO, TEN, PHAI, DIACHI, NGAYSINH, MALOP, DANGHIHOC)
    VALUES (@MASV, @HO, @TEN, @PHAI, @DIACHI, @NGAYSINH, @MALOP, 0)
    SELECT 1 AS KETQUA, N'Thêm sinh viên thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_THEM_SV TO PUBLIC
GO
PRINT N'Đã tạo SP_THEM_SV'
GO

-- ------------------------------------------------------------
-- SP_SUA_SV: Cập nhật thông tin sinh viên
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_SUA_SV' AND type = 'P')
    DROP PROCEDURE SP_SUA_SV
GO
CREATE PROCEDURE SP_SUA_SV
    @MASV      NCHAR(10),
    @HO        NVARCHAR(50),
    @TEN       NVARCHAR(10),
    @PHAI      BIT,
    @DIACHI    NVARCHAR(100),
    @NGAYSINH  DATE,
    @MALOP     NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM SINHVIEN WHERE MASV = @MASV)
    BEGIN
        SELECT -1 AS KETQUA, N'Sinh viên không tồn tại' AS THONGBAO
        RETURN
    END
    UPDATE SINHVIEN
    SET HO = @HO, TEN = @TEN, PHAI = @PHAI,
        DIACHI = @DIACHI, NGAYSINH = @NGAYSINH, MALOP = @MALOP
    WHERE MASV = @MASV
    SELECT 1 AS KETQUA, N'Cập nhật sinh viên thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_SUA_SV TO PUBLIC
GO
PRINT N'Đã tạo SP_SUA_SV'
GO

-- ------------------------------------------------------------
-- SP_XOA_SV: Xóa sinh viên (kiểm tra đã đăng ký LTC chưa)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XOA_SV' AND type = 'P')
    DROP PROCEDURE SP_XOA_SV
GO
CREATE PROCEDURE SP_XOA_SV
    @MASV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM DANGKY WHERE MASV = @MASV)
    BEGIN
        SELECT -1 AS KETQUA, N'Không thể xóa: sinh viên đã có đăng ký lớp tín chỉ' AS THONGBAO
        RETURN
    END
    DELETE FROM SINHVIEN WHERE MASV = @MASV
    SELECT 1 AS KETQUA, N'Xóa sinh viên thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_XOA_SV TO PUBLIC
GO
PRINT N'Đã tạo SP_XOA_SV'
GO

-- ------------------------------------------------------------
-- SP_THEM_LOPTINCHI: Mở lớp tín chỉ mới
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_THEM_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_THEM_LOPTINCHI
GO
CREATE PROCEDURE SP_THEM_LOPTINCHI
    @NIENKHOA     NCHAR(9),
    @HOCKY        INT,
    @MAMH         NCHAR(10),
    @NHOM         INT,
    @MAGV         NCHAR(10),
    @MAKHOA       NCHAR(10),
    @SOSVTOITHIEU INT
AS
BEGIN
    SET NOCOUNT ON

    -- [VALIDATE_SP_2026] Niên khóa đóng băng: chỉ cho phép NK >= 2025-2026
    IF @NIENKHOA < '2025-2026'
    BEGIN
        SELECT -10 AS KETQUA, N'Niên khóa < 2025-2026 đã bị đóng băng, không thể thêm lớp tín chỉ' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] HOCKY phải nằm trong [1, 3]
    IF @HOCKY < 1 OR @HOCKY > 3
    BEGIN
        SELECT -3 AS KETQUA, N'Học kỳ phải nằm trong khoảng [1, 3]' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] NHOM phải >= 1
    IF @NHOM < 1
    BEGIN
        SELECT -4 AS KETQUA, N'Nhóm phải >= 1' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] SOSVTOITHIEU phải > 0
    IF @SOSVTOITHIEU <= 0
    BEGIN
        SELECT -5 AS KETQUA, N'Số SV tối thiểu phải > 0' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Kiểm tra FK tồn tại (báo lỗi thân thiện thay vì để DB ném exception)
    IF NOT EXISTS (SELECT 1 FROM MONHOC    WHERE MAMH  = @MAMH)
    BEGIN
        SELECT -6 AS KETQUA, N'Mã môn học không tồn tại' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM GIANGVIEN WHERE MAGV  = @MAGV)
    BEGIN
        SELECT -7 AS KETQUA, N'Mã giảng viên không tồn tại' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM KHOA      WHERE MAKHOA = @MAKHOA)
    BEGIN
        SELECT -8 AS KETQUA, N'Mã khoa không tồn tại' AS THONGBAO
        RETURN
    END

    IF EXISTS (
        SELECT 1 FROM LOPTINCHI
        WHERE NIENKHOA = @NIENKHOA AND HOCKY = @HOCKY
          AND MAMH = @MAMH AND NHOM = @NHOM AND (HUYLOP = 0 OR HUYLOP IS NULL)
    )
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ đã tồn tại (cùng niên khóa, học kỳ, môn, nhóm)' AS THONGBAO
        RETURN
    END

    IF EXISTS (
        SELECT 1 FROM LOPTINCHI
        WHERE NIENKHOA = @NIENKHOA AND HOCKY = @HOCKY
          AND MAMH = @MAMH AND NHOM = @NHOM AND HUYLOP = 1
    )
    BEGIN
        UPDATE LOPTINCHI
        SET HUYLOP = 0, MAGV = @MAGV, MAKHOA = @MAKHOA, SOSVTOITHIEU = @SOSVTOITHIEU
        WHERE NIENKHOA = @NIENKHOA AND HOCKY = @HOCKY
          AND MAMH = @MAMH AND NHOM = @NHOM
        
        -- Get the ID to return it
        DECLARE @UpdatedID INT
        SELECT @UpdatedID = MALTC FROM LOPTINCHI 
        WHERE NIENKHOA = @NIENKHOA AND HOCKY = @HOCKY AND MAMH = @MAMH AND NHOM = @NHOM
        
        SELECT @UpdatedID AS KETQUA, N'Mở lại lớp tín chỉ đã hủy thành công' AS THONGBAO
        RETURN
    END

    INSERT INTO LOPTINCHI (NIENKHOA, HOCKY, MAMH, NHOM, MAGV, MAKHOA, SOSVTOITHIEU, HUYLOP)
    VALUES (@NIENKHOA, @HOCKY, @MAMH, @NHOM, @MAGV, @MAKHOA, @SOSVTOITHIEU, 0)
    SELECT 1 AS KETQUA, N'Mở lớp tín chỉ thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_THEM_LOPTINCHI TO PUBLIC
GO
PRINT N'Đã tạo SP_THEM_LOPTINCHI'
GO

-- ------------------------------------------------------------
-- SP_SUA_LOPTINCHI: Cập nhật lớp tín chỉ
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_SUA_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_SUA_LOPTINCHI
GO
CREATE PROCEDURE SP_SUA_LOPTINCHI
    @MALTC        INT,
    @NIENKHOA     NCHAR(9),
    @HOCKY        INT,
    @MAMH         NCHAR(10),
    @NHOM         INT,
    @MAGV         NCHAR(10),
    @MAKHOA       NCHAR(10),
    @SOSVTOITHIEU INT
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC)
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ không tồn tại' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Chặn nếu lớp đang sửa thuộc niên khóa đã đóng băng
    -- So sánh với NK CŨ của lớp (không dùng @NIENKHOA mới truyền vào để tránh né)
    DECLARE @OldNK NCHAR(9)
    SELECT @OldNK = NIENKHOA FROM LOPTINCHI WHERE MALTC = @MALTC
    IF @OldNK < '2025-2026'
    BEGIN
        SELECT -10 AS KETQUA, N'Lớp thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể sửa' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Validate các field giống SP_THEM_LOPTINCHI
    IF @HOCKY < 1 OR @HOCKY > 3
    BEGIN
        SELECT -3 AS KETQUA, N'Học kỳ phải nằm trong khoảng [1, 3]' AS THONGBAO
        RETURN
    END
    IF @NHOM < 1
    BEGIN
        SELECT -4 AS KETQUA, N'Nhóm phải >= 1' AS THONGBAO
        RETURN
    END
    IF @SOSVTOITHIEU <= 0
    BEGIN
        SELECT -5 AS KETQUA, N'Số SV tối thiểu phải > 0' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM MONHOC    WHERE MAMH  = @MAMH)
    BEGIN
        SELECT -6 AS KETQUA, N'Mã môn học không tồn tại' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM GIANGVIEN WHERE MAGV  = @MAGV)
    BEGIN
        SELECT -7 AS KETQUA, N'Mã giảng viên không tồn tại' AS THONGBAO
        RETURN
    END
    IF NOT EXISTS (SELECT 1 FROM KHOA      WHERE MAKHOA = @MAKHOA)
    BEGIN
        SELECT -8 AS KETQUA, N'Mã khoa không tồn tại' AS THONGBAO
        RETURN
    END

    UPDATE LOPTINCHI
    SET NIENKHOA = @NIENKHOA, HOCKY = @HOCKY,
        MAMH = @MAMH, NHOM = @NHOM,
        MAGV = @MAGV, MAKHOA = @MAKHOA,
        SOSVTOITHIEU = @SOSVTOITHIEU
    WHERE MALTC = @MALTC
    SELECT 1 AS KETQUA, N'Cập nhật lớp tín chỉ thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_SUA_LOPTINCHI TO PUBLIC
GO
PRINT N'Đã tạo SP_SUA_LOPTINCHI'
GO

-- ------------------------------------------------------------
-- SP_XOA_LOPTINCHI: Hủy lớp tín chỉ (set HUYLOP = 1)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XOA_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_XOA_LOPTINCHI
GO
CREATE PROCEDURE SP_XOA_LOPTINCHI
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC)
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ không tồn tại' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Chặn xóa lớp thuộc niên khóa đã đóng băng
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC AND NIENKHOA < '2025-2026')
    BEGIN
        SELECT -10 AS KETQUA, N'Lớp thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể xóa' AS THONGBAO
        RETURN
    END

    UPDATE LOPTINCHI SET HUYLOP = 1 WHERE MALTC = @MALTC
    SELECT 1 AS KETQUA, N'Hủy lớp tín chỉ thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_XOA_LOPTINCHI TO PUBLIC
GO
PRINT N'Đã tạo SP_XOA_LOPTINCHI'
GO

-- ------------------------------------------------------------
-- SP_PHUCHOI_LOPTINCHI: Phục hồi lớp tín chỉ đã hủy (HUYLOP = 0)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_PHUCHOI_LOPTINCHI' AND type = 'P')
    DROP PROCEDURE SP_PHUCHOI_LOPTINCHI
GO
CREATE PROCEDURE SP_PHUCHOI_LOPTINCHI
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC)
    BEGIN
        SELECT -1 AS KETQUA, N'Lớp tín chỉ không tồn tại' AS THONGBAO
        RETURN
    END

    -- [VALIDATE_SP_2026] Chặn phục hồi lớp thuộc niên khóa đã đóng băng
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MALTC = @MALTC AND NIENKHOA < '2025-2026')
    BEGIN
        SELECT -10 AS KETQUA, N'Lớp thuộc niên khóa < 2025-2026 đã bị đóng băng, không thể phục hồi' AS THONGBAO
        RETURN
    END

    UPDATE LOPTINCHI SET HUYLOP = 0 WHERE MALTC = @MALTC
    SELECT 1 AS KETQUA, N'Phục hồi lớp tín chỉ thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_PHUCHOI_LOPTINCHI TO PUBLIC
GO
PRINT N'Đã tạo SP_PHUCHOI_LOPTINCHI'
GO

-- ------------------------------------------------------------
-- SP_GET_SINHVIEN_THEO_LTC: DS sinh viên + điểm của 1 lớp TC
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_SINHVIEN_THEO_LTC' AND type = 'P')
    DROP PROCEDURE SP_GET_SINHVIEN_THEO_LTC
GO
CREATE PROCEDURE SP_GET_SINHVIEN_THEO_LTC
    @MALTC INT
AS
BEGIN
    SET NOCOUNT ON
    SELECT
        DK.MASV,
        RTRIM(SV.HO) + N' ' + RTRIM(SV.TEN) AS HOTEN,
        DK.DIEM_CC,
        DK.DIEM_GK,
        DK.DIEM_CK,
        CASE
            WHEN DK.DIEM_CC IS NOT NULL
             AND DK.DIEM_GK IS NOT NULL
             AND DK.DIEM_CK IS NOT NULL
            THEN ROUND(DK.DIEM_CC * 0.1 + DK.DIEM_GK * 0.3 + DK.DIEM_CK * 0.6, 1)
            ELSE NULL
        END AS DIEM_HM
    FROM DANGKY DK
    INNER JOIN SINHVIEN SV ON DK.MASV = SV.MASV
    INNER JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC
    WHERE DK.MALTC = @MALTC
      AND (DK.HUYDANGKY = 0 OR DK.HUYDANGKY IS NULL)
      AND (LTC.HUYLOP = 0 OR LTC.HUYLOP IS NULL)
    ORDER BY DK.MASV
END
GO
GRANT EXECUTE ON SP_GET_SINHVIEN_THEO_LTC TO PUBLIC
GO
PRINT N'Đã tạo SP_GET_SINHVIEN_THEO_LTC'
GO

PRINT N'=== TOÀN BỘ SP NHẬP LIỆU ĐÃ ĐƯỢC TẠO ==='
GO

-- ------------------------------------------------------------
-- SP_GET_ALL_NIENKHOA: Danh sách niên khóa đang có trong LTC
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_GET_ALL_NIENKHOA' AND type = 'P')
    DROP PROCEDURE SP_GET_ALL_NIENKHOA
GO
CREATE PROCEDURE SP_GET_ALL_NIENKHOA
AS
BEGIN
    SET NOCOUNT ON
    SELECT DISTINCT NIENKHOA FROM LOPTINCHI ORDER BY NIENKHOA
END
GO
GRANT EXECUTE ON SP_GET_ALL_NIENKHOA TO PUBLIC
GO
PRINT N'Đã tạo SP_GET_ALL_NIENKHOA'
GO

-- ============================================================
-- CRUD KHOA
-- ============================================================

IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_THEM_KHOA' AND type = 'P') DROP PROCEDURE SP_THEM_KHOA
GO
CREATE PROCEDURE SP_THEM_KHOA
    @MAKHOA NCHAR(10),
    @TENKHOA NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM KHOA WHERE MAKHOA = @MAKHOA)
    BEGIN SELECT -1 AS KETQUA, N'Mã khoa đã tồn tại' AS THONGBAO RETURN END
    INSERT INTO KHOA (MAKHOA, TENKHOA) VALUES (@MAKHOA, @TENKHOA)
    SELECT 1 AS KETQUA, N'Thêm khoa thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_THEM_KHOA TO PUBLIC
GO

IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_SUA_KHOA' AND type = 'P') DROP PROCEDURE SP_SUA_KHOA
GO
CREATE PROCEDURE SP_SUA_KHOA
    @MAKHOA NCHAR(10),
    @TENKHOA NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM KHOA WHERE MAKHOA = @MAKHOA)
    BEGIN SELECT -1 AS KETQUA, N'Khoa không tồn tại' AS THONGBAO RETURN END
    UPDATE KHOA SET TENKHOA = @TENKHOA WHERE MAKHOA = @MAKHOA
    SELECT 1 AS KETQUA, N'Cập nhật khoa thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_SUA_KHOA TO PUBLIC
GO

IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XOA_KHOA' AND type = 'P') DROP PROCEDURE SP_XOA_KHOA
GO
CREATE PROCEDURE SP_XOA_KHOA
    @MAKHOA NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM KHOA WHERE MAKHOA = @MAKHOA)
    BEGIN SELECT -1 AS KETQUA, N'Khoa không tồn tại' AS THONGBAO RETURN END
    IF EXISTS (SELECT 1 FROM LOP WHERE MAKHOA = @MAKHOA)
    BEGIN SELECT -1 AS KETQUA, N'Không thể xóa: khoa còn lớp học' AS THONGBAO RETURN END
    IF EXISTS (SELECT 1 FROM GIANGVIEN WHERE MAKHOA = @MAKHOA)
    BEGIN SELECT -1 AS KETQUA, N'Không thể xóa: khoa còn giảng viên' AS THONGBAO RETURN END
    DELETE FROM KHOA WHERE MAKHOA = @MAKHOA
    SELECT 1 AS KETQUA, N'Xóa khoa thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_XOA_KHOA TO PUBLIC
GO
PRINT N'Đã tạo SP CRUD KHOA'
GO

-- ============================================================
-- CRUD GIANGVIEN
-- ============================================================

IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_THEM_GIANGVIEN' AND type = 'P') DROP PROCEDURE SP_THEM_GIANGVIEN
GO
CREATE PROCEDURE SP_THEM_GIANGVIEN
    @MAGV      NCHAR(10),
    @MAKHOA    NCHAR(10),
    @HO        NVARCHAR(50),
    @TEN       NVARCHAR(10),
    @HOCVI     NVARCHAR(20),
    @HOCHAM    NVARCHAR(20),
    @CHUYENMON NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (SELECT 1 FROM GIANGVIEN WHERE MAGV = @MAGV)
    BEGIN SELECT -1 AS KETQUA, N'Mã giảng viên đã tồn tại' AS THONGBAO RETURN END
    IF NOT EXISTS (SELECT 1 FROM KHOA WHERE MAKHOA = @MAKHOA)
    BEGIN SELECT -1 AS KETQUA, N'Khoa không tồn tại' AS THONGBAO RETURN END
    INSERT INTO GIANGVIEN (MAGV, MAKHOA, HO, TEN, HOCVI, HOCHAM, CHUYENMON)
    VALUES (@MAGV, @MAKHOA, @HO, @TEN, @HOCVI, @HOCHAM, @CHUYENMON)
    SELECT 1 AS KETQUA, N'Thêm giảng viên thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_THEM_GIANGVIEN TO PUBLIC
GO

IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_SUA_GIANGVIEN' AND type = 'P') DROP PROCEDURE SP_SUA_GIANGVIEN
GO
CREATE PROCEDURE SP_SUA_GIANGVIEN
    @MAGV      NCHAR(10),
    @MAKHOA    NCHAR(10),
    @HO        NVARCHAR(50),
    @TEN       NVARCHAR(10),
    @HOCVI     NVARCHAR(20),
    @HOCHAM    NVARCHAR(20),
    @CHUYENMON NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM GIANGVIEN WHERE MAGV = @MAGV)
    BEGIN SELECT -1 AS KETQUA, N'Giảng viên không tồn tại' AS THONGBAO RETURN END
    UPDATE GIANGVIEN
    SET MAKHOA=@MAKHOA, HO=@HO, TEN=@TEN, HOCVI=@HOCVI, HOCHAM=@HOCHAM, CHUYENMON=@CHUYENMON
    WHERE MAGV = @MAGV
    SELECT 1 AS KETQUA, N'Cập nhật giảng viên thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_SUA_GIANGVIEN TO PUBLIC
GO

IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XOA_GIANGVIEN' AND type = 'P') DROP PROCEDURE SP_XOA_GIANGVIEN
GO
CREATE PROCEDURE SP_XOA_GIANGVIEN
    @MAGV NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF NOT EXISTS (SELECT 1 FROM GIANGVIEN WHERE MAGV = @MAGV)
    BEGIN SELECT -1 AS KETQUA, N'Giảng viên không tồn tại' AS THONGBAO RETURN END
    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MAGV = @MAGV)
    BEGIN SELECT -1 AS KETQUA, N'Không thể xóa: giảng viên đang dạy lớp tín chỉ' AS THONGBAO RETURN END
    DELETE FROM GIANGVIEN WHERE MAGV = @MAGV
    SELECT 1 AS KETQUA, N'Xóa giảng viên thành công' AS THONGBAO
END
GO
GRANT EXECUTE ON SP_XOA_GIANGVIEN TO PUBLIC
GO
PRINT N'Đã tạo SP CRUD GIANGVIEN'
GO
-- ------------------------------------------------------------
-- SP_CHECK_MONHOC_HISTORY: Kiểm tra môn học có lịch sử dạy chưa
-- Trả về 1 nếu đã từng dạy trong quá khứ (Niên khóa < 2025-2026)
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_CHECK_MONHOC_HISTORY' AND type = 'P')
    DROP PROCEDURE SP_CHECK_MONHOC_HISTORY
GO
CREATE PROCEDURE SP_CHECK_MONHOC_HISTORY
    @MAMH NCHAR(10)
AS
BEGIN
    SET NOCOUNT ON
    IF EXISTS (
        SELECT 1 FROM LOPTINCHI 
        WHERE MAMH = @MAMH 
          AND NIENKHOA < '2025-2026'
    )
    BEGIN
        SELECT 1 AS DUOC_DAY_QUAKHU
    END
    ELSE
    BEGIN
        SELECT 0 AS DUOC_DAY_QUAKHU
    END
END
GO
GRANT EXECUTE ON SP_CHECK_MONHOC_HISTORY TO PUBLIC
GO
PRINT N'Đã tạo SP_CHECK_MONHOC_HISTORY'
GO

-- ------------------------------------------------------------
-- SP_TAOTAIKHOAN: Tạo login, user và gán quyền cho PGV/KHOA
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_TAOTAIKHOAN' AND type = 'P')
    DROP PROCEDURE SP_TAOTAIKHOAN
GO
CREATE PROCEDURE SP_TAOTAIKHOAN
    @LGNAME VARCHAR(50),
    @PASS VARCHAR(50),
    @USRNAME VARCHAR(50),
    @ROLE VARCHAR(50)
WITH EXECUTE AS OWNER
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ORIG_LOGIN NVARCHAR(128) = ORIGINAL_LOGIN();
    DECLARE @CALLER_MAGV NVARCHAR(10) = RTRIM(@ORIG_LOGIN);
    
    DECLARE @IS_PGV BIT = 0;
    DECLARE @IS_KHOA BIT = 0;
    
    IF EXISTS (
        SELECT 1 FROM sys.database_role_members RM 
        JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id 
        JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id 
        WHERE R.name = 'PGV' AND U.name = @CALLER_MAGV
    )
        SET @IS_PGV = 1;
        
    IF EXISTS (
        SELECT 1 FROM sys.database_role_members RM 
        JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id 
        JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id 
        WHERE R.name = 'KHOA' AND U.name = @CALLER_MAGV
    )
        SET @IS_KHOA = 1;
        
    IF IS_SRVROLEMEMBER('sysadmin', @ORIG_LOGIN) = 1
        SET @IS_PGV = 1;
        
    IF @IS_PGV = 0 AND @IS_KHOA = 0
    BEGIN
        RAISERROR(N'Bạn không có quyền thực hiện chức năng này!', 16, 1);
        RETURN 3;
    END

    -- Nếu là KHOA, chỉ được tạo tài khoản cho KHOA và giảng viên thuộc cùng khoa
    IF @IS_KHOA = 1
    BEGIN
        IF @ROLE <> 'KHOA'
        BEGIN
            RAISERROR(N'Tài khoản thuộc Khoa chỉ được phép tạo tài khoản cho nhóm quyền KHOA!', 16, 1);
            RETURN 4;
        END
        
        DECLARE @CALLER_KHOA NCHAR(10);
        DECLARE @TARGET_KHOA NCHAR(10);
        
        SELECT @CALLER_KHOA = MAKHOA FROM GIANGVIEN WHERE MAGV = @CALLER_MAGV;
        SELECT @TARGET_KHOA = MAKHOA FROM GIANGVIEN WHERE MAGV = @USRNAME;
        
        IF @CALLER_KHOA IS NULL OR @TARGET_KHOA IS NULL OR RTRIM(@CALLER_KHOA) <> RTRIM(@TARGET_KHOA)
        BEGIN
            RAISERROR(N'Bạn chỉ được phép tạo tài khoản cho giảng viên thuộc khoa của mình!', 16, 1);
            RETURN 5;
        END
    END
    
    -- Kiểm tra login đã tồn tại chưa
    IF EXISTS(SELECT 1 FROM sys.server_principals WHERE name = @LGNAME)
    BEGIN
        RAISERROR(N'Tên tài khoản (Login Name) đã tồn tại trong SQL Server!', 16, 1);
        RETURN 1;
    END
    
    -- Kiểm tra giảng viên đã có tài khoản (User) trong DB chưa
    IF EXISTS(SELECT 1 FROM sys.database_principals WHERE name = @USRNAME)
    BEGIN
        RAISERROR(N'Giảng viên này đã có tài khoản truy cập trong cơ sở dữ liệu!', 16, 1);
        RETURN 2;
    END
    
    -- Tạo login, user và gán quyền
    DECLARE @sql NVARCHAR(MAX);
    BEGIN TRY
        SET @sql = 'CREATE LOGIN [' + @LGNAME + '] WITH PASSWORD = N''' + @PASS + ''', DEFAULT_DATABASE = [QLDSV_HTC], CHECK_POLICY = OFF';
        EXEC sp_executesql @sql;
        
        SET @sql = 'CREATE USER [' + @USRNAME + '] FOR LOGIN [' + @LGNAME + ']';
        EXEC sp_executesql @sql;
        
        SET @sql = 'ALTER ROLE [' + @ROLE + '] ADD MEMBER [' + @USRNAME + ']';
        EXEC sp_executesql @sql;
        
        -- Gán các quyền select cơ bản cho user mới
        SET @sql = 'GRANT EXECUTE ON SP_DANGNHAP_GV TO [' + @USRNAME + ']'; EXEC sp_executesql @sql;
        SET @sql = 'GRANT SELECT ON [dbo].[GIANGVIEN] TO [' + @USRNAME + ']'; EXEC sp_executesql @sql;
        SET @sql = 'GRANT SELECT ON [dbo].[KHOA] TO [' + @USRNAME + ']'; EXEC sp_executesql @sql;
        SET @sql = 'GRANT SELECT ON [dbo].[LOP] TO [' + @USRNAME + ']'; EXEC sp_executesql @sql;
        SET @sql = 'GRANT SELECT ON [dbo].[SINHVIEN] TO [' + @USRNAME + ']'; EXEC sp_executesql @sql;
        SET @sql = 'GRANT SELECT ON [dbo].[LOPTINCHI] TO [' + @USRNAME + ']'; EXEC sp_executesql @sql;
        SET @sql = 'GRANT SELECT ON [dbo].[DANGKY] TO [' + @USRNAME + ']'; EXEC sp_executesql @sql;
        SET @sql = 'GRANT SELECT ON [dbo].[MONHOC] TO [' + @USRNAME + ']'; EXEC sp_executesql @sql;
        
        RETURN 0;
    END TRY
    BEGIN CATCH
        DECLARE @ErrMsg NVARCHAR(4000), @ErrSeverity INT, @ErrState INT;
        SELECT @ErrMsg = ERROR_MESSAGE(), @ErrSeverity = ERROR_SEVERITY(), @ErrState = ERROR_STATE();
        RAISERROR(@ErrMsg, @ErrSeverity, @ErrState);
        RETURN 9;
    END CATCH
END
GO
GRANT EXECUTE ON SP_TAOTAIKHOAN TO PUBLIC
GO
PRINT N'Đã tạo SP_TAOTAIKHOAN'
GO

-- ------------------------------------------------------------
-- SP_XOATAIKHOAN: Xóa login, user của giảng viên
-- ------------------------------------------------------------
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'SP_XOATAIKHOAN' AND type = 'P')
    DROP PROCEDURE SP_XOATAIKHOAN
GO
CREATE PROCEDURE SP_XOATAIKHOAN
    @LGNAME VARCHAR(50),
    @USRNAME VARCHAR(50)
WITH EXECUTE AS OWNER
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ORIG_LOGIN NVARCHAR(128) = ORIGINAL_LOGIN();
    DECLARE @CALLER_MAGV NVARCHAR(10) = RTRIM(@ORIG_LOGIN);
    
    DECLARE @IS_PGV BIT = 0;
    DECLARE @IS_KHOA BIT = 0;
    
    IF EXISTS (
        SELECT 1 FROM sys.database_role_members RM 
        JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id 
        JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id 
        WHERE R.name = 'PGV' AND U.name = @CALLER_MAGV
    )
        SET @IS_PGV = 1;
        
    IF EXISTS (
        SELECT 1 FROM sys.database_role_members RM 
        JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id 
        JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id 
        WHERE R.name = 'KHOA' AND U.name = @CALLER_MAGV
    )
        SET @IS_KHOA = 1;
        
    IF IS_SRVROLEMEMBER('sysadmin', @ORIG_LOGIN) = 1
        SET @IS_PGV = 1;
        
    IF @IS_PGV = 0 AND @IS_KHOA = 0
    BEGIN
        RAISERROR(N'Bạn không có quyền thực hiện chức năng này!', 16, 1);
        RETURN 3;
    END

    -- Nếu là KHOA, chỉ được xóa tài khoản của giảng viên thuộc cùng khoa
    IF @IS_KHOA = 1
    BEGIN
        DECLARE @CALLER_KHOA NCHAR(10);
        DECLARE @TARGET_KHOA NCHAR(10);
        
        SELECT @CALLER_KHOA = MAKHOA FROM GIANGVIEN WHERE MAGV = @CALLER_MAGV;
        SELECT @TARGET_KHOA = MAKHOA FROM GIANGVIEN WHERE MAGV = @USRNAME;
        
        IF @CALLER_KHOA IS NULL OR @TARGET_KHOA IS NULL OR RTRIM(@CALLER_KHOA) <> RTRIM(@TARGET_KHOA)
        BEGIN
            RAISERROR(N'Bạn chỉ được phép xóa tài khoản của giảng viên thuộc khoa của mình!', 16, 1);
            RETURN 5;
        END
        
        -- Không được phép xóa tài khoản PGV
        IF EXISTS (
            SELECT 1 FROM sys.database_role_members RM 
            JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id 
            JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id 
            WHERE R.name = 'PGV' AND U.name = @USRNAME
        )
        BEGIN
            RAISERROR(N'Tài khoản thuộc Khoa không có quyền xóa tài khoản của nhóm PGV!', 16, 1);
            RETURN 6;
        END
    END

    -- Kiểm tra giảng viên được phân công giảng dạy chưa

    IF EXISTS (SELECT 1 FROM LOPTINCHI WHERE MAGV = @USRNAME)
    BEGIN
        RAISERROR(N'Không thể xóa tài khoản: Giảng viên đã được phân công dạy cho ít nhất 1 lớp tín chỉ!', 16, 1);
        RETURN 7;
    END

    -- Kiểm tra giảng viên đã nhập điểm cho lớp nào chưa
    IF EXISTS (
        SELECT 1 FROM DANGKY DK 
        JOIN LOPTINCHI LTC ON DK.MALTC = LTC.MALTC 
        WHERE LTC.MAGV = @USRNAME 
          AND (DK.DIEM_CC IS NOT NULL OR DK.DIEM_GK IS NOT NULL OR DK.DIEM_CK IS NOT NULL)
    )
    BEGIN
        RAISERROR(N'Không thể xóa tài khoản: Giảng viên đã nhập điểm cho ít nhất 1 lớp tín chỉ!', 16, 1);
        RETURN 8;
    END

    -- Kiểm tra user có tồn tại không
    IF NOT EXISTS(SELECT 1 FROM sys.database_principals WHERE name = @USRNAME)
    BEGIN
        RAISERROR(N'Tài khoản người dùng (User) không tồn tại trong cơ sở dữ liệu!', 16, 1);
        RETURN 1;
    END

    
    DECLARE @sql NVARCHAR(MAX);
    BEGIN TRY
        -- Xóa user trong database trước
        SET @sql = 'DROP USER [' + @USRNAME + ']';
        EXEC sp_executesql @sql;
        
        -- Xóa login trên server
        IF EXISTS(SELECT 1 FROM sys.server_principals WHERE name = @LGNAME)
        BEGIN
            SET @sql = 'DROP LOGIN [' + @LGNAME + ']';
            EXEC sp_executesql @sql;
        END
        
        RETURN 0;
    END TRY
    BEGIN CATCH
        DECLARE @ErrMsg NVARCHAR(4000), @ErrSeverity INT, @ErrState INT;
        SELECT @ErrMsg = ERROR_MESSAGE(), @ErrSeverity = ERROR_SEVERITY(), @ErrState = ERROR_STATE();
        RAISERROR(@ErrMsg, @ErrSeverity, @ErrState);
        RETURN 9;
    END CATCH
END
GO
GRANT EXECUTE ON SP_XOATAIKHOAN TO PUBLIC
GO
PRINT N'Đã tạo SP_XOATAIKHOAN'
GO
