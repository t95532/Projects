@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher was not found. Install Python 3.11 or newer.
  pause
  exit /b 1
)

if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Starting Video Studio local render engine...
echo Keep this window open while using the web app.
echo Health check: http://127.0.0.1:8765/health
python server.py
pause
