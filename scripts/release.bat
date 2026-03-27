@echo off
echo ===================================
echo   ColoringMaker Release
echo ===================================
echo.

cd /d "%~dp0\.."

:: Read current version
set /p CURRENT_VER=<VERSION
echo Current version: %CURRENT_VER%
echo.

:: Ask for new version
set /p NEW_VER="New version (e.g. 1.1.0): "
if "%NEW_VER%"=="" (
    echo [!] No version entered.
    pause
    exit /b 1
)

:: Update VERSION file
echo %NEW_VER%> VERSION

:: Git add, commit, tag, push
echo.
echo [1/4] Committing version %NEW_VER%...
git add -A
git commit -m "Release v%NEW_VER%"

echo [2/4] Creating tag v%NEW_VER%...
git tag v%NEW_VER%

echo [3/4] Pushing to origin...
git push origin main

echo [4/4] Pushing tag...
git push origin v%NEW_VER%

echo.
echo ===================================
echo   Done! GitHub Actions will build
echo   and create the release.
echo   Check: https://github.com/ComMslee/ColoringMaker/actions
echo ===================================
pause
