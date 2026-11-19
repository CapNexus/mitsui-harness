@echo off
rem Start Harness Studio (harness/studio) and open it in the browser.
rem Usage: studio            (from the repo root, PowerShell or cmd, or double-click)
rem        studio 8780       (another port)
setlocal
cd /d "%~dp0"
set "AEW_AUTO_APPROVE=1"
if not "%~1"=="" set "STUDIO_PORT=%~1"
if "%STUDIO_PORT%"=="" set "STUDIO_PORT=8765"
if not defined STUDIO_NO_BROWSER start "" /b cmd /c "timeout /t 4 /nobreak >nul & start http://127.0.0.1:%STUDIO_PORT%"
uv run --with-requirements harness/studio/requirements.txt python harness/studio/server.py
endlocal
