@echo off
chcp 65001 >nul
echo ===================================
echo   ColoringMaker 빌드
echo ===================================
echo.

cd /d "%~dp0"

set ICON_PATH=%cd%\src\res\icon.ico

echo [1/3] 빌드 시작...
py -m PyInstaller --onefile --windowed --name "ColoringMaker" --icon "%ICON_PATH%" "src\coloring_maker.py" --distpath "build" --workpath "build\temp" --specpath "build\temp" -y

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] 빌드 실패!
    pause
    exit /b 1
)

echo.
echo [2/3] 임시 파일 정리...
rd /s /q "build\temp" 2>nul

echo [3/3] 릴리즈 복사...
copy /y "build\ColoringMaker.exe" "ColoringMaker.exe" >nul

echo.
echo ===================================
echo   빌드 완료!
echo   build\ColoringMaker.exe
echo   ColoringMaker.exe (릴리즈)
echo ===================================
pause
