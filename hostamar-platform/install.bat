@echo off
echo ========================================
echo Hostamar Platform - Simple Setup
echo ========================================
echo.

cd /d c:\Users\romel\OneDrive\Documents\aiauto\hostamar-platform

echo [1/4] Cleaning...
if exist node_modules rmdir /s /q node_modules 2>nul
if exist package-lock.json del /f package-lock.json 2>nul
if exist .next rmdir /s /q .next 2>nul
echo Done
echo.

echo [2/4] Installing (2 minutes)...
call npm install
if errorlevel 1 (
    echo.
    echo ERROR: npm install failed!
    echo Try running in PowerShell instead:
    echo   cd c:\Users\romel\OneDrive\Documents\aiauto\hostamar-platform
    echo   npm install
    pause
    exit /b 1
)
echo Done
echo.

echo [3/4] Building...
set NODE_ENV=production
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo Done
echo.

echo ========================================
echo SUCCESS! Platform is ready!
echo ========================================
echo.
echo To start: npm run dev
echo Then visit: http://localhost:3000
echo.
pause
