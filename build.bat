@echo off
REM Build script for Windows
REM Creates a standalone executable for osu! Beatmap Downloader

echo ============================================
echo   osu! Beatmap Downloader - Build Script
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Build the executable
echo.
echo Building executable...
echo This may take a few minutes...
echo.
pyinstaller osu_downloader.spec --clean

REM Check if build was successful
if exist "dist\OsuBeatmapDownloader.exe" (
    echo.
    echo ============================================
    echo   BUILD SUCCESSFUL!
    echo ============================================
    echo.
    echo Executable created at: dist\OsuBeatmapDownloader.exe
    echo.
    echo You can now distribute this file to users.
    echo They can run it without installing Python!
) else (
    echo.
    echo ============================================
    echo   BUILD FAILED
    echo ============================================
    echo.
    echo Check the output above for errors.
)

REM Deactivate virtual environment
deactivate

pause
