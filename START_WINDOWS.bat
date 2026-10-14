@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    start "" "http://localhost:8000/"
    py -m http.server 8000
    goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
    start "" "http://localhost:8000/"
    python -m http.server 8000
    goto :end
)
echo Python is not installed. Opening index.html directly.
start "" "%~dp0index.html"
:end
pause
