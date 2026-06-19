USE QLDSV_HTC;
GO

-- 1. Kiểm tra và tạo role PGV nếu chưa tồn tại
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'PGV' AND type = 'R')
BEGIN
    CREATE ROLE PGV;
    PRINT N'Đã tạo Role PGV.';
END
ELSE
BEGIN
    PRINT N'Role PGV đã tồn tại.';
END
GO

-- 2. Đảm bảo GV01 đã có trong Database (Là database user mapped với Login)
-- Giả sử Login GV01 đã tồn tại và User GV01 đã được tạo
IF EXISTS (SELECT * FROM sys.database_principals WHERE name = 'GV01' AND type IN ('S', 'U'))
BEGIN
    -- Gán GV01 vào nhóm PGV
    -- (Đối với SQL Server < 2012 dùng sp_addrolemember 'PGV', 'GV01')
    ALTER ROLE PGV ADD MEMBER [GV01];
    PRINT N'Đã thêm GV01 vào Role PGV.';
    
    -- Khuyến cáo: Nên gỡ GV01 khỏi db_owner nếu GV01 bị gán nhầm để tránh dư thừa quyền hạn (Principle of least privilege)
    -- ALTER ROLE db_owner DROP MEMBER [GV01];
END
ELSE
BEGIN
    PRINT N'Lỗi: Không tìm thấy Database User GV01.';
END
GO

-- 3. Kiểm tra lại Role hiện tại của GV01
SELECT 
    U.name AS UserName, 
    R.name AS RoleName
FROM sys.database_role_members RM
JOIN sys.database_principals R ON RM.role_principal_id = R.principal_id
JOIN sys.database_principals U ON RM.member_principal_id = U.principal_id
WHERE U.name = 'GV01';
GO
