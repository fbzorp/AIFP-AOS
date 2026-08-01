@echo off
REM 
REM generate_ssl_cert.bat - Generate self-signed SSL certificates for development (Windows)
REM 
REM WARNING: These certificates are for development/testing only!
REM They should NEVER be used in production or committed to git.
REM For production, use Let's Encrypt/certbot or a proper CA.
REM
REM Usage: generate_ssl_cert.bat [domain]
REM Example: generate_ssl_cert.bat staging.aifp-aos.local

setlocal enabledelayedexpansion

REM Configuration
set "DOMAIN=%~1"
if "%DOMAIN%"=="" set "DOMAIN=staging.aifp-aos.local"
set "CERT_DIR=nginx\ssl"
set "DAYS_VALID=365"

echo ========================================
echo SSL Certificate Generator (Dev Only)
echo ========================================
echo.

REM Warning message
echo WARNING: This generates self-signed certificates for development only!
echo Do NOT use these in production or commit them to git.
echo.

REM Confirm
set /p CONTINUE="Continue? (y/N): "
if /i not "%CONTINUE%"=="y" (
    echo Aborted.
    exit /b 1
)

REM Generate the certificate using Python
echo Generating self-signed certificate for: %DOMAIN%
echo Valid for: %DAYS_VALID% days
echo.

python scripts\generate_ssl_cert.py %DOMAIN% --cert-dir %CERT_DIR% --days %DAYS_VALID%

if errorlevel 1 (
    echo.
    echo ERROR: Failed to generate certificates.
    exit /b 1
)

echo.
echo [SUCCESS] Certificates generated successfully!
echo.
echo The nginx\ssl directory is in .gitignore, so these won't be committed.
echo.
echo For production, use Let's Encrypt:
echo   sudo certbot certonly --standalone -d your-domain.com
echo   sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
echo   sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

endlocal
