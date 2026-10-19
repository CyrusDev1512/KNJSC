@echo off
setlocal
cd /d "%~dp0.."
python scripts\kiem-tai-kn-crm.py %*
exit /b %errorlevel%
