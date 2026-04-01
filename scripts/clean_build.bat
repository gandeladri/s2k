@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0clean_build.ps1"

exit /b %errorlevel%
