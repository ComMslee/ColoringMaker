@echo off
echo ===================================
echo   ColoringMaker Build
echo ===================================
echo.

cd /d "%~dp0\.."

where py >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python not found.
    pause
    exit /b 1
)

py -m PyInstaller --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing PyInstaller...
    py -m pip install pyinstaller
)

echo [1/4] Preparing icon...
copy /y "src\res\icon.ico" "%TEMP%\coloring_icon.ico" >nul

echo [2/4] Building exe...
py -m PyInstaller --onefile --windowed --name "ColoringMaker" --icon "%TEMP%\coloring_icon.ico" "src\coloring_maker.py" --distpath "build" --workpath "build\temp" --specpath "build\temp" -y

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Build FAILED!
    del "%TEMP%\coloring_icon.ico" 2>nul
    pause
    exit /b 1
)

echo.
echo [3/4] Cleanup...
if exist "build\temp" rd /s /q "build\temp"
del "%TEMP%\coloring_icon.ico" 2>nul

echo [4/4] Copy to release...
copy /y "build\ColoringMaker.exe" "ColoringMaker.exe" >nul

echo.
echo ===================================
echo   Done! -^> ColoringMaker.exe
echo ===================================
pause
