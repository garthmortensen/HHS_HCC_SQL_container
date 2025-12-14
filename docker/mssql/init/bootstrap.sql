:setvar DB_NAME "RiskAdjustment"

-- bootstrap.sql
-- Runs under sqlcmd. Expected usage:
--   sqlcmd -d master -v DB_NAME="<your_db>" -i /init/bootstrap.sql

SET NOCOUNT ON;

DECLARE @db sysname = N'$(DB_NAME)';

IF DB_ID(@db) IS NULL
BEGIN
    PRINT N'Creating database [' + @db + N']...';
    DECLARE @create nvarchar(max) = N'CREATE DATABASE [' + REPLACE(@db, ']', ']]') + N'];';
    EXEC sys.sp_executesql @create;
END
ELSE
BEGIN
    PRINT N'Database [' + @db + N'] already exists.';
END
GO

USE [$(DB_NAME)];
GO

:r "/workspace/Table-Load-Scripts/2 - Input Table Creation.sql"

PRINT 'Loading CSR_Factors_Table.sql'
GO
:r "/workspace/Table-Load-Scripts/CSR_Factors_Table.sql"
PRINT 'Loading dbo.DX_Mapping_Table.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.DX_Mapping_Table.Table.sql"
PRINT 'Loading dbo.Federal_Age_Curve.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.Federal_Age_Curve.Table.sql"
PRINT 'Loading dbo.GCF.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.GCF.Table.sql"
PRINT 'Loading dbo.HCPCSRXC.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.HCPCSRXC.Table.sql"
PRINT 'Loading dbo.metal_level_mapping.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.metal_level_mapping.Table.sql"
PRINT 'Loading dbo.NDC_RXC.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.NDC_RXC.Table.sql"
PRINT 'Loading dbo.Rating_Area_CountyMap.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.Rating_Area_CountyMap.Table.sql"
PRINT 'Loading dbo.RiskScoreFactors.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.RiskScoreFactors.Table.sql"
PRINT 'Loading dbo.ServiceCodeReference.Table.sql'
GO
:r "/workspace/Table-Load-Scripts/dbo.ServiceCodeReference.Table.sql"
PRINT 'Loading statewide_factors.sql'
GO
:r "/workspace/Table-Load-Scripts/statewide_factors.sql"
