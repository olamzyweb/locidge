@echo off
setlocal

cd /d "%~dp0.."

echo Building Locidge with PyInstaller...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name Locidge ^
  --icon "packaging\locidge.ico" ^
  --add-data "templates;templates" ^
  server.py

if errorlevel 1 (
  echo.
  echo Build failed.
  exit /b 1
)

echo.
echo Build complete. Executable created at dist\Locidge.exe
exit /b 0
