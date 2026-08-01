@echo off
REM Automated database backup script for AIFP-AOS (Windows)
REM This script creates daily backups with retention policies

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set BACKUP_DIR=%PROJECT_DIR%\backups
set RETENTION_DAYS=7
set DB_NAME=aifp_dev
set DB_USER=aifp

REM Create simple timestamp
set YEAR=%date:~10,4%
set MONTH=%date:~4,2%
set DAY=%date:~7,2%
set HOUR=%time:~0,2%
set MINUTE=%time:~3,2%
set SECOND=%time:~6,2%
set TIMESTAMP=%YEAR%%MONTH%%DAY%_%HOUR%%MINUTE%%SECOND%
set BACKUP_FILE=%BACKUP_DIR%\aifp_backup_%TIMESTAMP%.sql
set LOG_FILE=%PROJECT_DIR%\logs\aifp_backup.log

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

REM Logging function
echo [%date% %time%] Starting backup process >> "%LOG_FILE%"

REM Perform backup
echo [%date% %time%] Creating backup: %BACKUP_FILE% >> "%LOG_FILE%"
cd "%PROJECT_DIR%"
docker compose -f docker-compose.dev.yml exec -T postgres pg_dump -U %DB_USER% -d %DB_NAME% > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Backup created successfully: %BACKUP_FILE% >> "%LOG_FILE%"
    
    REM Get backup size
    for %%A in ("%BACKUP_FILE%") do set BACKUP_SIZE=%%~zA
    set /a BACKUP_SIZE_KB=%BACKUP_SIZE%/1024
    echo [%date% %time%] Backup size: %BACKUP_SIZE_KB% KB >> "%LOG_FILE%"
    
    REM Remove old backups (retention policy)
    echo [%date% %time%] Cleaning up backups older than %RETENTION_DAYS% days >> "%LOG_FILE%"
    forfiles /p "%BACKUP_DIR%" /m aifp_backup_*.sql /d -%RETENTION_DAYS% /c "cmd /c del @path" 2>nul
    
    REM Count remaining backups
    set BACKUP_COUNT=0
    for %%A in ("%BACKUP_DIR%\aifp_backup_*.sql") do set /a BACKUP_COUNT+=1
    echo [%date% %time%] Total backups after cleanup: %BACKUP_COUNT% >> "%LOG_FILE%"
    
    echo [%date% %time%] Backup process completed successfully >> "%LOG_FILE%"
    exit /b 0
) else (
    echo [%date% %time%] ERROR: Backup failed >> "%LOG_FILE%"
    exit /b 1
)