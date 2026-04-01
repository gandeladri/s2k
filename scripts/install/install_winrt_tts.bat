@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_winrt_tts.ps1"
exit /b %errorlevel%
