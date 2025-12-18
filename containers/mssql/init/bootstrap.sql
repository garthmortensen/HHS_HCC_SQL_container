-- bootstrap.sql
--
-- This file is meant to be run by `sqlcmd` (a SQL Server CLI tool), not by SSMS
-- as a normal query window script.
--
-- Key idea: this is a *driver* script.
-- - It makes sure the target database exists.
-- - It switches the session into that database.
-- - It then *includes* (loads) a bunch of other .sql files using sqlcmd's `:r`.
--
-- Expected usage (how the container runs it):
--   sqlcmd -d master -v DB_NAME="<your_db>" -i /init/bootstrap.sql
--
-- sqlcmd directives you’ll see below:
-- - `:setvar NAME "value"` sets a sqlcmd variable (only inside sqlcmd).
-- - `$(NAME)` is how you reference that variable later in the script.
-- - `:r "path"` reads/executes another file *as if its contents were pasted here*.
--
-- Provide a default DB name if `-v DB_NAME=...` is not passed.
:setvar DB_NAME "edge"

-- T-SQL from here down (runs on SQL Server).
-- NOCOUNT reduces "(X rows affected)" noise in logs.
SET NOCOUNT ON;

-- `$(DB_NAME)` is replaced by sqlcmd *before* SQL Server runs the script.
-- Example: if DB_NAME is "ra", then this becomes: N'ra'
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

-- `GO` is not T-SQL; it's a batch separator understood by tools like sqlcmd.
-- Think of it as: "send everything up to here to SQL Server now".

USE [$(DB_NAME)];
GO

-- Provision an application login/user (requested: riskadjustment / riskadjustment).
-- Note: Password policy is enforced by SQL Server; if it rejects this password,
-- change it here (and in your client connection settings).
IF SUSER_ID(N'riskadjustment') IS NULL
BEGIN
    PRINT N'Creating server login [riskadjustment]...';
    CREATE LOGIN [riskadjustment] WITH PASSWORD = N'riskadjustment', CHECK_POLICY = OFF, CHECK_EXPIRATION = OFF;
END
ELSE
BEGIN
    PRINT N'Server login [riskadjustment] already exists.';
END
GO

IF USER_ID(N'riskadjustment') IS NULL
BEGIN
    PRINT N'Creating database user [riskadjustment]...';
    CREATE USER [riskadjustment] FOR LOGIN [riskadjustment] WITH DEFAULT_SCHEMA = [dbo];
END
ELSE
BEGIN
    PRINT N'Database user [riskadjustment] already exists.';
END
GO

-- Give broad rights for local dev use.
ALTER ROLE [db_owner] ADD MEMBER [riskadjustment];
GO

-- Switch the connection into the target DB so the included scripts create tables
-- in the right place.

-- Include/execute the table creation + reference table scripts.
-- `:r` is a sqlcmd include; the path is inside the container.
PRINT 'Loading Input Tables...';
:r "/workspace/Table-Load-Scripts/2 - Input Table Creation.sql"

-- Note: Reference tables (Factors, DX Mappings, etc.) are now loaded via 'dbt seed'
-- and are no longer loaded here.

PRINT 'Bootstrap complete.';
GO
