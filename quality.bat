@echo off
REM Quality script for Windows - equivalent to 'make quality'

echo Running comprehensive code quality checks...

echo.
echo =============================================================
echo   Running Code Formatting
echo =============================================================
C:/Users/romel/.venv/Scripts/python.exe scripts/format.py
set FORMAT_EXIT=%ERRORLEVEL%

echo.
echo =============================================================
echo   Running Code Linting
echo =============================================================
C:/Users/romel/.venv/Scripts/python.exe scripts/lint.py
set LINT_EXIT=%ERRORLEVEL%

echo.
echo =============================================================
echo   FINAL SUMMARY
echo =============================================================

if %FORMAT_EXIT%==0 (
    echo 🎨 Formatting: ✅ PASSED
) else (
    echo 🎨 Formatting: ❌ FAILED
)

if %LINT_EXIT%==0 (
    echo 🔍 Linting:    ✅ PASSED
) else (
    echo 🔍 Linting:    ❌ FAILED
)

if %FORMAT_EXIT%==0 if %LINT_EXIT%==0 (
    echo.
    echo 🎉 All code quality checks passed! Your code is ready to go! 🚀
    exit /b 0
) else (
    echo.
    echo ⚠️  Some code quality checks failed. Please review the output above.
    echo.
    echo 💡 Next steps:
    if not %FORMAT_EXIT%==0 echo   1. Review formatting errors and fix manually if needed
    if not %LINT_EXIT%==0 echo   2. Review linting errors and fix the issues
    echo   3. Re-run this script to verify fixes
    exit /b 1
)
