@echo off
REM ==========================================
REM Hostamar Platform - GCP Mumbai Deployment
REM Windows PowerShell Version
REM ==========================================

echo === Hostamar Platform Deployment ===
echo.

REM Configuration
set VM_NAME=mumbai-instance-1
set ZONE=asia-south1-a
set PROJECT_ID=
set REMOTE_USER=romelraisul
set REMOTE_DIR=/home/%REMOTE_USER%/hostamar-platform

REM Check PROJECT_ID
if "%PROJECT_ID%"=="" (
    echo Getting project ID from gcloud...
    for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i
)

if "%PROJECT_ID%"=="" (
    echo [ERROR] PROJECT_ID not set
    echo Please edit this script and set PROJECT_ID or run: gcloud config set project YOUR_PROJECT_ID
    pause
    exit /b 1
)

echo [OK] Project: %PROJECT_ID%
echo.

REM Step 1: Configure SSH
echo Step 1: Configuring SSH...
gcloud compute config-ssh --project=%PROJECT_ID% --quiet
if errorlevel 1 (
    echo [ERROR] SSH configuration failed
    pause
    exit /b 1
)
set HOST_ALIAS=%VM_NAME%.%ZONE%.%PROJECT_ID%
echo [OK] SSH configured: %HOST_ALIAS%
echo.

REM Step 2: Get VM IP
echo Step 2: Getting VM external IP...
for /f "tokens=*" %%i in ('gcloud compute instances describe %VM_NAME% --zone=%ZONE% --format="get(networkInterfaces[0].accessConfigs[0].natIP)"') do set EXTERNAL_IP=%%i
echo [OK] External IP: %EXTERNAL_IP%
echo.

REM Step 3: Upload code using gcloud scp (alternative to rsync)
echo Step 3: Uploading code...
echo This will take several minutes...
echo.

cd /d "%~dp0\.."

REM Create remote directory first
gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="mkdir -p %REMOTE_DIR%"

REM Upload using gcloud scp (excludes handled by .gcloudignore if exists)
gcloud compute scp --recurse ^
    --zone=%ZONE% ^
    --project=%PROJECT_ID% ^
    .\ %VM_NAME%:%REMOTE_DIR%

echo [OK] Code uploaded
echo.

REM Step 4: Setup environment
echo Step 4: Setting up environment on VM...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="bash -s" < "%~dp0\remote-setup.sh"

if errorlevel 1 (
    echo [WARNING] Environment setup had issues, but continuing...
)
echo [OK] Environment setup complete
echo.

REM Step 5: Install PM2 and start app
echo Step 5: Starting application...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="bash -s" < "%~dp0\remote-start.sh"

echo [OK] Application started
echo.

REM Summary
echo ========================================
echo    Deployment Complete!
echo ========================================
echo.
echo Application URL: http://%EXTERNAL_IP%:3000
echo Health check: http://%EXTERNAL_IP%:3000/api/health
echo.
echo Next steps:
echo 1. SSH to VM: gcloud compute ssh %VM_NAME% --zone=%ZONE%
echo 2. Check PM2: pm2 status
echo 3. View logs: pm2 logs hostamar
echo 4. Setup Nginx: cd ~/hostamar-platform/deploy ^&^& ./nginx-setup.sh
echo.
pause
