@echo off
cd /d c:\Users\romel\OneDrive\Documents\aiauto\hostamar-platform

echo ========================================
echo Hostamar Platform Setup
echo ========================================
echo.

echo [1/5] Cleaning...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del /f package-lock.json
if exist .next rmdir /s /q .next
echo OK
echo.

echo [2/5] Installing dependencies (this will take 2-3 minutes)...
call npm install --legacy-peer-deps
if errorlevel 1 goto error
echo OK
echo.

echo [3/5] Creating .env.local...
if not exist .env.local (
    echo DATABASE_URL="postgresql://user:password@localhost:5432/hostamar" > .env.local
    echo GITHUB_TOKEN="your-token-here" >> .env.local
    echo NEXTAUTH_SECRET="change-me" >> .env.local
    echo NEXTAUTH_URL="http://localhost:3000" >> .env.local
)
echo OK
echo.

echo [4/5] Building production bundle...
set NODE_ENV=production
call npm run build
if errorlevel 1 goto error
echo OK
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Update .env.local with your GitHub token
echo   2. Run: npm run dev
echo   3. Visit: http://localhost:3000
echo.
goto end

:error
echo.
echo ========================================
echo Setup failed! Check errors above.
echo ========================================
exit /b 1

:end
